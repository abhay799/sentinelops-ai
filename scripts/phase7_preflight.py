from pathlib import Path

import polars as pl

INCIDENTS = Path(
    "data/processed/incidents/"
    "incidents_v1.parquet"
)

MEMBERS = Path(
    "data/processed/incidents/"
    "incident_members_v1.parquet"
)

INTELLIGENCE = Path(
    "data/processed/incidents/"
    "incident_intelligence_v1.parquet"
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
    " SENTINELOPS AI - PHASE 7 PREFLIGHT"
)
print("=" * 64)


print("\n[Incident Artifacts]")


if INCIDENTS.exists():
    passed(
        "Incident dataset"
    )
else:
    failed_check(
        "Incident dataset"
    )


if MEMBERS.exists():
    passed(
        "Incident membership dataset"
    )
else:
    failed_check(
        "Incident membership dataset"
    )


if INTELLIGENCE.exists():
    passed(
        "Incident intelligence dataset"
    )
else:
    failed_check(
        "Incident intelligence dataset"
    )


if INTELLIGENCE.exists():

    data = pl.read_parquet(
        INTELLIGENCE
    )

    required = {
        "incident_id",
        "primary_service",
        "severity",
        "confidence",
        "evidence_count",
        "evidence",
        "affected_upstream_services",
        "correlation_basis",
    }

    missing = (
        required
        - set(data.columns)
    )

    if not missing:
        passed(
            "Required intelligence columns"
        )
    else:
        failed_check(
            f"Missing columns: "
            f"{sorted(missing)}"
        )

    if data.height > 0:
        passed(
            f"Incident count "
            f"({data.height})"
        )
    else:
        failed_check(
            "No correlated incidents"
        )

    if (
        data[
            "confidence"
        ].max()
        > 0
    ):
        passed(
            "Incident confidence"
        )
    else:
        failed_check(
            "Incident confidence"
        )

    if (
        data[
            "evidence_count"
        ].sum()
        > 0
    ):
        passed(
            "Incident evidence"
        )
    else:
        failed_check(
            "Incident evidence"
        )

    impacted = (
        data
        .filter(
            pl.col(
                "affected_upstream_services"
            )
            .list.len()
            > 0
        )
    )

    if impacted.height > 0:
        passed(
            "Graph impact enrichment"
        )
    else:
        failed_check(
            "Graph impact enrichment"
        )


print()
print("=" * 64)


if failed:

    print(
        "PHASE 7 PREFLIGHT: FAILED"
    )

    print("=" * 64)

    raise SystemExit(1)


print(
    "PHASE 7 PREFLIGHT: PASSED"
)

print("=" * 64)
