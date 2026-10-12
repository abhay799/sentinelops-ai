import importlib.util
import json
from pathlib import Path


SCRIPT_PATH = Path("scripts/phase_c06_train_loop.py")

spec = importlib.util.spec_from_file_location(
    "phase_c06_train_loop_a9",
    SCRIPT_PATH,
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


def launcher_defect_summary(run_id: str) -> dict:
    return {
        "classification": "registered",
        "counted_in_analysis_denominator": False,
        "execution_state": {},
        "failure_reason": None,
        "harness_defect_reason":
            "non_environmental_exception:TypeError",
        "invalid_reason": None,
        "partition": "TRAIN",
        "registered_result_eligible": False,
        "replacement_for": None,
        "run_id": run_id,
        "scenario": "latency",
        "seed": 693336793,
        "status": "harness_defect",
        "traceback": (
            "Traceback...\n"
            "result = executor(entry, replacement_for)\n"
            "TypeError: run_registered_train() takes 1 positional "
            "argument but 2 were given\n"
        ),
    }


def test_launcher_defect_is_retry_eligible(tmp_path: Path):
    run_id = "C-TRAIN-LAT-11"
    run_dir = tmp_path / run_id
    write_json(
        run_dir / "run_summary.json",
        launcher_defect_summary(run_id),
    )

    assert loop.preexecutor_launcher_retry_eligible(
        tmp_path,
        run_id,
    ) is True


def test_rejects_if_execution_state_exists(tmp_path: Path):
    run_id = "C-TRAIN-LAT-11"
    run_dir = tmp_path / run_id

    write_json(
        run_dir / "run_summary.json",
        launcher_defect_summary(run_id),
    )
    write_json(
        run_dir / "execution_state.json",
        {
            "run_id": run_id,
            "injection_start": None,
        },
    )

    assert loop.preexecutor_launcher_retry_eligible(
        tmp_path,
        run_id,
    ) is False


def test_rejects_non_harness_defect(tmp_path: Path):
    run_id = "C-TRAIN-LAT-11"
    summary = launcher_defect_summary(run_id)
    summary["status"] = "infrastructure_invalid_interrupted"

    write_json(
        tmp_path / run_id / "run_summary.json",
        summary,
    )

    assert loop.preexecutor_launcher_retry_eligible(
        tmp_path,
        run_id,
    ) is False


def test_rejects_registered_result(tmp_path: Path):
    run_id = "C-TRAIN-LAT-11"
    summary = launcher_defect_summary(run_id)
    summary["registered_result_eligible"] = True
    summary["counted_in_analysis_denominator"] = True

    write_json(
        tmp_path / run_id / "run_summary.json",
        summary,
    )

    assert loop.preexecutor_launcher_retry_eligible(
        tmp_path,
        run_id,
    ) is False


def test_rejects_unrelated_harness_typeerror(tmp_path: Path):
    run_id = "C-TRAIN-LAT-11"
    summary = launcher_defect_summary(run_id)
    summary["traceback"] = (
        "Traceback...\n"
        "TypeError: unrelated production failure\n"
    )

    write_json(
        tmp_path / run_id / "run_summary.json",
        summary,
    )

    assert loop.preexecutor_launcher_retry_eligible(
        tmp_path,
        run_id,
    ) is False


def test_run_train_loop_preserves_launcher_defect_and_uses_retry_namespace(
    tmp_path: Path,
    monkeypatch,
):
    run_id = "C-TRAIN-LAT-11"
    entry = {
        "global_execution_index": 2,
        "partition": "TRAIN",
        "partition_execution_index": 2,
        "run_id": run_id,
        "scenario": "latency",
        "seed": 693336793,
    }

    evidence_root = tmp_path / "runs"
    control_root = tmp_path / "control"

    original = launcher_defect_summary(run_id)
    base_summary_path = evidence_root / run_id / "run_summary.json"
    write_json(base_summary_path, original)

    original_bytes = base_summary_path.read_bytes()

    monkeypatch.setattr(
        loop,
        "train_schedule",
        lambda registry: [entry],
    )
    monkeypatch.setattr(
        loop,
        "recover_interrupted_run",
        lambda **kwargs: None,
    )

    calls = []

    def fake_execute_once(
        received_entry,
        *,
        replacement_for,
        evidence_root,
        control_root,
        executor=None,
        attempt_label=None,
    ):
        calls.append(
            {
                "run_id": received_entry["run_id"],
                "replacement_for": replacement_for,
                "attempt_label": attempt_label,
            }
        )

        assert attempt_label == "launcher_retry_01"

        retry_dir = (
            evidence_root
            / f"{received_entry['run_id']}__{attempt_label}"
        )

        result = {
            "classification": "registered",
            "counted_in_analysis_denominator": True,
            "failure_reason": None,
            "harness_defect_reason": None,
            "invalid_reason": None,
            "partition": "TRAIN",
            "registered_result_eligible": True,
            "replacement_for": None,
            "run_id": received_entry["run_id"],
            "artifact_run_id":
                f"{received_entry['run_id']}__{attempt_label}",
            "scenario": received_entry["scenario"],
            "seed": received_entry["seed"],
            "status": "ok",
            "traceback": None,
        }

        write_json(
            retry_dir / "run_summary.json",
            result,
        )
        return result

    monkeypatch.setattr(
        loop,
        "_execute_once",
        fake_execute_once,
    )

    result = loop.run_train_loop(
        registry={
            "test": True,
            "reserved_spares": [],
        },
        evidence_root=evidence_root,
        control_root=control_root,
    )

    assert len(calls) == 1
    assert calls[0] == {
        "run_id": run_id,
        "replacement_for": None,
        "attempt_label": "launcher_retry_01",
    }

    # Historical launcher-defect evidence must remain byte-identical.
    assert base_summary_path.read_bytes() == original_bytes

    retry_summary = (
        evidence_root
        / f"{run_id}__launcher_retry_01"
        / "run_summary.json"
    )
    assert retry_summary.is_file()

    assert result["train_primary_accounted"] == 1
    assert result["train_primary_remaining"] == 0


def test_existing_launcher_retry_result_is_reused_without_reexecution(
    tmp_path: Path,
    monkeypatch,
):
    run_id = "C-TRAIN-LAT-11"
    entry = {
        "global_execution_index": 2,
        "partition": "TRAIN",
        "partition_execution_index": 2,
        "run_id": run_id,
        "scenario": "latency",
        "seed": 693336793,
    }

    evidence_root = tmp_path / "runs"
    control_root = tmp_path / "control"

    write_json(
        evidence_root / run_id / "run_summary.json",
        launcher_defect_summary(run_id),
    )

    retry_result = {
        "classification": "registered",
        "counted_in_analysis_denominator": True,
        "failure_reason": None,
        "harness_defect_reason": None,
        "invalid_reason": None,
        "partition": "TRAIN",
        "registered_result_eligible": True,
        "replacement_for": None,
        "run_id": run_id,
        "artifact_run_id": f"{run_id}__launcher_retry_01",
        "scenario": "latency",
        "seed": 693336793,
        "status": "ok",
        "traceback": None,
    }

    write_json(
        evidence_root
        / f"{run_id}__launcher_retry_01"
        / "run_summary.json",
        retry_result,
    )

    monkeypatch.setattr(
        loop,
        "train_schedule",
        lambda registry: [entry],
    )
    monkeypatch.setattr(
        loop,
        "recover_interrupted_run",
        lambda **kwargs: None,
    )

    def must_not_execute(*args, **kwargs):
        raise AssertionError(
            "existing launcher retry must not execute again"
        )

    monkeypatch.setattr(
        loop,
        "_execute_once",
        must_not_execute,
    )

    result = loop.run_train_loop(
        registry={
            "test": True,
            "reserved_spares": [],
        },
        evidence_root=evidence_root,
        control_root=control_root,
    )

    assert result["train_primary_accounted"] == 1
    assert result["train_primary_remaining"] == 0
