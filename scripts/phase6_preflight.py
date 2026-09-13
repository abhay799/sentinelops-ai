from pathlib import Path

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)

GRAPH_ARTIFACT = Path(
    "data/processed/graph/"
    "service_graph_v1.json"
)

RISK_ARTIFACT = Path(
    "data/processed/graph/"
    "service_risk_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed_check(message: str) -> None:
    global failed
    failed = True
    print(f"[FAIL] {message}")


print()
print("=" * 64)
print(" SENTINELOPS AI - PHASE 6 PREFLIGHT")
print("=" * 64)


print("\n[Service Graph]")

graph = (
    ServiceDependencyGraph
    .from_topology_file(
        Path("configs/topology.yaml")
    )
)

try:
    graph.validate()
    passed("Graph validation")
except Exception as exc:
    failed_check(
        f"Graph validation: {exc}"
    )


if len(graph.services()) == 7:
    passed("7 graph services")
else:
    failed_check("Graph service count")


if graph.graph.number_of_edges() == 6:
    passed("6 dependency edges")
else:
    failed_check("Dependency edge count")


path = graph.shortest_path(
    "api-gateway",
    "payment-service",
)

if path == [
    "api-gateway",
    "order-service",
    "payment-service",
]:
    passed("Gateway -> payment path")
else:
    failed_check("Gateway -> payment path")


print("\n[Graph Artifact]")

if GRAPH_ARTIFACT.exists():
    passed("Service graph snapshot")
else:
    failed_check("Service graph snapshot")


print("\n[Graph Risk]")

if not RISK_ARTIFACT.exists():

    failed_check(
        "Service risk artifact"
    )

else:

    risk = pl.read_parquet(
        RISK_ARTIFACT
    )

    required = {
        "service",
        "direct_anomaly_score",
        "propagated_risk_score",
        "graph_risk_score",
        "severity",
        "upstream_impact_count",
        "risk_sources",
    }

    missing = (
        required
        - set(risk.columns)
    )

    if not missing:
        passed(
            "Graph risk columns"
        )
    else:
        failed_check(
            f"Missing columns: "
            f"{sorted(missing)}"
        )

    if risk.height == 7:
        passed(
            "Risk coverage: 7 services"
        )
    else:
        failed_check(
            "Risk service coverage"
        )

    payment = (
        risk
        .filter(
            pl.col("service")
            == "payment-service"
        )
    )

    if payment.height == 1:
        passed(
            "Payment-service risk"
        )
    else:
        failed_check(
            "Payment-service risk"
        )

    propagated = (
        risk
        .filter(
            pl.col(
                "propagated_risk_score"
            )
            > 0
        )
    )

    if propagated.height > 0:
        passed(
            "Dependency risk propagation"
        )
    else:
        failed_check(
            "Dependency risk propagation"
        )


print()
print("=" * 64)

if failed:
    print(
        "PHASE 6 PREFLIGHT: FAILED"
    )
    print("=" * 64)
    raise SystemExit(1)


print(
    "PHASE 6 PREFLIGHT: PASSED"
)

print("=" * 64)
