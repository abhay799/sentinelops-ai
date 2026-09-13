from datetime import UTC, datetime, timedelta

from sentinelops.features.temporal import (
    build_temporal_service_features,
    validate_point_in_time,
)


def metric_event(
    timestamp: datetime,
    latency: float,
    status: int,
):
    return {
        "service": "payment-service",
        "telemetry_type": "metric",
        "event_time": timestamp.isoformat(),
        "payload": {
            "metric_name": "http_request_duration_ms",
            "value": latency,
            "status_code": status,
        },
    }


def test_temporal_features_are_point_in_time_safe():
    start = datetime(
        2026,
        9,
        14,
        0,
        0,
        tzinfo=UTC,
    )

    events = [
        metric_event(
            start,
            100,
            200,
        ),
        metric_event(
            start + timedelta(seconds=10),
            500,
            503,
        ),
        {
            "service": "payment-service",
            "telemetry_type": "change",
            "event_time": (
                start + timedelta(seconds=30)
            ).isoformat(),
            "payload": {
                "change_type": "deployment",
            },
        },
    ]

    topology = {
        "payment-service": [],
    }

    features = build_temporal_service_features(
        events,
        topology,
    )

    validate_point_in_time(features)

    assert features.height == 2

    final_row = (
        features
        .sort("feature_as_of_time")
        .tail(1)
        .to_dicts()[0]
    )

    assert final_row["error_rate_60s"] == 0.5

    # Future change must not leak into features.
    assert final_row["change_count_300s"] == 0


def test_rolling_latency_uses_history_only():
    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    events = [
        metric_event(
            start,
            100,
            200,
        ),
        metric_event(
            start + timedelta(seconds=10),
            200,
            200,
        ),
        metric_event(
            start + timedelta(seconds=20),
            900,
            200,
        ),
    ]

    features = build_temporal_service_features(
        events,
        {
            "payment-service": [],
        },
    )

    first = (
        features
        .sort("feature_as_of_time")
        .head(1)
        .to_dicts()[0]
    )

    assert first["latency_mean_60s"] == 100.0
