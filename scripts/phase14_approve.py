from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

APPROVALS = Path(
    "data/processed/execution/"
    "execution_approvals_v1.parquet"
)


parser = argparse.ArgumentParser()

parser.add_argument(
    "request_id"
)

decision = parser.add_mutually_exclusive_group(
    required=True
)

decision.add_argument(
    "--approve",
    action="store_true",
)

decision.add_argument(
    "--reject",
    action="store_true",
)

parser.add_argument(
    "--approved-by",
    required=True,
)

parser.add_argument(
    "--reason",
    default="Human-reviewed Phase 14 sandbox decision",
)

args = parser.parse_args()


data = pl.read_parquet(
    APPROVALS
)

rows = data.to_dicts()

matched = False


for row in rows:

    if (
        row["execution_request_id"]
        != args.request_id
    ):
        continue

    matched = True

    if not row[
        "approval_eligible"
    ]:

        raise RuntimeError(
            "Request is not eligible for approval"
        )

    row[
        "approval_status"
    ] = (
        "approved"
        if args.approve
        else "rejected"
    )

    row[
        "approved_by"
    ] = args.approved_by

    row[
        "approval_reason"
    ] = args.reason

    row[
        "approval_timestamp"
    ] = datetime.now(
        UTC
    ).isoformat()

    # Approval itself does not execute anything.
    row[
        "execution_allowed"
    ] = False


if not matched:
    raise RuntimeError(
        f"Unknown execution request: "
        f"{args.request_id}"
    )


updated = pl.DataFrame(
    rows,
    strict=False,
)

updated.write_parquet(
    APPROVALS
)


print()
print("=" * 68)
print(
    " SENTINELOPS AI - PHASE 14 HUMAN APPROVAL"
)
print("=" * 68)

print(
    updated
    .filter(
        pl.col(
            "execution_request_id"
        )
        == args.request_id
    )
    .select(
        [
            "execution_request_id",
            "candidate_service",
            "recommended_action",
            "approval_status",
            "approved_by",
            "execution_allowed",
        ]
    )
)

print()
print(
    "PHASE 14 HUMAN APPROVAL RECORDED"
)
