import asyncio
import json
from pathlib import Path

from aiokafka import AIOKafkaConsumer


class RawTelemetrySink:
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        output_path: Path,
    ) -> None:
        self.output_path = output_path

        self.consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap_servers,
            auto_offset_reset="latest",
            enable_auto_commit=False,
            group_id=None,
        )

    async def start(self) -> None:
        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        await self.consumer.start()

    async def stop(self) -> None:
        await self.consumer.stop()

    def persist(self, event: dict) -> None:
        with self.output_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    event,
                    separators=(",", ":"),
                )
                + "\n"
            )

    async def capture_until(
        self,
        expected_types: set[str],
        timeout_seconds: float = 30.0,
    ) -> set[str]:
        observed: set[str] = set()

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds

        while expected_types - observed:
            remaining = deadline - loop.time()

            if remaining <= 0:
                break

            try:
                message = await asyncio.wait_for(
                    self.consumer.getone(),
                    timeout=remaining,
                )
            except TimeoutError:
                break

            event = json.loads(
                message.value.decode("utf-8")
            )

            self.persist(event)

            telemetry_type = event.get(
                "telemetry_type"
            )

            if telemetry_type:
                observed.add(telemetry_type)

        return observed