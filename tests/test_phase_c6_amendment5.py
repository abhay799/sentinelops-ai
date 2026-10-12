from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

from sentinelops.chaos import registered_harness


MODULE_PATH = Path("scripts/phase_c06_train_loop.py")
SPEC = importlib.util.spec_from_file_location("phase_c06_train_loop_a5", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
train_loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(train_loop)


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"status": "ok"}


class FakeClient:
    def __init__(self):
        self.posts = []

    async def post(self, url, **kwargs):
        self.posts.append((url, kwargs.get("json")))
        return FakeResponse()


@pytest.mark.parametrize(
    "scenario,expected_duration",
    [
        ("latency", 120),
        ("errors", 120),
        ("bad_deployment_rollback", 180),
    ],
)
def test_registered_path_loads_each_frozen_scenario(
    monkeypatch: pytest.MonkeyPatch,
    scenario: str,
    expected_duration: int,
):
    async def no_workload(client, seconds):
        return None

    monkeypatch.setattr(registered_harness, "_workload", no_workload)

    client = FakeClient()
    _, duration = asyncio.run(
        registered_harness._activate_scenario(
            client,
            scenario,
            1900005001,
        )
    )

    assert duration == expected_duration


def test_bad_deployment_registered_path_uses_frozen_yaml_contract(
    monkeypatch: pytest.MonkeyPatch,
):
    async def no_workload(client, seconds):
        return None

    monkeypatch.setattr(registered_harness, "_workload", no_workload)

    client = FakeClient()
    asyncio.run(
        registered_harness._activate_scenario(
            client,
            "bad_deployment_rollback",
            1900005002,
        )
    )

    change_calls = [
        payload
        for url, payload in client.posts
        if url.endswith("/change-event")
    ]
    failure_calls = [
        payload
        for url, payload in client.posts
        if url.endswith("/failure-mode")
    ]

    assert len(change_calls) == 1
    assert change_calls[0]["version_before"] == "2.7"
    assert change_calls[0]["version_after"] == "2.8"

    assert [x["mode"] for x in failure_calls] == [
        "latency",
        "errors",
    ]


def _entry(run_id="NR-A5-DEFECT"):
    return {
        "partition": "TRAIN",
        "run_id": run_id,
        "scenario": "bad_deployment_rollback",
        "seed": 1900005101,
    }


@pytest.mark.parametrize(
    "exception",
    [
        KeyError("change_event"),
        ValueError("bad harness value"),
        RuntimeError("harness bug"),
    ],
)
def test_non_environmental_pre_injection_exception_is_harness_defect(
    tmp_path: Path,
    exception: Exception,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    entry = _entry()

    def executor(_entry, _replacement_for):
        raise exception

    with pytest.raises(type(exception)):
        train_loop._execute_once(
            entry,
            replacement_for=None,
            evidence_root=evidence,
            control_root=control,
            executor=executor,
        )

    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, entry["run_id"])
    )

    assert summary["status"] == "harness_defect"
    assert summary["registered_result_eligible"] is False
    assert summary["counted_in_analysis_denominator"] is False


@pytest.mark.parametrize(
    "exception",
    [
        httpx.ReadTimeout("timeout"),
        httpx.ConnectError("connect"),
    ],
)
def test_environmental_transport_exception_remains_infrastructure_invalid(
    tmp_path: Path,
    exception: Exception,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"
    entry = _entry("NR-A5-ENV")

    def executor(_entry, _replacement_for):
        raise exception

    with pytest.raises(type(exception)):
        train_loop._execute_once(
            entry,
            replacement_for=None,
            evidence_root=evidence,
            control_root=control,
            executor=executor,
        )

    summary = train_loop.read_json(
        train_loop.run_summary_path(evidence, entry["run_id"])
    )

    assert summary["status"].startswith("infrastructure_invalid")


def _write_execution_state(
    evidence_root: Path,
    run_id: str,
    stage: str,
    *,
    injected: bool,
):
    path = evidence_root / run_id / "execution_state.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "run_id": run_id,
                "scenario": "bad_deployment_rollback",
                "seed": 1900005201,
                "injection_start": (
                    "2026-10-12T18:00:00Z"
                    if injected
                    else None
                ),
                "current_stage": stage,
                "stage_timestamps": {
                    stage: {
                        "started": "2026-10-12T18:00:00Z"
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )


@pytest.mark.parametrize(
    "stage,injected",
    [
        ("preflight", False),
        ("pre_injection_reset", False),
        ("baseline", False),
        ("injection", True),
        ("detection", True),
        ("correlation", True),
        ("rca", True),
        ("challenge", True),
        ("plan_guard", True),
        ("authorization", True),
        ("remediation", True),
        ("verification", True),
    ],
)
def test_non_environmental_exception_is_harness_defect_at_every_stage(
    tmp_path: Path,
    stage: str,
    injected: bool,
):
    evidence = tmp_path / "evidence"
    active = {
        "run_id": f"NR-A5-{stage}",
        "scenario": "bad_deployment_rollback",
        "partition": "TRAIN",
        "seed": 1900005201,
        "replacement_for": None,
        "host_check": {
            "boot_id": "same-boot",
            "timestamp_utc": "2026-10-12T17:59:00Z",
            "uptime_seconds": 100.0,
        },
    }

    _write_execution_state(
        evidence,
        active["run_id"],
        stage,
        injected=injected,
    )

    status, reason, _, _ = train_loop.classify_interruption(
        active,
        evidence_root=evidence,
        current_host_check={
            "boot_id": "same-boot",
            "timestamp_utc": "2026-10-12T18:01:00Z",
            "uptime_seconds": 220.0,
        },
        exception=RuntimeError(f"defect-{stage}"),
    )

    assert status == "harness_defect"
    assert reason == "non_environmental_exception:RuntimeError"


@pytest.mark.parametrize(
    "stage,injected",
    [
        ("preflight", False),
        ("pre_injection_reset", False),
        ("baseline", False),
        ("injection", True),
        ("detection", True),
        ("correlation", True),
        ("rca", True),
        ("challenge", True),
        ("plan_guard", True),
        ("authorization", True),
        ("remediation", True),
        ("verification", True),
    ],
)
@pytest.mark.parametrize(
    "exception",
    [
        httpx.ReadTimeout("timeout"),
        httpx.ConnectError("connect"),
    ],
)
def test_environmental_exception_classification_by_stage(
    tmp_path: Path,
    stage: str,
    injected: bool,
    exception: Exception,
):
    evidence = tmp_path / "evidence"
    active = {
        "run_id": f"NR-A5-ENV-{stage}",
        "scenario": "latency",
        "partition": "TRAIN",
        "seed": 1900005301,
        "replacement_for": None,
        "host_check": {
            "boot_id": "same-boot",
            "timestamp_utc": "2026-10-12T17:59:00Z",
            "uptime_seconds": 100.0,
        },
    }

    _write_execution_state(
        evidence,
        active["run_id"],
        stage,
        injected=injected,
    )

    status, _, _, _ = train_loop.classify_interruption(
        active,
        evidence_root=evidence,
        current_host_check={
            "boot_id": "same-boot",
            "timestamp_utc": "2026-10-12T18:01:00Z",
            "uptime_seconds": 220.0,
        },
        exception=exception,
    )

    if injected:
        assert status == "run_failed_after_injection"
    else:
        assert status == "infrastructure_invalid_interrupted"


def test_recorded_host_event_remains_environmental_even_for_harness_exception(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    active = {
        "run_id": "NR-A5-HOST",
        "scenario": "errors",
        "partition": "TRAIN",
        "seed": 1900005401,
        "replacement_for": None,
        "host_check": {
            "boot_id": "boot-a",
            "timestamp_utc": "2026-10-12T17:59:00Z",
            "uptime_seconds": 100.0,
        },
    }

    _write_execution_state(
        evidence,
        active["run_id"],
        "rca",
        injected=True,
    )

    status, reason, _, _ = train_loop.classify_interruption(
        active,
        evidence_root=evidence,
        current_host_check={
            "boot_id": "boot-b",
            "timestamp_utc": "2026-10-12T18:01:00Z",
            "uptime_seconds": 5.0,
        },
        exception=RuntimeError("would otherwise be harness defect"),
    )

    assert status == "infrastructure_invalid_host_event"
    assert reason == "host_boot_id_changed"


def test_harness_defect_before_injection_is_original_seed_reexecution_eligible(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    run_id = "C-SPARE-TRAIN-BDR-02"

    _write_execution_state(
        evidence,
        run_id,
        "injection",
        injected=False,
    )

    state = train_loop._execution_state(evidence, run_id)

    assert state["injection_start"] is None
    assert state["current_stage"] == "injection"


def test_preserved_pre_injection_harness_defect_is_reexecution_eligible():
    summary = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
        "status": "harness_defect",
        "registered_result_eligible": False,
        "counted_in_analysis_denominator": False,
        "execution_state": {
            "current_stage": "injection_activation",
            "injection_start": None,
        },
    }

    assert train_loop.harness_defect_reexecution_eligible(summary) is True


def test_post_injection_harness_defect_is_not_reexecution_eligible():
    summary = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
        "status": "harness_defect",
        "registered_result_eligible": False,
        "execution_state": {
            "current_stage": "detection",
            "injection_start": "2026-10-11T21:16:00Z",
        },
    }

    assert train_loop.harness_defect_reexecution_eligible(summary) is False


def test_non_harness_failure_is_not_original_seed_reexecution_eligible():
    summary = {
        "run_id": "C-TRAIN-BDR-12",
        "seed": 681377953,
        "status": "infrastructure_invalid_interrupted",
        "execution_state": {
            "injection_start": None,
        },
    }

    assert train_loop.harness_defect_reexecution_eligible(summary) is False


def test_harness_defect_reexecution_uses_separate_attempt_directory(tmp_path: Path):
    evidence = tmp_path / "evidence"
    original = evidence / "C-SPARE-TRAIN-BDR-02"
    original.mkdir(parents=True)

    original_summary = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "seed": 300872472,
        "status": "harness_defect",
        "registered_result_eligible": False,
        "execution_state": {
            "injection_start": None,
            "current_stage": "injection_activation",
        },
    }

    (original / "run_summary.json").write_text(
        json.dumps(original_summary) + "\n",
        encoding="utf-8",
    )

    rerun_dir = train_loop.harness_defect_reexecution_dir(
        evidence,
        "C-SPARE-TRAIN-BDR-02",
    )

    assert rerun_dir != original
    assert rerun_dir.name == "C-SPARE-TRAIN-BDR-02__a5_rerun"
    assert (original / "run_summary.json").exists()


def test_harness_defect_reexecution_dir_refuses_existing_attempt(tmp_path: Path):
    evidence = tmp_path / "evidence"
    rerun = evidence / "C-SPARE-TRAIN-BDR-02__a5_rerun"
    rerun.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="already exists"):
        train_loop.harness_defect_reexecution_dir(
            evidence,
            "C-SPARE-TRAIN-BDR-02",
        )


def test_registered_harness_reexecution_artifact_id_is_separate():
    assert (
        registered_harness.reexecution_artifact_id(
            "C-SPARE-TRAIN-BDR-02",
            "a5_rerun",
        )
        == "C-SPARE-TRAIN-BDR-02__a5_rerun"
    )


def test_registered_harness_normal_artifact_id_is_original_run_id():
    assert (
        registered_harness.reexecution_artifact_id(
            "C-TRAIN-LAT-01",
            None,
        )
        == "C-TRAIN-LAT-01"
    )


def test_run_registered_train_signature_supports_attempt_label():
    import inspect

    params = inspect.signature(
        registered_harness.run_registered_train
    ).parameters

    assert "attempt_label" in params


def test_attempt_label_does_not_change_registry_identity():
    artifact_id = registered_harness.reexecution_artifact_id(
        "C-SPARE-TRAIN-BDR-02",
        "a5_rerun",
    )

    assert artifact_id == "C-SPARE-TRAIN-BDR-02__a5_rerun"
    assert artifact_id != "C-SPARE-TRAIN-BDR-02"


def test_attempt_label_routes_registered_evidence_to_separate_namespace(
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
            attempt_label="a5_rerun",
        )
    )

    assert result == (
        evidence / "C-SPARE-TRAIN-BDR-02__a5_rerun"
    )

    assert not (
        evidence / "C-SPARE-TRAIN-BDR-02"
    ).exists()

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


def test_execute_reexecution_calls_registered_executor_with_attempt_label(
    monkeypatch: pytest.MonkeyPatch,
):
    calls = []

    async def fake_run_registered_train(
        run_id,
        *,
        replacement_for=None,
        attempt_label=None,
    ):
        calls.append(
            {
                "run_id": run_id,
                "replacement_for": replacement_for,
                "attempt_label": attempt_label,
            }
        )
        return Path("/tmp/fake-rerun")

    monkeypatch.setattr(
        train_loop,
        "run_registered_train",
        fake_run_registered_train,
    )

    entry = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "partition": "TRAIN",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
    }

    asyncio.run(
        train_loop._default_executor(
            entry,
            "C-TRAIN-BDR-12",
            attempt_label="a5_rerun",
        )
    )

    assert calls == [
        {
            "run_id": "C-SPARE-TRAIN-BDR-02",
            "replacement_for": "C-TRAIN-BDR-12",
            "attempt_label": "a5_rerun",
        }
    ]


def test_execute_once_reexecution_bypasses_preserved_original_summary(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"

    entry = {
        "run_id": "C-SPARE-TRAIN-BDR-02",
        "partition": "TRAIN",
        "scenario": "bad_deployment_rollback",
        "seed": 300872472,
    }

    original = evidence / entry["run_id"]
    original.mkdir(parents=True)

    original_summary = {
        "run_id": entry["run_id"],
        "scenario": entry["scenario"],
        "seed": entry["seed"],
        "status": "harness_defect",
        "registered_result_eligible": False,
        "counted_in_analysis_denominator": False,
        "execution_state": {
            "injection_start": None,
            "current_stage": "injection_activation",
        },
    }

    (original / "run_summary.json").write_text(
        json.dumps(original_summary) + "\n",
        encoding="utf-8",
    )

    calls = []

    def executor(_entry, _replacement_for):
        calls.append(
            (_entry["run_id"], _replacement_for)
        )

        rerun = (
            evidence
            / "C-SPARE-TRAIN-BDR-02__a5_rerun"
        )
        rerun.mkdir(parents=True)

        (rerun / "run_summary.json").write_text(
            json.dumps(
                {
                    "run_id": entry["run_id"],
                    "scenario": entry["scenario"],
                    "seed": entry["seed"],
                    "status": "executed_verified",
                    "registered_result_eligible": True,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    result = train_loop._execute_once(
        entry,
        replacement_for="C-TRAIN-BDR-12",
        evidence_root=evidence,
        control_root=control,
        executor=executor,
        attempt_label="a5_rerun",
    )

    assert calls == [
        (
            "C-SPARE-TRAIN-BDR-02",
            "C-TRAIN-BDR-12",
        )
    ]

    assert result["status"] == "executed_verified"

    # Historical record remains untouched.
    preserved = json.loads(
        (
            original / "run_summary.json"
        ).read_text(encoding="utf-8")
    )
    assert preserved["status"] == "harness_defect"


def test_existing_harness_defect_stops_loop_and_consumes_no_spare(
    tmp_path: Path,
):
    evidence = tmp_path / "evidence"
    control = tmp_path / "control"

    primary = {
        "global_execution_index": 1,
        "partition": "TRAIN",
        "partition_execution_index": 1,
        "run_id": "NR-TRAIN-LAT-01",
        "scenario": "latency",
        "seed": 1900007001,
    }

    spare = {
        "partition": "TRAIN",
        "run_id": "NR-SPARE-TRAIN-LAT-01",
        "scenario": "latency",
        "seed": 1900007002,
        "spare_ordinal": 1,
    }

    registry = {
        "execution_schedule": [primary],
        "reserved_spares": [spare],
    }

    run_dir = evidence / primary["run_id"]
    run_dir.mkdir(parents=True)

    (run_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "run_id": primary["run_id"],
                "scenario": primary["scenario"],
                "seed": primary["seed"],
                "status": "harness_defect",
                "registered_result_eligible": False,
                "counted_in_analysis_denominator": False,
                "execution_state": {
                    "injection_start": None,
                    "current_stage": "baseline",
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    calls = []

    def executor(entry, replacement_for):
        calls.append(entry["run_id"])

    with pytest.raises(RuntimeError, match="harness_defect"):
        train_loop.run_train_loop(
            registry=registry,
            evidence_root=evidence,
            control_root=control,
            executor=executor,
        )

    assert calls == []

    assert not (
        evidence / spare["run_id"]
    ).exists()
