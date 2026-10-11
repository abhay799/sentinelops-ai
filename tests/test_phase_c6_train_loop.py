from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path("scripts/phase_c06_train_loop.py")
SPEC = importlib.util.spec_from_file_location("phase_c06_train_loop", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
train_loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(train_loop)


def _write_summary(
    evidence_root: Path,
    entry: dict,
    status: str,
    *,
    replacement_for: str | None = None,
) -> None:
    path = evidence_root / entry["run_id"] / "run_summary.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "classification": "non_registry_test_fixture",
                "partition": entry["partition"],
                "run_id": entry["run_id"],
                "scenario": entry["scenario"],
                "seed": entry["seed"],
                "replacement_for": replacement_for,
                "status": status,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _registry(primary: dict, spares: list[dict]) -> dict:
    return {
        "execution_schedule": [primary],
        "reserved_spares": spares,
    }


def test_loop_resume_after_interruption_never_reruns_primary(
    tmp_path: Path,
):
    primary = {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "NR-TRAIN-LAT-01",
        "scenario": "latency",
        "seed": 1900000001,
    }
    spares = [
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-LAT-01",
            "scenario": "latency",
            "seed": 1900000002,
            "spare_ordinal": 1,
        },
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-LAT-02",
            "scenario": "latency",
            "seed": 1900000003,
            "spare_ordinal": 2,
        },
    ]
    registry = _registry(primary, spares)
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    calls: list[str] = []

    def crashing_executor(entry, replacement_for):
        calls.append(entry["run_id"])
        run_dir = evidence / entry["run_id"]
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "partial_marker.txt").write_text(
            "preserve-me\n",
            encoding="utf-8",
        )
        raise KeyboardInterrupt("simulated kill")

    with pytest.raises(KeyboardInterrupt):
        train_loop.run_train_loop(
            registry=registry,
            evidence_root=evidence,
            control_root=control,
            executor=crashing_executor,
        )

    assert calls == ["NR-TRAIN-LAT-01"]
    primary_summary = train_loop.read_json(
        train_loop.run_summary_path(
            evidence,
            primary["run_id"],
        )
    )
    assert primary_summary["status"] == ("infrastructure_invalid_interrupted")
    assert (evidence / primary["run_id"] / "partial_marker.txt").read_text(
        encoding="utf-8"
    ) == "preserve-me\n"

    def resumed_executor(entry, replacement_for):
        calls.append(entry["run_id"])
        _write_summary(
            evidence,
            entry,
            "executed_verified",
            replacement_for=replacement_for,
        )

    result = train_loop.run_train_loop(
        registry=registry,
        evidence_root=evidence,
        control_root=control,
        executor=resumed_executor,
    )

    assert calls.count("NR-TRAIN-LAT-01") == 1
    assert calls.count("NR-SPARE-TRAIN-LAT-01") == 1
    assert calls.count("NR-SPARE-TRAIN-LAT-02") == 0
    assert result["loop_complete"] is True
    interruption_files = list((control / "interruptions").glob("*.json"))
    assert len(interruption_files) == 1
    assert train_loop.read_json(interruption_files[0])["event"] == "interruption"


def test_infrastructure_invalid_uses_next_same_cell_spare(
    tmp_path: Path,
):
    primary = {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "NR-TRAIN-ERR-01",
        "scenario": "errors",
        "seed": 1900000011,
    }
    spares = [
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-ERR-01",
            "scenario": "errors",
            "seed": 1900000012,
            "spare_ordinal": 1,
        },
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-ERR-02",
            "scenario": "errors",
            "seed": 1900000013,
            "spare_ordinal": 2,
        },
    ]
    registry = _registry(primary, spares)
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    calls: list[tuple[str, str | None]] = []

    def executor(entry, replacement_for):
        calls.append((entry["run_id"], replacement_for))
        if entry["run_id"] == primary["run_id"]:
            status = "infrastructure_invalid_before_injection"
        else:
            status = "executed_verified"
        _write_summary(
            evidence,
            entry,
            status,
            replacement_for=replacement_for,
        )

    train_loop.run_train_loop(
        registry=registry,
        evidence_root=evidence,
        control_root=control,
        executor=executor,
    )

    assert calls == [
        ("NR-TRAIN-ERR-01", None),
        ("NR-SPARE-TRAIN-ERR-01", "NR-TRAIN-ERR-01"),
    ]
    assert train_loop.run_summary_path(
        evidence,
        "NR-TRAIN-ERR-01",
    ).exists()
    assert train_loop.run_summary_path(
        evidence,
        "NR-SPARE-TRAIN-ERR-01",
    ).exists()
    assert not train_loop.run_summary_path(
        evidence,
        "NR-SPARE-TRAIN-ERR-02",
    ).exists()


def test_spare_exhaustion_stops_without_ad_hoc_seed(
    tmp_path: Path,
):
    primary = {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "NR-TRAIN-BDR-01",
        "scenario": "bad_deployment_rollback",
        "seed": 1900000021,
    }
    spares = [
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-BDR-01",
            "scenario": "bad_deployment_rollback",
            "seed": 1900000022,
            "spare_ordinal": 1,
        },
        {
            "partition": "TRAIN",
            "run_id": "NR-SPARE-TRAIN-BDR-02",
            "scenario": "bad_deployment_rollback",
            "seed": 1900000023,
            "spare_ordinal": 2,
        },
    ]
    registry = _registry(primary, spares)
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"

    def invalid_executor(entry, replacement_for):
        _write_summary(
            evidence,
            entry,
            "infrastructure_invalid_simulated",
            replacement_for=replacement_for,
        )

    with pytest.raises(RuntimeError, match="both reserved TRAIN spares"):
        train_loop.run_train_loop(
            registry=registry,
            evidence_root=evidence,
            control_root=control,
            executor=invalid_executor,
        )

    assert len(list(evidence.glob("*/run_summary.json"))) == 3
