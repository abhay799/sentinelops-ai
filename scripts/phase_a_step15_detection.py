from __future__ import annotations

import argparse
import json
import multiprocessing
import platform
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import polars as pl
from sklearn.metrics import average_precision_score, roc_auc_score

from sentinelops.evaluation.rcaeval_runner import (
    evaluate_detection_case,
    metrics_from_counts,
    summarize_detection_case,
)

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ob")
CASE_OUT = OUT / "detection_cases"
BOOTSTRAPS = 10_000
SEED = 42
def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()


def case_metadata() -> list[dict[str, object]]:
    frame = pl.read_parquet(ROOT / "cases.parquet")
    return (
        frame.filter(pl.col("dataset") == "RE2-OB")
        .sort("case")
        .select(
            [
                "case",
                "root_cause_service",
                "fault",
                "repetition",
                "inject_time",
            ]
        )
        .to_dicts()
    )


def run_case(meta: dict[str, object]) -> dict[str, object]:
    case_id = str(meta["case"])
    started = time.perf_counter()
    try:
        case = ROOT / case_id
        metrics = pl.read_parquet(case / "metrics.parquet")
        inject = int((case / "inject_time.txt").read_text().strip())
        result = evaluate_detection_case(metrics, inject)
        summary = summarize_detection_case(result, inject)
        payload: dict[str, object] = {
            "status": "ok",
            "case_id": case_id,
            "root_cause_service": meta["root_cause_service"],
            "fault": meta["fault"],
            "repetition": meta["repetition"],
            "inject_time": inject,
            "calibration_rows": result.calibration_rows,
            "normal_evaluation_rows": (
                result.pre_injection_rows - result.calibration_rows
            ),
            "fault_rows": result.fault_rows,
            **summary,
        }
    except Exception as exc:
        payload = {
            "status": "failed",
            "case_id": case_id,
            "root_cause_service": meta["root_cause_service"],
            "fault": meta["fault"],
            "repetition": meta["repetition"],
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
    payload["runtime_seconds"] = time.perf_counter() - started
    return payload


def save_case(payload: dict[str, object]) -> None:
    CASE_OUT.mkdir(parents=True, exist_ok=True)
    path = CASE_OUT / f"{payload['case_id']}.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def add_counts(
    left: dict[str, int],
    right: dict[str, int],
) -> dict[str, int]:
    return {
        key: int(left.get(key, 0) + right.get(key, 0))
        for key in ("tp", "fp", "tn", "fn")
    }


def aggregate_counts(
    cases: list[dict[str, object]],
    field: str,
) -> dict[str, int]:
    total = {"tp": 0, "fp": 0, "tn": 0, "fn": 0}
    for case in cases:
        total = add_counts(total, case[field])
    return total
def window_scores(
    cases: list[dict[str, object]],
) -> tuple[np.ndarray, np.ndarray]:
    labels: list[int] = []
    scores: list[float] = []
    for case in cases:
        labels.extend([0, 1])
        scores.extend(
            [
                float(case["normal_window_score"]),
                float(case["fault_window_score"]),
            ]
        )
    return np.asarray(labels), np.asarray(scores)


def metric_bundle(
    cases: list[dict[str, object]],
) -> dict[str, object]:
    timestamp_counts = aggregate_counts(cases, "timestamp_confusion")
    window_counts = aggregate_counts(cases, "window_confusion")
    labels, scores = window_scores(cases)
    detected_delays = [
        float(case["detection_delay_seconds"])
        for case in cases
        if case["detection_delay_seconds"] is not None
    ]
    return {
        "timestamp_confusion": timestamp_counts,
        "timestamp_metrics": metrics_from_counts(timestamp_counts),
        "window_confusion": window_counts,
        "window_metrics": metrics_from_counts(window_counts),
        "window_roc_auc": float(roc_auc_score(labels, scores)),
        "window_pr_auc": float(average_precision_score(labels, scores)),
        "detection_rate": len(detected_delays) / len(cases),
        "median_delay_seconds": (
            float(np.median(detected_delays))
            if detected_delays
            else None
        ),
    }
def _metric_arrays(
    totals: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    tp = totals[:, 0]
    fp = totals[:, 1]
    fn = totals[:, 3]
    precision = np.divide(
        tp,
        tp + fp,
        out=np.zeros_like(tp, dtype=float),
        where=(tp + fp) != 0,
    )
    recall = np.divide(
        tp,
        tp + fn,
        out=np.zeros_like(tp, dtype=float),
        where=(tp + fn) != 0,
    )
    f1 = np.divide(
        2.0 * precision * recall,
        precision + recall,
        out=np.zeros_like(precision),
        where=(precision + recall) != 0,
    )
    return precision, recall, f1


def _weighted_window_auc_ap(
    cases: list[dict[str, object]],
    weights: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    normal = np.asarray(
        [float(case["normal_window_score"]) for case in cases]
    )
    fault = np.asarray(
        [float(case["fault_window_score"]) for case in cases]
    )
    n = len(cases)

    comparison = (
        (fault[:, None] > normal[None, :]).astype(float)
        + 0.5
        * (fault[:, None] == normal[None, :]).astype(float)
    )
    auc = np.einsum(
        "bi,ij,bj->b",
        weights,
        comparison,
        weights,
        optimize=True,
    ) / float(n * n)

    all_scores = np.concatenate([fault, normal])
    unique_scores = np.unique(all_scores)[::-1]
    pos_groups = np.vstack(
        [(fault == score).astype(float) for score in unique_scores]
    )
    neg_groups = np.vstack(
        [(normal == score).astype(float) for score in unique_scores]
    )
    pos_weight = weights @ pos_groups.T
    neg_weight = weights @ neg_groups.T
    cum_tp = np.cumsum(pos_weight, axis=1)
    cum_fp = np.cumsum(neg_weight, axis=1)
    precision = np.divide(
        cum_tp,
        cum_tp + cum_fp,
        out=np.zeros_like(cum_tp, dtype=float),
        where=(cum_tp + cum_fp) != 0,
    )
    ap = np.sum((pos_weight / float(n)) * precision, axis=1)
    return auc, ap


def bootstrap(
    cases: list[dict[str, object]],
) -> dict[str, list[float]]:
    rng = np.random.default_rng(SEED)
    n = len(cases)
    indices = rng.integers(0, n, size=(BOOTSTRAPS, n))
    weights = np.zeros((BOOTSTRAPS, n), dtype=np.int16)
    rows = np.repeat(np.arange(BOOTSTRAPS), n)
    np.add.at(weights, (rows, indices.ravel()), 1)

    timestamp_case = np.asarray(
        [
            [
                int(case["timestamp_confusion"][key])
                for key in ("tp", "fp", "tn", "fn")
            ]
            for case in cases
        ],
        dtype=np.int64,
    )
    window_case = np.asarray(
        [
            [
                int(case["window_confusion"][key])
                for key in ("tp", "fp", "tn", "fn")
            ]
            for case in cases
        ],
        dtype=np.int64,
    )
    timestamp_totals = weights @ timestamp_case
    window_totals = weights @ window_case
    tp, tr, tf = _metric_arrays(timestamp_totals)
    wp, wr, wf = _metric_arrays(window_totals)
    auc, ap = _weighted_window_auc_ap(cases, weights)

    detected = np.asarray(
        [
            1.0 if case["detection_delay_seconds"] is not None else 0.0
            for case in cases
        ]
    )
    detection_rate = (weights @ detected) / float(n)

    delay_medians: list[float] = []
    delays = np.asarray(
        [
            np.nan
            if case["detection_delay_seconds"] is None
            else float(case["detection_delay_seconds"])
            for case in cases
        ]
    )
    for row in weights:
        expanded = np.repeat(delays[~np.isnan(delays)], row[~np.isnan(delays)])
        if len(expanded):
            delay_medians.append(float(np.median(expanded)))

    values = {
        "timestamp_precision": tp,
        "timestamp_recall": tr,
        "timestamp_f1": tf,
        "window_precision": wp,
        "window_recall": wr,
        "window_f1": wf,
        "window_roc_auc": auc,
        "window_pr_auc": ap,
        "detection_rate": detection_rate,
        "median_delay_seconds": np.asarray(delay_medians),
    }
    return {
        key: [
            float(np.percentile(series, 2.5)),
            float(np.percentile(series, 97.5)),
        ]
        for key, series in values.items()
        if len(series)
    }
def per_service_rates(
    cases: list[dict[str, object]],
) -> dict[str, object]:
    totals: dict[str, dict[str, float]] = {}
    for case in cases:
        normal_rows = int(case["normal_evaluation_rows"])
        fault_rows = int(case["fault_rows"])
        for service, metrics in case["per_service"].items():
            row = totals.setdefault(
                service,
                {
                    "normal_alerts": 0.0,
                    "normal_rows": 0.0,
                    "fault_alerts": 0.0,
                    "fault_rows": 0.0,
                },
            )
            row["normal_alerts"] += (
                float(metrics["normal_alert_rate"]) * normal_rows
            )
            row["normal_rows"] += normal_rows
            row["fault_alerts"] += (
                float(metrics["fault_alert_rate"]) * fault_rows
            )
            row["fault_rows"] += fault_rows
    return {
        service: {
            **row,
            "normal_alert_rate": row["normal_alerts"] / row["normal_rows"],
            "fault_alert_rate": row["fault_alerts"] / row["fault_rows"],
        }
        for service, row in sorted(totals.items())
    }
def per_fault(
    cases: list[dict[str, object]],
) -> dict[str, object]:
    result: dict[str, object] = {}
    for fault in sorted({str(case["fault"]) for case in cases}):
        subset = [case for case in cases if str(case["fault"]) == fault]
        result[fault] = {
            "case_count": len(subset),
            "metrics": metric_bundle(subset),
            "bootstrap_95_ci": bootstrap(subset),
        }
    return result


def always_alert_baseline(
    cases: list[dict[str, object]],
) -> dict[str, object]:
    normal_rows = sum(int(case["normal_evaluation_rows"]) for case in cases)
    fault_rows = sum(int(case["fault_rows"]) for case in cases)
    timestamp_counts = {
        "tp": fault_rows,
        "fp": normal_rows,
        "tn": 0,
        "fn": 0,
    }
    window_counts = {
        "tp": len(cases),
        "fp": len(cases),
        "tn": 0,
        "fn": 0,
    }
    return {
        "timestamp_confusion": timestamp_counts,
        "timestamp_metrics": metrics_from_counts(timestamp_counts),
        "window_confusion": window_counts,
        "window_metrics": metrics_from_counts(window_counts),
        "note": "Always predicts alert in both normal and fault windows.",
    }
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    started = time.perf_counter()
    metadata = case_metadata()
    CASE_OUT.mkdir(parents=True, exist_ok=True)

    existing: dict[str, dict[str, object]] = {}
    pending: list[dict[str, object]] = []
    for meta in metadata:
        path = CASE_OUT / f"{meta['case']}.json"
        if path.exists():
            existing[str(meta["case"])] = json.loads(path.read_text())
        else:
            pending.append(meta)

    if pending:
        with ProcessPoolExecutor(
            max_workers=args.workers,
            mp_context=multiprocessing.get_context("spawn"),
        ) as pool:
            futures = {pool.submit(run_case, meta): meta for meta in pending}
            for future in as_completed(futures):
                payload = future.result()
                save_case(payload)
                existing[str(payload["case_id"])] = payload
                print(
                    payload["case_id"],
                    payload["status"],
                    flush=True,
                )

    ordered = [existing[str(meta["case"])] for meta in metadata]
    ok = [case for case in ordered if case["status"] == "ok"]
    failed = [case for case in ordered if case["status"] != "ok"]
    aggregate = metric_bundle(ok) if ok else {}
    payload = {
        "step": 15,
        "status": "complete" if not failed else "completed_with_failures",
        "primary": "SentinelOps frozen v1 detector",
        "execution_date": "2026-10-02",
        "exact_command":
            "python scripts/phase_a_step15_detection.py --workers 4",
        "sentinelops_commit": git_head(),
        "rcaeval_revision":
            "259ea4167160256a74ad30004aa3d96a998c846e",
        "dataset_revision":
            "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
        "dataset": "RE2-OB",
        "seed": SEED,
        "bootstrap_resamples": BOOTSTRAPS,
        "python": platform.python_version(),
        "case_count_expected": len(metadata),
        "case_count_ok": len(ok),
        "case_count_failed": len(failed),
        "failed_cases": failed,
        "v1": aggregate,
        "v1_bootstrap_95_ci": bootstrap(ok) if ok else {},
        "always_alert_baseline": always_alert_baseline(ok) if ok else {},
        "per_service_alert_rates": per_service_rates(ok) if ok else {},
        "per_fault": per_fault(ok) if ok else {},
        "runtime_seconds": time.perf_counter() - started,
        "notes": [
            "Calibration rows excluded from detection metrics.",
            (
                "Window ROC-AUC/PR-AUC use max system continuous "
                "anomaly score per normal/fault window."
            ),
            "No tuning or threshold changes were performed.",
        ],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "step15_detection_summary.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
