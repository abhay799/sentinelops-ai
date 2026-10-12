import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/phase_c06_train_loop.py")

spec = importlib.util.spec_from_file_location(
    "phase_c06_train_loop_a7",
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def post_injection_state() -> dict:
    return {
        "current_stage": "injection",
        "injected_service": "payment-service",
        "injection_start": "2026-10-12T19:59:52.267600+00:00",
        "partition": "TRAIN",
        "replacement_for": "C-TRAIN-BDR-12",
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
        "stage_timestamps": {
            "injection": {
                "started": "2026-10-12T19:59:52.268245+00:00"
            }
        },
        "started_utc": "2026-10-12T19:57:50.761657+00:00",
    }


def test_finalize_orphaned_post_injection_attempt_writes_registered_failure(
    tmp_path: Path,
):
    attempt = tmp_path / "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    state_path = attempt / "execution_state.json"
    write_json(state_path, post_injection_state())
    original_hash = sha256(state_path)

    summary_path = loop.finalize_orphaned_post_injection_attempt(
        attempt,
        failure_reason=(
            "direct_registered_invocation_terminated_after_injection_start"
        ),
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert summary_path == attempt / "run_summary.json"
    assert summary["status"] == loop.RUN_FAILED_AFTER_INJECTION
    assert summary["run_id"] == "C-SPARE-TRAIN-BDR-02"
    assert summary["artifact_run_id"] == (
        "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    )
    assert summary["seed"] == 300872472
    assert summary["replacement_for"] == "C-TRAIN-BDR-12"
    assert summary["registered_result_eligible"] is True
    assert summary["counted_in_analysis_denominator"] is True
    assert summary["invalid_reason"] is None
    assert summary["traceback"] is None
    assert summary["run_record"]["injection_start"] == (
        "2026-10-12T19:59:52.267600+00:00"
    )

    # Finalization must not rewrite the persisted execution evidence.
    assert sha256(state_path) == original_hash


def test_finalize_refuses_pre_injection_attempt(tmp_path: Path):
    attempt = tmp_path / "attempt"
    state = post_injection_state()
    state["injection_start"] = None
    write_json(attempt / "execution_state.json", state)

    with pytest.raises(
        RuntimeError,
        match="injection_start",
    ):
        loop.finalize_orphaned_post_injection_attempt(
            attempt,
            failure_reason="should_not_finalize",
        )

    assert not (attempt / "run_summary.json").exists()


def test_finalize_refuses_existing_summary(tmp_path: Path):
    attempt = tmp_path / "attempt"
    write_json(attempt / "execution_state.json", post_injection_state())
    write_json(attempt / "run_summary.json", {"existing": True})

    with pytest.raises(
        RuntimeError,
        match="run_summary",
    ):
        loop.finalize_orphaned_post_injection_attempt(
            attempt,
            failure_reason="must_not_overwrite",
        )

    assert json.loads(
        (attempt / "run_summary.json").read_text(encoding="utf-8")
    ) == {"existing": True}


def test_finalize_requires_execution_state(tmp_path: Path):
    attempt = tmp_path / "attempt"
    attempt.mkdir()

    with pytest.raises(
        RuntimeError,
        match="execution_state",
    ):
        loop.finalize_orphaned_post_injection_attempt(
            attempt,
            failure_reason="missing_state",
        )
