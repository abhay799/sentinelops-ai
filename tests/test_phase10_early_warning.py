from datetime import UTC, datetime, timedelta

import polars as pl

from sentinelops.prediction.early_warning import (
    build_early_warning_dataset,
)

WEIGHTS = {
    "latency": 0.40,
    "error_rate": 0.30,
    "request_rate": 0.15,
    "change_signal": 0.15,
}


def dataset(
    final_latency: float = 900.0,
):
    start = datetime(
        2026,
        9,
        14,
        tzinfo=UTC,
    )

    latencies = [
        100.0,
        100.0,
        105.0,
        110.0,
        300.0,
        final_latency,
    ]

    anomalies = [
        0,
        0,
        0,
        0,
        0,
        1,
    ]

    return pl.DataFrame(
        {
            "service": [
                "payment-service"
                for _ in latencies
            ],

            "feature_as_of_time": [
                start
                + timedelta(
                    seconds=index * 10
                )
                for index
                in range(
                    len(latencies)
                )
            ],

            "latency_p95_60s":
                latencies,

            "error_rate_60s": [
                0.0,
                0.0,
                0.0,
                0.0,
                0.1,
                0.8,
            ],

            "request_rate_60s": [
                10.0,
                10.0,
                10.0,
                11.0,
                12.0,
                15.0,
            ],

            "change_count_300s": [
                0,
                0,
                0,
                0,
                1,
                1,
            ],

            "is_anomaly":
                anomalies,
        }
    )


def build(data):
    return (
        build_early_warning_dataset(
            anomaly_data=data,
            lookahead_events=3,
            minimum_history_events=3,
            history_window_events=20,
            warning_threshold=0.55,
            weights=WEIGHTS,
        )
    )


def test_future_anomaly_label_is_created():
    result = build(
        dataset()
    )

    pre_failure = (
        result
        .filter(
            pl.col("future_anomaly")
            == 1
        )
    )

    assert pre_failure.height > 0


def test_warning_never_claims_current_anomaly():
    result = build(
        dataset()
    )

    invalid = result.filter(
        (pl.col("warning_flag") == 1)
        &
        (
            pl.col("current_is_anomaly")
            == 1
        )
    )

    assert invalid.height == 0


def test_risk_score_does_not_use_future_values():

    first = build(
        dataset(
            final_latency=900.0
        )
    )

    second = build(
        dataset(
            final_latency=5000.0
        )
    )

    first_score = (
        first
        .filter(
            pl.col(
                "history_event_count"
            )
            == 3
        )
        [
            "early_warning_score"
        ][0]
    )

    second_score = (
        second
        .filter(
            pl.col(
                "history_event_count"
            )
            == 3
        )
        [
            "early_warning_score"
        ][0]
    )

    assert (
        first_score
        == second_score
    )


def test_warning_score_is_bounded():
    result = build(
        dataset()
    )

    assert (
        result[
            "early_warning_score"
        ].min()
        >= 0.0
    )

    assert (
        result[
            "early_warning_score"
        ].max()
        <= 1.0
    )
