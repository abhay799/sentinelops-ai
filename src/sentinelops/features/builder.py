from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

import polars as pl
import yaml


def percentile(
    values: list[float],
    percentile_value: float,
) -> float:
    if not values:
        return 0.0

    values = sorted(values)

    index = (len(values) - 1) * percentile_value

    lower = math.floor(index)
    upper = math.ceil(index)

    if lower == upper:
        return float(values[lower])

    weight = index - lower

    return float(
        values[lower] * (1 - weight)
        + values[upper] * weight
    )


def load_events(
    path: Path,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line in file:
            line = line.strip()

            if line:
                events.append(
                    json.loads(line)
                )

    return events


def load_topology(
    path: Path,
) -> dict[str, list[str]]:
    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        config = yaml.safe_load(file)

    return {
        service: value["depends_on"]
        for service, value
        in config["topology"].items()
    }


def calculate_request_rate_change(
    timestamps: list[datetime],
) -> float:
    if len(timestamps) < 4:
        return 0.0

    timestamps = sorted(timestamps)

    midpoint = len(timestamps) // 2

    first = timestamps[:midpoint]
    second = timestamps[midpoint:]

    def rate(
        values: list[datetime],
    ) -> float:
        if len(values) < 2:
            return float(len(values))

        duration = max(
            (
                values[-1] - values[0]
            ).total_seconds(),
            1.0,
        )

        return len(values) / duration * 60.0

    return rate(second) - rate(first)


def build_service_features(
    events: list[dict[str, Any]],
    topology: dict[str, list[str]],
    infrastructure: dict[str, dict[str, float]],
) -> pl.DataFrame:

    rows: list[dict[str, Any]] = []

    for service, dependencies in topology.items():

        service_events = [
            event
            for event in events
            if event.get("service") == service
        ]

        metric_events = [
            event
            for event in service_events
            if event.get("telemetry_type") == "metric"
            and event.get("payload", {}).get(
                "metric_name"
            )
            == "http_request_duration_ms"
        ]

        trace_events = [
            event
            for event in service_events
            if event.get("telemetry_type")
            == "trace"
        ]

        change_events = [
            event
            for event in service_events
            if event.get("telemetry_type")
            == "change"
        ]

        latencies = [
            float(
                event["payload"]["value"]
            )
            for event in metric_events
        ]

        statuses = [
            int(
                event["payload"]
                .get("status_code", 200)
            )
            for event in metric_events
        ]

        timestamps = [
            datetime.fromisoformat(
                event["event_time"]
            )
            for event in metric_events
        ]

        request_count = len(
            metric_events
        )

        error_count = sum(
            1
            for code in statuses
            if code >= 500
        )

        if timestamps:
            duration_seconds = max(
                (
                    max(timestamps)
                    - min(timestamps)
                ).total_seconds(),
                1.0,
            )
        else:
            duration_seconds = 1.0

        infra = infrastructure.get(
            service,
            {},
        )

        rows.append(
            {
                "service": service,

                "request_count":
                    request_count,

                "request_rate_per_min":
                    request_count
                    / duration_seconds
                    * 60.0,

                "request_rate_change":
                    calculate_request_rate_change(
                        timestamps
                    ),

                "error_rate":
                    (
                        error_count
                        / request_count
                        if request_count
                        else 0.0
                    ),

                "latency_mean_ms":
                    (
                        sum(latencies)
                        / len(latencies)
                        if latencies
                        else 0.0
                    ),

                "latency_p95_ms":
                    percentile(
                        latencies,
                        0.95,
                    ),

                "latency_p99_ms":
                    percentile(
                        latencies,
                        0.99,
                    ),

                "trace_count":
                    len(trace_events),

                "change_event_count":
                    len(change_events),

                "dependency_count":
                    len(dependencies),

                "cpu_seconds_per_second":
                    infra.get(
                        "cpu_seconds_per_second",
                        0.0,
                    ),

                "memory_rss_bytes":
                    infra.get(
                        "memory_rss_bytes",
                        0.0,
                    ),

                "memory_growth_bytes_per_second":
                    infra.get(
                        "memory_growth_bytes_per_second",
                        0.0,
                    ),
            }
        )

    return pl.DataFrame(rows)