from pathlib import Path

import polars as pl
import yaml

from sentinelops.counterfactual.engine import (
    simulate_counterfactuals,
)

DISPOSITION = Path(
    "data/processed/rca/"
    "rca_disposition_v1.parquet"
)

HYPOTHESES = Path(
    "data/processed/rca/"
    "rca_hypotheses_v1.parquet"
)

PREDICTIONS = Path(
    "data/processed/prediction/"
    "supervised_predictions_v1.parquet"
)

OUTPUT = Path(
    "data/processed/counterfactual/"
    "counterfactual_simulations_v1.parquet"
)


with open(
    "configs/counterfactual.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "counterfactual"
    ]


disposition = pl.read_parquet(
    DISPOSITION
)

hypotheses = pl.read_parquet(
    HYPOTHESES
)

predictions = pl.read_parquet(
    PREDICTIONS
)


result = simulate_counterfactuals(
    disposition=disposition,
    hypotheses=hypotheses,
    predictions=predictions,
    config=config,
)


if result.is_empty():
    raise RuntimeError(
        "No counterfactual simulations produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

result.write_parquet(
    OUTPUT
)


print()
print("=" * 76)
print(
    " SENTINELOPS AI - PHASE 11 COUNTERFACTUAL SIMULATION"
)
print("=" * 76)

print(
    result
    .filter(
        pl.col(
            "candidate_rank"
        )
        == 1
    )
    .select(
        [
            "incident_id",
            "candidate_service",
            "action",
            "action_applicable",
            "baseline_failure_risk",
            "projected_failure_risk",
            "risk_reduction",
            "net_benefit",
            "recommended_in_simulation",
            "execution_allowed",
        ]
    )
)

print()

print(
    "PHASE 11 COUNTERFACTUAL SIMULATION: PASSED"
)
