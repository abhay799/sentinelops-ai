from pathlib import Path

import polars as pl
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

INPUT = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

data = pl.read_parquet(INPUT)


# ------------------------------------------------------------
# Ground-truth proxy
#
# Phase 4 intentionally injected latency/errors into
# payment-service. Use those known conditions as labels.
# ------------------------------------------------------------

data = data.with_columns(
    (
        (
            pl.col("service")
            == "payment-service"
        )
        &
        (
            (
                pl.col("error_rate_300s")
                > 0
            )
            |
            (
                pl.col("latency_p95_300s")
                >= 200
            )
        )
    )
    .cast(pl.Int64)
    .alias("ground_truth_anomaly")
)


y_true = (
    data[
        "ground_truth_anomaly"
    ]
    .to_numpy()
)

y_pred = (
    data[
        "is_anomaly"
    ]
    .to_numpy()
)


precision = precision_score(
    y_true,
    y_pred,
    zero_division=0,
)

recall = recall_score(
    y_true,
    y_pred,
    zero_division=0,
)

f1 = f1_score(
    y_true,
    y_pred,
    zero_division=0,
)


tn, fp, fn, tp = (
    confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    )
    .ravel()
)


false_positive_rate = (
    fp / (fp + tn)
    if (fp + tn)
    else 0.0
)


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 5 EVALUATION"
)
print("=" * 64)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall:    {recall:.4f}"
)

print(
    f"F1:        {f1:.4f}"
)

print(
    f"FPR:       {false_positive_rate:.4f}"
)

print()

print(
    f"TP={tp} FP={fp} TN={tn} FN={fn}"
)

print()


if recall == 0:
    raise RuntimeError(
        "Anomaly detector failed to detect "
        "known injected anomalies"
    )


print(
    "PHASE 5 EVALUATION: PASSED"
)