from __future__ import annotations

import asyncio
import hashlib
import json
import os
import resource
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import polars as pl
import yaml
from aiokafka import AIOKafkaConsumer

from sentinelops.chaos.ground_truth import (
    build_injection_record,
    persist_injection_record,
)
from sentinelops.chaos.harness import run_dry_run
from sentinelops.chaos.schema import ChaosRunRecord
from sentinelops.chaos.stage_events import utc_now

REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_PATH = REPO_ROOT / "evidence/C/C04_run_registry.json"
SCENARIO_CONFIG_PATH = REPO_ROOT / "configs/chaos_scenarios_v1.yaml"
BAD_DEPLOYMENT_PATH = REPO_ROOT / "configs/chaos_bad_deployment_v1.yaml"
EXECUTION_CONFIG_PATH = REPO_ROOT / "configs/execution.yaml"
TRAIN_EVIDENCE_ROOT = REPO_ROOT / "evidence/C/C06_train_runs"
WORK_ROOT = REPO_ROOT / "data/chaos/registered_work"
RAW_TOPIC = "sentinelops.telemetry.raw"
SERVICES = {
    "api-gateway": 8100,
    "user-service": 8101,
    "order-service": 8102,
    "payment-service": 8103,
    "inventory-service": 8104,
    "notification-service": 8105,
    "auth-service": 8106,
}
TARGET_SERVICE = "payment-service"
SCRIPTED_APPROVER = "scripted_approver_v1"

PIPELINE_SCRIPTS = {
    "detection": [
        "scripts/build_phase4_temporal_features.py",
        "scripts/train_phase5_anomaly.py",
    ],
    "correlation": [
        "scripts/build_phase6_graph.py",
        "scripts/build_phase7_incidents.py",
        "scripts/build_phase7_incident_intelligence.py",
    ],
    "rca": [
        "scripts/build_phase8_rca.py",
        "scripts/build_phase8_rca_summary.py",
    ],
    "challenge": [
        "scripts/build_phase9_challenger.py",
        "scripts/build_phase9_causal_disposition.py",
    ],
    "plan_guard": [
        "scripts/build_phase10_early_warning.py",
        "scripts/train_phase10_predictor.py",
        "scripts/build_phase11_counterfactual.py",
        "scripts/build_phase11_counterfactual_summary.py",
        "scripts/build_phase12_service_impact.py",
        "scripts/build_phase12_incident_priority.py",
        "scripts/build_phase13_remediation.py",
    ],
    "authorization": [
        "scripts/build_phase14_execution_requests.py",
        "scripts/build_phase14_approval_queue.py",
    ],
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _execution_state_path(run_dir: Path) -> Path:
    return run_dir / "execution_state.json"


def _update_execution_state(run_dir: Path, **updates: Any) -> dict[str, Any]:
    path = _execution_state_path(run_dir)
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
    else:
        state = {}
    state.update(updates)
    _write_json(path, state)
    return state


def _record_stage_state(run_dir: Path, stage: str, event: str) -> str:
    timestamp = utc_now().isoformat()
    path = _execution_state_path(run_dir)
    state = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    stage_timestamps = dict(state.get("stage_timestamps", {}))
    stage_state = dict(stage_timestamps.get(stage, {}))
    stage_state[event] = timestamp
    stage_timestamps[stage] = stage_state
    state["current_stage"] = stage
    state["stage_timestamps"] = stage_timestamps
    _write_json(path, state)
    return timestamp


def _memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith(("MemTotal:", "MemAvailable:")):
            key, value, *_ = line.split()
            values[key.rstrip(":")] = int(value)
    return values


def _load_yaml(path: Path, key: str) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)[key]


def _load_registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_registry_entry(run_id: str) -> dict[str, Any]:
    registry = _load_registry()
    for row in registry["execution_schedule"]:
        if row["run_id"] == run_id:
            return row
    for row in registry["reserved_spares"]:
        if row["run_id"] == run_id:
            return {
                "partition": row["partition"],
                "run_id": row["run_id"],
                "scenario": row["scenario"],
                "seed": row["seed"],
                "spare_ordinal": row["spare_ordinal"],
                "reserved_spare": True,
            }
    raise ValueError(f"unknown registered run_id: {run_id}")


def registered_and_spare_seeds() -> set[int]:
    registry = _load_registry()
    primary = {int(row["seed"]) for row in registry["registered_runs"]}
    spares = {int(row["seed"]) for row in registry["reserved_spares"]}
    return primary | spares


def assert_non_registry_seed(seed: int) -> None:
    if seed in registered_and_spare_seeds():
        raise ValueError(
            f"non-registry seed {seed} collides with the frozen registry or reserved spares"
        )


def run_non_registry_dry_run(scenario: str, seed: int) -> Path:
    assert_non_registry_seed(seed)
    run_dir = run_dry_run(scenario, seed)
    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if summary.get("classification") != "non_registry":
        raise RuntimeError("non-registry executor produced wrong classification")
    if summary.get("registered_result_eligible") is not False:
        raise RuntimeError("non-registry executor produced result-eligible output")
    return run_dir


def _prepare_workdir(run_id: str) -> Path:
    workdir = WORK_ROOT / run_id
    if workdir.exists():
        raise RuntimeError(f"workdir already exists for {run_id}")
    workdir.mkdir(parents=True)
    os.symlink(REPO_ROOT / "configs", workdir / "configs", target_is_directory=True)
    (workdir / "data/telemetry/raw").mkdir(parents=True, exist_ok=True)
    return workdir


async def _health(client: httpx.AsyncClient) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for service, port in SERVICES.items():
        service_result: dict[str, Any] = {}
        for endpoint in ("live", "ready"):
            try:
                response = await client.get(f"http://localhost:{port}/{endpoint}")
                service_result[endpoint] = {
                    "ok": response.status_code == 200,
                    "status_code": response.status_code,
                    "body": response.json(),
                }
            except Exception as exc:
                service_result[endpoint] = {
                    "ok": False,
                    "error": type(exc).__name__,
                }
        result[service] = service_result
    return result


def _health_all_ok(health: dict[str, Any]) -> bool:
    return all(values["live"].get("ok") and values["ready"].get("ok") for values in health.values())


async def _reset_payment(client: httpx.AsyncClient) -> dict[str, Any]:
    response = await client.post("http://localhost:8103/failure-mode/reset")
    response.raise_for_status()
    return response.json()


async def _workload(client: httpx.AsyncClient, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        started = time.monotonic()
        await asyncio.gather(
            *[
                client.get(
                    f"http://localhost:{port}/work",
                    timeout=8.0,
                )
                for port in SERVICES.values()
            ],
            return_exceptions=True,
        )
        remaining = 1.0 - (time.monotonic() - started)
        if remaining > 0:
            await asyncio.sleep(remaining)


async def _consume(
    consumer: AIOKafkaConsumer,
    events: list[dict[str, Any]],
    stop: asyncio.Event,
) -> None:
    while not stop.is_set():
        try:
            batch = await consumer.getmany(timeout_ms=500, max_records=1000)
        except Exception:
            await asyncio.sleep(0.1)
            continue
        for messages in batch.values():
            for message in messages:
                try:
                    events.append(json.loads(message.value.decode("utf-8")))
                except Exception:
                    continue


async def _activate_scenario(
    client: httpx.AsyncClient,
    scenario: str,
    seed: int,
    *,
    run_dir: Path | None = None,
) -> tuple[datetime, int]:
    scenario_config = _load_yaml(
        SCENARIO_CONFIG_PATH,
        "chaos_scenarios_v1",
    )
    spec = scenario_config["scenarios"][scenario]

    if scenario == "bad_deployment_rollback":
        profile = _load_yaml(BAD_DEPLOYMENT_PATH, "chaos_bad_deployment_v1")
        change = profile["change_event"]
        change_response = await client.post(
            "http://localhost:8103/change-event",
            json={
                "change_type": "deployment",
                "description": "Phase C registered bad-deployment injection",
                "version_before": str(change["version_before"]),
                "version_after": str(change["version_after"]),
                "actor": "phase_c_registered_harness",
            },
        )
        change_response.raise_for_status()
        first = profile["degradation_stages"][0]
        injection_start = utc_now()
        if run_dir is not None:
            _update_execution_state(
                run_dir,
                injection_start=injection_start.isoformat(),
                current_stage="injection",
            )
            _record_stage_state(run_dir, "injection", "started")
        response = await client.post(
            "http://localhost:8103/failure-mode",
            json=first["failure_mode"],
        )
        response.raise_for_status()
        await _workload(client, float(first["duration_seconds"]))
        second = profile["degradation_stages"][1]
        response = await client.post(
            "http://localhost:8103/failure-mode",
            json=second["failure_mode"],
        )
        response.raise_for_status()
        await _workload(client, float(second["duration_seconds"]))
        return injection_start, int(profile["total_injection_duration_seconds"])

    failure = spec["failure_mode"]
    injection_start = utc_now()
    if run_dir is not None:
        _update_execution_state(
            run_dir,
            injection_start=injection_start.isoformat(),
            current_stage="injection",
        )
        _record_stage_state(run_dir, "injection", "started")
    response = await client.post(
        "http://localhost:8103/failure-mode",
        json=failure,
    )
    response.raise_for_status()
    duration = int(spec["duration_seconds"])
    await _workload(client, float(duration))
    return injection_start, duration


def _run_script(workdir: Path, relative_script: str) -> dict[str, Any]:
    started = time.perf_counter()
    result = subprocess.run(
        [str(REPO_ROOT / ".venv/bin/python"), str(REPO_ROOT / relative_script)],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "script": relative_script,
        "returncode": result.returncode,
        "runtime_seconds": time.perf_counter() - started,
        "stdout": result.stdout[-20000:],
        "stderr": result.stderr[-20000:],
    }


def _run_stage(
    run_dir: Path,
    workdir: Path,
    stage: str,
) -> tuple[datetime | None, bool, list[dict[str, Any]]]:
    _record_stage_state(run_dir, stage, "started")
    logs: list[dict[str, Any]] = []
    for script in PIPELINE_SCRIPTS[stage]:
        result = _run_script(workdir, script)
        logs.append(result)
        if result["returncode"] != 0:
            _write_json(
                run_dir / f"{stage}.json",
                {
                    "stage": stage,
                    "status": "pipeline_error",
                    "timestamp": None,
                    "scripts": logs,
                },
            )
            _record_stage_state(run_dir, stage, "failed")
            return None, False, logs
    timestamp = utc_now()
    _write_json(
        run_dir / f"{stage}.json",
        {
            "stage": stage,
            "status": "completed",
            "timestamp": timestamp.isoformat(),
            "scripts": logs,
        },
    )
    _record_stage_state(run_dir, stage, "completed")
    return timestamp, True, logs


def _first_payment_detection(
    workdir: Path,
    injection_start: datetime,
) -> datetime | None:
    path = workdir / "data/processed/anomalies/anomaly_scores_v1.parquet"
    if not path.exists():
        return None
    frame = pl.read_parquet(path)
    required = {"service", "feature_as_of_time", "is_anomaly"}
    if not required.issubset(frame.columns):
        return None
    rows = (
        frame.filter((pl.col("service") == TARGET_SERVICE) & (pl.col("is_anomaly") == 1))
        .sort("feature_as_of_time")
        .select("feature_as_of_time")
        .to_series()
        .to_list()
    )
    for value in rows:
        if isinstance(value, datetime):
            dt = value
        else:
            try:
                dt = datetime.fromisoformat(str(value))
            except ValueError:
                continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt.astimezone(timezone.utc) >= injection_start:
            return dt.astimezone(timezone.utc)
    return None


def _select_rca_ranking(workdir: Path) -> tuple[str | None, list[str]]:
    members_path = workdir / "data/processed/incidents/incident_members_v1.parquet"
    hypotheses_path = workdir / "data/processed/rca/rca_hypotheses_v1.parquet"
    if not members_path.exists() or not hypotheses_path.exists():
        return None, []
    members = pl.read_parquet(members_path)
    hypotheses = pl.read_parquet(hypotheses_path)
    if "service" not in members.columns:
        return None, []
    ids = (
        members.filter(pl.col("service") == TARGET_SERVICE)
        .select("incident_id")
        .unique()
        .to_series()
        .to_list()
    )
    if not ids:
        return None, []
    incident_id = str(ids[0])
    ranking = (
        hypotheses.filter(pl.col("incident_id") == incident_id)
        .sort("rank")
        .select("candidate_service")
        .to_series()
        .cast(pl.String)
        .to_list()
    )
    return incident_id, ranking


def _augment_stage_evidence(
    run_dir: Path,
    stage: str,
    details: dict[str, Any],
) -> None:
    path = run_dir / f"{stage}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["details"] = details
    _write_json(path, payload)


def _select_execution_request(workdir: Path) -> str | None:
    path = workdir / "data/processed/execution/execution_requests_v1.parquet"
    if not path.exists():
        return None
    frame = pl.read_parquet(path)
    matches = frame.filter(
        (pl.col("candidate_service") == TARGET_SERVICE)
        & (pl.col("recommended_action") == "rollback")
        & pl.col("preapproval_ready")
    )
    if matches.is_empty():
        return None
    return str(matches["execution_request_id"][0])


def _approve_request(workdir: Path, request_id: str) -> dict[str, Any]:
    script = "scripts/phase14_approve.py"
    result = subprocess.run(
        [
            str(REPO_ROOT / ".venv/bin/python"),
            str(REPO_ROOT / script),
            request_id,
            "--approve",
            "--approved-by",
            SCRIPTED_APPROVER,
            "--reason",
            "Phase C registered scripted authorization",
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "script": script,
        "returncode": result.returncode,
        "stdout": result.stdout[-20000:],
        "stderr": result.stderr[-20000:],
    }


def _execute_request(workdir: Path, request_id: str) -> dict[str, Any]:
    script = "scripts/execute_phase14_request.py"
    result = subprocess.run(
        [
            str(REPO_ROOT / ".venv/bin/python"),
            str(REPO_ROOT / script),
            request_id,
        ],
        cwd=workdir,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "script": script,
        "returncode": result.returncode,
        "stdout": result.stdout[-20000:],
        "stderr": result.stderr[-20000:],
    }


def _execution_result(workdir: Path, request_id: str) -> dict[str, Any] | None:
    path = workdir / "data/processed/execution/execution_results_v1.parquet"
    if not path.exists():
        return None
    frame = pl.read_parquet(path)
    rows = frame.filter(pl.col("execution_request_id") == request_id).to_dicts()
    return rows[0] if rows else None


async def run_registered_train(
    run_id: str,
    *,
    replacement_for: str | None = None,
) -> Path:
    entry = _load_registry_entry(run_id)
    if entry["partition"] != "TRAIN":
        raise RuntimeError("C6 runner accepts TRAIN entries only")

    run_dir = TRAIN_EVIDENCE_ROOT / run_id
    if run_dir.exists():
        raise RuntimeError(f"registered evidence already exists for {run_id}")
    run_dir.mkdir(parents=True)
    _update_execution_state(
        run_dir,
        run_id=run_id,
        partition="TRAIN",
        scenario=str(entry["scenario"]),
        seed=int(entry["seed"]),
        replacement_for=replacement_for,
        injected_service=TARGET_SERVICE,
        started_utc=utc_now().isoformat(),
        injection_start=None,
        current_stage="preflight",
        stage_timestamps={},
    )
    workdir = _prepare_workdir(run_id)
    ground_truth_root = TRAIN_EVIDENCE_ROOT / "_ground_truth_injection_only"

    wall_start = time.perf_counter()
    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    memory_before = _memory_snapshot()
    service_killed = False
    emergency_cleanup = {
        "performed": False,
        "counted_as_remediation": False,
        "reason": None,
        "status": None,
    }

    consumer = AIOKafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers="localhost:9092",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        group_id=None,
    )
    events: list[dict[str, Any]] = []
    stop_consumer = asyncio.Event()

    async with httpx.AsyncClient(timeout=10.0) as client:
        pre_health = await _health(client)
        _write_json(run_dir / "preflight_health.json", pre_health)
        if not _health_all_ok(pre_health):
            _write_json(
                run_dir / "run_summary.json",
                {
                    "classification": "registered",
                    "partition": "TRAIN",
                    "run_id": run_id,
                    "status": "infrastructure_invalid_before_injection",
                    "invalid_reason": "baseline_health_failed",
                    "registry_entry": entry,
                    "replacement_for": replacement_for,
                },
            )
            return run_dir

        _record_stage_state(run_dir, "pre_injection_reset", "started")
        await _reset_payment(client)
        _record_stage_state(run_dir, "pre_injection_reset", "completed")
        await consumer.start()
        consume_task = asyncio.create_task(_consume(consumer, events, stop_consumer))

        scenario_config = _load_yaml(
            SCENARIO_CONFIG_PATH,
            "chaos_scenarios_v1",
        )
        baseline_seconds = int(scenario_config["baseline_seconds"])
        cooldown_seconds = int(scenario_config["cooldown_seconds"])

        await _workload(client, float(baseline_seconds))
        _record_stage_state(run_dir, "injection_activation", "started")
        injection_start, injection_seconds = await _activate_scenario(
            client,
            str(entry["scenario"]),
            int(entry["seed"]),
            run_dir=run_dir,
        )
        planned_injection_complete_time = utc_now()
        injection_end: datetime | None = None

        stop_consumer.set()
        await consume_task
        await consumer.stop()

        raw_path = workdir / "data/telemetry/raw/phase4_capture.ndjson"
        with raw_path.open("w", encoding="utf-8") as handle:
            for event in events:
                handle.write(json.dumps(event, sort_keys=True) + "\n")

        telemetry_manifest = {
            "path": str(raw_path.relative_to(REPO_ROOT)),
            "event_count": len(events),
            "sha256": _sha256(raw_path),
            "injection_start": injection_start.isoformat(),
            "planned_injection_complete_time": (planned_injection_complete_time.isoformat()),
        }
        _write_json(run_dir / "telemetry_manifest.json", telemetry_manifest)

        ground_truth = build_injection_record(
            run_id=run_id,
            scenario=str(entry["scenario"]),
            seed=int(entry["seed"]),
            injection_start=injection_start.isoformat(),
            injected_service=TARGET_SERVICE,
            baseline_seconds=baseline_seconds,
            injection_seconds=injection_seconds,
            cooldown_seconds=cooldown_seconds,
            non_registry=False,
        )
        detection_stage_time, detection_stage_ok, _ = _run_stage(run_dir, workdir, "detection")
        detection_time = (
            _first_payment_detection(workdir, injection_start) if detection_stage_ok else None
        )
        _augment_stage_evidence(
            run_dir,
            "detection",
            {
                "qualifying_detection_time": (
                    detection_time.isoformat() if detection_time else None
                ),
                "detected": detection_time is not None,
                "detector_mode": "TRAIN_legacy_development_only",
            },
        )

        correlation_time = None
        rca_output_time = None
        guard_decision_time = None
        remediation_time = None
        verification_time = None
        recovery_time = None
        selected_request_id = None
        execution_result = None
        chain_status = "missed_detection"

        if detection_time is not None:
            correlation_time, correlation_ok, _ = _run_stage(run_dir, workdir, "correlation")
            if correlation_ok:
                rca_output_time, rca_ok, _ = _run_stage(run_dir, workdir, "rca")
                incident_id, ranking = _select_rca_ranking(workdir)
                _augment_stage_evidence(
                    run_dir,
                    "rca",
                    {
                        "incident_id": incident_id,
                        "ranking": ranking,
                    },
                )
                if rca_ok:
                    _, challenge_ok, _ = _run_stage(run_dir, workdir, "challenge")
                    if challenge_ok:
                        plan_guard_time, plan_guard_ok, _ = _run_stage(
                            run_dir, workdir, "plan_guard"
                        )
                        if plan_guard_ok:
                            guard_decision_time = plan_guard_time
                            _, authorization_ok, _ = _run_stage(run_dir, workdir, "authorization")
                            if authorization_ok:
                                selected_request_id = _select_execution_request(workdir)
                                if selected_request_id:
                                    approval = _approve_request(
                                        workdir,
                                        selected_request_id,
                                    )
                                    approval_time = utc_now()
                                    _write_json(
                                        run_dir / "human_authorization.json",
                                        {
                                            "stage": "human_authorization",
                                            "timestamp": approval_time.isoformat(),
                                            "approver": SCRIPTED_APPROVER,
                                            "request_id": selected_request_id,
                                            "result": approval,
                                        },
                                    )
                                    if approval["returncode"] == 0:
                                        _record_stage_state(run_dir, "remediation", "started")
                                        remediation_time = utc_now()
                                        injection_end = remediation_time
                                        execution = _execute_request(
                                            workdir,
                                            selected_request_id,
                                        )
                                        verification_time = utc_now()
                                        _record_stage_state(run_dir, "verification", "started")
                                        execution_result = _execution_result(
                                            workdir,
                                            selected_request_id,
                                        )
                                        _write_json(
                                            run_dir / "remediation.json",
                                            {
                                                "stage": "remediation",
                                                "timestamp": remediation_time.isoformat(),
                                                "request_id": selected_request_id,
                                                "result": execution,
                                            },
                                        )
                                        recovered = bool(
                                            execution_result
                                            and execution_result.get("recovery_verified")
                                        )
                                        if recovered:
                                            recovery_time = verification_time
                                        _record_stage_state(run_dir, "verification", "completed")
                                        _write_json(
                                            run_dir / "verification.json",
                                            {
                                                "stage": "verification",
                                                "timestamp": verification_time.isoformat(),
                                                "recovery_verified": recovered,
                                                "execution_result": execution_result,
                                            },
                                        )
                                        chain_status = (
                                            "executed_verified"
                                            if recovered
                                            else "remediation_or_verification_failed"
                                        )
                                    else:
                                        chain_status = "authorization_failed"
                                else:
                                    chain_status = "no_executable_rollback_request"
                            else:
                                chain_status = "authorization_stage_failed"
                        else:
                            chain_status = "plan_or_guard_stage_failed"
                    else:
                        chain_status = "challenge_stage_failed"
                else:
                    chain_status = "rca_stage_failed"
            else:
                chain_status = "correlation_stage_failed"

        if recovery_time is None:
            emergency_cleanup["performed"] = True
            emergency_cleanup["reason"] = chain_status
            try:
                await _reset_payment(client)
                cleanup_time = utc_now()
                if injection_end is None:
                    injection_end = cleanup_time
                cleanup_health = await _health(client)
                emergency_cleanup["status"] = (
                    "verified" if _health_all_ok(cleanup_health) else "health_failed"
                )
                _write_json(
                    run_dir / "cleanup.json",
                    {
                        **emergency_cleanup,
                        "timestamp": utc_now().isoformat(),
                        "health": cleanup_health,
                    },
                )
            except Exception as exc:
                emergency_cleanup["status"] = type(exc).__name__
                _write_json(run_dir / "cleanup.json", emergency_cleanup)

        post_health = await _health(client)
        service_killed = not _health_all_ok(post_health)
        _write_json(run_dir / "post_health.json", post_health)

        if injection_end is None:
            injection_end = utc_now()
        ground_truth["injection_end"] = injection_end.isoformat()
        telemetry_manifest["injection_end"] = injection_end.isoformat()
        _write_json(run_dir / "telemetry_manifest.json", telemetry_manifest)

        # Ground truth is persisted only after scored verification or cleanup
        # verification has completed.
        persist_injection_record(
            ground_truth_root,
            run_id,
            ground_truth,
        )

        await asyncio.sleep(float(cooldown_seconds))
        cooldown_health = await _health(client)
        _write_json(run_dir / "cooldown_health.json", cooldown_health)

    record = ChaosRunRecord(
        run_id=run_id,
        seed=int(entry["seed"]),
        scenario=str(entry["scenario"]),
        approver=SCRIPTED_APPROVER,
        injection_start=injection_start,
        injection_end=injection_end,
        recovery_time=recovery_time,
        detection_time=detection_time,
        rca_output_time=rca_output_time,
        guard_decision_time=guard_decision_time,
        remediation_time=remediation_time,
        verification_time=verification_time,
    )

    cpu_after = resource.getrusage(resource.RUSAGE_SELF)
    summary = {
        "classification": "registered",
        "partition": "TRAIN",
        "status": chain_status,
        "registry_entry": entry,
        "replacement_for": replacement_for,
        "run_record": record.model_dump(mode="json"),
        "telemetry_manifest": telemetry_manifest,
        "selected_execution_request_id": selected_request_id,
        "execution_result": execution_result,
        "emergency_cleanup": emergency_cleanup,
        "resources": {
            "wall_clock_seconds": time.perf_counter() - wall_start,
            "cpu_user_seconds": cpu_after.ru_utime - cpu_before.ru_utime,
            "cpu_system_seconds": cpu_after.ru_stime - cpu_before.ru_stime,
            "memory_before_kib": memory_before,
            "memory_after_kib": _memory_snapshot(),
            "service_killed": service_killed,
        },
    }
    _update_execution_state(run_dir, current_stage="completed", completed_utc=utc_now().isoformat())
    _write_json(run_dir / "run_summary.json", summary)
    return run_dir
