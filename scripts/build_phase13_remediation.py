from pathlib import Path

import polars as pl
import yaml

from sentinelops.remediation.planner import (
    build_remediation_plans,
)
from sentinelops.remediation.sentinelguard import (
    evaluate_sentinelguard,
)

COUNTERFACTUAL = Path(
    "data/processed/counterfactual/"
    "counterfactual_summary_v1.parquet"
)

PRIORITY = Path(
    "data/processed/impact/"
    "incident_priority_v1.parquet"
)

RCA = Path(
    "data/processed/rca/"
    "rca_disposition_v1.parquet"
)


with open(
    "configs/remediation.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "remediation"
    ]


counterfactual = pl.read_parquet(
    COUNTERFACTUAL
)

priority = pl.read_parquet(
    PRIORITY
)

rca = pl.read_parquet(
    RCA
)


plans = build_remediation_plans(
    counterfactual_summary=counterfactual,
    incident_priority=priority,
    rca_disposition=rca,
    config=config,
)


if plans.is_empty():
    raise RuntimeError(
        "No remediation plans produced"
    )


plans_path = Path(
    config[
        "output"
    ][
        "plans"
    ][
        "path"
    ]
)

guard_path = Path(
    config[
        "output"
    ][
        "guard"
    ][
        "path"
    ]
)


plans_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


plans.write_parquet(
    plans_path
)


decisions = evaluate_sentinelguard(
    plans,
    config,
)


if decisions.is_empty():
    raise RuntimeError(
        "No SentinelGuard decisions produced"
    )


decisions.write_parquet(
    guard_path
)


print()
print("=" * 78)
print(
    " SENTINELOPS AI - PHASE 13 REMEDIATION + SENTINELGUARD"
)
print("=" * 78)


print("\n[Remediation Plans]")

print(
    plans.select(
        [
            "plan_id",
            "incident_id",
            "candidate_service",
            "recommended_action",
            "plan_status",
            "causal_consistency_score",
            "remediation_priority_score",
            "execution_allowed",
        ]
    )
)


print("\n[SentinelGuard]")

print(
    decisions.select(
        [
            "plan_id",
            "recommended_action",
            "guard_decision",
            "checks_passed",
            "checks_total",
            "phase14_candidate",
            "human_approval_status",
            "execution_allowed",
        ]
    )
)


print()

print(
    "PHASE 13 SENTINELGUARD BUILD: PASSED"
)
