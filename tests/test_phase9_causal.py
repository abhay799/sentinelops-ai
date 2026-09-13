import polars as pl

from sentinelops.rca.causal import (
    build_causal_disposition,
)


def hypotheses():
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
            },
        ]
    )


def challenges():
    return pl.DataFrame(
        [
            {
                "hypothesis_id": "H1",
                "incident_id": "INC-1",
                "candidate_service":
                    "payment-service",
                "rank": 1,
                "challenge_score": 0.95,
                "challenge_status":
                    "supported",
                "supporting_evidence_count": 4,
                "contradicting_evidence_count": 0,
                "challenger_completed": True,
            },
            {
                "hypothesis_id": "H2",
                "incident_id": "INC-1",
                "candidate_service":
                    "order-service",
                "rank": 2,
                "challenge_score": 0.25,
                "challenge_status":
                    "rejected",
                "supporting_evidence_count": 1,
                "contradicting_evidence_count": 3,
                "challenger_completed": True,
            },
        ]
    )


def test_supported_candidate_survives():
    result = build_causal_disposition(
        hypotheses(),
        challenges(),
    )

    payment = (
        result
        .filter(
            pl.col("candidate_service")
            == "payment-service"
        )
        .to_dicts()[0]
    )

    assert (
        payment["final_disposition"]
        == "supported_candidate"
    )


def test_rejected_candidate_stays_rejected():
    result = build_causal_disposition(
        hypotheses(),
        challenges(),
    )

    order = (
        result
        .filter(
            pl.col("candidate_service")
            == "order-service"
        )
        .to_dicts()[0]
    )

    assert (
        order["final_disposition"]
        == "rejected_candidate"
    )


def test_phase9_never_auto_confirms():
    result = build_causal_disposition(
        hypotheses(),
        challenges(),
    )

    assert not result[
        "confirmed_root_cause"
    ].any()

    assert (
        result[
            "requires_human_confirmation"
        ].all()
    )


def test_root_cause_remains_unconfirmed():
    result = build_causal_disposition(
        hypotheses(),
        challenges(),
    )

    assert (
        result[
            "root_cause_status"
        ]
        == "unconfirmed"
    ).all()
