from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable

import numpy as np

BOOTSTRAP_SEED = 42
BOOTSTRAP_RESAMPLES = 10_000


def _iso_seconds(start: str | None, end: str | None) -> float | None:
    if start is None or end is None:
        return None
    from datetime import datetime

    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze_run(
    run_dir: Path,
    ground_truth_root: Path,
) -> dict[str, Any]:
    summary = _load_json(run_dir / "run_summary.json")
    if summary.get("status") == "run_failed_after_injection":
        record = summary["run_record"]
        return {
            "run_id": record["run_id"],
            "scenario": record["scenario"],
            "classification": summary["classification"],
            "status": "run_failed_after_injection",
            "detection_present": False,
            "detection_delay_seconds": None,
            "correlation_correct": False,
            "rca_hit_at_1": False,
            "rca_hit_at_3": False,
            "rca_hit_at_5": False,
            "guard_decision": "run_failed_after_injection",
            "remediation_success": False,
            "recovery_time_seconds": None,
        }
    record = summary["run_record"]
    ground_truth = _load_json(ground_truth_root / f"{record['run_id']}.json")
    injected_service_raw = ground_truth.get("injected_service")
    if injected_service_raw is None:
        if summary.get("classification") == "registered":
            raise ValueError(f"registered run {record['run_id']} lacks injected_service")
        injected_service_raw = "payment-service"
    injected_service = str(injected_service_raw)

    correlation = _load_json(run_dir / "correlation.json")
    rca = _load_json(run_dir / "rca.json")
    ranking = [str(value) for value in rca.get("details", {}).get("ranking", [])]

    detection_delay = _iso_seconds(
        record["injection_start"],
        record.get("detection_time"),
    )
    recovery_time = _iso_seconds(
        record.get("remediation_time"),
        record.get("recovery_time"),
    )

    correlation_service = correlation.get("details", {}).get("candidate_service")

    execution = summary["execution"]
    action_status = execution.get("action_http_status")
    remediation_success = bool(
        execution.get("execution_attempted")
        and action_status is not None
        and 200 <= int(action_status) < 300
    )

    return {
        "run_id": record["run_id"],
        "scenario": record["scenario"],
        "classification": summary["classification"],
        "detection_present": record.get("detection_time") is not None,
        "detection_delay_seconds": detection_delay,
        "correlation_correct": correlation_service == injected_service,
        "rca_hit_at_1": injected_service in ranking[:1],
        "rca_hit_at_3": injected_service in ranking[:3],
        "rca_hit_at_5": injected_service in ranking[:5],
        "guard_decision": summary["guard_decision"]["guard_decision"],
        "remediation_success": remediation_success,
        "recovery_time_seconds": recovery_time,
    }


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return float(np.mean(np.asarray(values, dtype=float)))


def _bootstrap_ci(
    rows: list[dict[str, Any]],
    extractor: Callable[[dict[str, Any]], float | None],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, float | int | None]:
    if not rows:
        return {
            "estimate": None,
            "ci95_low": None,
            "ci95_high": None,
            "valid_resamples": 0,
        }

    values = [extractor(row) for row in rows]
    estimate_values = [float(value) for value in values if value is not None]
    estimate = _mean(estimate_values)

    rng = np.random.default_rng(seed)
    samples: list[float] = []
    n = len(rows)

    for _ in range(resamples):
        indices = rng.integers(0, n, size=n)
        sample_values = [extractor(rows[int(index)]) for index in indices]
        observed = [float(value) for value in sample_values if value is not None]
        if observed:
            samples.append(float(np.mean(observed)))

    if not samples:
        return {
            "estimate": estimate,
            "ci95_low": None,
            "ci95_high": None,
            "valid_resamples": 0,
        }

    array = np.asarray(samples, dtype=float)
    return {
        "estimate": estimate,
        "ci95_low": float(np.percentile(array, 2.5)),
        "ci95_high": float(np.percentile(array, 97.5)),
        "valid_resamples": len(samples),
    }


def summarize_runs(
    rows: list[dict[str, Any]],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    guard_counts = dict(sorted(Counter(row["guard_decision"] for row in rows).items()))

    metrics = {
        "detection_rate": _bootstrap_ci(
            rows,
            lambda row: float(row["detection_present"]),
            seed=seed,
            resamples=resamples,
        ),
        "detection_delay_seconds": _bootstrap_ci(
            rows,
            lambda row: row["detection_delay_seconds"],
            seed=seed,
            resamples=resamples,
        ),
        "correlation_correct_rate": _bootstrap_ci(
            rows,
            lambda row: float(row["correlation_correct"]),
            seed=seed,
            resamples=resamples,
        ),
        "rca_hit_at_1": _bootstrap_ci(
            rows,
            lambda row: float(row["rca_hit_at_1"]),
            seed=seed,
            resamples=resamples,
        ),
        "rca_hit_at_3": _bootstrap_ci(
            rows,
            lambda row: float(row["rca_hit_at_3"]),
            seed=seed,
            resamples=resamples,
        ),
        "rca_hit_at_5": _bootstrap_ci(
            rows,
            lambda row: float(row["rca_hit_at_5"]),
            seed=seed,
            resamples=resamples,
        ),
        "remediation_success_rate": _bootstrap_ci(
            rows,
            lambda row: float(row["remediation_success"]),
            seed=seed,
            resamples=resamples,
        ),
        "recovery_time_seconds": _bootstrap_ci(
            rows,
            lambda row: row["recovery_time_seconds"],
            seed=seed,
            resamples=resamples,
        ),
    }

    guard_proportions = {
        decision: _bootstrap_ci(
            rows,
            lambda row, decision=decision: float(row["guard_decision"] == decision),
            seed=seed,
            resamples=resamples,
        )
        for decision in guard_counts
    }

    return {
        "run_count": len(rows),
        "bootstrap_seed": seed,
        "bootstrap_resamples": resamples,
        "metrics": metrics,
        "guard_decision_counts": guard_counts,
        "guard_decision_proportions": guard_proportions,
    }


def analyze_evidence_root(
    dry_or_registered_root: Path,
    *,
    allow_non_registry: bool = False,
) -> dict[str, Any]:
    ground_truth_root = dry_or_registered_root / "_ground_truth_injection_only"
    rows: list[dict[str, Any]] = []

    for run_dir in sorted(dry_or_registered_root.glob("*")):
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue
        summary_path = run_dir / "run_summary.json"
        if not summary_path.exists():
            continue
        summary = _load_json(summary_path)
        if summary.get("classification") != "registered" and not allow_non_registry:
            continue
        if str(summary.get("status", "")).startswith("infrastructure_invalid"):
            continue
        rows.append(analyze_run(run_dir, ground_truth_root))

    return {
        "rows": rows,
        "summary": summarize_runs(rows),
    }
