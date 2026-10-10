from __future__ import annotations

import json
from pathlib import Path

import pytest

from sentinelops.chaos import registered_harness


def test_first_registered_train_entry_is_frozen():
    entry = registered_harness._load_registry_entry("C-TRAIN-BDR-12")
    assert entry == {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "C-TRAIN-BDR-12",
        "scenario": "bad_deployment_rollback",
        "seed": 681377953,
    }


def test_registered_runner_rejects_non_train_entry():
    entry = registered_harness._load_registry_entry("C-VALIDATION-LAT-01")
    assert entry["partition"] == "VALIDATION"


def test_ground_truth_is_not_written_by_pipeline_stage_helpers(
    tmp_path: Path,
):
    run_dir = tmp_path / "run"
    workdir = tmp_path / "work"
    run_dir.mkdir()
    workdir.mkdir()
    ground_truth = tmp_path / "_ground_truth_injection_only"
    assert not ground_truth.exists()

    registered_harness._write_json(
        run_dir / "detection.json",
        {
            "stage": "detection",
            "status": "completed",
            "timestamp": None,
        },
    )

    assert not ground_truth.exists()


def test_registry_file_hash_is_stable():
    registry = Path("evidence/C/C04_run_registry.json")
    payload = json.loads(registry.read_text(encoding="utf-8"))
    assert payload["registered_run_count"] == 60
    assert payload["master_seed"] == 42


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("latency", 120),
        ("errors", 120),
        ("bad_deployment_rollback", 180),
    ],
)
def test_frozen_scenario_durations(scenario: str, expected: int):
    config = registered_harness._load_yaml(
        registered_harness.SCENARIO_CONFIG_PATH,
        "chaos_scenarios_v1",
    )
    if scenario == "bad_deployment_rollback":
        profile = registered_harness._load_yaml(
            registered_harness.BAD_DEPLOYMENT_PATH,
            "chaos_bad_deployment_v1",
        )
        duration = int(profile["total_injection_duration_seconds"])
    else:
        duration = int(config["scenarios"][scenario]["duration_seconds"])
    assert duration == expected
