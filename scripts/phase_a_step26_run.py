from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import polars as pl

from sentinelops.evaluation.rcaeval_baselines import (
    deterministic_random_ranking,
    pagerank_ranking,
    static_threshold_ranking,
)
from sentinelops.evaluation.rcaeval_rca import (
    graph_from_edges,
    sentinelops_continuous_ranking,
)
from sentinelops.evaluation.rcaeval_runner import (
    evaluate_detection_case,
    summarize_detection_case,
)
from sentinelops.evaluation.rcaeval_v2 import (
    compute_v2_strengths,
    sentinelops_v2_ranking,
)

RCA_ROOT = Path("/home/dell/benchmarks/RCAEval")
DATA_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ss")
ALLOW = {
    "front-end", "carts", "catalogue", "orders", "payment",
    "queue-master", "shipping", "user",
}
EDGES = (
    ("front-end", "carts"), ("orders", "carts"),
    ("front-end", "catalogue"), ("front-end", "orders"),
    ("orders", "payment"), ("orders", "shipping"),
    ("front-end", "user"), ("orders", "user"),
    ("shipping", "rabbitmq"), ("queue-master", "rabbitmq"),
    ("carts", "carts-db"), ("catalogue", "catalogue-db"),
    ("orders", "orders-db"), ("user", "user-db"),
)
METHODS = (
    "v1", "v2a", "threshold", "random", "pagerank",
    "baro", "circa", "mmbaro", "mmcirca",
)

sys.path.insert(0, str(RCA_ROOT))
from RCAEval.e2e import baro, circa  # noqa: E402


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def case_ids() -> list[str]:
    frame = pl.read_parquet(DATA_ROOT / "cases.parquet")
    ids = (
        frame.filter(pl.col("dataset") == "RE2-SS")
        .sort("case")["case"]
        .to_list()
    )
    if len(ids) != 90:
        raise RuntimeError(f"Expected 90 RE2-SS cases, found {len(ids)}")
    return ids


def filter_rows(rows: list[dict[str, object]]) -> list[str]:
    return [str(row["service"]) for row in rows if str(row["service"]) in ALLOW]


def local_rankings(case_id: str, method: str) -> dict[str, object]:
    case = DATA_ROOT / case_id
    metrics = pl.read_parquet(case / "metrics.parquet")
    inject = int((case / "inject_time.txt").read_text().strip())
    services = sorted(
        column.rsplit("_", 1)[0]
        for column in metrics.columns
        if column != "time" and "_" in column
    )
    service_set = sorted(set(services))
    graph = graph_from_edges(service_set, EDGES)

    detection = None
    v1_strengths = None
    if method in {"v1", "pagerank"}:
        detection = summarize_detection_case(
            evaluate_detection_case(metrics, inject), inject
        )
        v1_strengths = {
            service: float(values["fault_max_anomaly_strength"])
            for service, values in detection["per_service"].items()
        }

    if method == "v1":
        rows = sentinelops_continuous_ranking(
            v1_strengths, graph, max_candidates=len(v1_strengths)
        )
    elif method == "v2a":
        strengths = compute_v2_strengths(metrics, inject)
        rows, _primary = sentinelops_v2_ranking(strengths, graph, "v2a")
    elif method == "threshold":
        rows = static_threshold_ranking(metrics, inject, threshold=2.5)
    elif method == "random":
        source = static_threshold_ranking(metrics, inject, threshold=2.5)
        candidates = [str(row["service"]) for row in source]
        rows, derived_seed = deterministic_random_ranking(
            candidates, case_id=case_id, master_seed=42
        )
    elif method == "pagerank":
        rows = pagerank_ranking(
            services=v1_strengths,
            edges=list(EDGES),
            service_strengths=v1_strengths,
            damping=0.85,
        )
    else:
        raise ValueError(f"Unsupported local method: {method}")

    payload: dict[str, object] = {
        "status": "ok",
        "case_id": case_id,
        "method": method,
        "ranking": rows,
        "e3_filtered_service_ranking": filter_rows(rows),
        "ground_truth_used_for_ranking": False,
        "candidate_count": len(rows),
    }
    if method == "random":
        payload["master_seed"] = 42
        payload["derived_seed"] = derived_seed
    if method == "pagerank":
        payload["damping"] = 0.85
        payload["personalization_source"] = (
            "continuous v1 fault-window anomaly strength"
        )
    return payload


def native_service_ranking(ranks: list[str]) -> list[str]:
    out: list[str] = []
    for item in ranks:
        service = str(item).split("_")[0].replace("-db", "")
        if service not in out:
            out.append(service)
    return out


def prepare_rcaeval_case(case_id: str) -> tuple[pd.DataFrame, int]:
    case = DATA_ROOT / case_id
    data = pd.read_parquet(case / "metrics.parquet")
    data = data.loc[:, ~data.columns.str.endswith("_latency-50")]
    data = data.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    inject = int((case / "inject_time.txt").read_text().strip())
    window = 20 * 60 // 2
    normal = data[data["time"] < inject].tail(window)
    anomal = data[data["time"] >= inject].head(window)
    data = pd.concat([normal, anomal], ignore_index=True)
    data = data.rename(
        columns={
            col: col.replace("_latency-90", "_latency")
            for col in data.columns
            if col.endswith("_latency-90")
        }
    )
    return data, inject


def rcaeval_ranking(case_id: str, method: str) -> dict[str, object]:
    if method in {"mmbaro", "mmcirca"}:
        missing = ["logts.csv"]
        return {
            "status": "hard_failed",
            "case_id": case_id,
            "method": method,
            "error_type": "FrozenInputUnavailable",
            "error": (
                "Pinned RE2-SS case provides raw logs.parquet but pinned RCAEval "
                f"{method} requires preprocessed logts.csv; no pinned official "
                "raw-to-logts transform was found, and held-out preprocessing "
                "will not be invented."
            ),
            "missing_required_inputs": missing,
            "ground_truth_used_for_ranking": False,
            "e3_filtered_service_ranking": [],
        }

    data, inject = prepare_rcaeval_case(case_id)
    funcs = {"baro": baro, "circa": circa}
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        out = funcs[method](
            data.copy(deep=True),
            inject,
            dataset="re2-ss",
            anomalies=None,
            dk_select_useful=False,
            sli="front-end_latency",
            verbose=False,
            n_iter=len(data.columns) - 1,
            args=SimpleNamespace(
                root_path=str(RCA_ROOT),
                data_path=str(DATA_ROOT / case_id / "metrics.parquet"),
            ),
        )
    warning = stderr.getvalue()
    raw_ranks = [str(value) for value in out.get("ranks", [])]
    fallback = "returning the unranked column order" in warning
    if fallback:
        return {
            "status": "fallback_unranked",
            "case_id": case_id,
            "method": method,
            "fallback_detected": True,
            "fallback_reason": warning.strip(),
            "fallback_returned_feature_order": raw_ranks,
            "ground_truth_used_for_ranking": False,
            "e3_filtered_service_ranking": [],
        }
    native = native_service_ranking(raw_ranks)
    return {
        "status": "ok",
        "case_id": case_id,
        "method": method,
        "raw_feature_ranking": raw_ranks,
        "native_service_ranking": native,
        "e3_filtered_service_ranking": [s for s in native if s in ALLOW],
        "fallback_detected": False,
        "rcaeval_stderr": warning,
        "ground_truth_used_for_ranking": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    args = parser.parse_args()
    method = args.method
    started = time.perf_counter()
    out_dir = OUT / "cases" / method
    out_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    failures = 0
    fallbacks = 0
    ids = case_ids()

    for case_id in ids:
        path = out_dir / f"{case_id}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("status") in {"ok", "fallback_unranked", "hard_failed"}:
                completed += 1
                failures += int(cached.get("status") == "hard_failed")
                fallbacks += int(cached.get("status") == "fallback_unranked")
                continue
        try:
            if method in {"baro", "circa", "mmbaro", "mmcirca"}:
                payload = rcaeval_ranking(case_id, method)
            else:
                payload = local_rankings(case_id, method)
        except Exception as exc:
            payload = {
                "status": "hard_failed",
                "case_id": case_id,
                "method": method,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "ground_truth_used_for_ranking": False,
                "e3_filtered_service_ranking": [],
            }
        write_json(path, payload)
        completed += 1
        failures += int(payload["status"] == "hard_failed")
        fallbacks += int(payload["status"] == "fallback_unranked")
        print(method, case_id, payload["status"], flush=True)

    summary = {
        "method": method,
        "case_count_expected": len(ids),
        "case_count_written_or_cached": completed,
        "hard_failed": failures,
        "fallback_unranked": fallbacks,
        "runtime_seconds": time.perf_counter() - started,
        "resumable": True,
        "ground_truth_used_for_ranking": False,
        "re2tt_accessed": False,
    }
    write_json(OUT / f"step26_{method}_run_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
