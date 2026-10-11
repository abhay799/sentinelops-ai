from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from sentinelops.chaos.analysis import analyze_evidence_root

MODULE_PATH = Path("scripts/phase_c06_train_loop.py")
SPEC = importlib.util.spec_from_file_location("phase_c06_train_loop_amend4", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
train_loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(train_loop)


def _active(run_id: str = "NR-TRAIN-LAT-A4") -> dict:
    return {
        "run_id": run_id,
        "scenario": "latency",
        "partition": "TRAIN",
        "seed": 1900001001,
        "replacement_for": None,
        "started_utc": "2026-10-11T20:00:00Z",
        "host_check": {
            "timestamp_utc": "2026-10-11T20:00:00Z",
            "boot_id": "boot-a",
            "uptime_seconds": 100.0,
        },
    }


def _state(
    evidence_root: Path,
    active: dict,
    *,
    stage: str,
    injected: bool,
) -> None:
    path = evidence_root / active["run_id"] / "execution_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "run_id": active["run_id"],
                "scenario": active["scenario"],
                "seed": active["seed"],
                "injected_service": "payment-service",
                "injection_start": (
                    "2026-10-11T20:01:00Z" if injected else None
                ),
                "current_stage": stage,
                "stage_timestamps": {
                    stage: {"started": "2026-10-11T20:01:00Z"}
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _current_host(boot_id: str = "boot-a") -> dict:
    return {
        "timestamp_utc": "2026-10-11T20:02:00Z",
        "boot_id": boot_id,
        "uptime_seconds": 220.0,
    }


def test_exception_before_injection_is_replaceable_infrastructure_invalid(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    active = _active()
    _state(
        evidence,
        active,
        stage="pre_injection_reset",
        injected=False,
    )
    train_loop._record_interruption(
        active=active,
        evidence_root=evidence,
        control_root=control,
        reason="simulated_exception",
        traceback_text="traceback-before",
        current_host_check=_current_host(),
    )
    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, active["run_id"])
    )
    assert summary["status"] == "infrastructure_invalid_interrupted"
    assert summary["registered_result_eligible"] is False
    assert train_loop.is_infrastructure_invalid(summary)


@pytest.mark.parametrize(
    "stage",
    [
        "injection",
        "detection",
        "rca",
        "plan_guard",
        "remediation",
        "verification",
    ],
)
def test_exception_at_or_after_injection_is_counted_result(
    tmp_path: Path,
    stage: str,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    active = _active(f"NR-{stage}")
    _state(evidence, active, stage=stage, injected=True)
    train_loop._record_interruption(
        active=active,
        evidence_root=evidence,
        control_root=control,
        reason=f"simulated_{stage}_exception",
        traceback_text=f"traceback-{stage}",
        current_host_check=_current_host(),
    )
    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, active["run_id"])
    )
    assert summary["status"] == "run_failed_after_injection"
    assert summary["registered_result_eligible"] is True
    assert summary["counted_in_analysis_denominator"] is True
    assert summary["traceback"] == f"traceback-{stage}"
    assert not train_loop.is_infrastructure_invalid(summary)


def test_recorded_host_event_overrides_post_injection_failure(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    active = _active("NR-HOST-EVENT")
    _state(evidence, active, stage="detection", injected=True)
    train_loop._record_interruption(
        active=active,
        evidence_root=evidence,
        control_root=control,
        reason="simulated_host_event",
        traceback_text="traceback-host",
        current_host_check=_current_host("boot-b"),
    )
    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, active["run_id"])
    )
    interruption = next((control / "interruptions").glob("*.json"))
    record = train_loop.read_json(interruption)
    assert summary["status"] == "infrastructure_invalid_host_event"
    assert summary["invalid_reason"] == "host_boot_id_changed"
    assert record["host_check_at_interruption"]["boot_id"] == "boot-b"
    assert record["execution_state"]["injection_start"] is not None


def test_restart_classifies_from_recorded_stage_timestamps(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    active = _active("NR-RESTART-AFTER-INJECTION")
    _state(evidence, active, stage="rca", injected=True)
    train_loop.write_json(
        control / "state.json",
        {
            "version": 1,
            "active_run": active,
            "last_update_utc": "2026-10-11T20:01:30Z",
        },
    )
    monkeypatch.setattr(train_loop, "host_check", lambda: _current_host())
    interruption = train_loop.recover_interrupted_run(
        evidence_root=evidence,
        control_root=control,
    )
    assert interruption is not None
    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, active["run_id"])
    )
    assert summary["status"] == "run_failed_after_injection"
    assert summary["execution_state"]["current_stage"] == "rca"
    assert "rca" in summary["execution_state"]["stage_timestamps"]


def test_run_failed_after_injection_never_uses_spare(
    tmp_path: Path,
):
    primary = {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "NR-PRIMARY-A4",
        "scenario": "errors",
        "seed": 1900001101,
    }
    spares = [
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-A4-1",
            "scenario": "errors",
            "seed": 1900001102,
            "spare_ordinal": 1,
        },
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-A4-2",
            "scenario": "errors",
            "seed": 1900001103,
            "spare_ordinal": 2,
        },
    ]
    registry = {
        "execution_schedule": [primary],
        "reserved_spares": spares,
    }
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    summary_path = train_loop.run_summary_path(
        evidence,
        primary["run_id"],
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "classification": "registered",
                "partition": "TRAIN",
                "run_id": primary["run_id"],
                "scenario": "errors",
                "seed": primary["seed"],
                "status": "run_failed_after_injection",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    calls: list[str] = []

    def executor(entry, replacement_for):
        calls.append(entry["run_id"])
        raise AssertionError("no spare may execute")

    result = train_loop.run_train_loop(
        registry=registry,
        evidence_root=evidence,
        control_root=control,
        executor=executor,
    )
    assert calls == []
    assert result["loop_complete"] is True
    assert result["train_spares_used"] == 0


def test_analysis_excludes_infrastructure_invalid_and_counts_failed_result(
    tmp_path: Path,
):
    root = tmp_path / "runs"
    invalid_dir = root / "NR-INFRA"
    invalid_dir.mkdir(parents=True)
    (invalid_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "classification": "registered",
                "status": "infrastructure_invalid_interrupted",
                "run_id": "NR-INFRA",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    failed_dir = root / "NR-FAILED"
    failed_dir.mkdir(parents=True)
    (failed_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "classification": "registered",
                "status": "run_failed_after_injection",
                "run_id": "NR-FAILED",
                "run_record": {
                    "run_id": "NR-FAILED",
                    "scenario": "latency",
                    "seed": 1900001201,
                    "injection_start": "2026-10-11T20:00:00Z",
                    "detection_time": None,
                    "remediation_time": None,
                    "recovery_time": None,
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    payload = analyze_evidence_root(root)
    assert payload["summary"]["run_count"] == 1
    assert len(payload["rows"]) == 1
    assert payload["rows"][0]["status"] == "run_failed_after_injection"
    assert payload["summary"]["metrics"]["detection_rate"]["estimate"] == 0.0
    assert (
        payload["summary"]["metrics"]["remediation_success_rate"]["estimate"]
        == 0.0
    )
