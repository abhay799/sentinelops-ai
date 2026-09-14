from pathlib import Path

import polars as pl
import yaml

from sentinelops.impact.engine import (
    build_service_impact,
)

ANOMALIES = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

PREDICTIONS = Path(
    "data/processed/prediction/"
    "supervised_predictions_v1.parquet"
)

OUTPUT = Path(
    "data/processed/impact/"
    "service_impact_v1.parquet"
)


with open(
    "configs/slo_business_impact.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "slo_business_impact"
    ]


anomalies = pl.read_parquet(
    ANOMALIES
)

predictions = pl.read_parquet(
    PREDICTIONS
)


result = build_service_impact(
    anomaly_data=anomalies,
    predictions=predictions,
    config=config,
)


if result.is_empty():
    raise RuntimeError(
        "No service-impact records produced"
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
    " SENTINELOPS AI - PHASE 12 SLO / BUSINESS IMPACT"
)
print("=" * 76)

print(
    result.select(
        [
            "service",
            "service_criticality",
            "latency_slo_ratio",
            "error_slo_ratio",
            "predicted_failure_probability",
            "business_impact_score",
            "impact_severity",
        ]
    )
)

print()

print(
    "PHASE 12 SERVICE IMPACT BUILD: PASSED"
)
