import asyncio
import json
from pathlib import Path

import pytest

import importlib.util

SCRIPT_PATH = Path("scripts/phase_c06_train_loop.py")

spec = importlib.util.spec_from_file_location(
    "phase_c06_train_loop_a6",
    SCRIPT_PATH,
)
assert spec is not None
assert spec.loader is not None

train_loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(train_loop)
from sentinelops.chaos import registered_harness


def test_environmental_preinjection_retry_gets_new_attempt_namespace():
    assert (
        registered_harness.reexecution_artifact_id(
            "C-SPARE-TRAIN-BDR-02",
            "a5_rerun_02",
        )
        == "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    )


def test_partial_environmental_attempt_is_preserved_and_retryable(
    tmp_path: Path,
):
    attempt = (
        tmp_path
        / "C-SPARE-TRAIN-BDR-02__a5_rerun"
    )
    attempt.mkdir()

    state = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
        "current_stage": "pre_injection_reset",
        "injection_start": None,
    }

    (attempt / "execution_state.json").write_text(
        json.dumps(state) + "\n",
        encoding="utf-8",
    )

    result = train_loop.preinjection_environmental_retry_eligible(
        attempt,
        exception_name="ReadTimeout",
    )

    assert result is True


def test_partial_attempt_with_injection_start_is_not_retryable(
    tmp_path: Path,
):
    attempt = (
        tmp_path
        / "C-SPARE-TRAIN-BDR-02__a5_rerun"
    )
    attempt.mkdir()

    state = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
        "current_stage": "injection",
        "injection_start": "2026-10-12T20:00:00+00:00",
    }

    (attempt / "execution_state.json").write_text(
        json.dumps(state) + "\n",
        encoding="utf-8",
    )

    result = train_loop.preinjection_environmental_retry_eligible(
        attempt,
        exception_name="ReadTimeout",
    )

    assert result is False


@pytest.mark.parametrize(
    "exception_name",
    ["ReadTimeout", "ConnectTimeout", "ConnectError"],
)
def test_only_recognized_environmental_httpx_failures_are_retryable(
    tmp_path: Path,
    exception_name: str,
):
    attempt = tmp_path / exception_name
    attempt.mkdir()

    (attempt / "execution_state.json").write_text(
        json.dumps(
            {
                "injection_start": None,
                "current_stage": "pre_injection_reset",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        train_loop.preinjection_environmental_retry_eligible(
            attempt,
            exception_name=exception_name,
        )
        is True
    )


def test_generic_exception_is_not_environmental_retry(
    tmp_path: Path,
):
    attempt = tmp_path / "generic"
    attempt.mkdir()

    (attempt / "execution_state.json").write_text(
        json.dumps(
            {
                "injection_start": None,
                "current_stage": "pre_injection_reset",
            }
        )
        + "\n",
        encoding="utf-8",
    )

    assert (
        train_loop.preinjection_environmental_retry_eligible(
            attempt,
            exception_name="RuntimeError",
        )
        is False
    )


def test_environmental_retry_uses_distinct_second_attempt_namespace(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"

    first = evidence / "C-SPARE-TRAIN-BDR-02__a5_rerun"
    first.mkdir(parents=True)

    second = train_loop.environmental_retry_dir(
        evidence,
        "C-SPARE-TRAIN-BDR-02",
        attempt_label="a5_rerun_02",
    )

    assert second == (
        evidence / "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    )
    assert first.exists()


def test_environmental_retry_refuses_existing_second_attempt(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"

    second = evidence / "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    second.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="already exists"):
        train_loop.environmental_retry_dir(
            evidence,
            "C-SPARE-TRAIN-BDR-02",
            attempt_label="a5_rerun_02",
        )


def test_second_attempt_preserves_registered_identity_and_seed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    evidence = tmp_path / "evidence"
    work = tmp_path / "work"

    monkeypatch.setattr(
        registered_harness,
        "TRAIN_EVIDENCE_ROOT",
        evidence,
    )
    monkeypatch.setattr(
        registered_harness,
        "WORK_ROOT",
        work,
    )
    monkeypatch.setattr(
        registered_harness,
        "_load_registry_entry",
        lambda run_id: {
            "run_id": run_id,
            "partition": "TRAIN",
            "scenario": "bad_deployment_rollback",
            "seed": 300872472,
        },
    )

    class DummyConsumer:
        def __init__(self, *args, **kwargs):
            pass

    class DummyClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

    async def unhealthy(_client):
        return {"synthetic": True}

    monkeypatch.setattr(
        registered_harness,
        "AIOKafkaConsumer",
        DummyConsumer,
    )
    monkeypatch.setattr(
        registered_harness.httpx,
        "AsyncClient",
        lambda *args, **kwargs: DummyClient(),
    )
    monkeypatch.setattr(
        registered_harness,
        "_health",
        unhealthy,
    )
    monkeypatch.setattr(
        registered_harness,
        "_health_all_ok",
        lambda _health: False,
    )

    result = asyncio.run(
        registered_harness.run_registered_train(
            "C-SPARE-TRAIN-BDR-02",
            replacement_for="C-TRAIN-BDR-12",
            attempt_label="a5_rerun_02",
        )
    )

    assert result == (
        evidence
        / "C-SPARE-TRAIN-BDR-02__a5_rerun_02"
    )

    summary = json.loads(
        (
            result / "run_summary.json"
        ).read_text(encoding="utf-8")
    )

    assert (
        summary["registry_entry"]["run_id"]
        == "C-SPARE-TRAIN-BDR-02"
    )
    assert summary["registry_entry"]["seed"] == 300872472
