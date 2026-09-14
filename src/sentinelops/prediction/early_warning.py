from __future__ import annotations

from math import sqrt
from typing import Any

import polars as pl


def mean(
    values: list[float],
) -> float:

    if not values:
        return 0.0

    return sum(values) / len(values)


def standard_deviation(
    values: list[float],
) -> float:

    if len(values) < 2:
        return 0.0

    average = mean(values)

    variance = sum(
        (value - average) ** 2
        for value in values
    ) / len(values)

    return sqrt(variance)


def positive_deviation_score(
    current: float,
    history: list[float],
) -> float:

    if not history:
        return 0.0

    baseline = mean(history)

    std = standard_deviation(
        history
    )

    delta = current - baseline

    if delta <= 0:
        return 0.0

    if std > 1e-9:
        z_score = delta / std

        return min(
            z_score / 3.0,
            1.0,
        )

    scale = max(
        abs(baseline),
        1.0,
    )

    return min(
        delta / scale,
        1.0,
    )


def build_early_warning_dataset(
    anomaly_data: pl.DataFrame,
    lookahead_events: int,
    minimum_history_events: int,
    history_window_events: int,
    warning_threshold: float,
    weights: dict[str, float],
) -> pl.DataFrame:

    rows: list[
        dict[str, Any]
    ] = []

    services = (
        anomaly_data[
            "service"
        ]
        .unique()
        .to_list()
    )

    for service in services:

        service_data = (
            anomaly_data
            .filter(
                pl.col("service")
                == service
            )
            .sort(
                "feature_as_of_time"
            )
        )

        observations = (
            service_data
            .to_dicts()
        )

        for index, current in enumerate(
            observations
        ):

            history_start = max(
                0,
                index
                - history_window_events,
            )

            history = observations[
                history_start:index
            ]

            future = observations[
                index + 1:
                index + 1
                + lookahead_events
            ]

            future_anomaly = int(
                any(
                    int(
                        item[
                            "is_anomaly"
                        ]
                    )
                    == 1
                    for item in future
                )
            )

            lead_events = None

            for offset, item in enumerate(
                future,
                start=1,
            ):

                if int(
                    item[
                        "is_anomaly"
                    ]
                ) == 1:

                    lead_events = offset
                    break

            ready = (
                len(history)
                >= minimum_history_events
            )

            if ready:

                latency_component = (
                    positive_deviation_score(
                        float(
                            current[
                                "latency_p95_60s"
                            ]
                        ),
                        [
                            float(
                                item[
                                    "latency_p95_60s"
                                ]
                            )
                            for item in history
                        ],
                    )
                )

                error_component = (
                    positive_deviation_score(
                        float(
                            current[
                                "error_rate_60s"
                            ]
                        ),
                        [
                            float(
                                item[
                                    "error_rate_60s"
                                ]
                            )
                            for item in history
                        ],
                    )
                )

                request_component = (
                    positive_deviation_score(
                        float(
                            current[
                                "request_rate_60s"
                            ]
                        ),
                        [
                            float(
                                item[
                                    "request_rate_60s"
                                ]
                            )
                            for item in history
                        ],
                    )
                )

                current_changes = float(
                    current.get(
                        "change_count_300s",
                        0,
                    )
                )

                historical_changes = mean(
                    [
                        float(
                            item.get(
                                "change_count_300s",
                                0,
                            )
                        )
                        for item in history
                    ]
                )

                change_component = (
                    1.0
                    if current_changes
                    > historical_changes
                    and current_changes > 0
                    else 0.0
                )

                warning_score = (
                    weights["latency"]
                    * latency_component

                    + weights["error_rate"]
                    * error_component

                    + weights["request_rate"]
                    * request_component

                    + weights["change_signal"]
                    * change_component
                )

            else:

                latency_component = 0.0
                error_component = 0.0
                request_component = 0.0
                change_component = 0.0
                warning_score = 0.0

            current_is_anomaly = int(
                current[
                    "is_anomaly"
                ]
            )

            warning_flag = int(
                ready
                and current_is_anomaly == 0
                and warning_score
                >= warning_threshold
            )

            rows.append(
                {
                    "service":
                        service,

                    "feature_as_of_time":
                        current[
                            "feature_as_of_time"
                        ],

                    "history_event_count":
                        len(history),

                    "warning_ready":
                        ready,

                    "latency_warning_component":
                        round(
                            latency_component,
                            6,
                        ),

                    "error_warning_component":
                        round(
                            error_component,
                            6,
                        ),

                    "request_warning_component":
                        round(
                            request_component,
                            6,
                        ),

                    "change_warning_component":
                        round(
                            change_component,
                            6,
                        ),

                    "early_warning_score":
                        round(
                            warning_score,
                            6,
                        ),

                    "warning_flag":
                        warning_flag,

                    "current_is_anomaly":
                        current_is_anomaly,

                    "future_anomaly":
                        future_anomaly,

                    "lead_events":
                        lead_events,
                }
            )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(rows)
        .sort(
            [
                "feature_as_of_time",
                "service",
            ]
        )
    )