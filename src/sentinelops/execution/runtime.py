from __future__ import annotations

from typing import Any

import httpx

from sentinelops.execution.gate import (
    is_local_target,
)


def final_execution_gate(
    request: dict[str, Any],
    approval: dict[str, Any],
    config: dict[str, Any],
) -> tuple[
    bool,
    list[str],
]:

    failures: list[str] = []

    if not bool(
        config[
            "fail_closed"
        ]
    ):
        failures.append(
            "fail_closed_disabled"
        )

    if not bool(
        request.get(
            "preapproval_ready",
            False,
        )
    ):
        failures.append(
            "preapproval_not_ready"
        )

    if not bool(
        request.get(
            "guard_passed",
            False,
        )
    ):
        failures.append(
            "sentinelguard_not_passed"
        )

    if not bool(
        request.get(
            "rollback_available",
            False,
        )
    ):
        failures.append(
            "rollback_unavailable"
        )

    target = request.get(
        "target_url"
    )

    if (
        not target
        or not is_local_target(
            target
        )
    ):
        failures.append(
            "non_local_target"
        )

    action = request.get(
        "recommended_action"
    )

    if (
        action
        not in config[
            "allowed_actions"
        ]
    ):
        failures.append(
            "action_not_allowlisted"
        )

    if (
        action
        not in config[
            "sandbox_actions"
        ]
    ):
        failures.append(
            "sandbox_adapter_unavailable"
        )

    if (
        approval.get(
            "approval_status"
        )
        != "approved"
    ):
        failures.append(
            "human_approval_missing"
        )

    if not approval.get(
        "approved_by"
    ):
        failures.append(
            "approver_identity_missing"
        )

    return (
        len(failures) == 0,
        failures,
    )


def _probe(
    client: httpx.Client,
    base_url: str,
    path: str,
) -> bool:

    try:

        response = client.get(
            f"{base_url}{path}"
        )

        return (
            200
            <= response.status_code
            < 300
        )

    except httpx.HTTPError:
        return False


def execute_local_sandbox(
    request: dict[str, Any],
    approval: dict[str, Any],
    config: dict[str, Any],
    transport: httpx.BaseTransport
    | None = None,
) -> dict[str, Any]:

    gate_passed, failures = (
        final_execution_gate(
            request,
            approval,
            config,
        )
    )

    base = {
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

        "target_url":
            request[
                "target_url"
            ],

        "final_gate_passed":
            gate_passed,

        "gate_failures":
            failures,
    }

    if not gate_passed:

        return {
            **base,

            "pre_live":
                False,

            "pre_ready":
                False,

            "execution_attempted":
                False,

            "action_http_status":
                None,

            "post_live":
                False,

            "post_ready":
                False,

            "recovery_verified":
                False,

            "rollback_attempted":
                False,

            "rollback_succeeded":
                False,

            "execution_status":
                "blocked",
        }

    timeout = float(
        config[
            "safety"
        ][
            "request_timeout_seconds"
        ]
    )

    client = httpx.Client(
        timeout=timeout,
        transport=transport,
    )

    target = request[
        "target_url"
    ]

    action = request[
        "recommended_action"
    ]

    action_config = config[
        "sandbox_actions"
    ][
        action
    ]

    pre_live = _probe(
        client,
        target,
        "/live",
    )

    pre_ready = _probe(
        client,
        target,
        "/ready",
    )

    if not (
        pre_live
        and pre_ready
    ):

        client.close()

        return {
            **base,

            "pre_live":
                pre_live,

            "pre_ready":
                pre_ready,

            "execution_attempted":
                False,

            "action_http_status":
                None,

            "post_live":
                False,

            "post_ready":
                False,

            "recovery_verified":
                False,

            "rollback_attempted":
                False,

            "rollback_succeeded":
                False,

            "execution_status":
                "blocked_precheck",
        }

    action_attempted = False
    action_status = None

    try:

        action_attempted = True

        response = client.request(
            action_config[
                "method"
            ],
            (
                target
                + action_config[
                    "path"
                ]
            ),
        )

        action_status = (
            response.status_code
        )

    except httpx.HTTPError:

        action_status = None

    post_live = _probe(
        client,
        target,
        "/live",
    )

    post_ready = _probe(
        client,
        target,
        "/ready",
    )

    action_success = (
        action_status is not None
        and 200
        <= action_status
        < 300
    )

    recovery_verified = (
        action_success
        and post_live
        and post_ready
    )

    rollback_attempted = False
    rollback_succeeded = False

    if not recovery_verified:

        rollback_attempted = True

        try:

            rollback_response = (
                client.post(
                    target
                    + config[
                        "rollback_path"
                    ]
                )
            )

            rollback_succeeded = (
                200
                <= rollback_response.status_code
                < 300
            )

        except httpx.HTTPError:

            rollback_succeeded = False

        post_live = _probe(
            client,
            target,
            "/live",
        )

        post_ready = _probe(
            client,
            target,
            "/ready",
        )

        recovery_verified = (
            rollback_succeeded
            and post_live
            and post_ready
        )

    client.close()

    if (
        action_success
        and recovery_verified
        and not rollback_attempted
    ):

        status = "executed_verified"

    elif (
        rollback_attempted
        and recovery_verified
    ):

        status = "rolled_back_verified"

    else:

        status = "recovery_failed"

    return {
        **base,

        "pre_live":
            pre_live,

        "pre_ready":
            pre_ready,

        "execution_attempted":
            action_attempted,

        "action_http_status":
            action_status,

        "post_live":
            post_live,

        "post_ready":
            post_ready,

        "recovery_verified":
            recovery_verified,

        "rollback_attempted":
            rollback_attempted,

        "rollback_succeeded":
            rollback_succeeded,

        "execution_status":
            status,
    }
