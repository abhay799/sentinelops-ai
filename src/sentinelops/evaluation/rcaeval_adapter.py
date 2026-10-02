from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import polars as pl

REQUIRED_TRACE_COLUMNS = {
    "traceID",
    "spanID",
    "parentSpanID",
    "serviceName",
    "startTimeMillis",
}


@dataclass(frozen=True)
class TraceDuplicateStats:
    duplicate_key_count: int
    duplicate_row_count: int
    removed_row_count: int
    conflicting_duplicate_found: bool


@dataclass(frozen=True)
class TopologyValidation:
    edges: tuple[tuple[str, str], ...]
    unresolved_parent_count: int
    metric_only_services: tuple[str, ...]
    service_mapping: tuple[tuple[str, str], ...]
    trace_duplicate_stats: TraceDuplicateStats


def metric_services_from_columns(
    columns: Iterable[str],
) -> set[str]:
    services: set[str] = set()

    for column in columns:
        if column == "time":
            continue

        if "_" not in column:
            raise ValueError(
                f"Unparseable RCAEval metric column: {column}"
            )

        service, _metric = column.rsplit("_", 1)

        if not service:
            raise ValueError(
                f"Missing service name in metric column: {column}"
            )

        services.add(service)

    if not services:
        raise ValueError(
            "No RCAEval metric services found"
        )

    return services


def normalize_trace_service(
    name: str,
    metric_services: set[str],
) -> str:
    if name in metric_services:
        return name

    if name.endswith("service"):
        stripped = name[:-7]

        if stripped in metric_services:
            return stripped

    raise ValueError(
        "Cannot deterministically map trace service "
        f"{name!r} to metric service vocabulary"
    )


def load_rcaeval_traces(
    path: str | Path,
) -> pl.DataFrame:
    return (
        pl.read_parquet(path)
        .with_columns(
            [
                pl.col("traceID").cast(pl.Utf8),
                pl.col("spanID").cast(pl.Utf8),
                pl.col("parentSpanID").cast(pl.Utf8),
            ]
        )
    )


def _validate_trace_schema(
    traces: pl.DataFrame,
) -> None:
    missing = (
        REQUIRED_TRACE_COLUMNS
        - set(traces.columns)
    )

    if missing:
        raise ValueError(
            "Missing RCAEval trace columns: "
            + ", ".join(sorted(missing))
        )


def clean_exact_trace_duplicates(
    traces: pl.DataFrame,
) -> tuple[pl.DataFrame, TraceDuplicateStats]:
    key_counts = (
        traces.group_by(["traceID", "spanID"])
        .len()
        .filter(pl.col("len") > 1)
    )
    duplicate_key_count = key_counts.height
    duplicate_row_count = int(
        key_counts["len"].sum()
        if duplicate_key_count
        else 0
    )

    cleaned = traces.unique(maintain_order=True)
    remaining_duplicate_rows = int(
        cleaned.select(["traceID", "spanID"])
        .is_duplicated()
        .sum()
    )
    conflicting = remaining_duplicate_rows > 0

    if conflicting:
        raise ValueError(
            "Conflicting Duplicate (traceID, spanID) "
            "identifiers found in RCAEval traces"
        )

    stats = TraceDuplicateStats(
        duplicate_key_count=duplicate_key_count,
        duplicate_row_count=duplicate_row_count,
        removed_row_count=traces.height - cleaned.height,
        conflicting_duplicate_found=False,
    )
    return cleaned, stats


def derive_pre_injection_topology(
    metrics: pl.DataFrame,
    traces: pl.DataFrame,
    inject_time_s: int,
) -> TopologyValidation:
    if "time" not in metrics.columns:
        raise ValueError(
            "RCAEval metrics are missing time column"
        )

    _validate_trace_schema(traces)
    traces, duplicate_stats = clean_exact_trace_duplicates(
        traces
    )

    metric_services = (
        metric_services_from_columns(
            metrics.columns
        )
    )

    raw_trace_services = sorted(
        str(value)
        for value
        in traces[
            "serviceName"
        ]
        .drop_nulls()
        .unique()
        .to_list()
    )

    mapping: dict[str, str] = {}

    for name in raw_trace_services:
        mapping[name] = (
            normalize_trace_service(
                name,
                metric_services,
            )
        )

    pre = traces.filter(
        (
            pl.col("startTimeMillis")
            // 1000
        )
        < inject_time_s
    )

    lookup = (
        pre
        .select(
            [
                "traceID",
                "spanID",
                "serviceName",
            ]
        )
        .rename(
            {
                "spanID":
                    "parentSpanID",
                "serviceName":
                    "parentService",
            }
        )
    )

    linked = (
        pre
        .select(
            [
                "traceID",
                "spanID",
                "parentSpanID",
                "serviceName",
            ]
        )
        .join(
            lookup,
            on=[
                "traceID",
                "parentSpanID",
            ],
            how="left",
        )
    )

    unresolved = linked.filter(
        pl.col("parentSpanID").is_not_null()
        & pl.col("parentService").is_null()
    )

    full_keys = set(
        traces
        .select(
            [
                "traceID",
                "spanID",
            ]
        )
        .iter_rows()
    )

    unresolved_that_exist_full = 0

    for trace_id, parent_span_id in (
        unresolved
        .select(
            [
                "traceID",
                "parentSpanID",
            ]
        )
        .iter_rows()
    ):
        if (
            trace_id,
            parent_span_id,
        ) in full_keys:
            unresolved_that_exist_full += 1

    if unresolved_that_exist_full:
        raise ValueError(
            "A parent span excluded by the pre-injection "
            "boundary exists elsewhere in full traces; "
            "topology derivation is ambiguous"
        )

    raw_edges = (
        linked
        .filter(
            pl.col("parentService").is_not_null()
            & (
                pl.col("parentService")
                != pl.col("serviceName")
            )
        )
        .select(
            [
                "parentService",
                "serviceName",
            ]
        )
        .unique()
    )

    normalized_edges: set[
        tuple[str, str]
    ] = set()

    for parent, child in (
        raw_edges.iter_rows()
    ):
        parent_normalized = (
            normalize_trace_service(
                str(parent),
                metric_services,
            )
        )

        child_normalized = (
            normalize_trace_service(
                str(child),
                metric_services,
            )
        )

        if (
            parent_normalized
            != child_normalized
        ):
            normalized_edges.add(
                (
                    parent_normalized,
                    child_normalized,
                )
            )

    normalized_trace_services = {
        mapping[name]
        for name
        in mapping
    }

    metric_only = tuple(
        sorted(
            metric_services
            - normalized_trace_services
        )
    )

    return TopologyValidation(
        edges=tuple(
            sorted(
                normalized_edges
            )
        ),
        unresolved_parent_count=(
            unresolved.height
        ),
        metric_only_services=metric_only,
        service_mapping=tuple(
            sorted(
                mapping.items()
            )
        ),
        trace_duplicate_stats=duplicate_stats,
    )
