import polars as pl

from sentinelops.rca.challenger import (
    challenge_rca_hypotheses,
)


def config():
    return {
        "thresholds": {
            "support": 0.65,
            "reject": 0.35,
            "minimum_evidence": 2,
        },

        "penalties": {
            "no_change_signal": 0.15,
            "weak_anomaly": 0.20,
            "stronger_alternative": 0.25,
            "no_graph_impact": 0.10,
        },

        "bonuses": {
            "change_signal": 0.15,
            "strong_anomaly": 0.15,
            "graph_impact": 0.10,
            "primary_service": 0.10,
        },
    }


def fixture():
    return pl.DataFrame(
        [
            {
                "hypothesis_id": "H1",
                "incident_id": "INC-1",
                "candidate_service":
                    "payment-service",
                "rank": 1,
                "rca_score": 0.72,
                "anomaly_strength": 0.95,
                "change_signal": 1.0,
                "graph_impact": 0.33,
                "primary_service_bonus": 1.0,
            },
            {
                "hypothesis_id": "H2",
                "incident_id": "INC-1",
                "candidate_service":
                    "order-service",
                "rank": 2,
                "rca_score": 0.40,
                "anomaly_strength": 0.55,
                "change_signal": 0.0,
                "graph_impact": 0.16,
                "primary_service_bonus": 0.0,
            },
        ]
    )


def test_challenger_runs():

    result = challenge_rca_hypotheses(
        fixture(),
        config(),
    )

    assert result.height == 2

    assert (
        result[
            "challenger_completed"
        ].all()
    )


def test_strong_candidate_survives_challenge():

    result = challenge_rca_hypotheses(
        fixture(),
        config(),
    )

    payment = (
        result
        .filter(
            pl.col(
                "candidate_service"
            )
            == "payment-service"
        )
        .to_dicts()[0]
    )

    assert (
        payment[
            "challenge_status"
        ]
        == "supported"
    )


def test_weaker_candidate_gets_downgraded():

    result = challenge_rca_hypotheses(
        fixture(),
        config(),
    )

    order = (
        result
        .filter(
            pl.col(
                "candidate_service"
            )
            == "order-service"
        )
        .to_dicts()[0]
    )

    assert (
        order[
            "challenge_score"
        ]
        <
        order[
            "original_rca_score"
        ]
    )


def test_challenger_never_auto_confirms():

    result = challenge_rca_hypotheses(
        fixture(),
        config(),
    )

    assert not result[
        "confirmed_root_cause"
    ].any()

    assert result[
        "requires_human_confirmation"
    ].all()
