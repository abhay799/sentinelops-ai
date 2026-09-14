import polars as pl

from sentinelops.counterfactual.engine import (
    simulate_counterfactuals,
)

CONFIG = {
    "minimum_causal_score": 0.50,

    "actions": {
        "rollback": {
            "effectiveness": 0.70,
            "operational_risk": 0.10,
            "requires_change_signal": True,
        },

        "traffic_shift": {
            "effectiveness": 0.55,
            "operational_risk": 0.20,
            "requires_change_signal": False,
        },

        "restart": {
            "effectiveness": 0.30,
            "operational_risk": 0.25,
            "requires_change_signal": False,
        },

        "no_action": {
            "effectiveness": 0.0,
            "operational_risk": 0.0,
            "requires_change_signal": False,
        },
    },
}


def disposition(
    status="supported_candidate",
):
    return pl.DataFrame(
        [
            {
                "incident_id": "INC-1",
                "candidate_service":
                    "payment-service",
                "rank": 1,
                "causal_consistency_score":
                    0.90,
                "original_rca_score":
                    0.75,
                "final_disposition":
                    status,
            }
        ]
    )


def hypotheses(
    change_signal=1.0,
):
    return pl.DataFrame(
        [
            {
                "incident_id": "INC-1",
                "candidate_service":
                    "payment-service",
                "change_signal":
                    change_signal,
            }
        ]
    )


def predictions():
    return pl.DataFrame(
        [
            {
                "service":
                    "payment-service",

                "feature_as_of_time":
                    1,

                "failure_probability":
                    0.80,
            }
        ]
    )


def build(
    status="supported_candidate",
    change_signal=1.0,
):
    return simulate_counterfactuals(
        disposition(
            status
        ),
        hypotheses(
            change_signal
        ),
        predictions(),
        CONFIG,
    )


def test_simulation_never_allows_execution():

    result = build()

    assert not result[
        "execution_allowed"
    ].any()

    assert result[
        "simulation_only"
    ].all()


def test_rollback_requires_change_signal():

    result = build(
        change_signal=0.0
    )

    rollback = (
        result
        .filter(
            pl.col("action")
            == "rollback"
        )
        .to_dicts()[0]
    )

    assert (
        rollback[
            "action_applicable"
        ]
        is False
    )


def test_supported_action_reduces_risk():

    result = build()

    traffic = (
        result
        .filter(
            pl.col("action")
            == "traffic_shift"
        )
        .to_dicts()[0]
    )

    assert (
        traffic[
            "projected_failure_risk"
        ]
        <
        traffic[
            "baseline_failure_risk"
        ]
    )


def test_rejected_candidate_not_recommended():

    result = build(
        status="rejected_candidate"
    )

    assert not result[
        "recommended_in_simulation"
    ].any()


def test_one_action_can_be_recommended():

    result = build()

    recommended = (
        result
        .filter(
            pl.col(
                "recommended_in_simulation"
            )
        )
    )

    assert recommended.height == 1
