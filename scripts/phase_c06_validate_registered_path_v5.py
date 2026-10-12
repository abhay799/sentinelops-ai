from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

from sentinelops.chaos import registered_harness
from sentinelops.chaos.schema import ChaosRunRecord


SCENARIOS = (
    ("latency", 1900006101),
    ("errors", 1900006102),
    ("bad_deployment_rollback", 1900006103),
)

STAGES = (
    "detection",
    "rca",
    "guard_decision",
    "remediation",
    "verification",
)


def validate_utc_order(record: dict) -> bool:
    fields = [
        "injection_start",
        "detection_time",
        "rca_output_time",
        "guard_decision_time",
        "remediation_time",
        "verification_time",
    ]

    values = [
        record.get(name)
        for name in fields
        if record.get(name) is not None
    ]

    return values == sorted(values)


def validate_full_chain(
    run_dir: Path,
    status: str | None,
) -> bool:
    common = [
        "detection.json",
        "correlation.json",
        "rca.json",
        "challenge.json",
        "plan_guard.json",
        "authorization.json",
        "post_health.json",
        "cooldown_health.json",
        "telemetry_manifest.json",
        "run_summary.json",
    ]

    if not all((run_dir / name).exists() for name in common):
        return False

    if status == "no_executable_rollback_request":
        return (run_dir / "cleanup.json").exists()

    if status in {
        "executed_verified",
        "remediation_or_verification_failed",
    }:
        return (
            (run_dir / "remediation.json").exists()
            and (run_dir / "verification.json").exists()
        )

    return True


async def execute_one(
    scenario: str,
    seed: int,
    root: Path,
) -> dict:
    registered_harness.assert_non_registry_seed(seed)

    run_id = f"NR-V5-{scenario}-{seed}"

    evidence_root = root / "evidence"
    work_root = root / "work"

    old_evidence = registered_harness.TRAIN_EVIDENCE_ROOT
    old_work = registered_harness.WORK_ROOT
    old_loader = registered_harness._load_registry_entry

    entry = {
        "partition": "TRAIN",
        "run_id": run_id,
        "scenario": scenario,
        "seed": seed,
        "non_registry_validation": True,
    }

    try:
        registered_harness.TRAIN_EVIDENCE_ROOT = evidence_root
        registered_harness.WORK_ROOT = work_root
        registered_harness._load_registry_entry = lambda requested: (
            entry
            if requested == run_id
            else (_ for _ in ()).throw(
                ValueError(f"unexpected run id {requested}")
            )
        )

        run_dir = await registered_harness.run_registered_train(run_id)

    finally:
        registered_harness.TRAIN_EVIDENCE_ROOT = old_evidence
        registered_harness.WORK_ROOT = old_work
        registered_harness._load_registry_entry = old_loader

    summary_path = run_dir / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    record = summary.get("run_record")
    if record is None:
        return {
            "scenario": scenario,
            "seed": seed,
            "schema_valid": False,
            "utc_order": False,
            "full_chain": False,
            "status": summary.get("status"),
            "run_dir": str(run_dir),
        }

    ChaosRunRecord.model_validate(record)

    return {
        "scenario": scenario,
        "seed": seed,
        "schema_valid": True,
        "utc_order": validate_utc_order(record),
        "full_chain": validate_full_chain(
            run_dir,
            summary.get("status"),
        ),
        "status": summary.get("status"),
        "run_dir": str(run_dir),
    }


async def main() -> None:
    used = registered_harness.registered_and_spare_seeds()

    seeds = {seed for _, seed in SCENARIOS}

    if not seeds.isdisjoint(used):
        raise RuntimeError(
            f"validation seed collision: {sorted(seeds & used)}"
        )

    scratch_parent = (
        registered_harness.REPO_ROOT
        / "data"
        / "chaos"
        / "non_registry_v5_validation"
    )
    scratch_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="run-",
        dir=scratch_parent,
    ) as temp:
        root = Path(temp)

        results = []

        for scenario, seed in SCENARIOS:
            results.append(
                await execute_one(
                    scenario,
                    seed,
                    root,
                )
            )

        payload = {
            "classification": "non_registry_validation_only",
            "executor": "run_registered_train",
            "registered_rows_executed": 0,
            "validation_seeds": sorted(seeds),
            "seed_collision_count": len(seeds & used),
            "runs": results,
        }

        print(json.dumps(payload, indent=2))

        if not all(
            row["schema_valid"]
            and row["utc_order"]
            and row["full_chain"]
            for row in results
        ):
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
