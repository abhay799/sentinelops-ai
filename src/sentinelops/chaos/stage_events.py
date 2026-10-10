from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

STAGE_NAMES = {
    "detection",
    "correlation",
    "rca",
    "challenge",
    "plan",
    "guard_decision",
    "human_authorization",
    "remediation",
    "verification",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def write_stage_event(
    run_dir: Path, stage: str, details: dict[str, object] | None = None
) -> datetime:
    if stage not in STAGE_NAMES:
        raise ValueError(f"unknown stage: {stage}")
    timestamp = utc_now()
    payload = {
        "stage": stage,
        "timestamp": timestamp.isoformat(),
        "clock": "host_utc",
        "details": details or {},
    }
    path = run_dir / f"{stage}.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return timestamp
