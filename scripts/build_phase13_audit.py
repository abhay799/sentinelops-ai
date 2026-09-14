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

OUTPUT = Path(
    "data/processed/remediation/"
    "remediation_audit_v1.parquet"
)


plans = pl.read_parquet(
    PLANS
)

decisions = pl.read_parquet(
    GUARD
)


errors = validate_phase13(
    plans,
    decisions,
)

if errors:
    raise RuntimeError(
        "Phase 13 validation failed:\n"
        + "\n".join(errors)
    )


guard_fields = decisions.select(
    [
        "plan_id",
        "guard_decision",
        "guard_technical_approval",
        "checks_passed",
        "checks_total",
        "failed_checks",
        "phase14_candidate",
        "fail_closed",
    ]
)


audit = (
    plans
    .join(
        guard_fields,
        on="plan_id",
        how="inner",
    )
    .with_columns(
        [
            pl.lit(
                "phase13"
            ).alias(
                "audit_phase"
            ),

            pl.lit(
                True
            ).alias(
                "execution_block_enforced"
            ),
        ]
    )
)


if audit.is_empty():
    raise RuntimeError(
        "No remediation audit records produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

audit.write_parquet(
    OUTPUT
)


print()
print("=" * 78)
print(
    " SENTINELOPS AI - PHASE 13 SENTINELGUARD AUDIT"
)
print("=" * 78)

print(
    audit.select(
        [
            "plan_id",
            "incident_id",
            "candidate_service",
            "recommended_action",
            "plan_status",
            "guard_decision",
            "checks_passed",
            "checks_total",
            "phase14_candidate",
            "human_approval_status",
            "execution_allowed",
        ]
    )
)

print()

print(
    "PHASE 13 SENTINELGUARD VALIDATION: PASSED"
)
