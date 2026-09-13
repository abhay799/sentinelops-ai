from __future__ import annotations

from datetime import datetime
from typing import Any

import networkx as nx
import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


def severity_from_score(
    score: float,
    thresholds: dict[str, float],
) -> str:

    if score >= thresholds["critical"]:
        return "critical"

    if score >= thresholds["high"]:
        return "high"

    if score >= thresholds["medium"]:
        return "medium"

    if score >= thresholds["low"]:
        return "low"

    return "normal"


def to_datetime(
    value: datetime | str,
) -> datetime:

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(value)


def graph_related(
    graph: ServiceDependencyGraph,
    left: str,
    right: str,
    maximum_hops: int,
) -> bool:

    if left == right:
        return True

    undirected = graph.graph.to_undirected()

    try:
        distance = nx.shortest_path_length(
            undirected,
            source=left,
            target=right,
        )
    except (
        nx.NetworkXNoPath,
        nx.NodeNotFound,
    ):
        return False

    return distance <= maximum_hops


def correlate_incidents(
    anomaly_data: pl.DataFrame,
    graph: ServiceDependencyGraph,
    correlation_window_seconds: int = 120,
    maximum_graph_hops: int = 2,
    severity_thresholds: dict[str, float]
    | None = None,
) -> tuple[
    pl.DataFrame,
    pl.DataFrame,
]:

    if severity_thresholds is None:
        severity_thresholds = {
            "critical": 0.80,
            "high": 0.60,
            "medium": 0.35,
            "low": 0.10,
        }

    anomalies = (
        anomaly_data
        .filter(
            pl.col("is_anomaly") == 1
        )
        .sort("feature_as_of_time")
    )

    if anomalies.is_empty():
        return (
            pl.DataFrame(),
            pl.DataFrame(),
        )

    open_incidents: list[
        dict[str, Any]
    ] = []

    assignments: list[
        dict[str, Any]
    ] = []

    next_incident = 1

    for row in anomalies.to_dicts():

        service = row["service"]

        timestamp = to_datetime(
            row["feature_as_of_time"]
        )

        anomaly_score = float(
            row["anomaly_score"]
        )

        chosen: dict[str, Any] | None = None

        for incident in reversed(
            open_incidents
        ):

            delta = (
                timestamp
                - incident[
                    "end_time"
                ]
            ).total_seconds()

            if (
                delta < 0
                or delta
                > correlation_window_seconds
            ):
                continue

            related = any(
                graph_related(
                    graph,
                    service,
                    existing_service,
                    maximum_graph_hops,
                )
                for existing_service
                in incident["services"]
            )

            if related:
                chosen = incident
                break

        if chosen is None:

            incident_id = (
                f"INC-{next_incident:04d}"
            )

            next_incident += 1

            chosen = {
                "incident_id":
                    incident_id,

                "start_time":
                    timestamp,

                "end_time":
                    timestamp,

                "services":
                    set(),

                "members":
                    [],
            }

            open_incidents.append(
                chosen
            )

        chosen["services"].add(
            service
        )

        chosen["end_time"] = max(
            chosen["end_time"],
            timestamp,
        )

        member = {
            "incident_id":
                chosen["incident_id"],

            "service":
                service,

            "feature_as_of_time":
                timestamp,

            "anomaly_score":
                anomaly_score,

            "anomaly_votes":
                int(
                    row.get(
                        "anomaly_votes",
                        0,
                    )
                ),
        }

        chosen["members"].append(
            member
        )

        assignments.append(
            member
        )

    incident_rows: list[
        dict[str, Any]
    ] = []

    for incident in open_incidents:

        members = incident[
            "members"
        ]

        primary = max(
            members,
            key=lambda item: (
                item[
                    "anomaly_score"
                ],
                item["service"],
            ),
        )

        scores = [
            float(
                member[
                    "anomaly_score"
                ]
            )
            for member in members
        ]

        max_score = max(scores)

        incident_rows.append(
            {
                "incident_id":
                    incident[
                        "incident_id"
                    ],

                "start_time":
                    incident[
                        "start_time"
                    ],

                "end_time":
                    incident[
                        "end_time"
                    ],

                "duration_seconds":
                    (
                        incident[
                            "end_time"
                        ]
                        - incident[
                            "start_time"
                        ]
                    ).total_seconds(),

                "primary_service":
                    primary[
                        "service"
                    ],

                "services":
                    sorted(
                        incident[
                            "services"
                        ]
                    ),

                "service_count":
                    len(
                        incident[
                            "services"
                        ]
                    ),

                "anomaly_count":
                    len(members),

                "max_anomaly_score":
                    max_score,

                "mean_anomaly_score":
                    sum(scores)
                    / len(scores),

                "severity":
                    severity_from_score(
                        max_score,
                        severity_thresholds,
                    ),

                "upstream_impact_count":
                    len(
                        graph.upstream(
                            primary[
                                "service"
                            ]
                        )
                    ),
            }
        )

    incidents = (
        pl.DataFrame(
            incident_rows
        )
        .sort(
            "max_anomaly_score",
            descending=True,
        )
    )

    membership = (
        pl.DataFrame(
            assignments
        )
        .sort(
            [
                "incident_id",
                "feature_as_of_time",
            ]
        )
    )

    return (
        incidents,
        membership,
    )
