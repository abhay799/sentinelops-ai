from __future__ import annotations

from typing import Any

import polars as pl

from sentinelops.counterfactual.validation import (
    validate_counterfactuals,
)


def build_counterfactual_summary(
    simulations: pl.DataFrame,
) -> pl.DataFrame:

    errors = validate_counterfactuals(
        simulations
    )

    if errors:
        raise ValueError(
            "\n".join(errors)
        )

    rows: list[
        dict[str, Any]
    ] = []

    groups = simulations.partition_by(
        [
            "incident_id",
            "candidate_service",
            "candidate_rank",
        ],
        maintain_order=True,
    )

    for group in groups:

        incident_id = group[
            "incident_id"
        ][0]

        service = group[
            "candidate_service"
        ][0]

        candidate_rank = int(
            group[
                "candidate_rank"
            ][0]
        )

        actionable = (
            group
            .filter(
                (
                    pl.col("action")
                    != "no_action"
                )
                &
                pl.col(
                    "action_applicable"
                )
            )
            .sort(
                "net_benefit",
                descending=True,
            )
        )

        recommendation = group.filter(
            pl.col(
                "recommended_in_simulation"
            )
        )

        if recommendation.height == 1:

            recommended_action = (
                recommendation[
                    "action"
                ][0]
            )

            recommended_net_benefit = float(
                recommendation[
                    "net_benefit"
                ][0]
            )

            projected_failure_risk = float(
                recommendation[
                    "projected_failure_risk"
                ][0]
            )

            recommendation_status = (
                "simulation_recommendation"
            )

        else:

            recommended_action = (
                "no_action"
            )

            recommended_net_benefit = 0.0

            projected_failure_risk = float(
                group[
                    "baseline_failure_risk"
                ][0]
            )

            recommendation_status = (
                "no_safe_recommendation"
            )

        alternatives = []

        for rank, action in enumerate(
            actionable.to_dicts(),
            start=1,
        ):

            alternatives.append(
                {
                    "rank":
                        int(rank),

                    "action":
                        action[
                            "action"
                        ],

                    "net_benefit":
                        float(
                            action[
                                "net_benefit"
                            ]
                        ),

                    "projected_failure_risk":
                        float(
                            action[
                                "projected_failure_risk"
                            ]
                        ),

                    "risk_reduction":
                        float(
                            action[
                                "risk_reduction"
                            ]
                        ),
                }
            )

        rows.append(
            {
                "incident_id":
                    incident_id,

                "candidate_service":
                    service,

                "candidate_rank":
                    candidate_rank,

                "baseline_failure_risk":
                    float(
                        group[
                            "baseline_failure_risk"
                        ][0]
                    ),

                "recommended_action":
                    recommended_action,

                "recommended_net_benefit":
                    recommended_net_benefit,

                "projected_failure_risk":
                    projected_failure_risk,

                "recommendation_status":
                    recommendation_status,

                "actionable_alternative_count":
                    len(alternatives),

                "alternatives":
                    alternatives,

                "simulation_only":
                    True,

                "execution_allowed":
                    False,

                "requires_sentinelguard":
                    (
                        recommended_action
                        != "no_action"
                    ),

                "requires_human_confirmation":
                    True,
            }
        )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(
            rows,
            strict=False,
        )
        .sort(
            [
                "incident_id",
                "candidate_rank",
            ]
        )
    )
