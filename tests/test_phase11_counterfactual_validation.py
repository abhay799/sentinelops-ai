import polars as pl

from sentinelops.counterfactual.ranking import (
    build_counterfactual_summary,
)
from sentinelops.counterfactual.validation import (
    validate_counterfactuals,
)


def valid_data():

    return pl.DataFrame(
        [
            {
                "incident_id":
                    "INC-1",
                "candidate_service":
                    "payment-service",
                "candidate_rank":
                    1,
                "action":
                    "rollback",
                "action_applicable":
                    True,
                "baseline_failure_risk":
                    0.80,
                "projected_failure_risk":
                    0.30,
                "risk_reduction":
                    0.50,
                "net_benefit":
                    0.42,
                "simulation_only":
                    True,
                "execution_allowed":
                    False,
                "requires_sentinelguard":
                    True,
                "rollback_required":
                    True,
                "recommended_in_simulation":
                    True,
            },
            {
                "incident_id":
                    "INC-1",
                "candidate_service":
                    "payment-service",
                "candidate_rank":
                    1,
                "action":
                    "traffic_shift",
                "action_applicable":
                    True,
                "baseline_failure_risk":
                    0.80,
                "projected_failure_risk":
                    0.45,
                "risk_reduction":
                    0.35,
                "net_benefit":
                    0.19,
                "simulation_only":
                    True,
                "execution_allowed":
                    False,
                "requires_sentinelguard":
                    True,
                "rollback_required":
                    True,
                "recommended_in_simulation":
                    False,
            },
            {
                "incident_id":
                    "INC-1",
                "candidate_service":
                    "payment-service",
                "candidate_rank":
                    1,
                "action":
                    "no_action",
                "action_applicable":
                    True,
                "baseline_failure_risk":
                    0.80,
                "projected_failure_risk":
                    0.80,
                "risk_reduction":
                    0.0,
                "net_benefit":
                    0.0,
                "simulation_only":
                    True,
                "execution_allowed":
                    False,
                "requires_sentinelguard":
                    False,
                "rollback_required":
                    False,
                "recommended_in_simulation":
                    False,
            },
        ]
    )


def test_valid_counterfactuals_pass():

    errors = validate_counterfactuals(
        valid_data()
    )

    assert errors == []


def test_execution_permission_is_rejected():

    data = valid_data().with_columns(
        pl.when(
            pl.col("action")
            == "rollback"
        )
        .then(True)
        .otherwise(
            pl.col(
                "execution_allowed"
            )
        )
        .alias(
            "execution_allowed"
        )
    )

    errors = validate_counterfactuals(
        data
    )

    assert len(errors) > 0


def test_summary_preserves_execution_block():

    summary = build_counterfactual_summary(
        valid_data()
    )

    assert not summary[
        "execution_allowed"
    ].any()


def test_best_action_is_ranked():

    summary = build_counterfactual_summary(
        valid_data()
    )

    row = summary.to_dicts()[0]

    assert (
        row[
            "recommended_action"
        ]
        == "rollback"
    )


def test_human_confirmation_required():

    summary = build_counterfactual_summary(
        valid_data()
    )

    assert summary[
        "requires_human_confirmation"
    ].all()
