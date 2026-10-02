from __future__ import annotations

import hashlib
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


def deterministic_random_ranking(
    services: Iterable[str],
    case_id: str,
    master_seed: int = 42,
) -> tuple[list[dict[str, int | str]], int]:
    ordered = sorted(set(services))
    if not ordered:
        raise ValueError("Random baseline candidate set is empty")

    digest = hashlib.sha256(
        f"{master_seed}:{case_id}".encode("utf-8")
    ).digest()
    derived_seed = int.from_bytes(
        digest[:8],
        byteorder="big",
        signed=False,
    )
    rng = np.random.default_rng(derived_seed)
    permutation = rng.permutation(len(ordered))
    ranking: list[dict[str, int | str]] = []

    for rank, index in enumerate(permutation, start=1):
        ranking.append(
            {
                "service": ordered[int(index)],
                "rank": rank,
            }
        )

    return ranking, derived_seed


def pagerank_ranking(
    services: Iterable[str],
    edges: Iterable[tuple[str, str]],
    service_strengths: dict[str, float],
    damping: float = 0.85,
) -> list[dict[str, float | int | str]]:
    import networkx as nx

    candidates = sorted(set(services))
    if not candidates:
        raise ValueError("PageRank candidate set is empty")

    candidate_set = set(candidates)
    graph = nx.DiGraph()
    graph.add_nodes_from(candidates)
    graph.add_edges_from(
        (source, target)
        for source, target in edges
        if source in candidate_set
        and target in candidate_set
    )

    weights = {
        service: max(
            0.0,
            float(service_strengths.get(service, 0.0)),
        )
        for service in candidates
    }
    total = sum(weights.values())
    if total == 0.0:
        personalization = {
            service: 1.0 / len(candidates)
            for service in candidates
        }
    else:
        personalization = {
            service: value / total
            for service, value in weights.items()
        }

    scores = nx.pagerank(
        graph,
        alpha=damping,
        personalization=personalization,
    )
    rows: list[dict[str, float | int | str]] = [
        {
            "service": service,
            "score": float(scores[service]),
        }
        for service in candidates
    ]
    rows.sort(
        key=lambda row: (
            -float(row["score"]),
            str(row["service"]),
        )
    )
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows
