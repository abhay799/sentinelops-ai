from pathlib import Path

import joblib
import polars as pl
import yaml

ANOMALY_PATH = Path(
    "data/processed/anomalies/"
    "anomaly_scores_v1.parquet"
)

MODEL_PATH = Path(
    "models/anomaly/"
    "isolation_forest_v1.joblib"
)


failed = False


def passed(message: str) -> None:
    print(
        f"[PASS] {message}"
    )


def failed_check(
    message: str,
) -> None:
    global failed

    failed = True

    print(
        f"[FAIL] {message}"
    )


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 5 PREFLIGHT"
)
print("=" * 64)


# ------------------------------------------------------------
# Config
# ------------------------------------------------------------

print("\n[Configuration]")

with open(
    "configs/anomaly.yaml",
    encoding="utf-8",
) as file:
    config = yaml.safe_load(file)

if "anomaly_detection" in config:
    passed(
        "Anomaly configuration"
    )
else:
    failed_check(
        "Anomaly configuration"
    )


# ------------------------------------------------------------
# Dataset
# ------------------------------------------------------------

print("\n[Anomaly Dataset]")

if not ANOMALY_PATH.exists():

    failed_check(
        "Anomaly score dataset"
    )

else:

    data = pl.read_parquet(
        ANOMALY_PATH
    )

    required_columns = {
        "zscore_anomaly_score",
        "zscore_anomaly",
        "ewma_anomaly_score",
        "ewma_anomaly",
        "iforest_anomaly_score",
        "iforest_anomaly",
        "anomaly_votes",
        "anomaly_score",
        "is_anomaly",
    }

    missing = (
        required_columns
        - set(data.columns)
    )

    if not missing:
        passed(
            "Required anomaly columns"
        )
    else:
        failed_check(
            f"Missing columns: "
            f"{sorted(missing)}"
        )

    if data.height > 0:
        passed(
            f"Anomaly rows ({data.height})"
        )
    else:
        failed_check(
            "Anomaly dataset empty"
        )

    anomaly_count = int(
        data[
            "is_anomaly"
        ].sum()
    )

    if anomaly_count > 0:
        passed(
            f"Detected anomalies "
            f"({anomaly_count})"
        )
    else:
        failed_check(
            "No anomalies detected"
        )


# ------------------------------------------------------------
# Model artifact
# ------------------------------------------------------------

print("\n[Model Artifact]")

if MODEL_PATH.exists():

    model = joblib.load(
        MODEL_PATH
    )

    if hasattr(
        model,
        "predict",
    ):
        passed(
            "Isolation Forest artifact"
        )
    else:
        failed_check(
            "Invalid model artifact"
        )

else:
    failed_check(
        "Isolation Forest artifact"
    )


# ------------------------------------------------------------
# Known failure signal
# ------------------------------------------------------------

print(
    "\n[Known Failure Signal]"
)

if ANOMALY_PATH.exists():

    data = pl.read_parquet(
        ANOMALY_PATH
    )

    payment = data.filter(
        pl.col("service")
        == "payment-service"
    )

    if payment.height > 0:
        passed(
            "Payment-service coverage"
        )
    else:
        failed_check(
            "Payment-service coverage"
        )

    if (
        payment[
            "anomaly_score"
        ].max()
        > 0
    ):
        passed(
            "Payment anomaly signal"
        )
    else:
        failed_check(
            "Payment anomaly signal"
        )


print()
print("=" * 64)

if failed:

    print(
        "PHASE 5 PREFLIGHT: FAILED"
    )

    print("=" * 64)

    raise SystemExit(1)


print(
    "PHASE 5 PREFLIGHT: PASSED"
)

print("=" * 64)