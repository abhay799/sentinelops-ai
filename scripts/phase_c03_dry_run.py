from __future__ import annotations

import argparse

from sentinelops.chaos.harness import SCENARIOS, run_dry_run


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), required=True)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(run_dry_run(args.scenario, args.seed))


if __name__ == "__main__":
    main()
