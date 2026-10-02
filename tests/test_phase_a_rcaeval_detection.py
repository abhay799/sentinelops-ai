import numpy as np
import polars as pl
import pytest

from sentinelops.evaluation.rcaeval_detection import (
    calibration_ewma,
    calibration_isolation_forest,
    calibration_zscore,
    ensemble_two_of_three,
    floating_constant_tolerance,
    normalize_scores_from_calibration,
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


def test_isolation_forest_fits_calibration_only():
    calibration = np.array(
        [
            [0.00, 0.00],
            [0.05, 0.02],
            [-0.03, 0.04],
            [0.02, -0.02],
            [-0.04, -0.03],
            [0.01, 0.03],
            [-0.02, 0.01],
            [0.04, -0.01],
            [-0.01, -0.04],
            [0.03, 0.00],
            [0.00, 0.05],
            [-0.05, 0.00],
            [0.02, 0.02],
            [-0.02, -0.02],
            [0.01, -0.03],
            [-0.03, 0.01],
            [0.04, 0.03],
            [-0.04, 0.02],
            [0.03, -0.04],
            [-0.01, 0.02],
        ]
    )

    fault = np.array(
        [
            [100.0, 100.0],
        ]
    )

    matrix = np.vstack(
        [
            calibration,
            fault,
        ]
    )

    scores, flags = (
        calibration_isolation_forest(
            matrix,
            calibration_rows=20,
            n_estimators=200,
            contamination=0.10,
            random_state=42,
        )
    )

    assert len(scores) == 21
    assert len(flags) == 21
    assert flags[-1] == 1

    assert scores[-1] > np.median(
        scores[:20]
    )


def test_score_normalization_uses_calibration_only():
    scores = np.array(
        [
            10.0,
            20.0,
            15.0,
            1000.0,
        ]
    )

    normalized = (
        normalize_scores_from_calibration(
            scores,
            calibration_rows=3,
        )
    )

    assert normalized.tolist() == [
        0.0,
        1.0,
        0.5,
        1.0,
    ]


def test_constant_calibration_normalization():
    scores = np.array(
        [
            5.0,
            5.0,
            5.0,
            8.0,
        ]
    )

    normalized = (
        normalize_scores_from_calibration(
            scores,
            calibration_rows=3,
        )
    )

    assert normalized.tolist() == [
        0.0,
        0.0,
        0.0,
        1.0,
    ]


def test_ensemble_requires_two_votes():
    z_scores = np.array(
        [0.0, 1.0, 5.0]
    )
    ewma_scores = np.array(
        [0.0, 1.0, 4.0]
    )
    isolation_scores = np.array(
        [0.0, 1.0, 3.0]
    )

    z_flags = np.array(
        [0, 0, 1]
    )
    ewma_flags = np.array(
        [0, 0, 1]
    )
    isolation_flags = np.array(
        [0, 0, 0]
    )

    scores, votes, flags = (
        ensemble_two_of_three(
            z_scores=z_scores,
            z_flags=z_flags,
            ewma_scores=ewma_scores,
            ewma_flags=ewma_flags,
            isolation_scores=(
                isolation_scores
            ),
            isolation_flags=(
                isolation_flags
            ),
            calibration_rows=2,
        )
    )

    assert votes.tolist() == [
        0,
        0,
        2,
    ]

    assert flags.tolist() == [
        0,
        0,
        1,
    ]

    assert len(scores) == 3


def test_zscore_constant_calibration_flags_change():
    values = np.array([5.0, 5.0, 7.0])
    scores, flags = calibration_zscore(
        values,
        calibration_rows=2,
        threshold=2.5,
    )

    assert scores[:2].tolist() == [0.0, 0.0]
    assert scores[2] > 2.5
    assert flags.tolist() == [0, 0, 1]


def test_ewma_constant_calibration_flags_change():
    values = np.array([5.0, 5.0, 7.0])
    scores, flags = calibration_ewma(
        values,
        calibration_rows=2,
        alpha=0.30,
        threshold=2.5,
    )

    assert scores[:2].tolist() == [0.0, 0.0]
    assert scores[2] > 2.5
    assert flags.tolist() == [0, 0, 1]



def test_ewma_constant_calibration_ignores_float_roundoff():
    values = np.array([3.0, 3.0, 3.0, 3.0, 4.0])
    scores, flags = calibration_ewma(
        values,
        calibration_rows=4,
        alpha=0.30,
        threshold=2.5,
    )

    assert scores[:4].tolist() == [0.0, 0.0, 0.0, 0.0]
    assert flags[:4].tolist() == [0, 0, 0, 0]
    assert scores[4] > 2.5
    assert flags[4] == 1


def test_floating_constant_tolerance_is_machine_precision_based():
    values = np.array([1.0e8, 1.0e8])
    expected = (
        8.0
        * np.finfo(np.float64).eps
        * 1.0e8
    )
    assert floating_constant_tolerance(values) == pytest.approx(expected)


def test_isolation_forest_zero_variance_is_finite_and_stable():
    matrix = np.full((22, 2), 3.0)
    scores, flags = calibration_isolation_forest(
        matrix,
        calibration_rows=20,
    )
    assert np.isfinite(scores).all()
    assert flags[:20].tolist() == [0] * 20
    assert flags[20:].tolist() == [0, 0]
