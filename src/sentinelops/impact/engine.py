from __future__ import annotations

from typing import Any

import polars as pl


def clamp(
    value: float,
) -> float:

    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )


def severity_band(
    score: float,
    thresholds: dict[str, float],
) -> str:

    if score >= float(
        thresholds["critical"]
    ):
        return "critical"

    if score >= float(
        thresholds["high"]
    ):
        return "high"

    if score >= float(
        thresholds["medium"]
    ):
        return "medium"

    return "low"


def latest_prediction_risk(
    predictions: pl.DataFrame,
) -> dict[str, float]:

    if predictions.is_empty():
        return {}

    latest: dict[str, float] = {}

    for row in (
        predictions
        .sort("feature_as_of_time")
        .to_dicts()
    ):

        latest[
            row["service"]
        ] = float(
            row[
                "failure_probability"
            ]
        )

    return latest


def build_service_impact(
    anomaly_data: pl.DataFrame,
    predictions: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    prediction_risk = (
        latest_prediction_risk(
            predictions
        )
    )

    criticality = config[
        "service_criticality"
    ]

    weights = config[
        "weights"
    ]

    slo = config[
        "slo"
    ]

    thresholds = config[
        "severity"
    ]

    rows: list[
        dict[str, Any]
    ] = []

    for service in (
        anomaly_data[
            "service"
        ]
        .unique()
        .to_list()
    ):

        service_rows = (
            anomaly_data
            .filter(
                pl.col("service")
                == service
            )
            .sort(
                "feature_as_of_time"
            )
        )

        if service_rows.is_empty():
            continue

        latest = (
            service_rows
            .tail(1)
            .to_dicts()[0]
        )

        latency = float(
            latest.get(
                "latency_p95_60s",
                0.0,
            )
        )

        error_rate = float(
            latest.get(
                "error_rate_60s",
                0.0,
            )
        )

        anomaly_score = float(
            latest.get(
                "anomaly_score",
                0.0,
            )
        )

        failure_probability = float(
            prediction_risk.get(
                service,
                0.0,
            )
        )

        service_criticality = float(
            criticality.get(
                service,
                0.50,
            )
        )

        latency_ratio = (
            latency
            / float(
                slo[
                    "target_latency_p95_ms"
                ]
            )
        )

        error_ratio = (
            error_rate
            / float(
                slo[
                    "target_error_rate"
                ]
            )
        )

        latency_burn = clamp(
            latency_ratio / 4.0
        )

        error_burn = clamp(
            error_ratio / 4.0
        )

        anomaly_risk = clamp(
            anomaly_score
        )

        failure_probability = clamp(
            failure_probability
        )

        impact_score = (
            float(
                weights[
                    "service_criticality"
                ]
            )
            * service_criticality

            + float(
                weights[
                    "latency_burn"
                ]
            )
            * latency_burn

            + float(
                weights[
                    "error_burn"
                ]
            )
            * error_burn

            + float(
                weights[
                    "anomaly_risk"
                ]
            )
            * anomaly_risk

            + float(
                weights[
                    "predicted_failure"
                ]
            )
            * failure_probability
        )

        impact_score = clamp(
            impact_score
        )

        rows.append(
            {
                "service":
                    service,

                "feature_as_of_time":
                    latest[
                        "feature_as_of_time"
                    ],

                "service_criticality":
                    round(
                        service_criticality,
                        6,
                    ),

                "latency_p95_ms":
                    round(
                        latency,
                        6,
                    ),

                "error_rate":
                    round(
                        error_rate,
                        6,
                    ),

                "latency_slo_ratio":
                    round(
                        latency_ratio,
                        6,
                    ),

                "error_slo_ratio":
                    round(
                        error_ratio,
                        6,
                    ),

                "latency_burn_score":
                    round(
                        latency_burn,
                        6,
                    ),

                "error_burn_score":
                    round(
                        error_burn,
                        6,
                    ),

                "anomaly_risk":
                    round(
                        anomaly_risk,
                        6,
                    ),

                "predicted_failure_probability":
                    round(
                        failure_probability,
                        6,
                    ),

                "business_impact_score":
                    round(
                        impact_score,
                        6,
                    ),

                "impact_severity":
                    severity_band(
                        impact_score,
                        thresholds,
                    ),
            }
        )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(
            rows
        )
        .sort(
            "business_impact_score",
            descending=True,
        )
    )
