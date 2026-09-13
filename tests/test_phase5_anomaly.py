import numpy as np

from sentinelops.anomaly.detectors import (
    IsolationForestDetector,
    ewma_detector,
    zscore_detector,
)


def test_zscore_detects_extreme_value():
    matrix = np.array(
        [
            [1.0],
            [1.1],
            [0.9],
            [1.0],
            [1.1],
            [10.0],
        ]
    )

    scores, flags = zscore_detector(
        matrix,
        threshold=2.0,
    )

    assert scores.shape[0] == 6

    assert flags[-1] == 1


def test_ewma_returns_valid_shapes():
    values = np.array(
        [
            100,
            101,
            102,
            100,
            500,
        ],
        dtype=float,
    )

    scores, flags = ewma_detector(
        values,
        alpha=0.3,
        threshold_multiplier=1.5,
    )

    assert len(scores) == len(values)

    assert len(flags) == len(values)


def test_isolation_forest_detects_outlier():
    normal = np.array(
        [
            [1.0, 1.0],
            [1.1, 1.0],
            [0.9, 1.1],
            [1.0, 0.9],
            [1.1, 1.1],
            [0.9, 0.9],
        ]
    )

    anomaly = np.array(
        [
            [10.0, 10.0],
        ]
    )

    matrix = np.vstack(
        [
            normal,
            anomaly,
        ]
    )

    detector = IsolationForestDetector(
        n_estimators=100,
        contamination=0.15,
        random_state=42,
    )

    detector.fit(matrix)

    predictions = detector.predict(
        matrix
    )

    assert predictions[-1] == 1