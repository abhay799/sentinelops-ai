from __future__ import annotations

import argparse
import asyncio

from sentinelops.chaos.registered_harness import (
    run_non_registry_dry_run,
    run_registered_train,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--run-id")
    mode.add_argument(
        "--non-registry-scenario",
        choices=("latency", "errors", "bad_deployment_rollback"),
    )
    parser.add_argument("--seed", type=int)
    parser.add_argument("--replacement-for")
    args = parser.parse_args()

    if args.non_registry_scenario is not None:
        if args.seed is None:
            parser.error("--seed is required with --non-registry-scenario")
        run_dir = run_non_registry_dry_run(
            args.non_registry_scenario,
            args.seed,
        )
    else:
        if args.seed is not None:
            parser.error("--seed is only valid with --non-registry-scenario")
        run_dir = asyncio.run(
            run_registered_train(
                args.run_id,
                replacement_for=args.replacement_for,
            )
        )

    print(run_dir)


if __name__ == "__main__":
    main()
