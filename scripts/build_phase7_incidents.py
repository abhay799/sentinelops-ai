from pathlib import Path

import polars as pl
import yaml

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)
from sentinelops.incidents.correlator import (
    correlate_incidents,
)

ANOMALY_PATH = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

TOPOLOGY_PATH = Path(
    "configs/topology.yaml"
)


with open(
    "configs/incident_correlation.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(file)[
        "incident_correlation"
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


incidents, members = (
    correlate_incidents(
        anomaly_data=anomalies,
        graph=graph,

        correlation_window_seconds=
            config[
                "correlation_window_seconds"
            ],

        maximum_graph_hops=
            config[
                "maximum_graph_hops"
            ],

        severity_thresholds=
            config[
                "severity"
            ],
    )
)


if incidents.is_empty():
    raise RuntimeError(
        "No incidents were produced "
        "from detected anomalies"
    )


incident_path = Path(
    config[
        "output"
    ][
        "incidents"
    ][
        "path"
    ]
)

member_path = Path(
    config[
        "output"
    ][
        "members"
    ][
        "path"
    ]
)


incident_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


incidents.write_parquet(
    incident_path
)

members.write_parquet(
    member_path
)


print()
print("=" * 70)
print(
    " SENTINELOPS AI - PHASE 7 INCIDENT CORRELATION"
)
print("=" * 70)

print(
    incidents.select(
        [
            "incident_id",
            "primary_service",
            "services",
            "service_count",
            "anomaly_count",
            "max_anomaly_score",
            "severity",
            "upstream_impact_count",
        ]
    )
)

print()

print(
    "Incidents:",
    incidents.height,
)

print(
    "Correlated anomaly events:",
    members.height,
)

print(
    "Incident output:",
    incident_path,
)

print(
    "Membership output:",
    member_path,
)

print()

print(
    "PHASE 7 INCIDENT CORRELATION: PASSED"
)
