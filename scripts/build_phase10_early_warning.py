from pathlib import Path

import polars as pl
import yaml

from sentinelops.prediction.early_warning import (
    build_early_warning_dataset,
)

INPUT = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

OUTPUT = Path(
    "data/processed/prediction/"
    "early_warning_v1.parquet"
)


with open(
    "configs/failure_prediction.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "failure_prediction"
    ]


data = pl.read_parquet(
    INPUT
)


warnings = (
    build_early_warning_dataset(
        anomaly_data=data,

        lookahead_events=int(
            config[
                "lookahead_events"
            ]
        ),

        minimum_history_events=int(
            config[
                "minimum_history_events"
            ]
        ),

        history_window_events=int(
            config[
                "history_window_events"
            ]
        ),

        warning_threshold=float(
            config[
                "warning_threshold"
            ]
        ),

        weights=config[
            "weights"
        ],
    )
)


if warnings.is_empty():
    raise RuntimeError(
        "No early-warning observations produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

warnings.write_parquet(
    OUTPUT
)


print()
print("=" * 72)
print(
    " SENTINELOPS AI - PHASE 10 EARLY WARNING"
)
print("=" * 72)

print(
    warnings
    .filter(
        pl.col("warning_ready")
    )
    .sort(
        "early_warning_score",
        descending=True,
    )
    .select(
        [
            "service",
            "feature_as_of_time",
            "early_warning_score",
            "warning_flag",
            "current_is_anomaly",
            "future_anomaly",
            "lead_events",
        ]
    )
    .head(20)
)

print()

print(
    "Rows:",
    warnings.height,
)

print(
    "Warnings:",
    int(
        warnings[
            "warning_flag"
        ].sum()
    ),
)

print(
    "Future-anomaly labels:",
    int(
        warnings[
            "future_anomaly"
        ].sum()
    ),
)

print()

print(
    "PHASE 10 EARLY WARNING BUILD: PASSED"
)
