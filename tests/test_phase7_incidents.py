from datetime import UTC, datetime, timedelta
from pathlib import Path

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.incidents.correlator import (
    correlate_incidents,
)


def graph():
    return (
        ServiceDependencyGraph
        .from_topology_file(
            Path(
                "configs/topology.yaml"
            )
        )
    )


def anomaly_row(
    service: str,
    timestamp: datetime,
    score: float,
):
    return {
        "service":
            service,

        "feature_as_of_time":
            timestamp,

        "anomaly_score":
            score,

        "anomaly_votes":
            3,

        "is_anomaly":
            1,
    }


def test_related_anomalies_are_correlated():

    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    data = pl.DataFrame(
        [
            anomaly_row(
                "payment-service",
                start,
                0.95,
            ),

            anomaly_row(
                "order-service",
                start
                + timedelta(
                    seconds=20
                ),
                0.70,
            ),

            anomaly_row(
                "api-gateway",
                start
                + timedelta(
                    seconds=40
                ),
                0.50,
            ),
        ]
    )

    incidents, members = (
        correlate_incidents(
            data,
            graph(),
            correlation_window_seconds=120,
            maximum_graph_hops=2,
        )
    )

    assert incidents.height == 1

    assert members.height == 3

    assert (
        incidents[
            "service_count"
        ][0]
        == 3
    )


def test_distant_time_creates_new_incident():

    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    data = pl.DataFrame(
        [
            anomaly_row(
                "payment-service",
                start,
                0.9,
            ),

            anomaly_row(
                "payment-service",
                start
                + timedelta(
                    seconds=500
                ),
                0.8,
            ),
        ]
    )

    incidents, _ = (
        correlate_incidents(
            data,
            graph(),
            correlation_window_seconds=120,
        )
    )

    assert incidents.height == 2


def test_graph_distant_services_not_correlated():

    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    data = pl.DataFrame(
        [
            anomaly_row(
                "user-service",
                start,
                0.8,
            ),

            anomaly_row(
                "inventory-service",
                start
                + timedelta(
                    seconds=10
                ),
                0.8,
            ),
        ]
    )

    incidents, _ = (
        correlate_incidents(
            data,
            graph(),
            maximum_graph_hops=2,
        )
    )

    assert incidents.height == 2


def test_primary_service_is_highest_score():

    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    data = pl.DataFrame(
        [
            anomaly_row(
                "payment-service",
                start,
                0.95,
            ),

            anomaly_row(
                "order-service",
                start
                + timedelta(
                    seconds=10
                ),
                0.50,
            ),
        ]
    )

    incidents, _ = (
        correlate_incidents(
            data,
            graph(),
        )
    )

    assert (
        incidents[
            "primary_service"
        ][0]
        == "payment-service"
    )
