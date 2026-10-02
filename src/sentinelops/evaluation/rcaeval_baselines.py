from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_detection import (
    calibration_zscore,
    prepare_metrics,
)


def metric_columns_by_service(
    columns: Iterable[str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for column in columns:
        if column == "time":
            continue
        service, _metric = column.rsplit("_", 1)
        grouped.setdefault(service, []).append(column)
    return grouped


def static_threshold_ranking(
    metrics: pl.DataFrame,
    inject_time_s: int,
    threshold: float = 2.5,
) -> list[dict[str, float | int | str]]:
    prepared = prepare_metrics(
        metrics,
        inject_time_s=inject_time_s,
    )
    frame = prepared.frame
    grouped = metric_columns_by_service(frame.columns)
    post_calibration_start = prepared.calibration_rows
    rows: list[dict[str, float | int | str]] = []

    for service, columns in sorted(grouped.items()):
        service_score = 0.0
        for column in columns:
            values = frame[column].to_numpy()
            scores, _flags = calibration_zscore(
                values,
                prepared.calibration_rows,
                threshold=threshold,
            )
            metric_score = float(
                np.max(scores[post_calibration_start:])
            )
            service_score = max(
                service_score,
                metric_score,
            )

        rows.append(
            {
                "service": service,
                "score": service_score,
            }
        )
    rows.sort(
        key=lambda row: (
            -float(row["score"]),
            str(row["service"]),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows
