from pathlib import Path

import polars as pl

REQUESTS = Path(
    "data/processed/execution/"
    "execution_requests_v1.parquet"
)

APPROVALS = Path(
    "data/processed/execution/"
    "execution_approvals_v1.parquet"
)

RESULTS = Path(
    "data/processed/execution/"
    "execution_results_v1.parquet"
)

VERIFICATION = Path(
    "data/processed/execution/"
    "recovery_verification_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed_check(message: str) -> None:
    global failed
    failed = True
    print(f"[FAIL] {message}")


print()
print("=" * 68)
print(" SENTINELOPS AI - PHASE 14 PREFLIGHT")
print("=" * 68)


print("\n[Execution Requests]")

if REQUESTS.exists():

    requests = pl.read_parquet(
        REQUESTS
    )

    passed(
        "Execution requests artifact"
    )

    if requests[
        "fail_closed"
    ].all():
        passed(
            "Fail-closed requests"
        )
    else:
        failed_check(
            "Fail-closed execution requests"
        )

else:
    failed_check(
        "Execution requests artifact"
    )


print("\n[Human Approval]")

if APPROVALS.exists():

    approvals = pl.read_parquet(
        APPROVALS
    )

    passed(
        "Human approval artifact"
    )

    approved = approvals.filter(
        pl.col(
            "approval_status"
        )
        == "approved"
    )

    if approved.height > 0:
        passed(
            f"Explicit approvals ({approved.height})"
        )
    else:
        failed_check(
            "No explicitly approved sandbox request"
        )

else:
    failed_check(
        "Human approval artifact"
    )


print("\n[Controlled Execution]")

if RESULTS.exists():

    results = pl.read_parquet(
        RESULTS
    )

    passed(
        "Execution-results artifact"
    )

    successful = results.filter(
        pl.col(
            "execution_status"
        ).is_in(
            [
                "executed_verified",
                "rolled_back_verified",
            ]
        )
    )

    if successful.height > 0:
        passed(
            "Controlled execution verified"
        )
    else:
        failed_check(
            "No verified execution"
        )

    unsafe = results.filter(
        pl.col(
            "execution_attempted"
        )
        &
        (
            ~pl.col(
                "final_gate_passed"
            )
        )
    )

    if unsafe.height == 0:
        passed(
            "No execution bypassed final gate"
        )
    else:
        failed_check(
            "Execution-gate bypass detected"
        )

else:
    failed_check(
        "Execution-results artifact"
    )


print("\n[Recovery Verification]")

if VERIFICATION.exists():

    verification = pl.read_parquet(
        VERIFICATION
    )

    passed(
        "Recovery-verification artifact"
    )

    if verification[
        "recovery_verified"
    ].any():
        passed(
            "Recovery verified"
        )
    else:
        failed_check(
            "Recovery not verified"
        )

else:
    failed_check(
        "Recovery-verification artifact"
    )


print()
print("=" * 68)

if failed:

    print(
        "PHASE 14 PREFLIGHT: FAILED"
    )

    print("=" * 68)

    raise SystemExit(1)


print(
    "PHASE 14 PREFLIGHT: PASSED"
)

print("=" * 68)
