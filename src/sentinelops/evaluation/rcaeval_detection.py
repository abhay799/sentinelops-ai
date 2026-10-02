from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_adapter import (
    metric_services_from_columns,
)


@dataclass(frozen=True)
class PreparedMetrics:
    frame: pl.DataFrame
    calibration_rows: int
    pre_injection_rows: int
    fault_rows: int
    inject_time_s: int

    @property
    def evaluation_normal_rows(self) -> int:
        return (
            self.pre_injection_rows
            - self.calibration_rows
        )


def prepare_metrics(
    metrics: pl.DataFrame,
    inject_time_s: int,
) -> PreparedMetrics:
    if "time" not in metrics.columns:
        raise ValueError(
            "RCAEval metrics are missing time column"
        )

    metric_columns = [
        column
        for column in metrics.columns
        if column != "time"
    ]

    # Validate RCAEval metric naming before processing.
    metric_services_from_columns(
        metrics.columns
    )

    if not metric_columns:
        raise ValueError(
            "No RCAEval metric columns found"
        )

    # Exact duplicate rows may be removed.
    frame = metrics.unique(
        maintain_order=True
    )

    # Same timestamp with different values is ambiguous.
    if (
        frame["time"].n_unique()
        != frame.height
    ):
        raise ValueError(
            "Conflicting rows share the same "
            "RCAEval metric timestamp"
        )

    frame = frame.sort("time")

    expressions: list[pl.Expr] = []

    for column in metric_columns:
        value = pl.col(column).cast(
            pl.Float64,
            strict=False,
        )

        cleaned = (
            pl.when(
                value.is_nan()
                | value.is_infinite()
            )
            .then(None)
            .otherwise(value)
            .forward_fill()
            .fill_null(0.0)
            .alias(column)
        )

        expressions.append(cleaned)

    # Missing-value handling happens before any split:
    # inf -> missing -> chronological ffill -> leading 0.
    frame = frame.with_columns(
        expressions
    )

    pre_rows = frame.filter(
        pl.col("time") < inject_time_s
    ).height

    fault_rows = frame.filter(
        pl.col("time") >= inject_time_s
    ).height

    if pre_rows < 2:
        raise ValueError(
            "Insufficient pre-injection rows "
            "for calibration/evaluation split"
        )

    if fault_rows == 0:
        raise ValueError(
            "No fault-window rows at or after "
            "the injection timestamp"
        )

    calibration_rows = pre_rows // 2

    if calibration_rows == 0:
        raise ValueError(
            "Calibration window is empty"
        )

    if pre_rows - calibration_rows == 0:
        raise ValueError(
            "Pre-injection evaluation window is empty"
        )

    return PreparedMetrics(
        frame=frame,
        calibration_rows=calibration_rows,
        pre_injection_rows=pre_rows,
        fault_rows=fault_rows,
        inject_time_s=inject_time_s,
    )


def calibration_zscore(
    values: np.ndarray,
    calibration_rows: int,
    threshold: float = 2.5,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(
        values,
        dtype=float,
    )

    if not (
        0 < calibration_rows <= len(values)
    ):
        raise ValueError(
            "Invalid calibration row count"
        )

    calibration = values[
        :calibration_rows
    ]

    mean = float(
        np.mean(calibration)
    )

    std = float(
        np.std(
            calibration,
            ddof=0,
        )
    )

    if std == 0.0:
        scores = np.where(
            values == mean,
            0.0,
            np.nextafter(
                threshold,
                np.inf,
            ),
        )
    else:
        scores = np.abs(
            (values - mean) / std
        )

    flags = (
        scores >= threshold
    ).astype(int)

    return scores, flags


def calibration_ewma(
    values: np.ndarray,
    calibration_rows: int,
    alpha: float = 0.30,
    threshold: float = 2.5,
) -> tuple[np.ndarray, np.ndarray]:
    values = np.asarray(
        values,
        dtype=float,
    )

    if len(values) == 0:
        raise ValueError(
            "EWMA input is empty"
        )

    if not (
        0 < calibration_rows <= len(values)
    ):
        raise ValueError(
            "Invalid calibration row count"
        )

    if not 0.0 < alpha <= 1.0:
        raise ValueError(
            "EWMA alpha must be in (0, 1]"
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
            + (1.0 - alpha)
            * ewma[index - 1]
        )

    residuals = np.abs(
        values - ewma
    )

    calibration_std = float(
        np.std(
            residuals[:calibration_rows],
            ddof=0,
        )
    )
    calibration_values = values[:calibration_rows]
    calibration_is_constant = bool(
        np.all(
            calibration_values
            == calibration_values[0]
        )
    )

    if calibration_is_constant:
        scores = np.where(
            values == calibration_values[0],
            0.0,
            np.nextafter(
                threshold,
                np.inf,
            ),
        )
    elif calibration_std == 0.0:
        scores = np.where(
            residuals == 0.0,
            0.0,
            np.nextafter(
                threshold,
                np.inf,
            ),
        )
    else:
        scores = (
            residuals
            / calibration_std
        )

    flags = (
        scores >= threshold
    ).astype(int)

    return scores, flags


def calibration_isolation_forest(
    matrix: np.ndarray,
    calibration_rows: int,
    n_estimators: int = 200,
    contamination: float = 0.10,
    random_state: int = 42,
) -> tuple[np.ndarray, np.ndarray]:
    from sklearn.ensemble import IsolationForest

    matrix = np.asarray(
        matrix,
        dtype=float,
    )

    if matrix.ndim != 2:
        raise ValueError(
            "Isolation Forest input must be "
            "a 2D matrix"
        )

    if not (
        0 < calibration_rows <= matrix.shape[0]
    ):
        raise ValueError(
            "Invalid calibration row count"
        )

    if not np.isfinite(matrix).all():
        raise ValueError(
            "Isolation Forest input contains "
            "non-finite values"
        )

    model = IsolationForest(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )

    model.fit(
        matrix[:calibration_rows]
    )

    # sklearn score_samples gives larger values
    # to more normal samples. Reverse it so that
    # larger values mean more anomalous.
    scores = -model.score_samples(
        matrix
    )

    flags = (
        model.predict(matrix) == -1
    ).astype(int)

    return scores, flags


def normalize_scores_from_calibration(
    scores: np.ndarray,
    calibration_rows: int,
) -> np.ndarray:
    scores = np.asarray(
        scores,
        dtype=float,
    )

    if scores.ndim != 1:
        raise ValueError(
            "Score normalization expects "
            "a 1D array"
        )

    if not (
        0 < calibration_rows <= len(scores)
    ):
        raise ValueError(
            "Invalid calibration row count"
        )

    calibration = scores[
        :calibration_rows
    ]

    low = float(
        np.min(calibration)
    )

    high = float(
        np.max(calibration)
    )

    if high == low:
        return np.where(
            scores > high,
            1.0,
            0.0,
        )

    normalized = (
        (scores - low)
        / (high - low)
    )

    return np.clip(
        normalized,
        0.0,
        1.0,
    )


def ensemble_two_of_three(
    z_scores: np.ndarray,
    z_flags: np.ndarray,
    ewma_scores: np.ndarray,
    ewma_flags: np.ndarray,
    isolation_scores: np.ndarray,
    isolation_flags: np.ndarray,
    calibration_rows: int,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    arrays = [
        np.asarray(z_scores),
        np.asarray(z_flags),
        np.asarray(ewma_scores),
        np.asarray(ewma_flags),
        np.asarray(isolation_scores),
        np.asarray(isolation_flags),
    ]

    lengths = {
        len(array)
        for array in arrays
    }

    if len(lengths) != 1:
        raise ValueError(
            "Detector outputs have "
            "different lengths"
        )

    z_normalized = (
        normalize_scores_from_calibration(
            z_scores,
            calibration_rows,
        )
    )

    ewma_normalized = (
        normalize_scores_from_calibration(
            ewma_scores,
            calibration_rows,
        )
    )

    isolation_normalized = (
        normalize_scores_from_calibration(
            isolation_scores,
            calibration_rows,
        )
    )

    votes = (
        np.asarray(
            z_flags,
            dtype=int,
        )
        + np.asarray(
            ewma_flags,
            dtype=int,
        )
        + np.asarray(
            isolation_flags,
            dtype=int,
        )
    )

    flags = (
        votes >= 2
    ).astype(int)

    mean_normalized_score = (
        z_normalized
        + ewma_normalized
        + isolation_normalized
    ) / 3.0

    return (
        mean_normalized_score,
        votes,
        flags,
    )
