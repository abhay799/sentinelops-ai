from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import polars as pl

from sentinelops.features.builder import percentile


def event_time(event: dict[str, Any]) -> datetime:
    return datetime.fromisoformat(
        event["event_time"]
    )


def build_temporal_service_features(
    events: list[dict[str, Any]],
    topology: dict[str, list[str]],
    short_seconds: int = 60,
    medium_seconds: int = 300,
) -> pl.DataFrame:

    rows: list[dict[str, Any]] = []

    for service, dependencies in topology.items():

        service_events = sorted(
            [
                event
                for event in events
                if event.get("service") == service
            ],
            key=event_time,
        )

        metric_events = [
            event
            for event in service_events
            if (
                event.get("telemetry_type") == "metric"
                and event.get(
                    "payload",
                    {},
                ).get("metric_name")
                == "http_request_duration_ms"
            )
        ]

        trace_events = [
            event
            for event in service_events
            if event.get("telemetry_type") == "trace"
        ]

        change_events = [
            event
            for event in service_events
            if event.get("telemetry_type") == "change"
        ]

        for index, current in enumerate(metric_events):

            as_of = event_time(current)

            short_start = (
                as_of
                - timedelta(
                    seconds=short_seconds
                )
            )

            medium_start = (
                as_of
                - timedelta(
                    seconds=medium_seconds
                )
            )

            # Only events at or before as_of are allowed.
            # This prevents future-data leakage.

            short_history = [
                event
                for event in metric_events
                if (
                    short_start
                    <= event_time(event)
                    <= as_of
                )
            ]

            medium_history = [
                event
                for event in metric_events
                if (
                    medium_start
                    <= event_time(event)
                    <= as_of
                )
            ]

            short_latencies = [
                float(
                    event["payload"]["value"]
                )
                for event in short_history
            ]

            medium_latencies = [
                float(
                    event["payload"]["value"]
                )
                for event in medium_history
            ]

            short_statuses = [
                int(
                    event["payload"].get(
                        "status_code",
                        200,
                    )
                )
                for event in short_history
            ]

            medium_statuses = [
                int(
                    event["payload"].get(
                        "status_code",
                        200,
                    )
                )
                for event in medium_history
            ]

            short_errors = sum(
                1
                for code in short_statuses
                if code >= 500
            )

            medium_errors = sum(
                1
                for code in medium_statuses
                if code >= 500
            )

            trace_history = [
                event
                for event in trace_events
                if (
                    medium_start
                    <= event_time(event)
                    <= as_of
                )
            ]

            change_history = [
                event
                for event in change_events
                if (
                    medium_start
                    <= event_time(event)
                    <= as_of
                )
            ]

            trace_count_5m = len(
                trace_history
            )

            change_count_5m = len(
                change_history
            )

            window_events = (
                medium_history
                + trace_history
                + change_history
            )

            max_event_time = max(
                (
                    event_time(event)
                    for event in window_events
                ),
                default=as_of,
            )

            rows.append(
                {
                    "service":
                        service,

                    "event_index":
                        index,

                    # Keep these as real timezone-aware
                    # datetime objects.
                    "feature_as_of_time":
                        as_of,

                    "window_max_event_time":
                        max_event_time,

                    "current_latency_ms":
                        float(
                            current[
                                "payload"
                            ][
                                "value"
                            ]
                        ),

                    "current_is_error":
                        int(
                            current[
                                "payload"
                            ].get(
                                "status_code",
                                200,
                            )
                        )
                        >= 500,

                    "request_rate_60s":
                        len(short_history)
                        / short_seconds
                        * 60.0,

                    "error_rate_60s":
                        (
                            short_errors
                            / len(short_history)
                            if short_history
                            else 0.0
                        ),

                    "latency_mean_60s":
                        (
                            sum(short_latencies)
                            / len(short_latencies)
                            if short_latencies
                            else 0.0
                        ),

                    "latency_p95_60s":
                        percentile(
                            short_latencies,
                            0.95,
                        ),

                    "request_rate_300s":
                        len(medium_history)
                        / medium_seconds
                        * 60.0,

                    "error_rate_300s":
                        (
                            medium_errors
                            / len(medium_history)
                            if medium_history
                            else 0.0
                        ),

                    "latency_mean_300s":
                        (
                            sum(medium_latencies)
                            / len(medium_latencies)
                            if medium_latencies
                            else 0.0
                        ),

                    "latency_p95_300s":
                        percentile(
                            medium_latencies,
                            0.95,
                        ),

                    "latency_p99_300s":
                        percentile(
                            medium_latencies,
                            0.99,
                        ),

                    "trace_count_300s":
                        trace_count_5m,

                    "change_count_300s":
                        change_count_5m,

                    "dependency_count":
                        len(dependencies),
                }
            )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(rows)
        .sort(
            [
                "service",
                "feature_as_of_time",
            ]
        )
    )


def validate_point_in_time(
    features: pl.DataFrame,
) -> None:

    if features.is_empty():
        raise ValueError(
            "Temporal feature dataset is empty"
        )

    required_columns = {
        "feature_as_of_time",
        "window_max_event_time",
    }

    missing = (
        required_columns
        - set(features.columns)
    )

    if missing:
        raise ValueError(
            "Missing temporal columns: "
            f"{sorted(missing)}"
        )

    invalid = features.filter(
        pl.col(
            "window_max_event_time"
        )
        >
        pl.col(
            "feature_as_of_time"
        )
    )

    if invalid.height > 0:
        raise ValueError(
            "Point-in-time leakage detected"
        )