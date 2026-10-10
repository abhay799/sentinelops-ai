from __future__ import annotations

import argparse
import asyncio

from sentinelops.chaos.registered_harness import run_registered_train


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    run_dir = asyncio.run(run_registered_train(args.run_id))
    print(run_dir)


if __name__ == "__main__":
    main()
