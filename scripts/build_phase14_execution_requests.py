from pathlib import Path

import polars as pl
import yaml

from sentinelops.execution.gate import (
    build_execution_requests,
    validate_execution_requests,
)

PLANS = Path(
    "data/processed/remediation/"
    "remediation_plans_v1.parquet"
)

GUARD = Path(
    "data/processed/remediation/"
    "sentinelguard_decisions_v1.parquet"
)


with open(
    "configs/execution.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "execution"
    ]


plans = pl.read_parquet(
    PLANS
)

guard = pl.read_parquet(
    GUARD
)


requests = build_execution_requests(
    plans=plans,
    decisions=guard,
    config=config,
)


if requests.is_empty():

    raise RuntimeError(
        "No Phase 14 execution requests produced"
    )


errors = validate_execution_requests(
    requests
)

if errors:

    raise RuntimeError(
        "Execution request validation failed:\n"
        + "\n".join(errors)
    )


output = Path(
    config[
        "output"
    ][
        "requests"
    ][
        "path"
    ]
)


output.parent.mkdir(
    parents=True,
    exist_ok=True,
)


requests.write_parquet(
    output
)


print()
print("=" * 78)
print(
    " SENTINELOPS AI - PHASE 14 CONTROLLED EXECUTION GATE"
)
print("=" * 78)

print(
    requests.select(
        [
            "execution_request_id",
            "plan_id",
            "candidate_service",
            "recommended_action",
            "guard_passed",
            "rollback_available",
            "local_target",
            "preapproval_ready",
            "request_status",
            "human_approval_status",
            "execution_allowed",
        ]
    )
)

print()

print(
    "PHASE 14 EXECUTION GATE: PASSED"
)
