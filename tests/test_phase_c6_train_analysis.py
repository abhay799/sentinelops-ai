from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from sentinelops.chaos.analysis import (
    analyze_evidence_root,
    analyze_run,
    select_authoritative_run_dirs,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_current_train_summary_schema_uses_execution_result_without_fabricating_guard(
    tmp_path: Path,
) -> None:
    run_id = "C-TRAIN-BDR-11"
    run_dir = tmp_path / run_id
    gt_root = tmp_path / "_ground_truth_injection_only"

    _write_json(
        gt_root / f"{run_id}.json",
        {"run_id": run_id, "injected_service": "payment-service"},
    )

    _write_json(
        run_dir / "run_summary.json",
        {
            "classification": "registered",
            "status": "executed_verified",
            "run_record": {
                "run_id": run_id,
                "scenario": "bad_deployment_rollback",
                "injection_start": "2026-10-17T00:00:00+00:00",
                "detection_time": "2026-10-17T00:00:05+00:00",
                "remediation_time": "2026-10-17T00:00:20+00:00",
                "recovery_time": "2026-10-17T00:00:25+00:00",
            },
            "execution_result": {
                "execution_attempted": True,
                "action_http_status": 200,
                "execution_status": "executed_verified",
            },
        },
    )

    _write_json(
        run_dir / "correlation.json",
        {"details": {"candidate_service": "payment-service"}},
    )
    _write_json(
        run_dir / "rca.json",
        {"details": {"ranking": ["payment-service"]}},
    )

    row = analyze_run(run_dir, gt_root)

    assert row["artifact_run_id"] == run_id
    assert row["run_id"] == run_id
    assert row["status"] == "executed_verified"
    assert row["remediation_success"] is True
    assert row["guard_decision"] == "not_recorded"
    assert row["detection_delay_seconds"] == 5.0
    assert row["recovery_time_seconds"] == 5.0


def _registered_summary(
    run_id: str,
    scenario: str,
    *,
    status: str = "no_executable_rollback_request",
    record_run_id: str | None = None,
) -> dict:
    return {
        "classification": "registered",
        "status": status,
        "run_record": {
            "run_id": record_run_id or run_id,
            "scenario": scenario,
            "injection_start": "2026-10-17T00:00:00+00:00",
            "detection_time": "2026-10-17T00:00:01+00:00",
            "remediation_time": None,
            "recovery_time": None,
        },
        "execution_result": None,
    }


def test_authoritative_train_selection_is_exactly_34_without_double_counting(
    tmp_path: Path,
) -> None:
    scenarios = {
        "BDR": "bad_deployment_rollback",
        "ERR": "errors",
        "LAT": "latency",
    }

    for prefix, scenario in scenarios.items():
        for index in range(1, 13):
            run_id = f"C-TRAIN-{prefix}-{index:02d}"
            status = "no_executable_rollback_request"

            if run_id in {"C-TRAIN-BDR-04", "C-TRAIN-ERR-03"}:
                status = "infrastructure_invalid_before_injection"
            elif run_id == "C-TRAIN-BDR-12":
                status = "infrastructure_invalid_interrupted"
            elif run_id == "C-TRAIN-LAT-11":
                status = "harness_defect"

            _write_json(
                tmp_path / run_id / "run_summary.json",
                _registered_summary(run_id, scenario, status=status),
            )

    _write_json(
        tmp_path / "C-SPARE-TRAIN-BDR-02__a5_rerun_02" / "run_summary.json",
        {
            **_registered_summary(
                "C-SPARE-TRAIN-BDR-02__a5_rerun_02",
                "bad_deployment_rollback",
                status="run_failed_after_injection",
                record_run_id="C-SPARE-TRAIN-BDR-02",
            ),
            "registered_result_eligible": True,
            "counted_in_analysis_denominator": True,
            "replacement_for": "C-TRAIN-BDR-12",
        },
    )

    _write_json(
        tmp_path / "C-TRAIN-LAT-11__launcher_retry_01" / "run_summary.json",
        _registered_summary(
            "C-TRAIN-LAT-11__launcher_retry_01",
            "latency",
            status="no_executable_rollback_request",
            record_run_id="C-TRAIN-LAT-11",
        ),
    )

    selected = select_authoritative_run_dirs(tmp_path)
    names = [path.name for path in selected]

    assert len(names) == 34
    assert len(names) == len(set(names))

    assert "C-TRAIN-BDR-04" not in names
    assert "C-TRAIN-ERR-03" not in names
    assert "C-TRAIN-BDR-12" not in names
    assert "C-TRAIN-LAT-11" not in names

    assert names.count("C-SPARE-TRAIN-BDR-02__a5_rerun_02") == 1
    assert names.count("C-TRAIN-LAT-11__launcher_retry_01") == 1

    scenario_counts = Counter(
        json.loads((path / "run_summary.json").read_text())["run_record"]["scenario"]
        for path in selected
    )

    assert scenario_counts == {
        "bad_deployment_rollback": 11,
        "errors": 11,
        "latency": 12,
    }


def test_real_train_authoritative_denominator_and_status_counts() -> None:
    root = Path("evidence/C/C06_train_runs")

    selected = select_authoritative_run_dirs(root)
    names = [path.name for path in selected]

    assert len(names) == 34
    assert "C-SPARE-TRAIN-BDR-02__a5_rerun_02" in names
    assert "C-TRAIN-LAT-11__launcher_retry_01" in names
    assert "C-TRAIN-BDR-04" not in names
    assert "C-TRAIN-ERR-03" not in names

    statuses = Counter()
    scenarios = Counter()

    for path in selected:
        summary = json.loads((path / "run_summary.json").read_text())
        statuses[summary["status"]] += 1
        scenarios[summary["run_record"]["scenario"]] += 1

    assert statuses == {
        "executed_verified": 8,
        "no_executable_rollback_request": 22,
        "plan_or_guard_stage_failed": 3,
        "run_failed_after_injection": 1,
    }

    assert scenarios == {
        "bad_deployment_rollback": 11,
        "errors": 11,
        "latency": 12,
    }


def test_real_train_analysis_has_34_authoritative_rows() -> None:
    payload = analyze_evidence_root(Path("evidence/C/C06_train_runs"))

    assert payload["summary"]["run_count"] == 34
