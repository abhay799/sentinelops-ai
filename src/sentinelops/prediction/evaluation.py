from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)


def classification_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
) -> dict[str, float | int]:

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

    tn, fp, fn, tp = confusion_matrix(
        y_true,
        y_pred,
        labels=[0, 1],
    ).ravel()

    fpr = (
        fp / (fp + tn)
        if (fp + tn) > 0
        else 0.0
    )

    return {
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "false_positive_rate": float(fpr),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn),
    }


def choose_temporal_split(
    data: pl.DataFrame,
) -> int:

    if data.height < 8:
        raise ValueError(
            "Insufficient observations "
            "for temporal train/test split"
        )

    candidates = [
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
    ]

    labels = (
        data[
            "future_anomaly"
        ]
        .to_numpy()
        .astype(int)
    )

    for fraction in candidates:

        split = int(
            data.height * fraction
        )

        if split <= 0:
            continue

        if split >= data.height:
            continue

        train_labels = labels[:split]
        test_labels = labels[split:]

        if (
            len(
                np.unique(
                    train_labels
                )
            )
            >= 2
            and test_labels.sum() > 0
        ):
            return split

    for fraction in candidates:

        split = int(
            data.height * fraction
        )

        train_labels = labels[:split]

        if (
            len(
                np.unique(
                    train_labels
                )
            )
            >= 2
        ):
            return split

    raise ValueError(
        "Training window does not contain "
        "both failure and non-failure labels"
    )


def average_lead_events(
    data: pl.DataFrame,
    prediction_column: str,
) -> float:

    true_positive_warnings = (
        data
        .filter(
            (
                pl.col(
                    prediction_column
                )
                == 1
            )
            &
            (
                pl.col(
                    "future_anomaly"
                )
                == 1
            )
            &
            pl.col(
                "lead_events"
            ).is_not_null()
        )
    )

    if true_positive_warnings.is_empty():
        return 0.0

    return float(
        true_positive_warnings[
            "lead_events"
        ].mean()
    )


def validate_prediction_safety(
    data: pl.DataFrame,
) -> list[str]:

    errors: list[str] = []

    invalid_warning = data.filter(
        (
            pl.col(
                "warning_flag"
            )
            == 1
        )
        &
        (
            pl.col(
                "current_is_anomaly"
            )
            == 1
        )
    )

    if invalid_warning.height > 0:
        errors.append(
            "Warning emitted on an already "
            "anomalous observation"
        )

    invalid_scores = data.filter(
        (
            pl.col(
                "early_warning_score"
            )
            < 0
        )
        |
        (
            pl.col(
                "early_warning_score"
            )
            > 1
        )
    )

    if invalid_scores.height > 0:
        errors.append(
            "Early-warning score outside [0,1]"
        )

    return errors
