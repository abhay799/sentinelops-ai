import asyncio

import httpx

from sentinelops.core.event_loop import sentinelops_loop_factory
from sentinelops.db.postgres import check_postgres, close_postgres
from sentinelops.db.redis import check_redis, close_redis
from sentinelops.main import app
from sentinelops.messaging.kafka import check_kafka
from sentinelops.services.registry import get_service_registry


async def main() -> None:
    failed = False

    print()
    print("=" * 60)
    print(" SENTINELOPS AI - PHASE 1 PREFLIGHT")
    print("=" * 60)

    print("\n[Service Registry]")

    registry = get_service_registry()

    if registry:
        print(f"[PASS] Service registry ({len(registry)} services)")
    else:
        print("[FAIL] Service registry")
        failed = True

    print("\n[Infrastructure Connectivity]")

    postgres_ok, redis_ok, kafka_ok = await asyncio.gather(
        check_postgres(),
        check_redis(),
        check_kafka(),
    )

    checks = {
        "PostgreSQL": postgres_ok,
        "Redis": redis_ok,
        "Kafka": kafka_ok,
    }

    for name, result in checks.items():
        if result:
            print(f"[PASS] {name}")
        else:
            print(f"[FAIL] {name}")
            failed = True

    print("\n[API]")

    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://sentinelops.preflight",
    ) as client:
        endpoints = [
            "/",
            "/live",
            "/ready",
            "/system",
            "/services",
            "/incidents",
            "/telemetry",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)

            if response.status_code < 500:
                print(
                    f"[PASS] {endpoint} "
                    f"HTTP {response.status_code}"
                )
            else:
                print(
                    f"[FAIL] {endpoint} "
                    f"HTTP {response.status_code}"
                )
                failed = True

    await close_redis()
    await close_postgres()

    print()
    print("=" * 60)

    if failed:
        print("PHASE 1 PREFLIGHT: FAILED")
        raise SystemExit(1)

    print("PHASE 1 PREFLIGHT: PASSED")
    print("=" * 60)


asyncio.run(
    main(),
    loop_factory=sentinelops_loop_factory,
)