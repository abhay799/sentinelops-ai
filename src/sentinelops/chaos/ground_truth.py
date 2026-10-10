from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_injection_record(
    *,
    run_id: str,
    scenario: str,
    seed: int,
    injection_start: str,
    injected_service: str,
    baseline_seconds: int,
    injection_seconds: int,
    cooldown_seconds: int,
    non_registry: bool,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "classification": "ground_truth_injection_only",
        "non_registry": non_registry,
        "scenario": scenario,
        "seed": seed,
        "injected_service": injected_service,
        "injection_start": injection_start,
        "configured_baseline_seconds": baseline_seconds,
        "configured_injection_seconds": injection_seconds,
        "configured_cooldown_seconds": cooldown_seconds,
    }


def persist_injection_record(
    root: Path,
    run_id: str,
    payload: dict[str, Any],
) -> Path:
    path = root / f"{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return path
