from __future__ import annotations

from typing import Any

import polars as pl

ROLLBACK_STRATEGIES = {
    "rollback":
        "Restore previous known-good deployment version",

    "traffic_shift":
        "Return traffic to original service routing",

    "restart":
        "Stop restart attempt and restore previous runtime state",
}


def build_remediation_plans(
    counterfactual_summary: pl.DataFrame,
    incident_priority: pl.DataFrame,
    rca_disposition: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    if counterfactual_summary.is_empty():
        return pl.DataFrame()

    priority_lookup = {
        row["incident_id"]: row
        for row
        in incident_priority.to_dicts()
    }

    disposition_lookup = {
        (
            row["incident_id"],
            row["candidate_service"],
        ): row
        for row
        in rca_disposition.to_dicts()
    }

    allowed_actions = set(
        config[
            "allowed_actions"
        ]
    )

    planner_config = config[
        "planner"
    ]

    rows: list[
        dict[str, Any]
    ] = []

    for index, summary in enumerate(
        counterfactual_summary.to_dicts(),
        start=1,
    ):

        incident_id = summary[
            "incident_id"
        ]

        service = summary[
            "candidate_service"
        ]

        action = summary[
            "recommended_action"
        ]

        priority = priority_lookup.get(
            incident_id,
            {},
        )

        disposition = (
            disposition_lookup.get(
                (
                    incident_id,
                    service,
                ),
                {},
            )
        )

        causal_score = float(
            disposition.get(
                "causal_consistency_score",
                0.0,
            )
        )

        final_disposition = (
            disposition.get(
                "final_disposition",
                "unknown",
            )
        )

        priority_score = float(
            priority.get(
                "remediation_priority_score",
                0.0,
            )
        )

        net_benefit = float(
            summary.get(
                "recommended_net_benefit",
                0.0,
            )
        )

        projected_risk = float(
            summary.get(
                "projected_failure_risk",
                summary.get(
                    "baseline_failure_risk",
                    1.0,
                ),
            )
        )

        counterfactual_valid = (
            summary.get(
                "recommendation_status"
            )
            == "simulation_recommendation"
        )

        action_allowlisted = (
            action in allowed_actions
        )

        supported_rca = (
            final_disposition
            == "supported_candidate"
        )

        causal_ready = (
            causal_score
            >= float(
                planner_config[
                    "minimum_causal_score"
                ]
            )
        )

        priority_ready = (
            priority_score
            >= float(
                planner_config[
                    "minimum_priority_score"
                ]
            )
        )

        benefit_ready = (
            net_benefit
            >= float(
                planner_config[
                    "minimum_net_benefit"
                ]
            )
        )

        planner_ready = all(
            [
                counterfactual_valid,
                action_allowlisted,
                supported_rca,
                causal_ready,
                priority_ready,
                benefit_ready,
            ]
        )

        if planner_ready:
            plan_status = (
                "proposed_pending_guard"
            )
        else:
            plan_status = (
                "blocked_before_guard"
            )

        rollback_strategy = (
            ROLLBACK_STRATEGIES.get(
                action,
                "No rollback strategy available",
            )
        )

        rows.append(
            {
                "plan_id":
                    f"PLAN-{index:04d}",

                "incident_id":
                    incident_id,

                "candidate_service":
                    service,

                "recommended_action":
                    action,

                "plan_status":
                    plan_status,

                "planner_ready":
                    planner_ready,

                "action_allowlisted":
                    action_allowlisted,

                "counterfactual_valid":
                    counterfactual_valid,

                "final_rca_disposition":
                    final_disposition,

                "causal_consistency_score":
                    causal_score,

                "remediation_priority_score":
                    priority_score,

                "recommended_net_benefit":
                    net_benefit,

                "projected_failure_risk":
                    projected_risk,

                "rollback_strategy":
                    rollback_strategy,

                "rollback_available":
                    (
                        action
                        in ROLLBACK_STRATEGIES
                    ),

                "traceable_evidence":
                    True,

                "sentinelguard_required":
                    True,

                "human_approval_required":
                    True,

                "human_approval_status":
                    "pending",

                "execution_allowed":
                    False,
            }
        )

    return pl.DataFrame(
        rows,
        strict=False,
    )
