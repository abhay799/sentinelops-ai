from __future__ import annotations

from typing import Any
from uuid import uuid4

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


def confidence_band(
    score: float,
    high: float,
    medium: float,
) -> str:

    if score >= high:
        return "high"

    if score >= medium:
        return "medium"

    return "low"


def normalize_graph_impact(
    graph: ServiceDependencyGraph,
    service: str,
) -> float:

    service_count = max(
        len(graph.services()) - 1,
        1,
    )

    impacted = len(
        graph.upstream(service)
    )

    return min(
        impacted / service_count,
        1.0,
    )


def build_rca_hypotheses(
    incidents: pl.DataFrame,
    members: pl.DataFrame,
    anomaly_data: pl.DataFrame,
    graph: ServiceDependencyGraph,
    weights: dict[str, float],
    confidence_config: dict[str, float],
    max_candidates: int = 5,
) -> pl.DataFrame:

    rows: list[dict[str, Any]] = []

    for incident in incidents.to_dicts():

        incident_id = incident[
            "incident_id"
        ]

        primary_service = incident[
            "primary_service"
        ]

        incident_members = (
            members
            .filter(
                pl.col("incident_id")
                == incident_id
            )
        )

        candidate_services = sorted(
            set(
                incident_members[
                    "service"
                ].to_list()
            )
        )

        candidate_rows: list[
            dict[str, Any]
        ] = []

        for service in candidate_services:

            member_rows = (
                incident_members
                .filter(
                    pl.col("service")
                    == service
                )
            )

            anomaly_strength = float(
                member_rows[
                    "anomaly_score"
                ].max()
            )

            service_anomalies = (
                anomaly_data
                .filter(
                    pl.col("service")
                    == service
                )
            )

            if (
                "change_count_300s"
                in service_anomalies.columns
                and service_anomalies.height > 0
            ):
                change_count = int(
                    service_anomalies[
                        "change_count_300s"
                    ].max()
                )
            else:
                change_count = 0

            change_signal = min(
                float(change_count),
                1.0,
            )

            graph_impact = (
                normalize_graph_impact(
                    graph,
                    service,
                )
            )

            primary_bonus = (
                1.0
                if service
                == primary_service
                else 0.0
            )

            score = (
                weights[
                    "anomaly_strength"
                ]
                * anomaly_strength

                + weights[
                    "change_signal"
                ]
                * change_signal

                + weights[
                    "graph_impact"
                ]
                * graph_impact

                + weights[
                    "primary_service_bonus"
                ]
                * primary_bonus
            )

            evidence: list[
                dict[str, Any]
            ] = []

            # --------------------------------------------
            # Anomaly evidence
            # --------------------------------------------

            evidence.append(
                {
                    "type":
                        "anomaly",

                    "service":
                        service,

                    "value":
                        float(
                            anomaly_strength
                        ),

                    "description":
                        (
                            "Observed anomaly "
                            "strength in correlated "
                            "incident telemetry"
                        ),
                }
            )

            # --------------------------------------------
            # Change evidence
            # --------------------------------------------

            if change_count > 0:

                evidence.append(
                    {
                        "type":
                            "change",

                        "service":
                            service,

                        "value":
                            float(
                                change_count
                            ),

                        "description":
                            (
                                "Recent deployment "
                                "or configuration "
                                "change signal"
                            ),
                    }
                )

            # --------------------------------------------
            # Graph evidence
            # --------------------------------------------

            upstream = graph.upstream(
                service
            )

            if upstream:

                evidence.append(
                    {
                        "type":
                            "graph",

                        "service":
                            service,

                        "value":
                            float(
                                len(upstream)
                            ),

                        "description":
                            (
                                "Service can affect "
                                "upstream dependent "
                                "services"
                            ),
                    }
                )

            # --------------------------------------------
            # Correlation evidence
            # --------------------------------------------

            evidence.append(
                {
                    "type":
                        "correlation",

                    "service":
                        service,

                    "value":
                        float(
                            member_rows.height
                        ),

                    "description":
                        (
                            "Service appears in "
                            "the correlated incident"
                        ),
                }
            )

            candidate_rows.append(
                {
                    "hypothesis_id":
                        str(uuid4()),

                    "incident_id":
                        incident_id,

                    "candidate_service":
                        service,

                    "candidate_status":
                        "candidate",

                    "rca_score":
                        float(
                            round(
                                score,
                                6,
                            )
                        ),

                    "confidence":
                        confidence_band(
                            score,
                            high=float(
                                confidence_config[
                                    "high"
                                ]
                            ),
                            medium=float(
                                confidence_config[
                                    "medium"
                                ]
                            ),
                        ),

                    "anomaly_strength":
                        float(
                            anomaly_strength
                        ),

                    "change_signal":
                        float(
                            change_signal
                        ),

                    "change_count":
                        int(
                            change_count
                        ),

                    "graph_impact":
                        float(
                            graph_impact
                        ),

                    "primary_service_bonus":
                        float(
                            primary_bonus
                        ),

                    "evidence_count":
                        int(
                            len(evidence)
                        ),

                    "evidence":
                        evidence,

                    "confirmed_root_cause":
                        False,

                    "requires_challenger":
                        True,

                    "requires_human_confirmation":
                        True,
                }
            )

        candidate_rows.sort(
            key=lambda row: row[
                "rca_score"
            ],
            reverse=True,
        )

        candidate_rows = (
            candidate_rows[
                :max_candidates
            ]
        )

        for rank, candidate in enumerate(
            candidate_rows,
            start=1,
        ):

            candidate[
                "rank"
            ] = int(rank)

            rows.append(
                candidate
            )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(rows)
        .sort(
            [
                "incident_id",
                "rank",
            ]
        )
    )