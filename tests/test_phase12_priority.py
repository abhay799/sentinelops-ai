import polars as pl

from sentinelops.impact.prioritization import (
    build_incident_priority,
)

CONFIG = {
    "weights": {
        "max_service_impact": 0.55,
        "mean_service_impact": 0.25,
        "blast_radius": 0.20,
    },

    "blast_radius_reference_services": 7,

    "severity": {
        "critical": 0.80,
        "high": 0.60,
        "medium": 0.35,
    },
}


def members():

    return pl.DataFrame(
        [
            {
                "incident_id": "INC-1",
                "service": "payment-service",
            },
            {
                "incident_id": "INC-1",
                "service": "order-service",
            },
            {
                "incident_id": "INC-2",
                "service": "notification-service",
            },
        ]
    )


def impacts():

    return pl.DataFrame(
        [
            {
                "service": "payment-service",
                "business_impact_score": 0.95,
                "latency_burn_score": 1.0,
                "error_burn_score": 1.0,
                "predicted_failure_probability": 0.90,
            },
            {
                "service": "order-service",
                "business_impact_score": 0.70,
                "latency_burn_score": 0.70,
                "error_burn_score": 0.60,
                "predicted_failure_probability": 0.70,
            },
            {
                "service": "notification-service",
                "business_impact_score": 0.20,
                "latency_burn_score": 0.10,
                "error_burn_score": 0.10,
                "predicted_failure_probability": 0.10,
            },
        ]
    )


def test_high_impact_incident_ranks_first():

    result = build_incident_priority(
        members(),
        impacts(),
        CONFIG,
    )

    assert (
        result["incident_id"][0]
        == "INC-1"
    )


def test_priority_score_bounded():

    result = build_incident_priority(
        members(),
        impacts(),
        CONFIG,
    )

    assert (
        result[
            "remediation_priority_score"
        ].min()
        >= 0.0
    )

    assert (
        result[
            "remediation_priority_score"
        ].max()
        <= 1.0
    )


def test_blast_radius_is_present():

    result = build_incident_priority(
        members(),
        impacts(),
        CONFIG,
    )

    incident = (
        result
        .filter(
            pl.col("incident_id")
            == "INC-1"
        )
        .to_dicts()[0]
    )

    assert (
        incident[
            "affected_service_count"
        ]
        == 2
    )

    assert (
        incident[
            "blast_radius_score"
        ]
        > 0
    )


def test_highest_impact_service():

    result = build_incident_priority(
        members(),
        impacts(),
        CONFIG,
    )

    incident = (
        result
        .filter(
            pl.col("incident_id")
            == "INC-1"
        )
        .to_dicts()[0]
    )

    assert (
        incident[
            "highest_impact_service"
        ]
        == "payment-service"
    )
