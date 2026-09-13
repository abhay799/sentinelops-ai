from pathlib import Path

import polars as pl
import yaml

from sentinelops.graph.risk import (
    build_graph_risk,
)
from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)

ANOMALY_PATH = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

TOPOLOGY_PATH = Path(
    "configs/topology.yaml"
)


with open(
    "configs/graph.yaml",
    encoding="utf-8",
) as file:
    config = yaml.safe_load(file)[
        "graph_intelligence"
    ]


graph = (
    ServiceDependencyGraph
    .from_topology_file(
        TOPOLOGY_PATH
    )
)

graph.validate()


anomalies = pl.read_parquet(
    ANOMALY_PATH
)


risk, contributions = (
    build_graph_risk(
        graph=graph,
        anomaly_data=anomalies,
        decay=config[
            "propagation"
        ][
            "decay"
        ],
        minimum_source_score=config[
            "propagation"
        ][
            "minimum_source_score"
        ],
        severity_thresholds=config[
            "severity"
        ],
    )
)


output_path = Path(
    config[
        "output"
    ][
        "service_risk"
    ][
        "path"
    ]
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

risk.write_parquet(
    output_path
)


print()
print("=" * 70)
print(
    " SENTINELOPS AI - PHASE 6 GRAPH-AWARE RISK"
)
print("=" * 70)

print(
    risk.select(
        [
            "service",
            "direct_anomaly_score",
            "propagated_risk_score",
            "graph_risk_score",
            "severity",
            "upstream_impact_count",
            "risk_sources",
        ]
    )
)

print()

print(
    "Propagation contributions:",
    len(contributions),
)

print(
    "Output:",
    output_path,
)

print()

print(
    "PHASE 6 GRAPH RISK: PASSED"
)