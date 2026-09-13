import asyncio

import httpx

from sentinelops.core.event_loop import sentinelops_loop_factory
from sentinelops.main import app
from sentinelops.schemas.events import InternalEvent, InternalEventType
from sentinelops.services.registry import get_service, get_service_registry


def run_async(coro):
    return asyncio.run(
        coro,
        loop_factory=sentinelops_loop_factory,
    )


async def request(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://sentinelops.test",
    ) as client:
        return await client.get(path)


def test_service_registry_loaded():
    registry = get_service_registry()

    assert len(registry) >= 1

    payment = get_service("payment-service")

    assert payment is not None
    assert payment.criticality.value == "critical"


def test_internal_event_contract():
    event = InternalEvent(
        event_type=InternalEventType.INCIDENT_CREATED,
        source_service="sentinelops-api",
        correlation_id="INC-001",
        payload={"status": "test"},
    )

    assert event.source_service == "sentinelops-api"
    assert event.event_id is not None


def test_live_endpoint():
    response = run_async(request("/live"))

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_system_endpoint():
    response = run_async(request("/system"))

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "SentinelOps AI"
    assert body["sentinelguard"]["auto_execute"] is False


def test_services_endpoint():
    response = run_async(request("/services"))

    assert response.status_code == 200
    assert response.json()["count"] >= 1


def test_readiness_endpoint():
    response = run_async(request("/ready"))

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ready"
    assert body["components"]["postgres"] is True
    assert body["components"]["redis"] is True
    assert body["components"]["kafka"] is True