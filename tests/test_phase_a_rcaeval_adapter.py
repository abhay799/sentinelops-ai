from pathlib import Path

import polars as pl
import pytest

from sentinelops.evaluation.rcaeval_adapter import (
    derive_pre_injection_topology,
    load_rcaeval_traces,
    metric_services_from_columns,
    normalize_trace_service,
)


def test_metric_parser_splits_from_right():
    services = metric_services_from_columns(
        [
            "time",
            "checkoutservice_cpu",
            "frontend_latency-90",
            "frontend-external_workload",
        ]
    )

    assert services == {
        "checkoutservice",
        "frontend",
        "frontend-external",
    }


def test_trace_service_suffix_normalization():
    metric_services = {
        "frontend",
        "checkoutservice",
    }

    assert (
        normalize_trace_service(
            "checkoutservice",
            metric_services,
        )
        == "checkoutservice"
    )

    assert (
        normalize_trace_service(
            "frontendservice",
            metric_services,
        )
        == "frontend"
    )


def test_unknown_trace_service_fails_closed():
    with pytest.raises(
        ValueError,
        match="Cannot deterministically map",
    ):
        normalize_trace_service(
            "mysteryservice",
            {"frontend"},
        )


def test_topology_uses_pre_injection_traces():
    metrics = pl.DataFrame(
        {
            "time": [1, 2, 3],
            "frontend_cpu": [1.0, 1.0, 1.0],
            "checkoutservice_cpu": [1.0, 1.0, 1.0],
            "redis_cpu": [1.0, 1.0, 1.0],
        }
    )

    traces = pl.DataFrame(
        {
            "traceID": [
                "t1",
                "t1",
                "t2",
                "t2",
            ],
            "spanID": [
                "p1",
                "c1",
                "p2",
                "c2",
            ],
            "parentSpanID": [
                None,
                "p1",
                None,
                "p2",
            ],
            "serviceName": [
                "frontendservice",
                "checkoutservice",
                "checkoutservice",
                "frontendservice",
            ],
            "startTimeMillis": [
                1000,
                1100,
                3000,
                3100,
            ],
        }
    )

    result = derive_pre_injection_topology(
        metrics=metrics,
        traces=traces,
        inject_time_s=2,
    )

    assert result.edges == (
        (
            "frontend",
            "checkoutservice",
        ),
    )

    assert (
        result.metric_only_services
        == ("redis",)
    )


def test_missing_parent_is_recorded_not_invented():
    metrics = pl.DataFrame(
        {
            "time": [1, 2],
            "frontend_cpu": [1.0, 1.0],
        }
    )

    traces = pl.DataFrame(
        {
            "traceID": ["t1"],
            "spanID": ["child"],
            "parentSpanID": ["missing"],
            "serviceName": [
                "frontendservice"
            ],
            "startTimeMillis": [1000],
        }
    )

    result = derive_pre_injection_topology(
        metrics=metrics,
        traces=traces,
        inject_time_s=2,
    )

    assert (
        result.unresolved_parent_count
        == 1
    )

    assert result.edges == ()


def test_duplicate_trace_keys_fail():
    metrics = pl.DataFrame(
        {
            "time": [1],
            "frontend_cpu": [1.0],
        }
    )

    traces = pl.DataFrame(
        {
            "traceID": ["t1", "t1"],
            "spanID": ["s1", "s1"],
            "parentSpanID": [None, None],
            "serviceName": [
                "frontendservice",
                "frontendservice",
            ],
            "startTimeMillis": [
                1000,
                1001,
            ],
        }
    )

    with pytest.raises(
        ValueError,
        match="Duplicate",
    ):
        derive_pre_injection_topology(
            metrics=metrics,
            traces=traces,
            inject_time_s=2,
        )


def test_identical_trace_duplicates_are_removed_with_null_nan_equal(
    tmp_path: Path,
):
    metrics = pl.DataFrame(
        {
            "time": [1],
            "frontend_cpu": [1.0],
        }
    )
    trace_path = tmp_path / "traces.parquet"
    pl.DataFrame(
        {
            "traceID": ["t1", "t1"],
            "spanID": ["s1", "s1"],
            "parentSpanID": [None, None],
            "serviceName": [
                "frontendservice",
                "frontendservice",
            ],
            "startTimeMillis": [1000, 1000],
            "duration": [float("nan"), float("nan")],
            "attributes": [None, None],
        }
    ).write_parquet(trace_path)

    traces = load_rcaeval_traces(trace_path)
    assert traces.schema["traceID"] == pl.String
    assert traces.schema["spanID"] == pl.String
    assert traces.schema["parentSpanID"] == pl.String

    result = derive_pre_injection_topology(
        metrics=metrics,
        traces=traces,
        inject_time_s=2,
    )
    stats = result.trace_duplicate_stats
    assert stats.duplicate_key_count == 1
    assert stats.duplicate_row_count == 2
    assert stats.removed_row_count == 1
    assert stats.conflicting_duplicate_found is False


def test_conflicting_duplicate_error_is_specific():
    metrics = pl.DataFrame(
        {
            "time": [1, 2],
            "frontend_cpu": [1.0, 1.0],
        }
    )
    traces = pl.DataFrame(
        {
            "traceID": ["t1", "t1"],
            "spanID": ["s1", "s1"],
            "parentSpanID": ["p0", "p0"],
            "serviceName": [
                "frontendservice",
                "frontendservice",
            ],
            "startTimeMillis": [1000, 1001],
        }
    )

    with pytest.raises(
        ValueError,
        match=r"^Conflicting Duplicate \(traceID, spanID\)",
    ):
        derive_pre_injection_topology(
            metrics=metrics,
            traces=traces,
            inject_time_s=2,
        )


REAL_RE2OB_CASE = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e/"
    "re2ob_checkoutservice_cpu_1"
)


@pytest.mark.skipif(
    not REAL_RE2OB_CASE.exists(),
    reason="Local pinned RE2-OB benchmark case not available",
)
def test_real_no_duplicate_topology_edges_unchanged_by_trace_key_cast():
    metrics = pl.read_parquet(
        REAL_RE2OB_CASE / "metrics.parquet"
    )
    raw_traces = pl.read_parquet(
        REAL_RE2OB_CASE / "traces.parquet"
    )
    loaded_traces = load_rcaeval_traces(
        REAL_RE2OB_CASE / "traces.parquet"
    )
    inject = int(
        (REAL_RE2OB_CASE / "inject_time.txt")
        .read_text()
        .strip()
    )

    before = derive_pre_injection_topology(
        metrics,
        raw_traces,
        inject,
    )
    after = derive_pre_injection_topology(
        metrics,
        loaded_traces,
        inject,
    )

    assert before.trace_duplicate_stats.duplicate_key_count == 0
    assert after.trace_duplicate_stats.duplicate_key_count == 0
    assert before.edges == after.edges
