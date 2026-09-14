from pathlib import Path

import polars as pl
import yaml

from sentinelops.impact.prioritization import (
    build_incident_priority,
)

MEMBERS = Path(
    "data/processed/incidents/"
    "incident_members_v1.parquet"
)

SERVICE_IMPACT = Path(
    "data/processed/impact/"
    "service_impact_v1.parquet"
)

OUTPUT = Path(
    "data/processed/impact/"
    "incident_priority_v1.parquet"
)


with open(
    "configs/incident_priority.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )["incident_priority"]


members = pl.read_parquet(
    MEMBERS
)

impact = pl.read_parquet(
    SERVICE_IMPACT
)


priority = build_incident_priority(
    incident_members=members,
    service_impact=impact,
    config=config,
)


if priority.is_empty():
    raise RuntimeError(
        "No incident priorities produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

priority.write_parquet(
    OUTPUT
)


print()
print("=" * 76)
print(
    " SENTINELOPS AI - PHASE 12 INCIDENT PRIORITY"
)
print("=" * 76)

print(
    priority.select(
        [
            "priority_rank",
            "incident_id",
            "highest_impact_service",
            "affected_service_count",
            "max_latency_burn",
            "max_error_burn",
            "max_predicted_failure",
            "remediation_priority_score",
            "priority",
        ]
    )
)

print()

print(
    "PHASE 12 INCIDENT PRIORITY BUILD: PASSED"
)
