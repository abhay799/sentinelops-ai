from pathlib import Path

import polars as pl
import yaml

from sentinelops.features.temporal import (
    validate_point_in_time,
)

SERVICE_FEATURES = Path(
    "data/processed/features/"
    "service_features_v1.parquet"
)

TEMPORAL_FEATURES = Path(
    "data/processed/features/"
    "temporal_features_v1.parquet"
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

    print(
        f"[FAIL] {message}"
    )

    failed = True


print()
print("=" * 64)
print(
    " SENTINELOPS AI - PHASE 4 PREFLIGHT"
)
print("=" * 64)


# ============================================================
# Feature configuration
# ============================================================

print("\n[Configuration]")

with open(
    "configs/features.yaml",
    encoding="utf-8",
) as file:
    config = yaml.safe_load(file)

required = set(
    config[
        "feature_platform"
    ][
        "required_features"
    ]
)

passed("Feature configuration")


# ============================================================
# Service features
# ============================================================

print("\n[Service Features]")

if not SERVICE_FEATURES.exists():

    failed_check(
        "Service feature dataset"
    )

else:

    service_features = (
        pl.read_parquet(
            SERVICE_FEATURES
        )
    )

    if service_features.height == 7:
        passed(
            "7 service feature rows"
        )
    else:
        failed_check(
            f"Service rows "
            f"{service_features.height}/7"
        )

    available = set(
        service_features.columns
    )

    missing = (
        required
        - available
    )

    if not missing:
        passed(
            "Required service features"
        )
    else:
        failed_check(
            f"Missing features: "
            f"{sorted(missing)}"
        )

    if (
        service_features
        .select(
            pl.col(
                "dependency_count"
            ).sum()
        )
        .item()
        > 0
    ):
        passed(
            "Dependency features"
        )
    else:
        failed_check(
            "Dependency features"
        )

    if (
        service_features[
            "memory_rss_bytes"
        ].max()
        > 0
    ):
        passed(
            "Infrastructure features"
        )
    else:
        failed_check(
            "Infrastructure features"
        )


# ============================================================
# Temporal features
# ============================================================

print("\n[Temporal Features]")

if not TEMPORAL_FEATURES.exists():

    failed_check(
        "Temporal feature dataset"
    )

else:

    temporal = pl.read_parquet(
        TEMPORAL_FEATURES
    )

    if temporal.height > 0:
        passed(
            f"Temporal rows "
            f"({temporal.height})"
        )
    else:
        failed_check(
            "Temporal rows"
        )

    if (
        temporal[
            "service"
        ].n_unique()
        == 7
    ):
        passed(
            "Temporal coverage: 7 services"
        )
    else:
        failed_check(
            "Temporal service coverage"
        )

    validate_point_in_time(
        temporal
    )

    passed(
        "Point-in-time leakage validation"
    )


# ============================================================
# Injected failure signal
# ============================================================

print(
    "\n[Failure Signal Validation]"
)

payment = temporal.filter(
    pl.col("service")
    == "payment-service"
)

if (
    payment[
        "latency_p95_300s"
    ].max()
    >= 200
):
    passed(
        "Payment latency signal"
    )
else:
    failed_check(
        "Payment latency signal"
    )


if (
    payment[
        "error_rate_300s"
    ].max()
    > 0
):
    passed(
        "Payment error signal"
    )
else:
    failed_check(
        "Payment error signal"
    )


# ============================================================
# Final result
# ============================================================

print()
print("=" * 64)

if failed:

    print(
        "PHASE 4 PREFLIGHT: FAILED"
    )

    print("=" * 64)

    raise SystemExit(1)


print(
    "PHASE 4 PREFLIGHT: PASSED"
)

print("=" * 64)