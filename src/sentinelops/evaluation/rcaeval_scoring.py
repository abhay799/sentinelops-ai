"""Frozen E3/E4/E6 service-level accuracy and paired uncertainty."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np

from sentinelops.evaluation.rcaeval_rca import RCA_WEIGHTS, graph_from_edges
from sentinelops.rca.engine import normalize_graph_impact

METRICS = ("AC@1", "AC@2", "AC@3", "AC@4", "AC@5", "Avg@5", "Chance@5", "Lift@5")


def case_hits(
    native_ranking: list[str],
    answer: str,
    allowlist: set[str],
    status: str = "ok",
) -> np.ndarray:
    if status not in {"ok", "fallback_unranked"}:
        raise ValueError(f"Invalid ranking status: {status}")
    if answer not in allowlist:
        raise ValueError("Ground truth outside frozen allowlist")
    if status == "fallback_unranked":
        return np.zeros(5, dtype=float)
    if len(native_ranking) != len(set(native_ranking)):
        raise ValueError("Ranking contains duplicate services")
    filtered = [s for s in native_ranking if s in allowlist]
    return np.array([float(answer in filtered[:k]) for k in range(1, 6)])


def metric_values(hits: np.ndarray, chance: float | np.ndarray) -> dict:
    hits = np.asarray(hits, dtype=float)
    if hits.ndim != 2 or hits.shape[1] != 5:
        raise ValueError("Expected case-by-five hit matrix")
    if not len(hits):
        return dict.fromkeys(METRICS)
    if not np.all(np.isfinite(hits)):
        raise ValueError("Non-finite case accuracy")
    chance = np.asarray(chance, dtype=float)
    if chance.ndim and chance.shape != (len(hits),):
        raise ValueError("Chance values must align with cases")
    floor = float(np.mean(chance))
    if not np.isfinite(floor) or floor <= 0:
        raise ValueError("Chance must be finite and positive")
    ac = hits.mean(axis=0)
    return {
        **{f"AC@{k}": float(ac[k - 1]) for k in range(1, 6)},
        "Avg@5": float(ac.mean()),
        "Chance@5": floor,
        "Lift@5": float(ac[4] / floor),
    }


def bootstrap_indices(case_count: int, seed: int = 42, resamples: int = 10000) -> np.ndarray:
    if case_count < 1 or resamples < 1:
        raise ValueError("Bootstrap requires cases and resamples")
    return np.random.default_rng(seed).integers(0, case_count, size=(resamples, case_count))


def percentile_intervals(
    hits: np.ndarray,
    indices: np.ndarray,
    chance: float | np.ndarray,
) -> dict:
    hits = np.asarray(hits, dtype=float)
    if not len(hits):
        return dict.fromkeys(METRICS)
    # Validate metric input and chance alignment before indexing.
    metric_values(hits, chance)
    draws = hits[indices].mean(axis=1)
    c = np.asarray(chance)
    floor = np.full(len(indices), float(c)) if c.ndim == 0 else c[indices].mean(axis=1)
    values = np.column_stack([draws, draws.mean(axis=1), floor, draws[:, 4] / floor])
    ci = np.quantile(values, [0.025, 0.975], axis=0, method="linear")
    return {name: ci[:, i].tolist() for i, name in enumerate(METRICS)}


def paired_intervals(left: np.ndarray, right: np.ndarray, indices: np.ndarray) -> dict:
    if left.shape != right.shape or left.ndim != 2 or left.shape[1] != 5:
        raise ValueError("Paired methods must have matching case-by-five matrices")
    if not len(left):
        return {f"AC@{k}": {"difference": None, "ci95": None} for k in (1, 3, 5)}
    difference = np.asarray(left, dtype=float) - np.asarray(right, dtype=float)
    draws = difference[indices].mean(axis=1)
    ci = np.quantile(draws, [0.025, 0.975], axis=0, method="linear")
    point = difference.mean(axis=0)
    return {
        f"AC@{k}": {"difference": float(point[k - 1]), "ci95": ci[:, k - 1].tolist()}
        for k in (1, 3, 5)
    }


def summarize_group(
    hits: dict[str, np.ndarray],
    valid: dict[str, np.ndarray],
    chance: float,
) -> dict:
    primary, secondary = {}, {}
    for method, values in hits.items():
        mask = np.asarray(valid[method], dtype=bool)
        if mask.shape != (len(values),):
            raise ValueError("Validity mask must align with cases")
        valid_count = int(mask.sum())
        primary[method] = {
            "denominator": len(values),
            "valid_ranking_count": valid_count,
            "fallback_unranked_count": len(values) - valid_count,
            "failed_count": 0,
            "valid_ranking_coverage": valid_count / len(values) if len(values) else None,
            "metrics": metric_values(values, chance),
        }
        secondary[method] = {
            "denominator": valid_count,
            "cohort": "valid-rankings-only",
            "metrics": metric_values(values[mask], chance),
        }
    return {"primary": primary, "valid_rankings_only": secondary}


def a4_sentinelops_ranking(
    saved_native_rows: list[dict],
    allowlist: set[str],
    edges: Iterable[tuple[str, str]],
) -> list[dict]:
    """Change graph impact only, preserving strengths and original primary bonus."""
    graph = graph_from_edges(allowlist, edges)
    if set(graph.services()) != allowlist:
        raise ValueError("A4 edges must stay inside the frozen allowlist")
    rows = []
    for original in saved_native_rows:
        row = dict(original)
        service = row["service"]
        impact = normalize_graph_impact(graph, service) if service in allowlist else 0.0
        row["graph_impact"] = impact
        row["rca_score"] = round(
            RCA_WEIGHTS["anomaly_strength"] * row["anomaly_strength"]
            + RCA_WEIGHTS["change_signal"] * row["change_signal"]
            + RCA_WEIGHTS["graph_impact"] * impact
            + RCA_WEIGHTS["primary_service_bonus"] * row["primary_service_bonus"],
            6,
        )
        rows.append(row)
    rows.sort(key=lambda row: (-row["rca_score"], row["service"]))
    for rank, row in enumerate(rows, 1):
        row["rank"] = rank
    return rows
