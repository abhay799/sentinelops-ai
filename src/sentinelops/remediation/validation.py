from __future__ import annotations

import polars as pl

PLAN_REQUIRED = {
    "plan_id",
    "incident_id",
    "candidate_service",
    "recommended_action",
    "plan_status",
    "planner_ready",
    "rollback_available",
    "traceable_evidence",
    "sentinelguard_required",
    "human_approval_required",
    "human_approval_status",
    "execution_allowed",
}


GUARD_REQUIRED = {
    "plan_id",
    "incident_id",
    "candidate_service",
    "recommended_action",
    "guard_decision",
    "guard_technical_approval",
    "phase14_candidate",
    "rollback_available",
    "human_approval_required",
    "human_approval_status",
    "execution_allowed",
    "fail_closed",
}


def validate_phase13(
    plans: pl.DataFrame,
    decisions: pl.DataFrame,
) -> list[str]:

    errors: list[str] = []

    if plans.is_empty():
        errors.append(
            "Remediation plans are empty"
        )
        return errors

    if decisions.is_empty():
        errors.append(
            "SentinelGuard decisions are empty"
        )
        return errors

    missing_plans = (
        PLAN_REQUIRED
        - set(plans.columns)
    )

    if missing_plans:
        errors.append(
            "Missing plan columns: "
            f"{sorted(missing_plans)}"
        )

    missing_guard = (
        GUARD_REQUIRED
        - set(decisions.columns)
    )

    if missing_guard:
        errors.append(
            "Missing guard columns: "
            f"{sorted(missing_guard)}"
        )

    if missing_plans or missing_guard:
        return errors

    if plans[
        "execution_allowed"
    ].any():
        errors.append(
            "Planner must never allow execution"
        )

    if decisions[
        "execution_allowed"
    ].any():
        errors.append(
            "SentinelGuard must not allow "
            "execution in Phase 13"
        )

    if not plans[
        "sentinelguard_required"
    ].all():
        errors.append(
            "SentinelGuard requirement missing"
        )

    if not plans[
        "human_approval_required"
    ].all():
        errors.append(
            "Planner human approval gate missing"
        )

    if not decisions[
        "human_approval_required"
    ].all():
        errors.append(
            "Guard human approval gate missing"
        )

    if not (
        decisions[
            "human_approval_status"
        ]
        == "pending"
    ).all():
        errors.append(
            "Phase 13 human approval must remain pending"
        )

    if not decisions[
        "fail_closed"
    ].all():
        errors.append(
            "SentinelGuard must operate fail-closed"
        )

    invalid_decisions = decisions.filter(
        ~pl.col(
            "guard_decision"
        ).is_in(
            [
                "eligible_pending_human",
                "blocked",
            ]
        )
    )

    if invalid_decisions.height > 0:
        errors.append(
            "Unknown SentinelGuard decision"
        )

    approved = decisions.filter(
        pl.col(
            "guard_technical_approval"
        )
    )

    if approved.height > 0:

        invalid = approved.filter(
            ~pl.col(
                "phase14_candidate"
            )
        )

        if invalid.height > 0:
            errors.append(
                "Technically approved plan "
                "not marked Phase 14 candidate"
            )

    blocked = decisions.filter(
        pl.col(
            "guard_decision"
        )
        == "blocked"
    )

    if blocked.height > 0:

        invalid = blocked.filter(
            pl.col(
                "phase14_candidate"
            )
        )

        if invalid.height > 0:
            errors.append(
                "Blocked plan incorrectly marked "
                "Phase 14 candidate"
            )

    proposed = plans.filter(
        pl.col(
            "plan_status"
        )
        == "proposed_pending_guard"
    )

    if proposed.height > 0:

        invalid = proposed.filter(
            ~pl.col(
                "planner_ready"
            )
        )

        if invalid.height > 0:
            errors.append(
                "Planner status inconsistent "
                "with planner_ready"
            )

    return errors
