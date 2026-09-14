from pathlib import Path

import polars as pl

from sentinelops.counterfactual.ranking import (
    build_counterfactual_summary,
)
from sentinelops.counterfactual.validation import (
    validate_counterfactuals,
)

INPUT = Path(
    "data/processed/counterfactual/"
    "counterfactual_simulations_v1.parquet"
)

OUTPUT = Path(
    "data/processed/counterfactual/"
    "counterfactual_summary_v1.parquet"
)


simulations = pl.read_parquet(
    INPUT
)


errors = validate_counterfactuals(
    simulations
)

if errors:
    raise RuntimeError(
        "Counterfactual validation failed:\n"
        + "\n".join(errors)
    )


summary = build_counterfactual_summary(
    simulations
)


if summary.is_empty():
    raise RuntimeError(
        "No counterfactual summaries produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary.write_parquet(
    OUTPUT
)


print()
print("=" * 76)
print(
    " SENTINELOPS AI - PHASE 11 COUNTERFACTUAL DECISION SUMMARY"
)
print("=" * 76)

print(
    summary.select(
        [
            "incident_id",
            "candidate_service",
            "candidate_rank",
            "baseline_failure_risk",
            "recommended_action",
            "projected_failure_risk",
            "recommendation_status",
            "execution_allowed",
        ]
    )
)

print()
print(
    "PHASE 11 COUNTERFACTUAL VALIDATION: PASSED"
)
