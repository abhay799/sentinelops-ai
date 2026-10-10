from __future__ import annotations

import json
import resource
import time
from pathlib import Path
from typing import Any

import yaml

from sentinelops.chaos.dry_run_stages import (
    INJECTED_SERVICE,
    SCRIPTED_APPROVER,
    challenge_stage,
    correlation_stage,
    detection_stage,
    guard_stage,
    human_authorization_stage,
    plan_stage,
    rca_stage,
    remediation_and_verification_stages,
)
from sentinelops.chaos.ground_truth import (
    build_injection_record,
    persist_injection_record,
)
from sentinelops.chaos.schema import ChaosRunRecord
from sentinelops.chaos.stage_events import utc_now

DRY_RUN_ROOT = Path("evidence/C/C03_dry_runs")
SCENARIO_CONFIG_PATH = Path("configs/chaos_scenarios_v1.yaml")


def load_scenario_config() -> dict[str, Any]:
    with SCENARIO_CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["chaos_scenarios_v1"]


def scenario_duration_seconds(
    scenario: str,
    config: dict[str, Any],
) -> int:
    spec = config["scenarios"][scenario]
    if "duration_seconds" in spec:
        return int(spec["duration_seconds"])
    with Path(str(spec["profile_path"])).open(encoding="utf-8") as handle:
        profile = yaml.safe_load(handle)["chaos_bad_deployment_v1"]
    return int(profile["total_injection_duration_seconds"])


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
    config = load_scenario_config()
    if scenario not in config["scenarios"]:
        raise ValueError(f"unknown scenario: {scenario}")

    run_id = f"C03-DRY-{scenario}-{seed}"
    run_dir = DRY_RUN_ROOT / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    ground_truth_root = DRY_RUN_ROOT / "_ground_truth_injection_only"
    ground_truth_path = ground_truth_root / f"{run_id}.json"
    if ground_truth_path.exists():
        ground_truth_path.unlink()

    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    memory_before = memory_snapshot()
    wall_start = time.perf_counter()

    injection_start = utc_now()
    injection_seconds = scenario_duration_seconds(
        scenario,
        config,
    )
    ground_truth = build_injection_record(
        run_id=run_id,
        scenario=scenario,
        seed=seed,
        injection_start=injection_start.isoformat(),
        injected_service=INJECTED_SERVICE,
        baseline_seconds=int(config["baseline_seconds"]),
        injection_seconds=injection_seconds,
        cooldown_seconds=int(config["cooldown_seconds"]),
        non_registry=True,
    )

    detection_time = detection_stage(run_dir)
    correlation_stage(run_dir)
    rca_output_time = rca_stage(run_dir)
    challenge_stage(run_dir)
    _, plan = plan_stage(run_dir)
    guard_decision_time, guard_decision = guard_stage(
        run_dir,
        plan,
    )
    _, approval = human_authorization_stage(run_dir)

    remediation_time, verification_time, execution = remediation_and_verification_stages(
        run_dir,
        approval,
        load_execution_config(),
    )

    # Ground truth remains in memory until verification has completed.
    persist_injection_record(
        ground_truth_root,
        run_id,
        ground_truth,
    )

    injection_end = remediation_time
    recovery_time = verification_time if execution["recovery_verified"] else None

    record = ChaosRunRecord(
        run_id=run_id,
        seed=seed,
        scenario=scenario,
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
    memory_after = memory_snapshot()
    resources = {
        "wall_clock_seconds": time.perf_counter() - wall_start,
        "cpu_user_seconds": (cpu_after.ru_utime - cpu_before.ru_utime),
        "cpu_system_seconds": (cpu_after.ru_stime - cpu_before.ru_stime),
        "memory_before_kib": memory_before,
        "memory_after_kib": memory_after,
        "wsl_memory_note": ("host WSL environment approximately 3.7 GiB"),
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
            "baseline": int(config["baseline_seconds"]),
            "injection": injection_seconds,
            "cooldown": int(config["cooldown_seconds"]),
        },
        "dry_run_timing_note": (
            "control-path dry run; configured long waits are not slept "
            "and no registered timing/result inference is permitted"
        ),
        "emergency_cleanup": {
            "performed": False,
            "counted_as_remediation": False,
        },
    }
    (run_dir / "run_summary.json").write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return run_dir
