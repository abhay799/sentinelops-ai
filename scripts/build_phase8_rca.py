from pathlib import Path

import polars as pl
import yaml

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.rca.engine import (
    build_rca_hypotheses,
)

INCIDENTS = Path(
    "data/processed/incidents/"
    "incident_intelligence_v1.parquet"
)

MEMBERS = Path(
    "data/processed/incidents/"
    "incident_members_v1.parquet"
)

ANOMALIES = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)


with open(
    "configs/rca.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )["rca"]


graph = (
    ServiceDependencyGraph
    .from_topology_file(
        Path(
            "configs/topology.yaml"
        )
    )
)

graph.validate()


incidents = pl.read_parquet(
    INCIDENTS
)

members = pl.read_parquet(
    MEMBERS
)

anomalies = pl.read_parquet(
    ANOMALIES
)


hypotheses = build_rca_hypotheses(
    incidents=incidents,
    members=members,
    anomaly_data=anomalies,
    graph=graph,
    weights=config[
        "weights"
    ],
    confidence_config=config[
        "confidence"
    ],
    max_candidates=int(
        config[
            "max_candidates"
        ]
    ),
)


if hypotheses.is_empty():

    raise RuntimeError(
        "No RCA hypotheses produced"
    )


output = Path(
    config[
        "output"
    ][
        "hypotheses"
    ][
        "path"
    ]
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

hypotheses.write_parquet(
    output
)


print()
print("=" * 70)
print(
    " SENTINELOPS AI - PHASE 8 EVIDENCE-BASED RCA"
)
print("=" * 70)

print(
    hypotheses.select(
        [
            "incident_id",
            "rank",
            "candidate_service",
            "rca_score",
            "confidence",
            "change_count",
            "graph_impact",
            "evidence_count",
            "confirmed_root_cause",
        ]
    )
)

print()

print(
    "Hypotheses:",
    hypotheses.height,
)

print(
    "Output:",
    output,
)

print()

print(
    "PHASE 8 RCA HYPOTHESIS BUILD: PASSED"
)
