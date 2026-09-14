from pathlib import Path

import polars as pl

SERVICE_IMPACT = Path(
    "data/processed/impact/"
    "service_impact_v1.parquet"
)

INCIDENT_PRIORITY = Path(
    "data/processed/impact/"
    "incident_priority_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed_check(message: str) -> None:
    global failed

    failed = True
    print(f"[FAIL] {message}")


print()
print("=" * 66)
print(
    " SENTINELOPS AI - PHASE 12 PREFLIGHT"
)
print("=" * 66)


print("\n[Service Impact]")


if SERVICE_IMPACT.exists():

    impact = pl.read_parquet(
        SERVICE_IMPACT
    )

    passed(
        "Service-impact artifact"
    )

    required = {
        "service",
        "latency_burn_score",
        "error_burn_score",
        "business_impact_score",
        "impact_severity",
    }

    missing = (
        required
        - set(impact.columns)
    )

    if not missing:
        passed(
            "Required impact columns"
        )
    else:
        failed_check(
            f"Missing columns: {sorted(missing)}"
        )

    invalid = impact.filter(
        (
            pl.col(
                "business_impact_score"
            )
            < 0
        )
        |
        (
            pl.col(
                "business_impact_score"
            )
            > 1
        )
    )

    if invalid.height == 0:
        passed(
            "Impact-score bounds"
        )
    else:
        failed_check(
            "Invalid impact score"
        )

else:

    failed_check(
        "Service-impact artifact"
    )


print("\n[Incident Priority]")


if INCIDENT_PRIORITY.exists():

    priority = pl.read_parquet(
        INCIDENT_PRIORITY
    )

    passed(
        "Incident-priority artifact"
    )

    required = {
        "priority_rank",
        "incident_id",
        "highest_impact_service",
        "affected_service_count",
        "max_latency_burn",
        "max_error_burn",
        "remediation_priority_score",
        "priority",
    }

    missing = (
        required
        - set(priority.columns)
    )

    if not missing:
        passed(
            "Required priority columns"
        )
    else:
        failed_check(
            f"Missing columns: {sorted(missing)}"
        )

    if priority.height > 0:
        passed(
            f"Priority rows ({priority.height})"
        )
    else:
        failed_check(
            "No prioritized incidents"
        )

    invalid = priority.filter(
        (
            pl.col(
                "remediation_priority_score"
            )
            < 0
        )
        |
        (
            pl.col(
                "remediation_priority_score"
            )
            > 1
        )
    )

    if invalid.height == 0:
        passed(
            "Priority-score bounds"
        )
    else:
        failed_check(
            "Invalid priority score"
        )

    ranks = priority[
        "priority_rank"
    ].to_list()

    if ranks == list(
        range(
            1,
            priority.height + 1,
        )
    ):
        passed(
            "Deterministic priority ranking"
        )
    else:
        failed_check(
            "Priority ranking"
        )

else:

    failed_check(
        "Incident-priority artifact"
    )


print()
print("=" * 66)


if failed:

    print(
        "PHASE 12 PREFLIGHT: FAILED"
    )

    print("=" * 66)

    raise SystemExit(1)


print(
    "PHASE 12 PREFLIGHT: PASSED"
)

print("=" * 66)
