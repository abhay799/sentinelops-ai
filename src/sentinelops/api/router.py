import asyncio

from fastapi import APIRouter, Response, status

from sentinelops.core.config import get_settings
from sentinelops.db.postgres import check_postgres
from sentinelops.db.redis import check_redis
from sentinelops.messaging.kafka import check_kafka
from sentinelops.services.registry import get_service_registry

router = APIRouter()

settings = get_settings()


@router.get("/live")
async def live() -> dict[str, str]:
    return {
        "status": "alive",
        "service": "sentinelops-api",
    }


@router.get("/ready")
async def ready(response: Response) -> dict[str, object]:
    postgres_ok, redis_ok, kafka_ok = await asyncio.gather(
        check_postgres(),
        check_redis(),
        check_kafka(),
    )

    components = {
        "postgres": postgres_ok,
        "redis": redis_ok,
        "kafka": kafka_ok,
    }

    is_ready = all(components.values())

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not_ready",
        "components": components,
    }


@router.get("/system")
async def system() -> dict[str, object]:
    return {
        "name": "SentinelOps AI",
        "version": "0.1.0",
        "environment": settings.SENTINELOPS_ENV,
        "sentinelguard": {
            "mode": settings.SENTINELGUARD_MODE,
            "auto_execute": settings.SENTINELGUARD_AUTO_EXECUTE,
        },
    }


@router.get("/services")
async def services() -> dict[str, object]:
    registry = get_service_registry()

    return {
        "count": len(registry),
        "services": [
            service.model_dump(mode="json")
            for service in registry
        ],
    }


@router.get("/incidents")
async def incidents() -> dict[str, object]:
    return {
        "count": 0,
        "items": [],
        "state": "foundation_only",
        "implementation_phase": 7,
    }


@router.get("/telemetry")
async def telemetry() -> dict[str, object]:
    return {
        "state": "foundation_only",
        "implementation_phase": 3,
    }
