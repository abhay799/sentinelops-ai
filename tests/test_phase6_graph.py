from pathlib import Path

from sentinelops.graph.service_graph import (
    ServiceDependencyGraph,
)


def graph():
    return (
        ServiceDependencyGraph
        .from_topology_file(
            Path("configs/topology.yaml")
        )
    )


def test_graph_is_valid():
    service_graph = graph()

    service_graph.validate()

    assert len(
        service_graph.services()
    ) == 7


def test_gateway_dependencies():
    service_graph = graph()

    dependencies = (
        service_graph.dependencies(
            "api-gateway"
        )
    )

    assert "order-service" in dependencies
    assert "user-service" in dependencies
    assert "auth-service" in dependencies


def test_payment_failure_affects_order_and_gateway():
    service_graph = graph()

    upstream = (
        service_graph.upstream(
            "payment-service"
        )
    )

    assert "order-service" in upstream
    assert "api-gateway" in upstream


def test_payment_propagation_distance():
    service_graph = graph()

    distances = (
        service_graph.propagation_distances(
            "payment-service"
        )
    )

    assert distances["order-service"] == 1
    assert distances["api-gateway"] == 2


def test_risk_decays_with_distance():
    service_graph = graph()

    risk = (
        service_graph.risk_propagation(
            "payment-service",
            base_risk=1.0,
            decay=0.6,
        )
    )

    assert (
        risk["order-service"]
        >
        risk["api-gateway"]
    )


def test_shortest_dependency_path():
    service_graph = graph()

    path = (
        service_graph.shortest_path(
            "api-gateway",
            "payment-service",
        )
    )

    assert path == [
        "api-gateway",
        "order-service",
        "payment-service",
    ]
