from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.incidents.intelligence import (
    confidence_from_incident,
    enrich_incidents,
)


def graph():
    return (
        ServiceDependencyGraph
        .from_topology_file(
            Path("configs/topology.yaml")
        )
    )


def test_confidence_increases_with_stronger_incident():
    weak = confidence_from_incident(
        anomaly_count=1,
        service_count=1,
        max_anomaly_score=0.3,
    )

    strong = confidence_from_incident(
        anomaly_count=5,
        service_count=3,
        max_anomaly_score=0.95,
    )

    assert strong > weak


def test_incident_enrichment_contains_evidence():

    incidents = pl.DataFrame(
        {
            "incident_id": [
                "INC-0001"
            ],

            "start_time": [
                datetime(
                    2026,
                    9,
                    14,
                    tzinfo=UTC,
                )
            ],

            "end_time": [
                datetime(
                    2026,
                    9,
                    14,
                    tzinfo=UTC,
                )
            ],

            "duration_seconds": [
                0.0
            ],

            "primary_service": [
                "payment-service"
            ],

            "services": [
                [
                    "payment-service",
                    "order-service",
                ]
            ],

            "service_count": [
                2
            ],

            "anomaly_count": [
                2
            ],

            "max_anomaly_score": [
                0.95
            ],

            "mean_anomaly_score": [
                0.80
            ],

            "severity": [
                "critical"
            ],

            "upstream_impact_count": [
                2
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
                datetime(
                    2026,
                    9,
                    14,
                    tzinfo=UTC,
                ),
                datetime(
                    2026,
                    9,
                    14,
                    tzinfo=UTC,
                ),
            ],

            "anomaly_score": [
                0.95,
                0.65,
            ],

            "anomaly_votes": [
                3,
                2,
            ],
        }
    )

    enriched = enrich_incidents(
        incidents,
        members,
        graph(),
    )

    row = enriched.to_dicts()[0]

    assert row[
        "evidence_count"
    ] == 2

    assert (
        "order-service"
        in row[
            "affected_upstream_services"
        ]
    )

    assert (
        "api-gateway"
        in row[
            "affected_upstream_services"
        ]
    )

    assert (
        row["confidence"]
        > 0
    )
