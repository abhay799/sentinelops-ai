from pathlib import Path

import polars as pl

from sentinelops.graph.risk import (
    build_graph_risk,
)
from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


def graph():
    return (
        ServiceDependencyGraph
        .from_topology_file(
            Path("configs/topology.yaml")
        )
    )


def anomaly_fixture():
    return pl.DataFrame(
        {
            "service": [
                "api-gateway",
                "order-service",
                "payment-service",
            ],
            "anomaly_score": [
                0.05,
                0.10,
                1.00,
            ],
            "is_anomaly": [
                0,
                0,
                1,
            ],
            "anomaly_votes": [
                0,
                1,
                3,
            ],
        }
    )


def test_payment_risk_propagates_upstream():
    risk, _ = build_graph_risk(
        graph(),
        anomaly_fixture(),
        decay=0.6,
    )

    rows = {
        row["service"]: row
        for row in risk.to_dicts()
    }

    assert (
        rows["payment-service"]["graph_risk_score"]
        == 1.0
    )

    assert (
        rows["order-service"]["propagated_risk_score"]
        == 0.6
    )

    assert (
        rows["api-gateway"]["propagated_risk_score"]
        == 0.36
    )


def test_propagated_risk_decays():
    risk, _ = build_graph_risk(
        graph(),
        anomaly_fixture(),
        decay=0.6,
    )

    rows = {
        row["service"]: row
        for row in risk.to_dicts()
    }

    assert (
        rows["order-service"]["graph_risk_score"]
        >
        rows["api-gateway"]["graph_risk_score"]
    )


def test_unrelated_service_not_impacted():
    risk, _ = build_graph_risk(
        graph(),
        anomaly_fixture(),
        decay=0.6,
    )

    inventory = (
        risk
        .filter(
            pl.col("service")
            == "inventory-service"
        )
        .to_dicts()[0]
    )

    assert (
        inventory["propagated_risk_score"]
        == 0.0
    )


def test_payment_has_two_upstream_impacts():
    risk, _ = build_graph_risk(
        graph(),
        anomaly_fixture(),
    )

    payment = (
        risk
        .filter(
            pl.col("service")
            == "payment-service"
        )
        .to_dicts()[0]
    )

    assert (
        payment["upstream_impact_count"]
        == 2
    )
