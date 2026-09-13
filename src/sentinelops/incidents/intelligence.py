from __future__ import annotations

from typing import Any

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


def confidence_from_incident(
    anomaly_count: int,
    service_count: int,
    max_anomaly_score: float,
) -> float:

    anomaly_component = min(
        anomaly_count / 5.0,
        1.0,
    )

    service_component = min(
        service_count / 3.0,
        1.0,
    )

    score_component = min(
        max_anomaly_score,
        1.0,
    )

    confidence = (
        0.40 * score_component
        + 0.35 * anomaly_component
        + 0.25 * service_component
    )

    return round(
        min(confidence, 1.0),
        6,
    )


def enrich_incidents(
    incidents: pl.DataFrame,
    members: pl.DataFrame,
    graph: ServiceDependencyGraph,
) -> pl.DataFrame:

    rows: list[dict[str, Any]] = []

    for incident in incidents.to_dicts():

        incident_id = incident[
            "incident_id"
        ]

        incident_members = (
            members
            .filter(
                pl.col("incident_id")
                == incident_id
            )
            .sort(
                "anomaly_score",
                descending=True,
            )
        )

        evidence = []

        for member in (
            incident_members
            .head(5)
            .to_dicts()
        ):

            evidence.append(
                {
                    "service":
                        member["service"],

                    "timestamp":
                        member[
                            "feature_as_of_time"
                        ],

                    "anomaly_score":
                        float(
                            member[
                                "anomaly_score"
                            ]
                        ),

                    "anomaly_votes":
                        int(
                            member[
                                "anomaly_votes"
                            ]
                        ),
                }
            )

        primary_service = incident[
            "primary_service"
        ]

        confidence = (
            confidence_from_incident(
                anomaly_count=int(
                    incident[
                        "anomaly_count"
                    ]
                ),
                service_count=int(
                    incident[
                        "service_count"
                    ]
                ),
                max_anomaly_score=float(
                    incident[
                        "max_anomaly_score"
                    ]
                ),
            )
        )

        rows.append(
            {
                **incident,

                "confidence":
                    confidence,

                "evidence_count":
                    len(evidence),

                "evidence":
                    evidence,

                "direct_dependencies":
                    graph.dependencies(
                        primary_service
                    ),

                "direct_dependents":
                    graph.dependents(
                        primary_service
                    ),

                "affected_upstream_services":
                    graph.upstream(
                        primary_service
                    ),

                "correlation_basis":
                    [
                        "temporal_proximity",
                        "service_graph_proximity",
                        "anomaly_strength",
                    ],
            }
        )

    return (
        pl.DataFrame(rows)
        .sort(
            [
                "severity",
                "confidence",
            ],
            descending=True,
        )
    )