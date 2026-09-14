from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

import polars as pl


def is_local_target(
    url: str,
) -> bool:

    parsed = urlparse(
        url
    )

    return parsed.hostname in {
        "localhost",
        "127.0.0.1",
        "::1",
    }


def build_execution_requests(
    plans: pl.DataFrame,
    decisions: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    if plans.is_empty():
        return pl.DataFrame()

    if decisions.is_empty():
        return pl.DataFrame()

    decision_lookup = {
        row["plan_id"]: row
        for row
        in decisions.to_dicts()
    }

    allowed_actions = set(
        config[
            "allowed_actions"
        ]
    )

    service_targets = config[
        "services"
    ]

    require_local = bool(
        config[
            "safety"
        ][
            "require_local_target"
        ]
    )

    rows: list[
        dict[str, Any]
    ] = []

    for index, plan in enumerate(
        plans.to_dicts(),
        start=1,
    ):

        plan_id = plan[
            "plan_id"
        ]

        decision = decision_lookup.get(
            plan_id,
            {},
        )

        service = plan[
            "candidate_service"
        ]

        action = plan[
            "recommended_action"
        ]

        target_url = (
            service_targets.get(
                service
            )
        )

        guard_passed = (
            bool(
                decision.get(
                    "guard_technical_approval",
                    False,
                )
            )
            and
            decision.get(
                "guard_decision"
            )
            == "eligible_pending_human"
            and
            bool(
                decision.get(
                    "phase14_candidate",
                    False,
                )
            )
        )

        action_allowlisted = (
            action
            in allowed_actions
        )

        rollback_available = bool(
            plan.get(
                "rollback_available",
                False,
            )
        )

        target_known = (
            target_url
            is not None
        )

        local_target = (
            is_local_target(
                target_url
            )
            if target_url
            else False
        )

        local_target_valid = (
            local_target
            if require_local
            else target_known
        )

        preapproval_ready = all(
            [
                guard_passed,
                action_allowlisted,
                rollback_available,
                target_known,
                local_target_valid,
            ]
        )

        if preapproval_ready:
            request_status = (
                "awaiting_human_approval"
            )
        else:
            request_status = (
                "blocked"
            )

        rows.append(
            {
                "execution_request_id":
                    f"EXEC-{index:04d}",

                "plan_id":
                    plan_id,

                "incident_id":
                    plan[
                        "incident_id"
                    ],

                "candidate_service":
                    service,

                "recommended_action":
                    action,

                "target_url":
                    target_url,

                "guard_passed":
                    guard_passed,

                "action_allowlisted":
                    action_allowlisted,

                "rollback_available":
                    rollback_available,

                "local_target":
                    local_target,

                "preapproval_ready":
                    preapproval_ready,

                "request_status":
                    request_status,

                "human_approval_required":
                    True,

                "human_approval_status":
                    "pending",

                "execution_allowed":
                    False,

                "execution_attempted":
                    False,

                "rollback_strategy":
                    plan.get(
                        "rollback_strategy",
                        "",
                    ),

                "fail_closed":
                    bool(
                        config[
                            "fail_closed"
                        ]
                    ),
            }
        )

    return pl.DataFrame(
        rows,
        strict=False,
    )


def validate_execution_requests(
    requests: pl.DataFrame,
) -> list[str]:

    errors: list[str] = []

    if requests.is_empty():
        return [
            "Execution request dataset is empty"
        ]

    required = {
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
        "execution_attempted",
        "fail_closed",
    }

    missing = (
        required
        - set(requests.columns)
    )

    if missing:

        errors.append(
            f"Missing columns: {sorted(missing)}"
        )

        return errors

    if requests[
        "execution_allowed"
    ].any():

        errors.append(
            "Execution permission must remain "
            "disabled before human approval"
        )

    if requests[
        "execution_attempted"
    ].any():

        errors.append(
            "Execution was attempted before approval"
        )

    if not (
        requests[
            "human_approval_status"
        ]
        == "pending"
    ).all():

        errors.append(
            "Initial approval status must be pending"
        )

    if not requests[
        "fail_closed"
    ].all():

        errors.append(
            "Execution gate must fail closed"
        )

    eligible = requests.filter(
        pl.col(
            "preapproval_ready"
        )
    )

    if eligible.height > 0:

        invalid = eligible.filter(
            pl.col(
                "request_status"
            )
            != "awaiting_human_approval"
        )

        if invalid.height > 0:
            errors.append(
                "Eligible request not waiting "
                "for human approval"
            )

    blocked = requests.filter(
        ~pl.col(
            "preapproval_ready"
        )
    )

    if blocked.height > 0:

        invalid = blocked.filter(
            pl.col(
                "request_status"
            )
            != "blocked"
        )

        if invalid.height > 0:
            errors.append(
                "Unsafe request not blocked"
            )

    return errors
