from __future__ import annotations

import json
from pathlib import Path

from sentinelops.chaos.analysis import (
    BOOTSTRAP_RESAMPLES,
    BOOTSTRAP_SEED,
    analyze_evidence_root,
    analyze_run,
    summarize_runs,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def synthetic_run(root: Path) -> tuple[Path, Path]:
    run_id = "SYN-1"
    run_dir = root / run_id
    gt_root = root / "_ground_truth_injection_only"
    _write_json(
        gt_root / f"{run_id}.json",
        {
            "run_id": run_id,
            "injected_service": "payment-service",
        },
    )
    _write_json(
        run_dir / "run_summary.json",
        {
            "classification": "registered",
            "run_record": {
                "run_id": run_id,
                "scenario": "latency",
                "injection_start": "2026-10-11T10:00:00+00:00",
                "detection_time": "2026-10-11T10:00:05+00:00",
                "remediation_time": "2026-10-11T10:00:20+00:00",
                "recovery_time": "2026-10-11T10:00:25+00:00",
            },
            "guard_decision": {"guard_decision": "eligible_pending_human"},
            "execution": {
                "execution_attempted": True,
                "action_http_status": 200,
            },
        },
    )
    _write_json(
        run_dir / "correlation.json",
        {
            "details": {
                "candidate_service": "payment-service",
            }
        },
    )
    _write_json(
        run_dir / "rca.json",
        {
            "details": {
                "ranking": [
                    "order-service",
                    "payment-service",
                    "inventory-service",
                ]
            }
        },
    )
    return run_dir, gt_root


def test_registered_analysis_synthetic_fixture(tmp_path: Path):
    run_dir, gt_root = synthetic_run(tmp_path)
    row = analyze_run(run_dir, gt_root)
    assert row["detection_delay_seconds"] == 5.0
    assert row["correlation_correct"]
    assert not row["rca_hit_at_1"]
    assert row["rca_hit_at_3"]
    assert row["rca_hit_at_5"]
    assert row["remediation_success"]
    assert row["recovery_time_seconds"] == 5.0


def test_bootstrap_is_frozen_and_deterministic():
    rows = [
        {
            "detection_present": True,
            "detection_delay_seconds": float(index + 1),
            "correlation_correct": index % 2 == 0,
            "rca_hit_at_1": index % 3 == 0,
            "rca_hit_at_3": True,
            "rca_hit_at_5": True,
            "guard_decision": ("eligible_pending_human" if index < 3 else "blocked"),
            "remediation_success": index != 4,
            "recovery_time_seconds": float(index + 2),
        }
        for index in range(5)
    ]
    first = summarize_runs(rows)
    second = summarize_runs(rows)
    assert first == second
    assert first["bootstrap_seed"] == BOOTSTRAP_SEED == 42
    assert first["bootstrap_resamples"] == BOOTSTRAP_RESAMPLES == 10_000
    assert first["guard_decision_counts"] == {
        "blocked": 2,
        "eligible_pending_human": 3,
    }


def test_analysis_runs_on_committed_dry_run_artifacts():
    root = Path("evidence/C/C03_dry_runs")
    payload = analyze_evidence_root(
        root,
        allow_non_registry=True,
    )
    assert payload["summary"]["run_count"] == 3
    assert {row["scenario"] for row in payload["rows"]} == {
        "latency",
        "errors",
        "bad_deployment_rollback",
    }
