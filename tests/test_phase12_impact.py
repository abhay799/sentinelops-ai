from datetime import UTC, datetime

import polars as pl

from sentinelops.impact.engine import (
    build_service_impact,
    severity_band,
)

CONFIG = {
    "slo": {
        "target_latency_p95_ms":
            250.0,
        "target_error_rate":
            0.01,
    },

    "service_criticality": {
        "payment-service":
            1.0,

        "notification-service":
            0.4,
    },

    "weights": {
        "service_criticality":
            0.30,

        "latency_burn":
            0.20,

        "error_burn":
            0.20,

        "anomaly_risk":
            0.15,

        "predicted_failure":
            0.15,
    },

    "severity": {
        "critical": 0.80,
        "high": 0.60,
        "medium": 0.35,
    },
}


def anomaly_data():

    timestamp = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    return pl.DataFrame(
        [
            {
                "service":
                    "payment-service",

                "feature_as_of_time":
                    timestamp,

                "latency_p95_60s":
                    900.0,

                "error_rate_60s":
                    0.08,

                "anomaly_score":
                    0.95,
            },
            {
                "service":
                    "notification-service",

                "feature_as_of_time":
                    timestamp,

                "latency_p95_60s":
                    100.0,

                "error_rate_60s":
                    0.0,

                "anomaly_score":
                    0.10,
            },
        ]
    )


def predictions():

    timestamp = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    return pl.DataFrame(
        [
            {
                "service":
                    "payment-service",

                "feature_as_of_time":
                    timestamp,

                "failure_probability":
                    0.90,
            },
            {
                "service":
                    "notification-service",

                "feature_as_of_time":
                    timestamp,

                "failure_probability":
                    0.10,
            },
        ]
    )


def test_high_impact_service_ranks_first():

    result = build_service_impact(
        anomaly_data(),
        predictions(),
        CONFIG,
    )

    assert (
        result[
            "service"
        ][0]
        == "payment-service"
    )


def test_scores_are_bounded():

    result = build_service_impact(
        anomaly_data(),
        predictions(),
        CONFIG,
    )

    assert (
        result[
            "business_impact_score"
        ].min()
        >= 0.0
    )

    assert (
        result[
            "business_impact_score"
        ].max()
        <= 1.0
    )


def test_slo_breach_increases_impact():

    result = build_service_impact(
        anomaly_data(),
        predictions(),
        CONFIG,
    )

    payment = (
        result
        .filter(
            pl.col("service")
            == "payment-service"
        )
        .to_dicts()[0]
    )

    assert (
        payment[
            "latency_slo_ratio"
        ]
        > 1.0
    )

    assert (
        payment[
            "error_slo_ratio"
        ]
        > 1.0
    )


def test_severity_band():

    assert (
        severity_band(
            0.90,
            CONFIG[
                "severity"
            ],
        )
        == "critical"
    )

    assert (
        severity_band(
            0.20,
            CONFIG[
                "severity"
            ],
        )
        == "low"
    )
