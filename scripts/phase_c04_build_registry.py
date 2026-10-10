from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinelops.chaos.registry import build_registry


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/C/C04_run_registry.json"),
    )
    args = parser.parse_args()

    payload = build_registry()
    args.output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    args.output.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
