import numpy as np
import polars as pl
import pytest

from sentinelops.evaluation.rcaeval_detection import (
    calibration_ewma,
    calibration_zscore,
    prepare_metrics,
)


def test_prepare_metrics_uses_frozen_split():
    metrics = pl.DataFrame(
        {
            "time": [1, 2, 3, 4, 5, 6, 7],
            "checkoutservice_cpu": [
                1.0,
                1.0,
                1.0,
                1.0,
                1.0,
                10.0,
                10.0,
            ],
        }
    )

    result = prepare_metrics(
        metrics,
        inject_time_s=6,
    )

    assert result.pre_injection_rows == 5
    assert result.calibration_rows == 2
    assert result.evaluation_normal_rows == 3
    assert result.fault_rows == 2


def test_prepare_metrics_cleans_before_split():
    metrics = pl.DataFrame(
        {
            "time": [1, 2, 3, 4, 5],
            "checkoutservice_cpu": [
                None,
                2.0,
                float("inf"),
                4.0,
                5.0,
            ],
        }
    )

    result = prepare_metrics(
        metrics,
        inject_time_s=5,
    )

    assert (
        result.frame[
            "checkoutservice_cpu"
        ].to_list()
        == [
            0.0,
            2.0,
            2.0,
            4.0,
            5.0,
        ]
    )


def test_exact_duplicate_rows_are_deduplicated():
    metrics = pl.DataFrame(
        {
            "time": [1, 1, 2, 3],
            "checkoutservice_cpu": [
                1.0,
                1.0,
                2.0,
                10.0,
            ],
        }
    )

    result = prepare_metrics(
        metrics,
        inject_time_s=3,
    )

    assert result.frame.height == 3


def test_conflicting_duplicate_timestamp_fails():
    metrics = pl.DataFrame(
        {
            "time": [1, 1, 2, 3],
            "checkoutservice_cpu": [
                1.0,
                2.0,
                2.0,
                10.0,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Conflicting rows",
    ):
        prepare_metrics(
            metrics,
            inject_time_s=3,
        )


def test_zscore_fits_calibration_only():
    values = np.array(
        [
            0.0,
            2.0,
            100.0,
        ]
    )

    scores, flags = calibration_zscore(
        values,
        calibration_rows=2,
        threshold=2.5,
    )

    assert np.allclose(
        scores[:2],
        [1.0, 1.0],
    )

    assert scores[2] == pytest.approx(
        99.0
    )

    assert flags.tolist() == [
        0,
        0,
        1,
    ]


def test_ewma_threshold_scale_uses_calibration_only():
    values = np.array(
        [
            0.0,
            2.0,
            100.0,
        ]
    )

    scores, flags = calibration_ewma(
        values,
        calibration_rows=2,
        alpha=0.5,
        threshold=2.5,
    )

    assert scores[2] == pytest.approx(
        99.0
    )

    assert flags.tolist() == [
        0,
        0,
        1,
    ]
