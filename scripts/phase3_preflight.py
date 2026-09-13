import asyncio
import subprocess
from pathlib import Path

import httpx

from sentinelops.core.event_loop import (
    sentinelops_loop_factory,
)
from sentinelops.telemetry.raw_sink import (
    RawTelemetrySink,
)

EXPECTED_TYPES = {
    "metric",
    "log",
    "trace",
    "change",
}

OUTPUT_PATH = Path(
    "data/telemetry/raw/phase3_preflight.ndjson"
)


def pass_check(name: str) -> None:
    print(f"[PASS] {name}")


def fail_check(name: str) -> None:
    print(f"[FAIL] {name}")


async def main() -> None:
    failed = False

    print()
    print("=" * 64)
    print(" SENTINELOPS AI - PHASE 3 PREFLIGHT")
    print("=" * 64)

    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    # --------------------------------------------------------
    # OpenTelemetry Collector
    # --------------------------------------------------------

    print("\n[OpenTelemetry]")

    result = subprocess.run(
        [
            "docker",
            "inspect",
            "-f",
            "{{.State.Status}}",
            "sentinelops-otel",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.stdout.strip() == "running":
        pass_check("OpenTelemetry Collector")
    else:
        fail_check("OpenTelemetry Collector")
        failed = True

    # --------------------------------------------------------
    # Kafka raw telemetry capture
    # --------------------------------------------------------

    print("\n[Kafka Telemetry Pipeline]")

    sink = RawTelemetrySink(
        bootstrap_servers="localhost:9092",
        topic="sentinelops.telemetry.raw",
        output_path=OUTPUT_PATH,
    )

    await sink.start()

    try:
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:

            # Generate metrics/logs/traces.
            for _ in range(5):
                response = await client.get(
                    "http://localhost:8103/work"
                )

                if response.status_code != 200:
                    failed = True

            # Generate an explicit system-change event.
            change_response = await client.post(
                "http://localhost:8103/change-event",
                json={
                    "change_type": "deployment",
                    "description": (
                        "Phase 3 telemetry "
                        "validation deployment"
                    ),
                    "version_before": "2.7",
                    "version_after": "2.8",
                    "actor": "phase3-preflight",
                },
            )

            if change_response.status_code == 200:
                pass_check("Change event generation")
            else:
                fail_check("Change event generation")
                failed = True

        observed = await sink.capture_until(
            EXPECTED_TYPES,
            timeout_seconds=30.0,
        )

    finally:
        await sink.stop()

    for telemetry_type in sorted(
        EXPECTED_TYPES
    ):
        if telemetry_type in observed:
            pass_check(
                f"Kafka {telemetry_type} telemetry"
            )
        else:
            fail_check(
                f"Kafka {telemetry_type} telemetry"
            )
            failed = True

    # --------------------------------------------------------
    # Persistent raw storage
    # --------------------------------------------------------

    print("\n[Raw Telemetry Storage]")

    if OUTPUT_PATH.exists():
        line_count = sum(
            1
            for line in OUTPUT_PATH.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        )

        if line_count >= 4:
            pass_check(
                f"Raw NDJSON persistence "
                f"({line_count} events)"
            )
        else:
            fail_check("Raw NDJSON persistence")
            failed = True
    else:
        fail_check("Raw NDJSON persistence")
        failed = True

    # --------------------------------------------------------
    # Prometheus metrics
    # --------------------------------------------------------

    print("\n[Prometheus Metrics]")

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        metrics = await client.get(
            "http://localhost:8103/metrics"
        )

        if (
            metrics.status_code == 200
            and
            "sentinelops_http_requests_total"
            in metrics.text
        ):
            pass_check(
                "Service Prometheus metrics"
            )
        else:
            fail_check(
                "Service Prometheus metrics"
            )
            failed = True

        # ----------------------------------------------------
        # Prometheus targets
        # ----------------------------------------------------

        target_response = await client.get(
            "http://localhost:9090/api/v1/targets"
        )

        target_body = target_response.json()

        active_targets = (
            target_body
            .get("data", {})
            .get("activeTargets", [])
        )

        service_targets = [
            target
            for target in active_targets
            if target
            .get("labels", {})
            .get("job")
            == "sentinelops-services"
        ]

        healthy_targets = [
            target
            for target in service_targets
            if target.get("health") == "up"
        ]

        if len(healthy_targets) >= 7:
            pass_check(
                "Prometheus service targets "
                f"({len(healthy_targets)}/7 up)"
            )
        else:
            fail_check(
                "Prometheus service targets "
                f"({len(healthy_targets)}/7 up)"
            )
            failed = True

    print()
    print("=" * 64)

    if failed:
        print("PHASE 3 PREFLIGHT: FAILED")
        print("=" * 64)
        raise SystemExit(1)

    print("PHASE 3 PREFLIGHT: PASSED")
    print("=" * 64)


asyncio.run(
    main(),
    loop_factory=sentinelops_loop_factory,
)