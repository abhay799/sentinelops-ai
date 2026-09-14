from pathlib import Path

import polars as pl
import yaml

REQUESTS = Path(
    "data/processed/execution/"
    "execution_requests_v1.parquet"
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


requests = pl.read_parquet(
    REQUESTS
)


rows = []


for request in requests.to_dicts():

    approval_eligible = bool(
        request[
            "preapproval_ready"
        ]
    )

    rows.append(
        {
            "execution_request_id":
                request[
                    "execution_request_id"
                ],

            "plan_id":
                request[
                    "plan_id"
                ],

            "incident_id":
                request[
                    "incident_id"
                ],

            "candidate_service":
                request[
                    "candidate_service"
                ],

            "recommended_action":
                request[
                    "recommended_action"
                ],

            "approval_eligible":
                approval_eligible,

            "approval_status":
                (
                    "pending"
                    if approval_eligible
                    else "not_eligible"
                ),

            "approved_by":
                None,

            "approval_reason":
                None,

            "execution_allowed":
                False,
        }
    )


approvals = pl.DataFrame(
    rows,
    strict=False,
)


output = Path(
    config[
        "output"
    ][
        "approvals"
    ][
        "path"
    ]
)


output.parent.mkdir(
    parents=True,
    exist_ok=True,
)


approvals.write_parquet(
    output
)


print()
print("=" * 74)
print(
    " SENTINELOPS AI - PHASE 14 HUMAN APPROVAL QUEUE"
)
print("=" * 74)

print(
    approvals.select(
        [
            "execution_request_id",
            "candidate_service",
            "recommended_action",
            "approval_eligible",
            "approval_status",
            "execution_allowed",
        ]
    )
)

print()

print(
    "PHASE 14 APPROVAL QUEUE: PASSED"
)
