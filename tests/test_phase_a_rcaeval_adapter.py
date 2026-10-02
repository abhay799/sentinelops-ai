import polars as pl
import pytest

from sentinelops.evaluation.rcaeval_adapter import (
    derive_pre_injection_topology,
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
