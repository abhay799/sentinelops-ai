from sentinelops.chaos.registry import (
    MASTER_SEED,
    PARTITIONS,
    SCENARIOS,
    build_registry,
)


def test_registry_is_deterministic_and_has_frozen_counts():
    first = build_registry()
    second = build_registry()

    assert first == second
    assert first["master_seed"] == MASTER_SEED == 42
    assert first["registered_run_count"] == 60
    assert first["registered_counts"] == {
        "TRAIN": 36,
        "VALIDATION": 12,
        "TEST": 12,
    }
    assert first["reserved_spare_count"] == 18

    for scenario in SCENARIOS:
        assert first["scenario_registered_counts"][scenario] == 20

    for partition in PARTITIONS:
        for scenario in SCENARIOS:
            primary = [
                run
                for run in first["registered_runs"]
                if (run["partition"] == partition and run["scenario"] == scenario)
            ]
            spares = [
                run
                for run in first["reserved_spares"]
                if (run["partition"] == partition and run["scenario"] == scenario)
            ]
            expected = {
                "TRAIN": 12,
                "VALIDATION": 4,
                "TEST": 4,
            }[partition]
            assert len(primary) == expected
            assert len(spares) == 2


def test_execution_schedule_is_partition_constrained():
    registry = build_registry()
    partitions = [row["partition"] for row in registry["execution_schedule"]]
    assert partitions[:36] == ["TRAIN"] * 36
    assert partitions[36:48] == ["VALIDATION"] * 12
    assert partitions[48:] == ["TEST"] * 12

    ids = [row["run_id"] for row in registry["execution_schedule"]]
    assert len(ids) == len(set(ids)) == 60
