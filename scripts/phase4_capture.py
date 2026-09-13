import asyncio
import json
from pathlib import Path

import httpx
from aiokafka import AIOKafkaConsumer

from sentinelops.core.event_loop import (
    sentinelops_loop_factory,
)

TOPIC = "sentinelops.telemetry.raw"

OUTPUT = Path(
    "data/telemetry/raw/phase4_capture.ndjson"
)

SERVICES = {
    "api-gateway": 8100,
    "user-service": 8101,
    "order-service": 8102,
    "payment-service": 8103,
    "inventory-service": 8104,
    "notification-service": 8105,
    "auth-service": 8106,
}


async def generate_load() -> None:

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        # Normal traffic across all services.
        for _ in range(10):

            for port in SERVICES.values():

                await client.get(
                    f"http://localhost:{port}/work"
                )

        # Payment latency scenario.
        await client.post(
            "http://localhost:8103/failure-mode",
            json={
                "mode": "latency",
                "latency_ms": 300,
                "error_rate": 0,
            },
        )

        for _ in range(5):
            await client.get(
                "http://localhost:8103/work"
            )

        await client.post(
            "http://localhost:8103/failure-mode/reset"
        )

        # Payment error scenario.
        await client.post(
            "http://localhost:8103/failure-mode",
            json={
                "mode": "errors",
                "latency_ms": 0,
                "error_rate": 1.0,
            },
        )

        for _ in range(5):
            await client.get(
                "http://localhost:8103/work"
            )

        await client.post(
            "http://localhost:8103/failure-mode/reset"
        )

        # Change signal.
        await client.post(
            "http://localhost:8103/change-event",
            json={
                "change_type": "deployment",
                "description": (
                    "Phase 4 feature validation"
                ),
                "version_before": "2.7",
                "version_after": "2.8",
                "actor": "phase4-capture",
            },
        )


async def main() -> None:

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if OUTPUT.exists():
        OUTPUT.unlink()

    consumer = AIOKafkaConsumer(
        TOPIC,
        bootstrap_servers="localhost:9092",
        auto_offset_reset="latest",
        enable_auto_commit=False,
        group_id=None,
    )

    await consumer.start()

    try:

        await generate_load()

        events = []

        while True:

            try:
                message = await asyncio.wait_for(
                    consumer.getone(),
                    timeout=3.0,
                )

                event = json.loads(
                    message.value.decode(
                        "utf-8"
                    )
                )

                events.append(event)

            except TimeoutError:
                break

        with OUTPUT.open(
            "w",
            encoding="utf-8",
        ) as file:

            for event in events:

                file.write(
                    json.dumps(event)
                    + "\n"
                )

        print(
            f"Captured events: {len(events)}"
        )

        types = sorted(
            {
                event.get(
                    "telemetry_type"
                )
                for event in events
            }
        )

        print(
            "Telemetry types:",
            types,
        )

        if len(events) < 100:
            raise RuntimeError(
                "Insufficient Phase 4 telemetry"
            )

        print(
            "PHASE 4 CAPTURE: PASSED"
        )

    finally:
        await consumer.stop()


asyncio.run(
    main(),
    loop_factory=sentinelops_loop_factory,
)