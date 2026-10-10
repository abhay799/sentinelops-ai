from __future__ import annotations

import argparse
import json
from pathlib import Path

from sentinelops.chaos.analysis import analyze_evidence_root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--allow-non-registry",
        action="store_true",
        help="Development/testing only; never use for registered reporting.",
    )
    args = parser.parse_args()

    payload = analyze_evidence_root(
        args.evidence_root,
        allow_non_registry=args.allow_non_registry,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
