from __future__ import annotations

import json
import re
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



TRAIN_EXCLUDED_PRIMARY_IDS = frozenset(
    {
        "C-TRAIN-BDR-04",
        "C-TRAIN-ERR-03",
    }
)

TRAIN_AUTHORITATIVE_OVERRIDES = {
    "C-TRAIN-BDR-12": "C-SPARE-TRAIN-BDR-02__a5_rerun_02",
    "C-TRAIN-LAT-11": "C-TRAIN-LAT-11__launcher_retry_01",
}

_TRAIN_PRIMARY_RE = re.compile(r"^C-TRAIN-(?:BDR|ERR|LAT)-\d{2}$")


def select_authoritative_run_dirs(
    evidence_root: Path,
    *,
    allow_non_registry: bool = False,
) -> list[Path]:
    primary_dirs = sorted(
        path
        for path in evidence_root.iterdir()
        if path.is_dir()
        and _TRAIN_PRIMARY_RE.fullmatch(path.name)
        and (path / "run_summary.json").exists()
    )

    if primary_dirs and not allow_non_registry:
        selected: list[Path] = []

        for primary_dir in primary_dirs:
            primary_id = primary_dir.name

            if primary_id in TRAIN_EXCLUDED_PRIMARY_IDS:
                continue

            selected_name = TRAIN_AUTHORITATIVE_OVERRIDES.get(
                primary_id,
                primary_id,
            )
            selected_dir = evidence_root / selected_name
            summary_path = selected_dir / "run_summary.json"

            if not summary_path.exists():
                raise ValueError(
                    f"authoritative TRAIN namespace missing for "
                    f"{primary_id}: {selected_name}"
                )

            summary = _load_json(summary_path)

            if summary.get("classification") != "registered":
                raise ValueError(
                    f"authoritative TRAIN namespace is not registered: "
                    f"{selected_name}"
                )

            status = str(summary.get("status", ""))

            if status.startswith("infrastructure_invalid"):
                raise ValueError(
                    f"authoritative TRAIN namespace is infrastructure-invalid: "
                    f"{selected_name}"
                )

            if primary_id == "C-TRAIN-BDR-12":
                if (
                    summary.get("registered_result_eligible") is not True
                    or summary.get("counted_in_analysis_denominator") is not True
                ):
                    raise ValueError(
                        "BDR-12 authoritative rerun is not explicitly "
                        "eligible for the denominator"
                    )

            selected.append(selected_dir)

        return selected

    selected: list[Path] = []

    for run_dir in sorted(evidence_root.glob("*")):
        if not run_dir.is_dir() or run_dir.name.startswith("_"):
            continue

        summary_path = run_dir / "run_summary.json"
        if not summary_path.exists():
            continue

        summary = _load_json(summary_path)

        if (
            summary.get("classification") != "registered"
            and not allow_non_registry
        ):
            continue

        if str(summary.get("status", "")).startswith(
            "infrastructure_invalid"
        ):
            continue

        selected.append(run_dir)

    # Historical C03 dry-run trees may contain later duplicate reruns.
    # The committed analysis contract is one canonical dry-run artifact
    # per scenario. Prefer the numerically smaller seed namespace.
    if allow_non_registry and evidence_root.name == "C03_dry_runs":
        by_scenario: dict[str, Path] = {}

        def _dry_seed(path: Path) -> int:
            try:
                return int(path.name.rsplit("-", 1)[1])
            except (IndexError, ValueError):
                return 2**63 - 1

        for run_dir in selected:
            summary = _load_json(run_dir / "run_summary.json")
            scenario = str(
                summary.get("run_record", {}).get("scenario", "")
            )

            current = by_scenario.get(scenario)

            if current is None or _dry_seed(run_dir) < _dry_seed(current):
                by_scenario[scenario] = run_dir

        return sorted(by_scenario.values())

    return selected


def _guard_decision(summary: dict[str, Any]) -> str:
    legacy = summary.get("guard_decision")

    if isinstance(legacy, dict):
        value = legacy.get("guard_decision")
        if value is not None:
            return str(value)

    return "not_recorded"


def _execution_payload(summary: dict[str, Any]) -> dict[str, Any]:
    legacy = summary.get("execution")
    if isinstance(legacy, dict):
        return legacy

    current = summary.get("execution_result")
    if isinstance(current, dict):
        return current

    return {}


def analyze_run(
    run_dir: Path,
    ground_truth_root: Path,
) -> dict[str, Any]:
    summary = _load_json(run_dir / "run_summary.json")
    if summary.get("status") == "run_failed_after_injection":
        record = summary["run_record"]
        return {
            "artifact_run_id": run_dir.name,
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

    execution = _execution_payload(summary)
    action_status = execution.get("action_http_status")
    remediation_success = bool(
        execution.get("execution_attempted")
        and action_status is not None
        and 200 <= int(action_status) < 300
    )

    return {
        "artifact_run_id": run_dir.name,
        "run_id": record["run_id"],
        "scenario": record["scenario"],
        "classification": summary["classification"],
        "status": str(summary.get("status", "")),
        "detection_present": record.get("detection_time") is not None,
        "detection_delay_seconds": detection_delay,
        "correlation_correct": correlation_service == injected_service,
        "rca_hit_at_1": injected_service in ranking[:1],
        "rca_hit_at_3": injected_service in ranking[:3],
        "rca_hit_at_5": injected_service in ranking[:5],
        "guard_decision": _guard_decision(summary),
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
        "scenario_counts": dict(
            sorted(
                Counter(
                    row["scenario"]
                    for row in rows
                    if "scenario" in row
                ).items()
            )
        ),
        "status_counts": dict(
            sorted(
                Counter(
                    row["status"]
                    for row in rows
                    if "status" in row
                ).items()
            )
        ),
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

    for run_dir in select_authoritative_run_dirs(
        dry_or_registered_root,
        allow_non_registry=allow_non_registry,
    ):
        rows.append(analyze_run(run_dir, ground_truth_root))

    return {
        "rows": rows,
        "summary": summarize_runs(rows),
    }
