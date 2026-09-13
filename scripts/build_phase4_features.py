import re
import time
from pathlib import Path

import httpx

from sentinelops.features.builder import (
    build_service_features,
    load_events,
    load_topology,
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


def metric_value(
    text: str,
    metric: str,
) -> float:

    pattern = rf"^{re.escape(metric)}\s+([0-9.eE+-]+)$"

    match = re.search(
        pattern,
        text,
        re.MULTILINE,
    )

    if not match:
        return 0.0

    return float(
        match.group(1)
    )


def snapshot() -> dict[str, dict[str, float]]:

    result = {}

    with httpx.Client(
        timeout=5.0
    ) as client:

        for service, port in SERVICES.items():

            text = client.get(
                f"http://localhost:{port}/metrics"
            ).text

            result[service] = {
                "cpu":
                    metric_value(
                        text,
                        "process_cpu_seconds_total",
                    ),

                "memory":
                    metric_value(
                        text,
                        "process_resident_memory_bytes",
                    ),
            }

    return result


before = snapshot()

started = time.perf_counter()

time.sleep(2)

after = snapshot()

elapsed = max(
    time.perf_counter() - started,
    0.001,
)


infrastructure = {}

for service in SERVICES:

    before_values = before[service]
    after_values = after[service]

    infrastructure[service] = {

        "cpu_seconds_per_second":
            max(
                (
                    after_values["cpu"]
                    - before_values["cpu"]
                )
                / elapsed,
                0.0,
            ),

        "memory_rss_bytes":
            after_values["memory"],

        "memory_growth_bytes_per_second":
            (
                after_values["memory"]
                - before_values["memory"]
            )
            / elapsed,
    }


events = load_events(
    Path(
        "data/telemetry/raw/"
        "phase4_capture.ndjson"
    )
)

topology = load_topology(
    Path("configs/topology.yaml")
)


features = build_service_features(
    events,
    topology,
    infrastructure,
)


output = Path(
    "data/processed/features/"
    "service_features_v1.parquet"
)

output.parent.mkdir(
    parents=True,
    exist_ok=True,
)

features.write_parquet(output)


print(features)

print()
print(
    "Feature rows:",
    features.height,
)

print(
    "Feature columns:",
    features.width,
)

print(
    "Output:",
    output,
)

print()
print(
    "PHASE 4 FEATURE BUILD: PASSED"
)