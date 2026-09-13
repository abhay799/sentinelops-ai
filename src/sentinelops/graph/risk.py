from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


@dataclass(frozen=True)
class RiskContribution:
    source_service: str
    target_service: str
    source_score: float
    distance: int
    propagated_score: float


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


def aggregate_direct_risk(
    anomaly_data: pl.DataFrame,
) -> dict[str, dict[str, float | int]]:

    grouped = (
        anomaly_data
        .group_by("service")
        .agg(
            [
                pl.col("anomaly_score")
                .max()
                .alias("direct_anomaly_score"),

                pl.col("is_anomaly")
                .sum()
                .alias("anomaly_count"),

                pl.col("anomaly_votes")
                .max()
                .alias("max_anomaly_votes"),
            ]
        )
    )

    result: dict[
        str,
        dict[str, float | int],
    ] = {}

    for row in grouped.to_dicts():

        result[row["service"]] = {
            "direct_anomaly_score":
                float(
                    row[
                        "direct_anomaly_score"
                    ]
                ),

            "anomaly_count":
                int(
                    row[
                        "anomaly_count"
                    ]
                ),

            "max_anomaly_votes":
                int(
                    row[
                        "max_anomaly_votes"
                    ]
                ),
        }

    return result


def build_graph_risk(
    graph: ServiceDependencyGraph,
    anomaly_data: pl.DataFrame,
    decay: float = 0.60,
    minimum_source_score: float = 0.10,
    severity_thresholds: dict[str, float]
    | None = None,
) -> tuple[
    pl.DataFrame,
    list[RiskContribution],
]:

    if severity_thresholds is None:
        severity_thresholds = {
            "critical": 0.80,
            "high": 0.60,
            "medium": 0.35,
            "low": 0.10,
        }

    direct_risk = aggregate_direct_risk(
        anomaly_data
    )

    propagated_by_target: dict[
        str,
        list[RiskContribution],
    ] = defaultdict(list)

    contributions: list[
        RiskContribution
    ] = []

    for source in graph.services():

        source_values = direct_risk.get(
            source,
            {
                "direct_anomaly_score": 0.0,
                "anomaly_count": 0,
                "max_anomaly_votes": 0,
            },
        )

        source_score = float(
            source_values[
                "direct_anomaly_score"
            ]
        )

        if (
            source_score
            < minimum_source_score
        ):
            continue

        distances = (
            graph.propagation_distances(
                source
            )
        )

        for target, distance in (
            distances.items()
        ):

            propagated_score = (
                source_score
                * (decay ** distance)
            )

            contribution = (
                RiskContribution(
                    source_service=source,
                    target_service=target,
                    source_score=source_score,
                    distance=distance,
                    propagated_score=round(
                        propagated_score,
                        6,
                    ),
                )
            )

            contributions.append(
                contribution
            )

            propagated_by_target[
                target
            ].append(
                contribution
            )

    rows: list[dict[str, Any]] = []

    for service in graph.services():

        service_values = (
            direct_risk.get(
                service,
                {
                    "direct_anomaly_score":
                        0.0,
                    "anomaly_count":
                        0,
                    "max_anomaly_votes":
                        0,
                },
            )
        )

        direct_score = float(
            service_values[
                "direct_anomaly_score"
            ]
        )

        incoming = (
            propagated_by_target.get(
                service,
                [],
            )
        )

        propagated_score = max(
            (
                item.propagated_score
                for item in incoming
            ),
            default=0.0,
        )

        graph_risk_score = max(
            direct_score,
            propagated_score,
        )

        rows.append(
            {
                "service":
                    service,

                "direct_anomaly_score":
                    direct_score,

                "propagated_risk_score":
                    propagated_score,

                "graph_risk_score":
                    graph_risk_score,

                "severity":
                    severity_from_score(
                        graph_risk_score,
                        severity_thresholds,
                    ),

                "anomaly_count":
                    int(
                        service_values[
                            "anomaly_count"
                        ]
                    ),

                "max_anomaly_votes":
                    int(
                        service_values[
                            "max_anomaly_votes"
                        ]
                    ),

                "dependency_count":
                    len(
                        graph.dependencies(
                            service
                        )
                    ),

                "dependent_count":
                    len(
                        graph.dependents(
                            service
                        )
                    ),

                "upstream_impact_count":
                    len(
                        graph.upstream(
                            service
                        )
                    ),

                "risk_source_count":
                    len(incoming),

                "risk_sources":
                    sorted(
                        {
                            item.source_service
                            for item in incoming
                        }
                    ),
            }
        )

    return (
        pl.DataFrame(rows)
        .sort(
            "graph_risk_score",
            descending=True,
        ),
        contributions,
    )