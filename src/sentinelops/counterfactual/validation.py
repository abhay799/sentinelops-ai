from __future__ import annotations

import polars as pl

REQUIRED_COLUMNS = {
    "incident_id",
    "candidate_service",
    "candidate_rank",
    "action",
    "action_applicable",
    "baseline_failure_risk",
    "projected_failure_risk",
    "risk_reduction",
    "net_benefit",
    "simulation_only",
    "execution_allowed",
    "requires_sentinelguard",
    "rollback_required",
    "recommended_in_simulation",
}


def validate_counterfactuals(
    simulations: pl.DataFrame,
) -> list[str]:

    errors: list[str] = []

    if simulations.is_empty():
        return [
            "Counterfactual simulation dataset is empty"
        ]

    missing = (
        REQUIRED_COLUMNS
        - set(simulations.columns)
    )

    if missing:
        errors.append(
            f"Missing columns: {sorted(missing)}"
        )
        return errors

    if not simulations[
        "simulation_only"
    ].all():
        errors.append(
            "Counterfactual actions must remain simulation-only"
        )

    if simulations[
        "execution_allowed"
    ].any():
        errors.append(
            "Phase 11 must never allow execution"
        )

    invalid_baseline = simulations.filter(
        (pl.col("baseline_failure_risk") < 0)
        |
        (pl.col("baseline_failure_risk") > 1)
    )

    if invalid_baseline.height > 0:
        errors.append(
            "Baseline failure risk outside [0,1]"
        )

    invalid_projected = simulations.filter(
        (pl.col("projected_failure_risk") < 0)
        |
        (pl.col("projected_failure_risk") > 1)
    )

    if invalid_projected.height > 0:
        errors.append(
            "Projected failure risk outside [0,1]"
        )

    invalid_recommendations = (
        simulations
        .filter(
            pl.col(
                "recommended_in_simulation"
            )
        )
        .filter(
            (~pl.col("action_applicable"))
            |
            (
                pl.col("action")
                == "no_action"
            )
        )
    )

    if invalid_recommendations.height > 0:
        errors.append(
            "Invalid simulated recommendation"
        )

    actionable = simulations.filter(
        (
            pl.col("action")
            != "no_action"
        )
        &
        pl.col("action_applicable")
    )

    if (
        actionable.height > 0
        and not actionable[
            "requires_sentinelguard"
        ].all()
    ):
        errors.append(
            "Actionable remediation is missing SentinelGuard requirement"
        )

    if (
        actionable.height > 0
        and not actionable[
            "rollback_required"
        ].all()
    ):
        errors.append(
            "Actionable remediation is missing rollback requirement"
        )

    groups = simulations.partition_by(
        [
            "incident_id",
            "candidate_service",
        ],
        maintain_order=True,
    )

    for group in groups:

        recommendations = group.filter(
            pl.col(
                "recommended_in_simulation"
            )
        )

        if recommendations.height > 1:
            errors.append(
                "More than one recommended action "
                f"for incident={group['incident_id'][0]} "
                f"service={group['candidate_service'][0]}"
            )

    return errors
