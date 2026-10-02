from __future__ import annotations

from collections.abc import Iterable

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.rca.engine import normalize_graph_impact

RCA_WEIGHTS = {
    "anomaly_strength": 0.45,
    "change_signal": 0.25,
    "graph_impact": 0.20,
    "primary_service_bonus": 0.10,
}


def graph_from_edges(
    services: Iterable[str],
    edges: Iterable[tuple[str, str]],
) -> ServiceDependencyGraph:
    graph = ServiceDependencyGraph()
    graph.graph.add_nodes_from(sorted(set(services)))
    graph.graph.add_edges_from(sorted(set(edges)))
    return graph


def sentinelops_continuous_ranking(
    service_strengths: dict[str, float],
    graph: ServiceDependencyGraph,
    max_candidates: int = 5,
) -> list[dict[str, float | int | str]]:
    if not service_strengths:
        raise ValueError("No candidate service strengths")
    missing = set(service_strengths) - set(graph.services())
    if missing:
        raise ValueError(
            "RCA graph is missing services: "
            + ", ".join(sorted(missing))
        )

    primary_service = max(
        sorted(service_strengths),
        key=lambda service: (
            float(service_strengths[service]),
            service,
        ),
    )
    rows: list[dict[str, float | int | str]] = []

    for service in sorted(service_strengths):
        anomaly_strength = float(service_strengths[service])
        graph_impact = normalize_graph_impact(graph, service)
        primary_bonus = 1.0 if service == primary_service else 0.0
        score = round(
            RCA_WEIGHTS["anomaly_strength"] * anomaly_strength
            + RCA_WEIGHTS["graph_impact"] * graph_impact
            + RCA_WEIGHTS["primary_service_bonus"] * primary_bonus,
            6,
        )
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
        key=lambda row: (
            -float(row["rca_score"]),
            str(row["service"]),
        )
    )
    rows = rows[:max_candidates]
    for rank, row in enumerate(rows, start=1):
        row["rank"] = rank
    return rows
