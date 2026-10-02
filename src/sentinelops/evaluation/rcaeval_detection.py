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
        scores = np.zeros_like(
            values,
            dtype=float,
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

    if calibration_std == 0.0:
        scores = np.zeros_like(
            residuals,
            dtype=float,
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
