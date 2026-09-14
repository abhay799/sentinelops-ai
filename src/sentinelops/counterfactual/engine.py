from __future__ import annotations

from typing import Any

import polars as pl


def clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )


def latest_failure_risk(
    predictions: pl.DataFrame,
) -> dict[str, float]:

    if predictions.is_empty():
        return {}

    rows = (
        predictions
        .sort("feature_as_of_time")
        .to_dicts()
    )

    latest: dict[
        str,
        float,
    ] = {}

    for row in rows:
        latest[
            row["service"]
        ] = float(
            row[
                "failure_probability"
            ]
        )

    return latest


def simulate_counterfactuals(
    disposition: pl.DataFrame,
    hypotheses: pl.DataFrame,
    predictions: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    prediction_risk = (
        latest_failure_risk(
            predictions
        )
    )

    hypothesis_lookup = {
        (
            row["incident_id"],
            row["candidate_service"],
        ): row
        for row in hypotheses.to_dicts()
    }

    rows: list[
        dict[str, Any]
    ] = []

    for candidate in disposition.to_dicts():

        incident_id = candidate[
            "incident_id"
        ]

        service = candidate[
            "candidate_service"
        ]

        key = (
            incident_id,
            service,
        )

        hypothesis = (
            hypothesis_lookup.get(
                key,
                {},
            )
        )

        causal_score = float(
            candidate[
                "causal_consistency_score"
            ]
        )

        original_rca_score = float(
            candidate.get(
                "original_rca_score",
                causal_score,
            )
        )

        baseline_risk = float(
            prediction_risk.get(
                service,
                original_rca_score,
            )
        )

        baseline_risk = clamp(
            baseline_risk
        )

        change_signal = float(
            hypothesis.get(
                "change_signal",
                0.0,
            )
        )

        disposition_status = (
            candidate[
                "final_disposition"
            ]
        )

        if (
            disposition_status
            == "supported_candidate"
        ):
            disposition_factor = 1.0

        elif (
            disposition_status
            == "weakened_candidate"
        ):
            disposition_factor = 0.60

        elif (
            disposition_status
            == "inconclusive"
        ):
            disposition_factor = 0.35

        else:
            disposition_factor = 0.0

        candidate_rows = []

        for (
            action,
            action_config,
        ) in config[
            "actions"
        ].items():

            base_effectiveness = float(
                action_config[
                    "effectiveness"
                ]
            )

            operational_risk = float(
                action_config[
                    "operational_risk"
                ]
            )

            requires_change = bool(
                action_config[
                    "requires_change_signal"
                ]
            )

            applicable = True

            reason = (
                "Action eligible for simulation"
            )

            if (
                action != "no_action"
                and disposition_factor <= 0
            ):
                applicable = False
                reason = (
                    "RCA candidate rejected"
                )

            if (
                requires_change
                and change_signal <= 0
            ):
                applicable = False
                reason = (
                    "Rollback requires "
                    "recent change evidence"
                )

            if action == "no_action":
                applicable = True

            if applicable:

                adjusted_effectiveness = (
                    base_effectiveness
                    * disposition_factor
                    * (
                        0.50
                        + 0.50
                        * causal_score
                    )
                )

            else:
                adjusted_effectiveness = 0.0

            adjusted_effectiveness = clamp(
                adjusted_effectiveness
            )

            risk_reduction = (
                baseline_risk
                * adjusted_effectiveness
            )

            projected_risk = clamp(
                baseline_risk
                - risk_reduction
            )

            net_benefit = (
                risk_reduction
                - (
                    operational_risk
                    * baseline_risk
                )
            )

            row = {
                "incident_id":
                    incident_id,

                "candidate_service":
                    service,

                "candidate_rank":
                    int(
                        candidate["rank"]
                    ),

                "final_disposition":
                    disposition_status,

                "causal_consistency_score":
                    causal_score,

                "change_signal":
                    change_signal,

                "action":
                    action,

                "action_applicable":
                    applicable,

                "applicability_reason":
                    reason,

                "baseline_failure_risk":
                    round(
                        baseline_risk,
                        6,
                    ),

                "adjusted_effectiveness":
                    round(
                        adjusted_effectiveness,
                        6,
                    ),

                "risk_reduction":
                    round(
                        risk_reduction,
                        6,
                    ),

                "projected_failure_risk":
                    round(
                        projected_risk,
                        6,
                    ),

                "operational_risk":
                    operational_risk,

                "net_benefit":
                    round(
                        net_benefit,
                        6,
                    ),

                "simulation_only":
                    True,

                "execution_allowed":
                    False,

                "requires_sentinelguard":
                    (
                        action != "no_action"
                    ),

                "rollback_required":
                    (
                        action != "no_action"
                    ),

                "recommended_in_simulation":
                    False,
            }

            candidate_rows.append(
                row
            )

        eligible_actions = [
            row
            for row in candidate_rows
            if (
                row[
                    "action_applicable"
                ]
                and row[
                    "action"
                ]
                != "no_action"
            )
        ]

        may_recommend = (
            disposition_status
            == "supported_candidate"
            and causal_score
            >= float(
                config[
                    "minimum_causal_score"
                ]
            )
        )

        if (
            may_recommend
            and eligible_actions
        ):

            best = max(
                eligible_actions,
                key=lambda item: (
                    item[
                        "net_benefit"
                    ]
                ),
            )

            best[
                "recommended_in_simulation"
            ] = True

        rows.extend(
            candidate_rows
        )

    if not rows:
        return pl.DataFrame()

    return (
        pl.DataFrame(
            rows
        )
        .sort(
            [
                "incident_id",
                "candidate_rank",
                "action",
            ]
        )
    )
