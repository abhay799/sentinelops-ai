from __future__ import annotations

import hashlib
from typing import Any

MASTER_SEED = 42
SCENARIOS = (
    "latency",
    "errors",
    "bad_deployment_rollback",
)
PARTITIONS = (
    "TRAIN",
    "VALIDATION",
    "TEST",
)
PRIMARY_COUNTS = {
    "TRAIN": 12,
    "VALIDATION": 4,
    "TEST": 4,
}
SPARES_PER_CELL = 2

SEED_DERIVATION_RULE = (
    "seed = first 8 bytes of SHA256("
    "'42|seed|partition|scenario|kind|ordinal') "
    "interpreted unsigned big-endian, modulo 2147483646, plus 1"
)
ORDER_RULE = (
    "within each partition, sort registered runs by first 16 hex chars "
    "of SHA256('42|order|partition|run_id'); execute TRAIN, then "
    "fit/freeze detector, then VALIDATION, then TEST"
)


def _hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def derive_seed(
    partition: str,
    scenario: str,
    kind: str,
    ordinal: int,
) -> int:
    text = f"{MASTER_SEED}|seed|{partition}|{scenario}|{kind}|{ordinal}"
    raw = int.from_bytes(
        hashlib.sha256(text.encode("utf-8")).digest()[:8],
        "big",
        signed=False,
    )
    return (raw % 2_147_483_646) + 1


def _prefix(scenario: str) -> str:
    return {
        "latency": "LAT",
        "errors": "ERR",
        "bad_deployment_rollback": "BDR",
    }[scenario]


def build_registry() -> dict[str, Any]:
    registered: list[dict[str, Any]] = []
    spares: list[dict[str, Any]] = []

    for partition in PARTITIONS:
        for scenario in SCENARIOS:
            for ordinal in range(
                1,
                PRIMARY_COUNTS[partition] + 1,
            ):
                run_id = f"C-{partition}-{_prefix(scenario)}-{ordinal:02d}"
                registered.append(
                    {
                        "run_id": run_id,
                        "partition": partition,
                        "scenario": scenario,
                        "ordinal": ordinal,
                        "seed": derive_seed(
                            partition,
                            scenario,
                            "registered",
                            ordinal,
                        ),
                        "order_key": _hash(f"{MASTER_SEED}|order|{partition}|{run_id}")[:16],
                        "status": "preregistered_not_started",
                        "replacement_for": None,
                    }
                )

            for spare_ordinal in range(
                1,
                SPARES_PER_CELL + 1,
            ):
                run_id = f"C-SPARE-{partition}-{_prefix(scenario)}-{spare_ordinal:02d}"
                spares.append(
                    {
                        "run_id": run_id,
                        "partition": partition,
                        "scenario": scenario,
                        "spare_ordinal": spare_ordinal,
                        "seed": derive_seed(
                            partition,
                            scenario,
                            "spare",
                            spare_ordinal,
                        ),
                        "status": "reserved_spare_not_started",
                    }
                )

    execution_schedule: list[dict[str, Any]] = []
    global_index = 1

    for partition in PARTITIONS:
        partition_runs = sorted(
            (run for run in registered if run["partition"] == partition),
            key=lambda run: run["order_key"],
        )
        for partition_index, run in enumerate(
            partition_runs,
            start=1,
        ):
            execution_schedule.append(
                {
                    "global_execution_index": global_index,
                    "partition_execution_index": partition_index,
                    "partition": partition,
                    "run_id": run["run_id"],
                    "scenario": run["scenario"],
                    "seed": run["seed"],
                }
            )
            global_index += 1

    return {
        "registry_version": "C-v1",
        "master_seed": MASTER_SEED,
        "seed_derivation_rule": SEED_DERIVATION_RULE,
        "order_rule": ORDER_RULE,
        "partition_gate": [
            "complete all TRAIN registered runs",
            "fit and freeze registered detector from TRAIN baseline only",
            "execute VALIDATION registered runs",
            "execute TEST registered runs",
        ],
        "registered_run_count": len(registered),
        "registered_counts": {
            "TRAIN": 36,
            "VALIDATION": 12,
            "TEST": 12,
        },
        "scenario_registered_counts": {scenario: 20 for scenario in SCENARIOS},
        "spares_per_scenario_partition": SPARES_PER_CELL,
        "reserved_spare_count": len(spares),
        "registered_runs": registered,
        "reserved_spares": spares,
        "execution_schedule": execution_schedule,
    }
