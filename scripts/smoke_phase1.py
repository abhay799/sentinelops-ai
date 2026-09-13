import asyncio

import httpx

from sentinelops.core.event_loop import sentinelops_loop_factory
from sentinelops.main import app


async def main() -> None:
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://sentinelops.local",
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

            print(
                f"{endpoint:<12}",
                response.status_code,
                response.json(),
            )

            if response.status_code >= 500:
                raise RuntimeError(
                    f"Smoke test failed: {endpoint}"
                )

    print()
    print("PHASE 1 API SMOKE TEST: PASSED")


asyncio.run(
    main(),
    loop_factory=sentinelops_loop_factory,
)
