import json
from pathlib import Path

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)

TOPOLOGY = Path(
    "configs/topology.yaml"
)

OUTPUT = Path(
    "data/processed/graph/"
    "service_graph_v1.json"
)


graph = (
    ServiceDependencyGraph
    .from_topology_file(
        TOPOLOGY
    )
)

graph.validate()


snapshot = graph.snapshot()


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

OUTPUT.write_text(
    json.dumps(
        snapshot,
        indent=2,
    ),
    encoding="utf-8",
)


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 6 SERVICE GRAPH"
)
print("=" * 64)

print(
    "Nodes:",
    snapshot["node_count"],
)

print(
    "Edges:",
    snapshot["edge_count"],
)

print()


for node in graph.services():

    print(
        f"{node}:"
    )

    print(
        "  dependencies =",
        graph.dependencies(
            node
        ),
    )

    print(
        "  dependents   =",
        graph.dependents(
            node
        ),
    )


print()
print(
    "Payment failure propagation:"
)

print(
    graph.risk_propagation(
        "payment-service",
        base_risk=1.0,
    )
)

print()

print(
    "PHASE 6 GRAPH BUILD: PASSED"
)