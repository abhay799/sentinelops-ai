from __future__ import annotations

import json
from pathlib import Path
from typing import Any

GROUND_TRUTH_ROOT = Path("evidence/C/C03_dry_runs/_ground_truth_injection_only")


def write_injection_record(run_id: str, payload: dict[str, Any]) -> Path:
    path = GROUND_TRUTH_ROOT / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path
