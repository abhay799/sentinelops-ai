from pathlib import Path

import polars as pl

from sentinelops.counterfactual.validation import (
    validate_counterfactuals,
)

SIMULATIONS = Path(
    "data/processed/counterfactual/"
    "counterfactual_simulations_v1.parquet"
)

SUMMARY = Path(
    "data/processed/counterfactual/"
    "counterfactual_summary_v1.parquet"
)


failed = False


def passed(message: str) -> None:
    print(f"[PASS] {message}")


def failed_check(message: str) -> None:
    global failed
    failed = True
    print(f"[FAIL] {message}")


print()
print("=" * 66)
print(
    " SENTINELOPS AI - PHASE 11 PREFLIGHT"
)
print("=" * 66)


print("\n[Counterfactual Simulation]")


if SIMULATIONS.exists():

    simulations = pl.read_parquet(
        SIMULATIONS
    )

    passed(
        "Simulation artifact"
    )

    errors = validate_counterfactuals(
        simulations
    )

    if not errors:
        passed(
            "Counterfactual safety validation"
        )
    else:
        for error in errors:
            failed_check(error)

    if simulations.height > 0:
        passed(
            f"Simulation rows ({simulations.height})"
        )
    else:
        failed_check(
            "No simulation rows"
        )

    if not simulations[
        "execution_allowed"
    ].any():
        passed(
            "Execution hard-disabled"
        )
    else:
        failed_check(
            "Execution permission detected"
        )

    if simulations[
        "simulation_only"
    ].all():
        passed(
            "Simulation-only contract"
        )
    else:
        failed_check(
            "Simulation-only contract"
        )

else:

    failed_check(
        "Simulation artifact"
    )


print("\n[Counterfactual Ranking]")


if SUMMARY.exists():

    summary = pl.read_parquet(
        SUMMARY
    )

    passed(
        "Counterfactual summary"
    )

    if summary.height > 0:
        passed(
            f"Decision summaries ({summary.height})"
        )
    else:
        failed_check(
            "No decision summaries"
        )

    if not summary[
        "execution_allowed"
    ].any():
        passed(
            "Summary cannot execute"
        )
    else:
        failed_check(
            "Summary permits execution"
        )

    if summary[
        "requires_human_confirmation"
    ].all():
        passed(
            "Human confirmation required"
        )
    else:
        failed_check(
            "Human confirmation gate"
        )

    recommended = summary.filter(
        pl.col(
            "recommended_action"
        )
        != "no_action"
    )

    if recommended.height > 0:

        if recommended[
            "requires_sentinelguard"
        ].all():
            passed(
                "SentinelGuard required for recommendations"
            )
        else:
            failed_check(
                "SentinelGuard bypass detected"
            )

    else:
        passed(
            "No unsafe recommendation forced"
        )

else:

    failed_check(
        "Counterfactual summary"
    )


print()
print("=" * 66)


if failed:

    print(
        "PHASE 11 PREFLIGHT: FAILED"
    )

    print("=" * 66)

    raise SystemExit(1)


print(
    "PHASE 11 PREFLIGHT: PASSED"
)

print("=" * 66)
