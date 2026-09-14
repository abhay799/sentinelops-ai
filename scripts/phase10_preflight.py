import json
from pathlib import Path

import joblib
import polars as pl

from sentinelops.prediction.evaluation import (
    validate_prediction_safety,
)

EARLY_WARNING = Path(
    "data/processed/prediction/early_warning_v1.parquet"
)

PREDICTIONS = Path(
    "data/processed/prediction/supervised_predictions_v1.parquet"
)

EVALUATION = Path(
    "data/processed/prediction/evaluation_v1.json"
)

MODEL = Path(
    "models/prediction/failure_predictor_v1.joblib"
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
print(" SENTINELOPS AI - PHASE 10 PREFLIGHT")
print("=" * 64)


print("\n[Early Warning]")

if EARLY_WARNING.exists():

    warnings = pl.read_parquet(
        EARLY_WARNING
    )

    passed("Early-warning artifact")

    errors = validate_prediction_safety(
        warnings
    )

    if not errors:
        passed("Leakage/safety validation")
    else:
        for error in errors:
            failed_check(error)

    if warnings["future_anomaly"].sum() > 0:
        passed("Future-failure labels")
    else:
        failed_check(
            "No future-failure labels"
        )

else:
    failed_check(
        "Early-warning artifact"
    )


print("\n[Supervised Predictor]")

if PREDICTIONS.exists():

    predictions = pl.read_parquet(
        PREDICTIONS
    )

    passed("Prediction artifact")

    required = {
        "failure_probability",
        "supervised_warning",
        "future_anomaly",
        "lead_events",
    }

    missing = (
        required
        - set(predictions.columns)
    )

    if not missing:
        passed("Prediction columns")
    else:
        failed_check(
            f"Missing columns: {sorted(missing)}"
        )

    invalid = predictions.filter(
        (
            pl.col("failure_probability") < 0
        )
        |
        (
            pl.col("failure_probability") > 1
        )
    )

    if invalid.height == 0:
        passed("Probability bounds")
    else:
        failed_check(
            "Probability bounds"
        )

else:
    failed_check(
        "Prediction artifact"
    )


print("\n[Evaluation]")

if EVALUATION.exists():

    evaluation = json.loads(
        EVALUATION.read_text(
            encoding="utf-8"
        )
    )

    passed("Evaluation artifact")

    if evaluation["training"]["temporal_split"]:
        passed(
            "Temporal train/test split"
        )
    else:
        failed_check(
            "Temporal split disabled"
        )

    supervised = evaluation[
        "supervised"
    ]

    for metric in [
        "precision",
        "recall",
        "f1",
        "false_positive_rate",
    ]:

        value = float(
            supervised[metric]
        )

        if 0.0 <= value <= 1.0:
            passed(
                f"{metric} valid"
            )
        else:
            failed_check(
                f"{metric} invalid"
            )

else:
    failed_check(
        "Evaluation artifact"
    )


print("\n[Model Artifact]")

if MODEL.exists():

    artifact = joblib.load(
        MODEL
    )

    if (
        "model" in artifact
        and "features" in artifact
    ):
        passed(
            "Failure predictor model"
        )
    else:
        failed_check(
            "Invalid predictor artifact"
        )

else:
    failed_check(
        "Failure predictor model"
    )


print()
print("=" * 64)

if failed:
    print("PHASE 10 PREFLIGHT: FAILED")
    print("=" * 64)
    raise SystemExit(1)

print("PHASE 10 PREFLIGHT: PASSED")
print("=" * 64)
