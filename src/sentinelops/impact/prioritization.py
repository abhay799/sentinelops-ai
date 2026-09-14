from __future__ import annotations

from typing import Any

import polars as pl


def clamp(value: float) -> float:
    return max(
        0.0,
        min(1.0, value),
    )


def priority_band(
    score: float,
    thresholds: dict[str, float],
) -> str:

    if score >= float(thresholds["critical"]):
        return "critical"

    if score >= float(thresholds["high"]):
        return "high"

    if score >= float(thresholds["medium"]):
        return "medium"

    return "low"


def _detect_service_column(
    members: pl.DataFrame,
) -> str:

    candidates = [
        "service",
        "member_service",
        "service_name",
    ]

    for candidate in candidates:
        if candidate in members.columns:
            return candidate

    raise ValueError(
        "Could not determine service column "
        f"from incident-members columns: {members.columns}"
    )


def build_incident_priority(
    incident_members: pl.DataFrame,
    service_impact: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    if incident_members.is_empty():
        return pl.DataFrame()

    if service_impact.is_empty():
        return pl.DataFrame()

    service_column = _detect_service_column(
        incident_members
    )

    members = (
        incident_members
        .select(
            [
                "incident_id",
                pl.col(
                    service_column
                ).alias("service"),
            ]
        )
        .unique()
    )

    joined = members.join(
        service_impact,
        on="service",
        how="left",
    )

    joined = joined.with_columns(
        [
            pl.col(
                "business_impact_score"
            )
            .fill_null(0.0),

            pl.col(
                "latency_burn_score"
            )
            .fill_null(0.0),

            pl.col(
                "error_burn_score"
            )
            .fill_null(0.0),

            pl.col(
                "predicted_failure_probability"
            )
            .fill_null(0.0),
        ]
    )

    weights = config["weights"]

    blast_reference = max(
        int(
            config[
                "blast_radius_reference_services"
            ]
        ),
        1,
    )

    rows: list[dict[str, Any]] = []

    for incident_id in (
        joined["incident_id"]
        .unique()
        .to_list()
    ):

        incident = joined.filter(
            pl.col("incident_id")
            == incident_id
        )

        if incident.is_empty():
            continue

        top = (
            incident
            .sort(
                "business_impact_score",
                descending=True,
            )
            .to_dicts()[0]
        )

        affected_services = (
            incident["service"]
            .unique()
            .to_list()
        )

        service_count = len(
            affected_services
        )

        max_impact = float(
            incident[
                "business_impact_score"
            ].max()
        )

        mean_impact = float(
            incident[
                "business_impact_score"
            ].mean()
        )

        blast_radius = clamp(
            service_count
            / blast_reference
        )

        priority_score = (
            float(
                weights[
                    "max_service_impact"
                ]
            )
            * max_impact

            + float(
                weights[
                    "mean_service_impact"
                ]
            )
            * mean_impact

            + float(
                weights[
                    "blast_radius"
                ]
            )
            * blast_radius
        )

        priority_score = clamp(
            priority_score
        )

        rows.append(
            {
                "incident_id":
                    incident_id,

                "affected_service_count":
                    service_count,

                "affected_services":
                    affected_services,

                "highest_impact_service":
                    top["service"],

                "max_service_impact":
                    round(
                        max_impact,
                        6,
                    ),

                "mean_service_impact":
                    round(
                        mean_impact,
                        6,
                    ),

                "max_latency_burn":
                    round(
                        float(
                            incident[
                                "latency_burn_score"
                            ].max()
                        ),
                        6,
                    ),

                "max_error_burn":
                    round(
                        float(
                            incident[
                                "error_burn_score"
                            ].max()
                        ),
                        6,
                    ),

                "max_predicted_failure":
                    round(
                        float(
                            incident[
                                "predicted_failure_probability"
                            ].max()
                        ),
                        6,
                    ),

                "blast_radius_score":
                    round(
                        blast_radius,
                        6,
                    ),

                "remediation_priority_score":
                    round(
                        priority_score,
                        6,
                    ),

                "priority":
                    priority_band(
                        priority_score,
                        config["severity"],
                    ),
            }
        )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(
            rows,
            strict=False,
        )
        .sort(
            "remediation_priority_score",
            descending=True,
        )
        .with_row_index(
            "priority_rank",
            offset=1,
        )
    )
