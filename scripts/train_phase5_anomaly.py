from pathlib import Path

import joblib
import numpy as np
import polars as pl
import yaml

from sentinelops.anomaly.detectors import (
    IsolationForestDetector,
    ewma_detector,
    zscore_detector,
)

FEATURE_PATH = Path(
    "data/processed/features/"
    "temporal_features_v1.parquet"
)


with open(
    "configs/anomaly.yaml",
    encoding="utf-8",
) as file:
    config = yaml.safe_load(file)[
        "anomaly_detection"
    ]


features = pl.read_parquet(
    FEATURE_PATH
)


feature_columns = config[
    "features"
]


missing = [
    column
    for column in feature_columns
    if column not in features.columns
]

if missing:
    raise RuntimeError(
        f"Missing anomaly features: {missing}"
    )


matrix = (
    features
    .select(feature_columns)
    .fill_null(0)
    .to_numpy()
    .astype(float)
)


# ============================================================
# Z-score detector
# ============================================================

zscore_scores, zscore_flags = (
    zscore_detector(
        matrix,
        threshold=config[
            "statistical"
        ][
            "zscore_threshold"
        ],
    )
)


# ============================================================
# EWMA
#
# Use latency p95 as the first
# temporal-shift signal.
# ============================================================

ewma_scores = np.zeros(
    features.height
)

ewma_flags = np.zeros(
    features.height,
    dtype=int,
)


services = features[
    "service"
].unique().to_list()


for service in services:

    indexes = np.where(
        features[
            "service"
        ].to_numpy()
        == service
    )[0]

    service_latency = (
        features[
            "latency_p95_60s"
        ]
        .to_numpy()[indexes]
        .astype(float)
    )

    service_scores, service_flags = (
        ewma_detector(
            service_latency,
            alpha=config[
                "ewma"
            ][
                "alpha"
            ],
            threshold_multiplier=config[
                "ewma"
            ][
                "threshold_multiplier"
            ],
        )
    )

    ewma_scores[indexes] = (
        service_scores
    )

    ewma_flags[indexes] = (
        service_flags
    )


# ============================================================
# Isolation Forest
# ============================================================

iforest_config = config[
    "isolation_forest"
]


isolation_detector = (
    IsolationForestDetector(
        n_estimators=iforest_config[
            "n_estimators"
        ],
        contamination=iforest_config[
            "contamination"
        ],
        random_state=iforest_config[
            "random_state"
        ],
    )
)


isolation_detector.fit(
    matrix
)


iforest_scores = (
    isolation_detector.score(
        matrix
    )
)

iforest_flags = (
    isolation_detector.predict(
        matrix
    )
)


# ============================================================
# Ensemble
# ============================================================

votes = (
    zscore_flags
    + ewma_flags
    + iforest_flags
)


minimum_votes = config[
    "ensemble"
][
    "minimum_votes"
]


ensemble_flag = (
    votes >= minimum_votes
).astype(int)


# Normalize component scores
# for a combined severity signal.

def normalize(
    values: np.ndarray,
) -> np.ndarray:

    minimum = np.min(values)
    maximum = np.max(values)

    if maximum == minimum:
        return np.zeros_like(
            values
        )

    return (
        values - minimum
    ) / (
        maximum - minimum
    )


combined_score = (
    normalize(zscore_scores)
    + normalize(ewma_scores)
    + normalize(iforest_scores)
) / 3.0


output = features.with_columns(
    [
        pl.Series(
            "zscore_anomaly_score",
            zscore_scores,
        ),

        pl.Series(
            "zscore_anomaly",
            zscore_flags,
        ),

        pl.Series(
            "ewma_anomaly_score",
            ewma_scores,
        ),

        pl.Series(
            "ewma_anomaly",
            ewma_flags,
        ),

        pl.Series(
            "iforest_anomaly_score",
            iforest_scores,
        ),

        pl.Series(
            "iforest_anomaly",
            iforest_flags,
        ),

        pl.Series(
            "anomaly_votes",
            votes,
        ),

        pl.Series(
            "anomaly_score",
            combined_score,
        ),

        pl.Series(
            "is_anomaly",
            ensemble_flag,
        ),
    ]
)


output_path = Path(
    config[
        "output"
    ][
        "anomaly_scores"
    ][
        "path"
    ]
)

output_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

output.write_parquet(
    output_path
)


model_path = Path(
    config[
        "output"
    ][
        "model"
    ][
        "path"
    ]
)

model_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

joblib.dump(
    isolation_detector,
    model_path,
)


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 5 ANOMALY TRAINING"
)
print("=" * 64)

print(
    "Rows:",
    output.height,
)

print(
    "Anomalies:",
    int(
        output[
            "is_anomaly"
        ].sum()
    ),
)

print(
    "Z-score:",
    int(
        output[
            "zscore_anomaly"
        ].sum()
    ),
)

print(
    "EWMA:",
    int(
        output[
            "ewma_anomaly"
        ].sum()
    ),
)

print(
    "Isolation Forest:",
    int(
        output[
            "iforest_anomaly"
        ].sum()
    ),
)

print(
    "Output:",
    output_path,
)

print(
    "Model:",
    model_path,
)

print()

print(
    "PHASE 5 ANOMALY TRAINING: PASSED"
)