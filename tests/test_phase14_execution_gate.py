import polars as pl

from sentinelops.execution.gate import (
    build_execution_requests,
    validate_execution_requests,
)

CONFIG = {
    "allowed_actions": [
        "rollback",
        "traffic_shift",
        "restart",
    ],

    "services": {
        "payment-service":
            "http://localhost:8103",
    },

    "safety": {
        "require_local_target":
            True,
    },

    "fail_closed":
        True,
}


def plans():

    return pl.DataFrame(
        [
            {
                "plan_id":
                    "PLAN-0001",

                "incident_id":
                    "INC-0001",

                "candidate_service":
                    "payment-service",

                "recommended_action":
                    "rollback",

                "rollback_available":
                    True,

                "rollback_strategy":
                    "restore previous deployment",
            }
        ]
    )


def decisions():

    return pl.DataFrame(
        [
            {
                "plan_id":
                    "PLAN-0001",

                "guard_decision":
                    "eligible_pending_human",

                "guard_technical_approval":
                    True,

                "phase14_candidate":
                    True,
            }
        ]
    )


def build():

    return build_execution_requests(
        plans(),
        decisions(),
        CONFIG,
    )


def test_safe_request_waits_for_human():

    result = build()

    row = result.to_dicts()[0]

    assert row[
        "preapproval_ready"
    ]

    assert (
        row[
            "request_status"
        ]
        == "awaiting_human_approval"
    )


def test_execution_is_disabled():

    result = build()

    assert not result[
        "execution_allowed"
    ].any()

    assert not result[
        "execution_attempted"
    ].any()


def test_only_local_target_is_accepted():

    result = build()

    assert result[
        "local_target"
    ].all()


def test_missing_rollback_blocks_request():

    unsafe_plans = (
        plans()
        .with_columns(
            pl.lit(False)
            .alias(
                "rollback_available"
            )
        )
    )

    result = build_execution_requests(
        unsafe_plans,
        decisions(),
        CONFIG,
    )

    assert not result[
        "preapproval_ready"
    ].any()

    assert (
        result[
            "request_status"
        ][0]
        == "blocked"
    )


def test_validation_passes():

    errors = validate_execution_requests(
        build()
    )

    assert errors == []


def test_preapproval_cannot_enable_execution():

    unsafe = (
        build()
        .with_columns(
            pl.lit(True)
            .alias(
                "execution_allowed"
            )
        )
    )

    errors = validate_execution_requests(
        unsafe
    )

    assert len(errors) > 0
