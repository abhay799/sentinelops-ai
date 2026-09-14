from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import polars as pl
import yaml

from sentinelops.execution.runtime import (
    execute_local_sandbox,
)

REQUESTS = Path(
    "data/processed/execution/"
    "execution_requests_v1.parquet"
)

APPROVALS = Path(
    "data/processed/execution/"
    "execution_approvals_v1.parquet"
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "request_id"
)

args = parser.parse_args()


with open(
    "configs/execution.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "execution"
    ]


requests = pl.read_parquet(
    REQUESTS
)

approvals = pl.read_parquet(
    APPROVALS
)


request_rows = (
    requests
    .filter(
        pl.col(
            "execution_request_id"
        )
        == args.request_id
    )
    .to_dicts()
)

approval_rows = (
    approvals
    .filter(
        pl.col(
            "execution_request_id"
        )
        == args.request_id
    )
    .to_dicts()
)


if len(request_rows) != 1:
    raise RuntimeError(
        "Execution request not found"
    )

if len(approval_rows) != 1:
    raise RuntimeError(
        "Approval record not found"
    )


result = execute_local_sandbox(
    request_rows[0],
    approval_rows[0],
    config,
)


result[
    "execution_timestamp"
] = datetime.now(
    UTC
).isoformat()


results_path = Path(
    config[
        "output"
    ][
        "results"
    ][
        "path"
    ]
)

verification_path = Path(
    config[
        "output"
    ][
        "verification"
    ][
        "path"
    ]
)


results_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


new_result = pl.DataFrame(
    [result],
    strict=False,
)


if results_path.exists():

    previous = pl.read_parquet(
        results_path
    )

    previous = previous.filter(
        pl.col(
            "execution_request_id"
        )
        != args.request_id
    )

    results = pl.concat(
        [
            previous,
            new_result,
        ],
        how="diagonal_relaxed",
    )

else:

    results = new_result


results.write_parquet(
    results_path
)


verification = results.select(
    [
        "execution_request_id",
        "incident_id",
        "candidate_service",
        "recommended_action",
        "pre_live",
        "pre_ready",
        "post_live",
        "post_ready",
        "recovery_verified",
        "rollback_attempted",
        "rollback_succeeded",
        "execution_status",
        "execution_timestamp",
    ]
)


verification.write_parquet(
    verification_path
)


print()
print("=" * 78)
print(
    " SENTINELOPS AI - PHASE 14 CONTROLLED SANDBOX EXECUTION"
)
print("=" * 78)

print(
    new_result.select(
        [
            "execution_request_id",
            "candidate_service",
            "recommended_action",
            "final_gate_passed",
            "pre_live",
            "pre_ready",
            "execution_attempted",
            "post_live",
            "post_ready",
            "recovery_verified",
            "rollback_attempted",
            "execution_status",
        ]
    )
)

print()

if result[
    "execution_status"
] in {
    "executed_verified",
    "rolled_back_verified",
}:

    print(
        "PHASE 14 CONTROLLED EXECUTION: PASSED"
    )

else:

    raise SystemExit(
        "PHASE 14 CONTROLLED EXECUTION: FAILED"
    )
