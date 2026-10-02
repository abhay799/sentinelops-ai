from __future__ import annotations

from dataclasses import dataclass
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
class TopologyValidation:
    edges: tuple[tuple[str, str], ...]
    unresolved_parent_count: int
    metric_only_services: tuple[str, ...]
    service_mapping: tuple[tuple[str, str], ...]


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


def _validate_trace_keys(
    traces: pl.DataFrame,
) -> None:
    duplicates = (
        traces
        .select(
            [
                "traceID",
                "spanID",
            ]
        )
        .is_duplicated()
        .sum()
    )

    if int(duplicates) > 0:
        raise ValueError(
            "Duplicate (traceID, spanID) identifiers "
            "found in RCAEval traces"
        )


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
    _validate_trace_keys(traces)

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
    )
