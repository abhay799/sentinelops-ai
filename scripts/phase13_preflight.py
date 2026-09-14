from pathlib import Path

import polars as pl

from sentinelops.remediation.validation import (
    validate_phase13,
)

PLANS = Path(
    "data/processed/remediation/"
    "remediation_plans_v1.parquet"
)

GUARD = Path(
    "data/processed/remediation/"
    "sentinelguard_decisions_v1.parquet"
)

AUDIT = Path(
    "data/processed/remediation/"
    "remediation_audit_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(
        f"[PASS] {message}"
    )


def failed_check(message: str) -> None:
    global failed

    failed = True

    print(
        f"[FAIL] {message}"
    )


print()
print("=" * 68)
print(
    " SENTINELOPS AI - PHASE 13 PREFLIGHT"
)
print("=" * 68)


print("\n[Remediation Planner]")


if PLANS.exists():

    plans = pl.read_parquet(
        PLANS
    )

    passed(
        "Remediation plans artifact"
    )

    if plans.height > 0:
        passed(
            f"Plans ({plans.height})"
        )
    else:
        failed_check(
            "No remediation plans"
        )

    if not plans[
        "execution_allowed"
    ].any():
        passed(
            "Planner execution blocked"
        )
    else:
        failed_check(
            "Planner execution permission"
        )

else:

    failed_check(
        "Remediation plans artifact"
    )


print("\n[SentinelGuard]")


if GUARD.exists():

    decisions = pl.read_parquet(
        GUARD
    )

    passed(
        "SentinelGuard decisions artifact"
    )

    if not decisions[
        "execution_allowed"
    ].any():
        passed(
            "Guard execution hard-disabled"
        )
    else:
        failed_check(
            "Guard execution permission"
        )

    if decisions[
        "fail_closed"
    ].all():
        passed(
            "Fail-closed enforcement"
        )
    else:
        failed_check(
            "Fail-closed enforcement"
        )

    if (
        decisions[
            "human_approval_status"
        ]
        == "pending"
    ).all():
        passed(
            "Human approval pending"
        )
    else:
        failed_check(
            "Invalid human approval state"
        )

else:

    failed_check(
        "SentinelGuard decisions artifact"
    )


if (
    PLANS.exists()
    and GUARD.exists()
):

    errors = validate_phase13(
        plans,
        decisions,
    )

    if not errors:
        passed(
            "Phase 13 safety validation"
        )
    else:
        for error in errors:
            failed_check(error)


print("\n[Audit Trail]")


if AUDIT.exists():

    audit = pl.read_parquet(
        AUDIT
    )

    passed(
        "Remediation audit artifact"
    )

    if audit.height > 0:
        passed(
            f"Audit rows ({audit.height})"
        )
    else:
        failed_check(
            "No audit rows"
        )

    if audit[
        "execution_block_enforced"
    ].all():
        passed(
            "Execution block audited"
        )
    else:
        failed_check(
            "Execution-block audit"
        )

else:

    failed_check(
        "Remediation audit artifact"
    )


print()
print("=" * 68)


if failed:

    print(
        "PHASE 13 PREFLIGHT: FAILED"
    )

    print("=" * 68)

    raise SystemExit(1)


print(
    "PHASE 13 PREFLIGHT: PASSED"
)

print("=" * 68)
