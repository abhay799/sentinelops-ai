from pathlib import Path

import polars as pl

CHALLENGES = Path(
    "data/processed/rca/"
    "rca_challenges_v1.parquet"
)

DISPOSITION = Path(
    "data/processed/rca/"
    "rca_disposition_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed_check(message: str) -> None:
    global failed
    failed = True
    print(f"[FAIL] {message}")


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 9 PREFLIGHT"
)
print("=" * 64)


print("\n[RCA Challenger]")


if CHALLENGES.exists():
    passed(
        "RCA challenger artifact"
    )
else:
    failed_check(
        "RCA challenger artifact"
    )


if DISPOSITION.exists():
    passed(
        "Causal disposition artifact"
    )
else:
    failed_check(
        "Causal disposition artifact"
    )


if CHALLENGES.exists():

    challenges = pl.read_parquet(
        CHALLENGES
    )

    if challenges[
        "challenger_completed"
    ].all():
        passed(
            "Challenger completed"
        )
    else:
        failed_check(
            "Incomplete challenger"
        )

    if not challenges[
        "confirmed_root_cause"
    ].any():
        passed(
            "Challenger did not auto-confirm RCA"
        )
    else:
        failed_check(
            "Challenger auto-confirmed RCA"
        )


if DISPOSITION.exists():

    result = pl.read_parquet(
        DISPOSITION
    )

    required = {
        "candidate_service",
        "challenge_status",
        "causal_consistency_score",
        "causal_checks_passed",
        "final_disposition",
        "root_cause_status",
        "confirmed_root_cause",
        "requires_human_confirmation",
    }

    missing = (
        required
        - set(result.columns)
    )

    if not missing:
        passed(
            "Required Phase 9 columns"
        )
    else:
        failed_check(
            f"Missing columns: "
            f"{sorted(missing)}"
        )

    if result.height > 0:
        passed(
            f"RCA dispositions "
            f"({result.height})"
        )
    else:
        failed_check(
            "No RCA dispositions"
        )

    if not result[
        "confirmed_root_cause"
    ].any():
        passed(
            "No automatic root-cause confirmation"
        )
    else:
        failed_check(
            "Automatic root-cause confirmation"
        )

    if (
        result[
            "root_cause_status"
        ]
        == "unconfirmed"
    ).all():
        passed(
            "Root cause remains unconfirmed"
        )
    else:
        failed_check(
            "Invalid root-cause status"
        )

    if result[
        "requires_human_confirmation"
    ].all():
        passed(
            "Human confirmation required"
        )
    else:
        failed_check(
            "Human confirmation gate"
        )


print()
print("=" * 64)


if failed:
    print(
        "PHASE 9 PREFLIGHT: FAILED"
    )
    print("=" * 64)
    raise SystemExit(1)


print(
    "PHASE 9 PREFLIGHT: PASSED"
)

print("=" * 64)
