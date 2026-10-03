from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_detection import (
    calibration_ewma,
    calibration_isolation_forest,
    calibration_zscore,
    ensemble_two_of_three,
    floating_constant_tolerance,
    prepare_metrics,
)
from sentinelops.evaluation.rcaeval_rca import RCA_WEIGHTS
from sentinelops.graph.service_graph import ServiceDependencyGraph
from sentinelops.rca.engine import normalize_graph_impact

Variant = Literal["v2a", "v2b"]


@dataclass(frozen=True)
class V2Strengths:
    clipped: dict[str, float]
    unclipped: dict[str, float]


def normalize_unclipped_from_calibration(
    scores: np.ndarray,
    calibration_rows: int,
) -> np.ndarray:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1:
        raise ValueError("V2 normalization expects a 1D array")
    if not 0 < calibration_rows <= len(values):
        raise ValueError("Invalid calibration row count")
    if not np.isfinite(values).all():
        raise ValueError("V2 normalization received non-finite scores")

    calibration = values[:calibration_rows]
    low = float(np.min(calibration))
    high = float(np.max(calibration))
    tolerance = floating_constant_tolerance(calibration)

    if high - low <= tolerance:
        normalized = np.where(
            values > float(calibration[0]) + tolerance,
            1.0,
            0.0,
        )
    else:
        normalized = (values - low) / (high - low)

    if not np.isfinite(normalized).all():
        raise ValueError("V2 normalization produced non-finite values")
    return normalized


def compute_v2_strengths(
    metrics: pl.DataFrame,
    inject_time_s: int,
) -> V2Strengths:
    prepared = prepare_metrics(metrics, inject_time_s)
    frame = prepared.frame
    fault = slice(
        prepared.pre_injection_rows,
        prepared.pre_injection_rows + prepared.fault_rows,
    )
    grouped: dict[str, list[str]] = {}
    for column in frame.columns:
        if column == "time":
            continue
        service, _metric = column.rsplit("_", 1)
        grouped.setdefault(service, []).append(column)

    clipped: dict[str, float] = {}
    unclipped: dict[str, float] = {}
    for service, columns in sorted(grouped.items()):
        matrix = frame.select(columns).to_numpy()
        z_scores: list[np.ndarray] = []
        z_flags: list[np.ndarray] = []
        ewma_scores: list[np.ndarray] = []
        ewma_flags: list[np.ndarray] = []
        for index in range(matrix.shape[1]):
            score, flag = calibration_zscore(
                matrix[:, index], prepared.calibration_rows
            )
            z_scores.append(score)
            z_flags.append(flag)
            score, flag = calibration_ewma(
                matrix[:, index], prepared.calibration_rows
            )
            ewma_scores.append(score)
            ewma_flags.append(flag)

        service_z_score = np.max(np.column_stack(z_scores), axis=1)
        service_z_flag = np.max(np.column_stack(z_flags), axis=1)
        service_ewma_score = np.max(np.column_stack(ewma_scores), axis=1)
        service_ewma_flag = np.max(np.column_stack(ewma_flags), axis=1)
        iforest_score, iforest_flag = calibration_isolation_forest(
            matrix, prepared.calibration_rows
        )

        clipped_score, _votes, _flags = ensemble_two_of_three(
            service_z_score,
            service_z_flag,
            service_ewma_score,
            service_ewma_flag,
            iforest_score,
            iforest_flag,
            prepared.calibration_rows,
        )
        z_unclipped = normalize_unclipped_from_calibration(
            service_z_score, prepared.calibration_rows
        )
        ewma_unclipped = normalize_unclipped_from_calibration(
            service_ewma_score, prepared.calibration_rows
        )
        iforest_unclipped = normalize_unclipped_from_calibration(
            iforest_score, prepared.calibration_rows
        )
        raw_score = (z_unclipped + ewma_unclipped + iforest_unclipped) / 3.0
        if not np.isfinite(raw_score).all():
            raise ValueError("V2 service score contains non-finite values")

        clipped[service] = float(np.max(clipped_score[fault]))
        unclipped[service] = float(np.max(raw_score[fault]))

    if not all(np.isfinite(value) for value in unclipped.values()):
        raise ValueError("V2 service strength contains non-finite values")
    return V2Strengths(clipped=clipped, unclipped=unclipped)


def _primary_service_v2a(
    strengths: dict[str, float],
) -> str:
    return max(
        sorted(strengths),
        key=lambda service: (float(strengths[service]), service),
    )


def _primary_service_v2b(
    clipped_strengths: dict[str, float],
    raw_strengths: dict[str, float],
) -> str | None:
    max_clipped = max(clipped_strengths.values())
    tied = sorted(
        service
        for service, value in clipped_strengths.items()
        if value == max_clipped
    )
    if len(tied) == 1:
        return tied[0]
    max_raw = max(raw_strengths[service] for service in tied)
    raw_winners = [
        service for service in tied if raw_strengths[service] == max_raw
    ]
    if len(raw_winners) != 1:
        return None
    return raw_winners[0]


def sentinelops_v2_ranking(
    strengths: V2Strengths,
    graph: ServiceDependencyGraph,
    variant: Variant,
) -> tuple[list[dict[str, float | int | str]], str | None]:
    raw = strengths.unclipped
    missing = set(raw) - set(graph.services())
    if missing:
        raise ValueError(
            "RCA graph is missing services: " + ", ".join(sorted(missing))
        )
    if variant == "v2a":
        primary_service: str | None = _primary_service_v2a(raw)
    elif variant == "v2b":
        primary_service = _primary_service_v2b(strengths.clipped, raw)
    else:
        raise ValueError(f"Unsupported v2 variant: {variant}")

    rows: list[dict[str, float | int | str]] = []
    for service in sorted(raw):
        anomaly_strength = float(raw[service])
        graph_impact = normalize_graph_impact(graph, service)
        primary_bonus = 1.0 if service == primary_service else 0.0
        score = round(
            RCA_WEIGHTS["anomaly_strength"] * anomaly_strength
            + RCA_WEIGHTS["graph_impact"] * graph_impact
            + RCA_WEIGHTS["primary_service_bonus"] * primary_bonus,
            6,
        )
        if not np.isfinite(score):
            raise ValueError("V2 RCA score is non-finite")
        rows.append(
            {
                "service": service,
                "rca_score": score,
                "anomaly_strength": anomaly_strength,
                "change_signal": 0.0,
                "graph_impact": graph_impact,
                "primary_service_bonus": primary_bonus,
            }
        )

    rows.sort(
        key=lambda row: (-float(row["rca_score"]), str(row["service"]))
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows, primary_service
