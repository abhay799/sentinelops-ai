import polars as pl

from sentinelops.remediation.validation import (
    validate_phase13,
)


def plans():

    return pl.DataFrame(
        [
            {
                "plan_id":
                    "PLAN-0001",

                "incident_id":
                    "INC-1",

                "candidate_service":
                    "payment-service",

                "recommended_action":
                    "rollback",

                "plan_status":
                    "proposed_pending_guard",

                "planner_ready":
                    True,

                "rollback_available":
                    True,

                "traceable_evidence":
                    True,

                "sentinelguard_required":
                    True,

                "human_approval_required":
                    True,

                "human_approval_status":
                    "pending",

                "execution_allowed":
                    False,
            }
        ]
    )


def decisions():

    return pl.DataFrame(
        [
            {
                "plan_id":
                    "PLAN-0001",

                "incident_id":
                    "INC-1",

                "candidate_service":
                    "payment-service",

                "recommended_action":
                    "rollback",

                "guard_decision":
                    "eligible_pending_human",

                "guard_technical_approval":
                    True,

                "phase14_candidate":
                    True,

                "rollback_available":
                    True,

                "human_approval_required":
                    True,

                "human_approval_status":
                    "pending",

                "execution_allowed":
                    False,

                "fail_closed":
                    True,
            }
        ]
    )


def test_valid_phase13_passes():

    errors = validate_phase13(
        plans(),
        decisions(),
    )

    assert errors == []


def test_execution_permission_fails():

    guard = (
        decisions()
        .with_columns(
            pl.lit(True)
            .alias(
                "execution_allowed"
            )
        )
    )

    errors = validate_phase13(
        plans(),
        guard,
    )

    assert len(errors) > 0


def test_human_approval_cannot_be_preapproved():

    guard = (
        decisions()
        .with_columns(
            pl.lit(
                "approved"
            )
            .alias(
                "human_approval_status"
            )
        )
    )

    errors = validate_phase13(
        plans(),
        guard,
    )

    assert len(errors) > 0


def test_fail_closed_required():

    guard = (
        decisions()
        .with_columns(
            pl.lit(False)
            .alias(
                "fail_closed"
            )
        )
    )

    errors = validate_phase13(
        plans(),
        guard,
    )

    assert len(errors) > 0
