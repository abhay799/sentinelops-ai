import httpx

from sentinelops.execution.runtime import (
    execute_local_sandbox,
    final_execution_gate,
)

CONFIG = {
    "fail_closed":
        True,

    "allowed_actions": [
        "rollback",
        "traffic_shift",
        "restart",
    ],

    "sandbox_actions": {
        "rollback": {
            "method": "POST",
            "path": "/failure-mode/reset",
        },
    },

    "rollback_path":
        "/failure-mode/reset",

    "safety": {
        "request_timeout_seconds":
            5,
    },
}


def request():

    return {
        "execution_request_id":
            "EXEC-0001",

        "plan_id":
            "PLAN-0001",

        "incident_id":
            "INC-0001",

        "candidate_service":
            "payment-service",

        "recommended_action":
            "rollback",

        "target_url":
            "http://localhost:8103",

        "preapproval_ready":
            True,

        "guard_passed":
            True,

        "rollback_available":
            True,
    }


def approval():

    return {
        "approval_status":
            "approved",

        "approved_by":
            "test-user",
    }


def test_final_gate_passes():

    allowed, failures = (
        final_execution_gate(
            request(),
            approval(),
            CONFIG,
        )
    )

    assert allowed
    assert failures == []


def test_missing_human_approval_fails():

    denied = approval()

    denied[
        "approval_status"
    ] = "pending"

    allowed, failures = (
        final_execution_gate(
            request(),
            denied,
            CONFIG,
        )
    )

    assert not allowed

    assert (
        "human_approval_missing"
        in failures
    )


def test_non_local_target_fails():

    unsafe = request()

    unsafe[
        "target_url"
    ] = "https://example.com"

    allowed, failures = (
        final_execution_gate(
            unsafe,
            approval(),
            CONFIG,
        )
    )

    assert not allowed

    assert (
        "non_local_target"
        in failures
    )


def test_missing_adapter_fails():

    unsupported = request()

    unsupported[
        "recommended_action"
    ] = "restart"

    allowed, failures = (
        final_execution_gate(
            unsupported,
            approval(),
            CONFIG,
        )
    )

    assert not allowed

    assert (
        "sandbox_adapter_unavailable"
        in failures
    )


def test_controlled_execution_verifies_recovery():

    def handler(
        request_object:
            httpx.Request,
    ) -> httpx.Response:

        if (
            request_object.url.path
            in {
                "/live",
                "/ready",
            }
        ):

            return httpx.Response(
                200,
                json={
                    "status": "ok"
                },
            )

        if (
            request_object.url.path
            == "/failure-mode/reset"
        ):

            return httpx.Response(
                200,
                json={
                    "status": "reset"
                },
            )

        return httpx.Response(
            404
        )

    transport = httpx.MockTransport(
        handler
    )

    result = execute_local_sandbox(
        request(),
        approval(),
        CONFIG,
        transport=transport,
    )

    assert result[
        "final_gate_passed"
    ]

    assert result[
        "execution_attempted"
    ]

    assert result[
        "recovery_verified"
    ]

    assert (
        result[
            "execution_status"
        ]
        == "executed_verified"
    )
