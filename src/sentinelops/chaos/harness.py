from __future__ import annotations

import json
import resource
import time
from pathlib import Path
from typing import Any

import yaml

from sentinelops.chaos.dry_run_stages import (
    challenge_stage,
    correlation_stage,
    detection_stage,
    guard_stage,
    human_authorization_stage,
    plan_stage,
    rca_stage,
    remediation_and_verification_stages,
)
from sentinelops.chaos.ground_truth import write_injection_record
from sentinelops.chaos.schema import ChaosRunRecord
from sentinelops.chaos.stage_events import utc_now

DRY_RUN_ROOT = Path("evidence/C/C03_dry_runs")
BASELINE_SECONDS = 120
COOLDOWN_SECONDS = 120
SCENARIOS = {
    "latency": {
        "duration_seconds": 120,
        "mode": "latency",
        "latency_ms": 300,
        "error_rate": 0.0,
    },
    "errors": {
        "duration_seconds": 120,
        "mode": "errors",
        "latency_ms": 0,
        "error_rate": 1.0,
    },
    "bad_deployment_rollback": {
        "config": "configs/chaos_bad_deployment_v1.yaml",
    },
}


def scenario_duration_seconds(scenario: str) -> int:
    spec = SCENARIOS[scenario]
    if "duration_seconds" in spec:
        return int(spec["duration_seconds"])
    with Path(str(spec["config"])).open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)["chaos_bad_deployment_v1"]
    return int(config["total_injection_duration_seconds"])


def load_execution_config() -> dict[str, Any]:
    with Path("configs/execution.yaml").open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["execution"]


def memory_snapshot() -> dict[str, int]:
    values: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith(("MemTotal:", "MemAvailable:")):
            key, value, *_ = line.split()
            values[key.rstrip(":")] = int(value)
    return values


def run_dry_run(scenario: str, seed: int) -> Path:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown scenario: {scenario}")
    run_id = f"C03-DRY-{scenario}-{seed}"
    run_dir = DRY_RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    memory_before = memory_snapshot()
    wall_start = time.perf_counter()

    injection_start = utc_now()
    write_injection_record(
        run_id,
        {
            "run_id": run_id,
            "classification": "ground_truth_injection_only",
            "non_registry": True,
            "scenario": scenario,
            "seed": seed,
            "injection_start": injection_start.isoformat(),
            "configured_baseline_seconds": BASELINE_SECONDS,
            "configured_injection_seconds": scenario_duration_seconds(scenario),
            "configured_cooldown_seconds": COOLDOWN_SECONDS,
        },
    )

    detection_time = detection_stage(run_dir)
    correlation_stage(run_dir)
    rca_output_time = rca_stage(run_dir)
    challenge_stage(run_dir)
    _, plan = plan_stage(run_dir)
    guard_decision_time, guard_decision = guard_stage(run_dir, plan)
    _, approval = human_authorization_stage(run_dir)
    remediation_time, verification_time, execution = remediation_and_verification_stages(
        run_dir,
        approval,
        load_execution_config(),
    )
    injection_end = remediation_time
    recovery_time = verification_time if execution["recovery_verified"] else None

    record = ChaosRunRecord(
        run_id=run_id,
        seed=seed,
        scenario=scenario,
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
    memory_after = memory_snapshot()
    resources = {
        "wall_clock_seconds": time.perf_counter() - wall_start,
        "cpu_user_seconds": cpu_after.ru_utime - cpu_before.ru_utime,
        "cpu_system_seconds": cpu_after.ru_stime - cpu_before.ru_stime,
        "memory_before_kib": memory_before,
        "memory_after_kib": memory_after,
        "wsl_memory_note": "host WSL environment approximately 3.7 GiB",
        "service_killed": False,
        "service_kill_note": None,
    }

    summary = {
        "classification": "non_registry",
        "dry_run": True,
        "registered_result_eligible": False,
        "run_record": record.model_dump(mode="json"),
        "guard_decision": guard_decision,
        "execution": execution,
        "resources": resources,
        "configured_protocol_seconds": {
            "baseline": BASELINE_SECONDS,
            "injection": scenario_duration_seconds(scenario),
            "cooldown": COOLDOWN_SECONDS,
        },
        "dry_run_timing_note": (
            "control-path dry run; configured long waits are not slept and "
            "no registered timing/result inference is permitted"
        ),
        "emergency_cleanup": {"performed": False, "counted_as_remediation": False},
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return run_dir
