from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest


def safe_zscore(
    values: np.ndarray,
) -> np.ndarray:

    values = np.asarray(
        values,
        dtype=float,
    )

    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return np.zeros_like(values)

    return (
        values - mean
    ) / std


def zscore_detector(
    matrix: np.ndarray,
    threshold: float = 2.5,
) -> tuple[np.ndarray, np.ndarray]:

    matrix = np.asarray(
        matrix,
        dtype=float,
    )

    scores = np.zeros(
        matrix.shape[0],
        dtype=float,
    )

    for column in range(
        matrix.shape[1]
    ):
        zscores = np.abs(
            safe_zscore(
                matrix[:, column]
            )
        )

        scores = np.maximum(
            scores,
            zscores,
        )

    predictions = (
        scores >= threshold
    ).astype(int)

    return scores, predictions


def ewma_detector(
    values: np.ndarray,
    alpha: float = 0.30,
    threshold_multiplier: float = 2.5,
) -> tuple[np.ndarray, np.ndarray]:

    values = np.asarray(
        values,
        dtype=float,
    )

    if len(values) == 0:
        return (
            np.array([]),
            np.array([]),
        )

    ewma = np.zeros_like(
        values,
        dtype=float,
    )

    ewma[0] = values[0]

    for index in range(
        1,
        len(values),
    ):
        ewma[index] = (
            alpha * values[index]
            + (1 - alpha)
            * ewma[index - 1]
        )

    residuals = np.abs(
        values - ewma
    )

    baseline_std = np.std(
        residuals
    )

    if baseline_std == 0:
        scores = np.zeros_like(
            residuals
        )
    else:
        scores = (
            residuals
            / baseline_std
        )

    predictions = (
        scores
        >= threshold_multiplier
    ).astype(int)

    return scores, predictions


class IsolationForestDetector:

    def __init__(
        self,
        n_estimators: int = 200,
        contamination: float = 0.10,
        random_state: int = 42,
    ) -> None:

        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
        )

    def fit(
        self,
        matrix: np.ndarray,
    ) -> None:

        self.model.fit(matrix)

    def score(
        self,
        matrix: np.ndarray,
    ) -> np.ndarray:

        # sklearn gives higher values
        # for normal points.
        # Reverse it so larger means
        # more anomalous.
        return -self.model.score_samples(
            matrix
        )

    def predict(
        self,
        matrix: np.ndarray,
    ) -> np.ndarray:

        predictions = self.model.predict(
            matrix
        )

        return (
            predictions == -1
        ).astype(int)