import asyncio
import time

import httpx
import yaml

from sentinelops.core.event_loop import sentinelops_loop_factory

SERVICES = {
    "api-gateway": "http://localhost:8100",
    "user-service": "http://localhost:8101",
    "order-service": "http://localhost:8102",
    "payment-service": "http://localhost:8103",
    "inventory-service": "http://localhost:8104",
    "notification-service": "http://localhost:8105",
    "auth-service": "http://localhost:8106",
}


def load_expected_topology() -> dict[str, list[str]]:
    with open("configs/topology.yaml", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    return {
        service: value["depends_on"]
        for service, value in config["topology"].items()
    }


async def main() -> None:
    failed = False

    print()
    print("=" * 64)
    print(" SENTINELOPS AI - PHASE 2 PREFLIGHT")
    print("=" * 64)

    async with httpx.AsyncClient(timeout=5.0) as client:

        # ----------------------------------------------------
        # Service health
        # ----------------------------------------------------

        print("\n[Service Health]")

        for service, base_url in SERVICES.items():
            try:
                response = await client.get(f"{base_url}/live")

                if response.status_code == 200:
                    print(f"[PASS] {service}")
                else:
                    print(
                        f"[FAIL] {service} "
                        f"HTTP {response.status_code}"
                    )
                    failed = True

            except Exception as exc:
                print(
                    f"[FAIL] {service}: "
                    f"{type(exc).__name__}"
                )
                failed = True

        # ----------------------------------------------------
        # Service identities
        # ----------------------------------------------------

        print("\n[Service Identity]")

        for service, base_url in SERVICES.items():
            response = await client.get(f"{base_url}/identity")
            body = response.json()

            if body["service"] == service:
                print(f"[PASS] {service} identity")
            else:
                print(
                    f"[FAIL] {service} identity "
                    f"reported {body['service']}"
                )
                failed = True

        # ----------------------------------------------------
        # Dependency topology
        # ----------------------------------------------------

        print("\n[Dependency Topology]")

        expected_topology = load_expected_topology()

        for service, expected_dependencies in expected_topology.items():

            base_url = SERVICES[service]

            response = await client.get(
                f"{base_url}/dependencies"
            )

            actual = response.json()["dependencies"]

            if set(actual.keys()) != set(expected_dependencies):
                print(
                    f"[FAIL] {service} topology "
                    f"expected={expected_dependencies} "
                    f"actual={list(actual.keys())}"
                )
                failed = True
                continue

            unreachable = [
                dependency
                for dependency, result in actual.items()
                if not result["reachable"]
            ]

            if unreachable:
                print(
                    f"[FAIL] {service} unreachable: "
                    f"{unreachable}"
                )
                failed = True
            else:
                print(
                    f"[PASS] {service} topology"
                )

        # ----------------------------------------------------
        # Controlled latency failure
        # ----------------------------------------------------

        print("\n[Failure Injection: Latency]")

        payment = SERVICES["payment-service"]

        try:
            await client.post(
                f"{payment}/failure-mode",
                json={
                    "mode": "latency",
                    "latency_ms": 800,
                    "error_rate": 0,
                },
            )

            started = time.perf_counter()

            response = await client.get(
                f"{payment}/work"
            )

            elapsed = time.perf_counter() - started

            if (
                response.status_code == 200
                and elapsed >= 0.70
            ):
                print(
                    f"[PASS] latency injection "
                    f"({elapsed:.3f}s)"
                )
            else:
                print(
                    f"[FAIL] latency injection "
                    f"({elapsed:.3f}s)"
                )
                failed = True

        finally:
            await client.post(
                f"{payment}/failure-mode/reset"
            )

        # ----------------------------------------------------
        # Controlled error failure
        # ----------------------------------------------------

        print("\n[Failure Injection: Errors]")

        try:
            await client.post(
                f"{payment}/failure-mode",
                json={
                    "mode": "errors",
                    "latency_ms": 0,
                    "error_rate": 1.0,
                },
            )

            response = await client.get(
                f"{payment}/work"
            )

            if response.status_code == 503:
                print(
                    "[PASS] deterministic error injection"
                )
            else:
                print(
                    "[FAIL] deterministic error injection "
                    f"HTTP {response.status_code}"
                )
                failed = True

        finally:
            await client.post(
                f"{payment}/failure-mode/reset"
            )

        # ----------------------------------------------------
        # Recovery verification
        # ----------------------------------------------------

        print("\n[Recovery Verification]")

        response = await client.get(
            f"{payment}/work"
        )

        if response.status_code == 200:
            body = response.json()

            if body["failure_mode"] == "normal":
                print(
                    "[PASS] payment-service recovered"
                )
            else:
                print(
                    "[FAIL] failure mode not reset"
                )
                failed = True
        else:
            print(
                "[FAIL] payment-service did not recover"
            )
            failed = True

    print()
    print("=" * 64)

    if failed:
        print("PHASE 2 PREFLIGHT: FAILED")
        print("=" * 64)
        raise SystemExit(1)

    print("PHASE 2 PREFLIGHT: PASSED")
    print("=" * 64)


asyncio.run(
    main(),
    loop_factory=sentinelops_loop_factory,
)