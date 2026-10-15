import importlib.util
import json
from pathlib import Path


SCRIPT = Path("scripts/phase_c06_train_loop.py")

spec = importlib.util.spec_from_file_location(
    "phase_c06_train_loop_a10",
    SCRIPT,
)
assert spec is not None
assert spec.loader is not None

loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_exhausted_spares_are_detected_without_reuse(tmp_path: Path):
    primary = {
        "run_id": "C-TRAIN-BDR-04",
        "scenario": "bad_deployment_rollback",
        "seed": 1926564664,
        "partition": "TRAIN",
    }

    registry = {
        "reserved_spares": [
            {
                "run_id": "C-SPARE-TRAIN-BDR-01",
                "spare_ordinal": 1,
                "scenario": "bad_deployment_rollback",
                "seed": 1359673832,
                "partition": "TRAIN",
            },
            {
                "run_id": "C-SPARE-TRAIN-BDR-02",
                "spare_ordinal": 2,
                "scenario": "bad_deployment_rollback",
                "seed": 300872472,
                "partition": "TRAIN",
            },
        ]
    }

    write_json(
        tmp_path
        / "C-SPARE-TRAIN-BDR-01"
        / "run_summary.json",
        {
            "run_id": "C-SPARE-TRAIN-BDR-01",
            "replacement_for": "C-TRAIN-BDR-12",
            "status": "infrastructure_invalid_interrupted",
        },
    )

    write_json(
        tmp_path
        / "C-SPARE-TRAIN-BDR-02"
        / "run_summary.json",
        {
            "run_id": "C-SPARE-TRAIN-BDR-02",
            "replacement_for": "C-TRAIN-BDR-12",
            "status": "infrastructure_invalid_interrupted",
        },
    )

    assert loop.registered_spares_exhausted_for_primary(
        primary,
        registry,
        evidence_root=tmp_path,
    ) is True


def test_unused_registered_spare_means_not_exhausted(tmp_path: Path):
    primary = {
        "run_id": "C-TRAIN-BDR-04",
        "scenario": "bad_deployment_rollback",
        "seed": 1926564664,
        "partition": "TRAIN",
    }

    registry = {
        "reserved_spares": [
            {
                "run_id": "C-SPARE-TRAIN-BDR-01",
                "spare_ordinal": 1,
                "scenario": "bad_deployment_rollback",
                "seed": 1359673832,
                "partition": "TRAIN",
            }
        ]
    }

    assert loop.registered_spares_exhausted_for_primary(
        primary,
        registry,
        evidence_root=tmp_path,
    ) is False


def test_spare_already_used_for_same_primary_is_not_exhaustion(
    tmp_path: Path,
):
    primary = {
        "run_id": "C-TRAIN-BDR-04",
        "scenario": "bad_deployment_rollback",
        "seed": 1926564664,
        "partition": "TRAIN",
    }

    registry = {
        "reserved_spares": [
            {
                "run_id": "C-SPARE-TRAIN-BDR-01",
                "spare_ordinal": 1,
                "scenario": "bad_deployment_rollback",
                "seed": 1359673832,
                "partition": "TRAIN",
            }
        ]
    }

    write_json(
        tmp_path
        / "C-SPARE-TRAIN-BDR-01"
        / "run_summary.json",
        {
            "run_id": "C-SPARE-TRAIN-BDR-01",
            "replacement_for": "C-TRAIN-BDR-04",
            "status": "executed_verified",
        },
    )

    assert loop.registered_spares_exhausted_for_primary(
        primary,
        registry,
        evidence_root=tmp_path,
    ) is False


def test_train_loop_continues_when_registered_spares_exhausted(
    tmp_path: Path,
    monkeypatch,
):
    first = {
        "run_id": "C-TRAIN-BDR-04",
        "scenario": "bad_deployment_rollback",
        "seed": 1926564664,
        "partition": "TRAIN",
    }
    second = {
        "run_id": "C-TRAIN-ERR-10",
        "scenario": "errors",
        "seed": 1369559267,
        "partition": "TRAIN",
    }

    registry = {
        "reserved_spares": [
            {
                "run_id": "C-SPARE-TRAIN-BDR-01",
                "spare_ordinal": 1,
                "scenario": "bad_deployment_rollback",
                "seed": 1359673832,
                "partition": "TRAIN",
            },
            {
                "run_id": "C-SPARE-TRAIN-BDR-02",
                "spare_ordinal": 2,
                "scenario": "bad_deployment_rollback",
                "seed": 300872472,
                "partition": "TRAIN",
            },
        ]
    }

    evidence_root = tmp_path / "runs"
    control_root = tmp_path / "control"

    write_json(
        evidence_root / first["run_id"] / "run_summary.json",
        {
            "classification": "registered",
            "invalid_reason": "baseline_health_failed",
            "partition": "TRAIN",
            "registry_entry": first,
            "replacement_for": None,
            "run_id": first["run_id"],
            "status": "infrastructure_invalid_before_injection",
        },
    )

    for ordinal, spare_id in enumerate(
        (
            "C-SPARE-TRAIN-BDR-01",
            "C-SPARE-TRAIN-BDR-02",
        ),
        start=1,
    ):
        write_json(
            evidence_root / spare_id / "run_summary.json",
            {
                "run_id": spare_id,
                "replacement_for": "C-TRAIN-BDR-12",
                "status": "infrastructure_invalid_interrupted",
            },
        )

    executed = []

    def fake_execute_once(
        entry,
        *,
        replacement_for,
        evidence_root,
        control_root,
        executor=None,
        attempt_label=None,
    ):
        executed.append(entry["run_id"])

        result = {
            "classification": "registered",
            "partition": "TRAIN",
            "registry_entry": entry,
            "replacement_for": replacement_for,
            "status": "no_executable_rollback_request",
        }

        write_json(
            evidence_root / entry["run_id"] / "run_summary.json",
            result,
        )
        return result

    monkeypatch.setattr(
        loop,
        "train_schedule",
        lambda registry: [first, second],
    )
    monkeypatch.setattr(
        loop,
        "recover_interrupted_run",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        loop,
        "_execute_once",
        fake_execute_once,
    )

    result = loop.run_train_loop(
        registry=registry,
        evidence_root=evidence_root,
        control_root=control_root,
    )

    assert executed == ["C-TRAIN-ERR-10"]
    assert (
        result["train_primary_accounted"] == 2
    )
    assert (
        result["train_primary_remaining"] == 0
    )


def test_exhausted_spare_continuation_does_not_create_new_spare(
    tmp_path: Path,
    monkeypatch,
):
    first = {
        "run_id": "C-TRAIN-BDR-04",
        "scenario": "bad_deployment_rollback",
        "seed": 1926564664,
        "partition": "TRAIN",
    }

    registry = {
        "reserved_spares": [
            {
                "run_id": "C-SPARE-TRAIN-BDR-01",
                "spare_ordinal": 1,
                "scenario": "bad_deployment_rollback",
                "seed": 1359673832,
                "partition": "TRAIN",
            },
            {
                "run_id": "C-SPARE-TRAIN-BDR-02",
                "spare_ordinal": 2,
                "scenario": "bad_deployment_rollback",
                "seed": 300872472,
                "partition": "TRAIN",
            },
        ]
    }

    evidence_root = tmp_path / "runs"
    control_root = tmp_path / "control"

    write_json(
        evidence_root / first["run_id"] / "run_summary.json",
        {
            "run_id": first["run_id"],
            "status": "infrastructure_invalid_before_injection",
            "invalid_reason": "baseline_health_failed",
        },
    )

    for spare_id in (
        "C-SPARE-TRAIN-BDR-01",
        "C-SPARE-TRAIN-BDR-02",
    ):
        write_json(
            evidence_root / spare_id / "run_summary.json",
            {
                "run_id": spare_id,
                "replacement_for": "C-TRAIN-BDR-12",
                "status": "infrastructure_invalid_interrupted",
            },
        )

    monkeypatch.setattr(
        loop,
        "train_schedule",
        lambda registry: [first],
    )
    monkeypatch.setattr(
        loop,
        "recover_interrupted_run",
        lambda **kwargs: None,
    )

    result = loop.run_train_loop(
        registry=registry,
        evidence_root=evidence_root,
        control_root=control_root,
    )

    dirs = sorted(
        p.name
        for p in evidence_root.iterdir()
        if p.is_dir()
    )

    assert "C-SPARE-TRAIN-BDR-03" not in dirs
    assert result["train_primary_accounted"] == 1
