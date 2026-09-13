from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.rca.engine import (
    build_rca_hypotheses,
)


def graph():
    return (
        ServiceDependencyGraph
        .from_topology_file(
            Path("configs/topology.yaml")
        )
    )


def fixtures():

    now = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    incidents = pl.DataFrame(
        {
            "incident_id": [
                "INC-0001"
            ],
            "primary_service": [
                "payment-service"
            ],
            "severity": [
                "critical"
            ],
            "confidence": [
                0.9
            ],
        }
    )

    members = pl.DataFrame(
        {
            "incident_id": [
                "INC-0001",
                "INC-0001",
            ],
            "service": [
                "payment-service",
                "order-service",
            ],
            "feature_as_of_time": [
                now,
                now,
            ],
            "anomaly_score": [
                0.95,
                0.60,
            ],
            "anomaly_votes": [
                3,
                2,
            ],
        }
    )

    anomalies = pl.DataFrame(
        {
            "service": [
                "payment-service",
                "order-service",
            ],
            "anomaly_score": [
                0.95,
                0.60,
            ],
            "is_anomaly": [
                1,
                1,
            ],
            "change_count_300s": [
                1,
                0,
            ],
        }
    )

    return (
        incidents,
        members,
        anomalies,
    )


def weights():
    return {
        "anomaly_strength": 0.45,
        "change_signal": 0.25,
        "graph_impact": 0.20,
        "primary_service_bonus": 0.10,
    }


def confidence():
    return {
        "high": 0.75,
        "medium": 0.50,
    }


def test_rca_ranks_payment_first():

    incidents, members, anomalies = fixtures()

    result = build_rca_hypotheses(
        incidents=incidents,
        members=members,
        anomaly_data=anomalies,
        graph=graph(),
        weights=weights(),
        confidence_config=confidence(),
    )

    first = (
        result
        .filter(
            pl.col("rank") == 1
        )
        .to_dicts()[0]
    )

    assert (
        first["candidate_service"]
        == "payment-service"
    )


def test_rca_has_evidence():

    incidents, members, anomalies = fixtures()

    result = build_rca_hypotheses(
        incidents=incidents,
        members=members,
        anomaly_data=anomalies,
        graph=graph(),
        weights=weights(),
        confidence_config=confidence(),
    )

    assert (
        result["evidence_count"].min()
        > 0
    )


def test_rca_never_auto_confirms():

    incidents, members, anomalies = fixtures()

    result = build_rca_hypotheses(
        incidents=incidents,
        members=members,
        anomaly_data=anomalies,
        graph=graph(),
        weights=weights(),
        confidence_config=confidence(),
    )

    assert not (
        result[
            "confirmed_root_cause"
        ].any()
    )


def test_rca_requires_challenger():

    incidents, members, anomalies = fixtures()

    result = build_rca_hypotheses(
        incidents=incidents,
        members=members,
        anomaly_data=anomalies,
        graph=graph(),
        weights=weights(),
        confidence_config=confidence(),
    )

    assert (
        result[
            "requires_challenger"
        ].all()
    )

    assert (
        result[
            "requires_human_confirmation"
        ].all()
    )
