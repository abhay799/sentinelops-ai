from pathlib import Path

import polars as pl

from sentinelops.rca.validation import (
    validate_rca_hypotheses,
)

HYPOTHESES = Path(
    "data/processed/rca/"
    "rca_hypotheses_v1.parquet"
)

SUMMARY = Path(
    "data/processed/rca/"
    "rca_summary_v1.parquet"
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
print(" SENTINELOPS AI - PHASE 8 PREFLIGHT")
print("=" * 64)


print("\n[RCA Artifacts]")


if HYPOTHESES.exists():
    passed("RCA hypotheses")
else:
    failed_check("RCA hypotheses")


if SUMMARY.exists():
    passed("RCA summary")
else:
    failed_check("RCA summary")


if HYPOTHESES.exists():

    hypotheses = pl.read_parquet(
        HYPOTHESES
    )

    errors = validate_rca_hypotheses(
        hypotheses
    )

    if not errors:
        passed(
            "RCA evidence validation"
        )
    else:
        for error in errors:
            failed_check(error)

    if (
        hypotheses[
            "evidence_count"
        ].min()
        > 0
    ):
        passed(
            "Evidence-backed hypotheses"
        )
    else:
        failed_check(
            "Missing RCA evidence"
        )

    if not hypotheses[
        "confirmed_root_cause"
    ].any():
        passed(
            "No premature RCA confirmation"
        )
    else:
        failed_check(
            "Premature RCA confirmation"
        )

    if hypotheses[
        "requires_challenger"
    ].all():
        passed(
            "Challenger required"
        )
    else:
        failed_check(
            "Challenger requirement"
        )

    if hypotheses[
        "requires_human_confirmation"
    ].all():
        passed(
            "Human confirmation required"
        )
    else:
        failed_check(
            "Human confirmation requirement"
        )


if SUMMARY.exists():

    summary = pl.read_parquet(
        SUMMARY
    )

    if summary.height > 0:
        passed(
            f"RCA summaries ({summary.height})"
        )
    else:
        failed_check(
            "No RCA summaries"
        )

    if (
        summary[
            "root_cause_status"
        ]
        == "unconfirmed"
    ).all():
        passed(
            "Root-cause status unconfirmed"
        )
    else:
        failed_check(
            "Root-cause status"
        )


print()
print("=" * 64)


if failed:

    print(
        "PHASE 8 PREFLIGHT: FAILED"
    )

    print("=" * 64)

    raise SystemExit(1)


print(
    "PHASE 8 PREFLIGHT: PASSED"
)

print("=" * 64)
