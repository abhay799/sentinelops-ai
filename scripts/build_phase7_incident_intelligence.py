from pathlib import Path

import polars as pl

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.incidents.intelligence import (
    enrich_incidents,
)

INCIDENTS = Path(
    "data/processed/incidents/"
    "incidents_v1.parquet"
)

MEMBERS = Path(
    "data/processed/incidents/"
    "incident_members_v1.parquet"
)

OUTPUT = Path(
    "data/processed/incidents/"
    "incident_intelligence_v1.parquet"
)


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


enriched = enrich_incidents(
    incidents,
    members,
    graph,
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

enriched.write_parquet(
    OUTPUT
)


print()
print("=" * 70)
print(
    " SENTINELOPS AI - PHASE 7 INCIDENT INTELLIGENCE"
)
print("=" * 70)

print(
    enriched.select(
        [
            "incident_id",
            "primary_service",
            "severity",
            "confidence",
            "service_count",
            "anomaly_count",
            "evidence_count",
            "affected_upstream_services",
        ]
    )
)

print()

print(
    "Incidents:",
    enriched.height,
)

print(
    "Output:",
    OUTPUT,
)

print()

print(
    "PHASE 7 INCIDENT INTELLIGENCE: PASSED"
)