from __future__ import annotations

from pathlib import Path
from typing import Any

import polars as pl
import yaml

SENTINELGUARD_CONFIG_PATH = (
    Path(__file__).resolve().parents[3]
    / "configs"
    / "sentinelguard.yaml"
)


def load_sentinelguard_config() -> dict[str, Any]:
    payload = yaml.safe_load(
        SENTINELGUARD_CONFIG_PATH.read_text(
            encoding="utf-8",
        )
    )
    return payload["sentinelguard"]


def evaluate_sentinelguard(
    plans: pl.DataFrame,
) -> pl.DataFrame:

    if plans.is_empty():
        return pl.DataFrame()

    guard = load_sentinelguard_config()
    allowed_actions = set(
        guard[
            "allowed_actions"
        ]
    )

    rows: list[
        dict[str, Any]
    ] = []

    for plan in plans.to_dicts():

        checks = {
            "planner_ready":
                bool(
                    plan[
                        "planner_ready"
                    ]
                ),

            "action_allowlisted":
                (
                    plan[
                        "recommended_action"
                    ]
                    in allowed_actions
                ),

            "supported_rca":
                (
                    plan[
                        "final_rca_disposition"
                    ]
                    == "supported_candidate"
                ),

            "causal_score":
                float(
                    plan[
                        "causal_consistency_score"
                    ]
                )
                >= float(
                    guard[
                        "minimum_causal_score"
                    ]
                ),

            "priority_score":
                float(
                    plan[
                        "remediation_priority_score"
                    ]
                )
                >= float(
                    guard[
                        "minimum_priority_score"
                    ]
                ),

            "positive_net_benefit":
                float(
                    plan[
                        "recommended_net_benefit"
                    ]
                )
                >= float(
                    guard[
                        "minimum_net_benefit"
                    ]
                ),

            "projected_risk":
                float(
                    plan[
                        "projected_failure_risk"
                    ]
                )
                <= float(
                    guard[
                        "maximum_projected_failure_risk"
                    ]
                ),

            "rollback_available":
                bool(
                    plan[
                        "rollback_available"
                    ]
                ),

            "traceable_evidence":
                bool(
                    plan[
                        "traceable_evidence"
                    ]
                ),
        }

        failed_checks = [
            check
            for check, passed
            in checks.items()
            if not passed
        ]

        technical_approval = (
            len(failed_checks)
            == 0
        )

        if technical_approval:

            guard_decision = (
                "eligible_pending_human"
            )

            phase14_candidate = True

        else:

            guard_decision = (
                "blocked"
            )

            phase14_candidate = False

        rows.append(
            {
                "plan_id":
                    plan[
                        "plan_id"
                    ],

                "incident_id":
                    plan[
                        "incident_id"
                    ],

                "candidate_service":
                    plan[
                        "candidate_service"
                    ],

                "recommended_action":
                    plan[
                        "recommended_action"
                    ],

                "guard_decision":
                    guard_decision,

                "guard_technical_approval":
                    technical_approval,

                "checks_passed":
                    len(checks)
                    - len(failed_checks),

                "checks_total":
                    len(checks),

                "failed_checks":
                    failed_checks,

                "phase14_candidate":
                    phase14_candidate,

                "rollback_available":
                    bool(
                        plan[
                            "rollback_available"
                        ]
                    ),

                "human_approval_required":
                    True,

                "human_approval_status":
                    "pending",

                "execution_allowed":
                    False,

                "fail_closed":
                    bool(
                        guard[
                            "fail_closed"
                        ]
                    ),
            }
        )

    return pl.DataFrame(
        rows,
        strict=False,
    )
