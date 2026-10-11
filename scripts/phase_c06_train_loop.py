from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from sentinelops.chaos.registered_harness import (
    REGISTRY_PATH,
    TRAIN_EVIDENCE_ROOT,
    run_registered_train,
)

CONTROL_ROOT = Path("evidence/C/C06_train_control")
STATE_PATH = CONTROL_ROOT / "state.json"
INTERRUPTION_ROOT = CONTROL_ROOT / "interruptions"
PID_PATH = CONTROL_ROOT / "train_loop.pid"
LOG_PATH = CONTROL_ROOT / "train_loop.log"

INFRASTRUCTURE_INVALID_PREFIX = "infrastructure_invalid"


def utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run_summary_path(evidence_root: Path, run_id: str) -> Path:
    return evidence_root / run_id / "run_summary.json"


def is_infrastructure_invalid(summary: dict[str, Any]) -> bool:
    return str(summary.get("status", "")).startswith(INFRASTRUCTURE_INVALID_PREFIX)


def train_schedule(registry: dict[str, Any]) -> list[dict[str, Any]]:
    return [row for row in registry["execution_schedule"] if row["partition"] == "TRAIN"]


def train_spares(
    registry: dict[str, Any],
    scenario: str,
) -> list[dict[str, Any]]:
    return sorted(
        [
            row
            for row in registry["reserved_spares"]
            if row["partition"] == "TRAIN" and row["scenario"] == scenario
        ],
        key=lambda row: int(row["spare_ordinal"]),
    )


def _state(control_root: Path) -> dict[str, Any]:
    path = control_root / "state.json"
    if not path.exists():
        return {
            "version": 1,
            "active_run": None,
            "last_update_utc": None,
        }
    return read_json(path)


def _save_state(control_root: Path, state: dict[str, Any]) -> None:
    state["last_update_utc"] = utc_iso()
    write_json(control_root / "state.json", state)


def _mark_active(
    control_root: Path,
    entry: dict[str, Any],
    *,
    replacement_for: str | None,
) -> None:
    state = _state(control_root)
    state["active_run"] = {
        "run_id": entry["run_id"],
        "scenario": entry["scenario"],
        "partition": entry["partition"],
        "seed": int(entry["seed"]),
        "replacement_for": replacement_for,
        "started_utc": utc_iso(),
    }
    _save_state(control_root, state)


def _clear_active(control_root: Path) -> None:
    state = _state(control_root)
    state["active_run"] = None
    _save_state(control_root, state)


def _record_interruption(
    *,
    active: dict[str, Any],
    evidence_root: Path,
    control_root: Path,
    reason: str,
) -> Path:
    timestamp = utc_iso()
    safe_stamp = timestamp.replace(":", "").replace("-", "")
    record = {
        "classification": "registered_control_record",
        "event": "interruption",
        "timestamp_utc": timestamp,
        "reason": reason,
        "run": active,
        "registered_result": False,
    }
    interruption_path = control_root / "interruptions" / f"{safe_stamp}_{active['run_id']}.json"
    write_json(interruption_path, record)

    summary_path = run_summary_path(
        evidence_root,
        str(active["run_id"]),
    )
    if not summary_path.exists():
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        write_json(
            summary_path,
            {
                "classification": "registered",
                "partition": active["partition"],
                "run_id": active["run_id"],
                "scenario": active["scenario"],
                "seed": active["seed"],
                "replacement_for": active.get("replacement_for"),
                "status": "infrastructure_invalid_interrupted",
                "invalid_reason": reason,
                "interruption_record": str(interruption_path),
            },
        )
    return interruption_path


def recover_interrupted_run(
    *,
    evidence_root: Path = TRAIN_EVIDENCE_ROOT,
    control_root: Path = CONTROL_ROOT,
) -> Path | None:
    state = _state(control_root)
    active = state.get("active_run")
    if not active:
        return None

    summary = run_summary_path(
        evidence_root,
        str(active["run_id"]),
    )
    if summary.exists():
        _clear_active(control_root)
        return None

    interruption = _record_interruption(
        active=active,
        evidence_root=evidence_root,
        control_root=control_root,
        reason="loop_restart_detected_unfinished_active_run",
    )
    _clear_active(control_root)
    return interruption


async def _default_executor(
    entry: dict[str, Any],
    replacement_for: str | None,
) -> Path:
    return await run_registered_train(
        str(entry["run_id"]),
        replacement_for=replacement_for,
    )


def _execute_once(
    entry: dict[str, Any],
    *,
    replacement_for: str | None,
    evidence_root: Path,
    control_root: Path,
    executor: Callable[
        [dict[str, Any], str | None],
        Any,
    ]
    | None = None,
) -> dict[str, Any]:
    summary_path = run_summary_path(
        evidence_root,
        str(entry["run_id"]),
    )
    if summary_path.exists():
        return read_json(summary_path)

    _mark_active(
        control_root,
        entry,
        replacement_for=replacement_for,
    )

    try:
        if executor is None:
            asyncio.run(
                _default_executor(
                    entry,
                    replacement_for,
                )
            )
        else:
            result = executor(entry, replacement_for)
            if hasattr(result, "__await__"):
                asyncio.run(result)
    except BaseException:
        state = _state(control_root)
        active = state.get("active_run")
        if active:
            _record_interruption(
                active=active,
                evidence_root=evidence_root,
                control_root=control_root,
                reason="executor_interrupted_or_crashed",
            )
        _clear_active(control_root)
        raise

    _clear_active(control_root)

    if not summary_path.exists():
        raise RuntimeError(f"executor returned without run_summary.json for {entry['run_id']}")
    return read_json(summary_path)


def _replacement_complete(
    primary: dict[str, Any],
    registry: dict[str, Any],
    *,
    evidence_root: Path,
    control_root: Path,
    executor: Callable[
        [dict[str, Any], str | None],
        Any,
    ]
    | None = None,
) -> dict[str, Any]:
    spares = train_spares(
        registry,
        str(primary["scenario"]),
    )

    for spare in spares:
        summary_path = run_summary_path(
            evidence_root,
            str(spare["run_id"]),
        )
        if summary_path.exists():
            summary = read_json(summary_path)
        else:
            summary = _execute_once(
                spare,
                replacement_for=str(primary["run_id"]),
                evidence_root=evidence_root,
                control_root=control_root,
                executor=executor,
            )

        if not is_infrastructure_invalid(summary):
            return summary

    raise RuntimeError(
        "STOP: both reserved TRAIN spares are used/invalid for "
        f"scenario={primary['scenario']} while replacing "
        f"{primary['run_id']}; no ad-hoc replacement is permitted"
    )


def run_train_loop(
    *,
    registry: dict[str, Any] | None = None,
    evidence_root: Path = TRAIN_EVIDENCE_ROOT,
    control_root: Path = CONTROL_ROOT,
    executor: Callable[
        [dict[str, Any], str | None],
        Any,
    ]
    | None = None,
) -> dict[str, Any]:
    registry = registry or load_registry()
    recover_interrupted_run(
        evidence_root=evidence_root,
        control_root=control_root,
    )

    for primary in train_schedule(registry):
        summary_path = run_summary_path(
            evidence_root,
            str(primary["run_id"]),
        )

        if summary_path.exists():
            summary = read_json(summary_path)
        else:
            summary = _execute_once(
                primary,
                replacement_for=None,
                evidence_root=evidence_root,
                control_root=control_root,
                executor=executor,
            )

        if is_infrastructure_invalid(summary):
            _replacement_complete(
                primary,
                registry,
                evidence_root=evidence_root,
                control_root=control_root,
                executor=executor,
            )

    result = status_snapshot(
        registry=registry,
        evidence_root=evidence_root,
        control_root=control_root,
    )
    result["loop_complete"] = True
    _save_state(
        control_root,
        {
            **_state(control_root),
            "active_run": None,
            "loop_complete": True,
        },
    )
    return result


def status_snapshot(
    *,
    registry: dict[str, Any] | None = None,
    evidence_root: Path = TRAIN_EVIDENCE_ROOT,
    control_root: Path = CONTROL_ROOT,
) -> dict[str, Any]:
    registry = registry or load_registry()
    primaries = train_schedule(registry)
    completed = 0
    infra_invalid = 0
    for entry in primaries:
        path = run_summary_path(
            evidence_root,
            str(entry["run_id"]),
        )
        if not path.exists():
            continue
        completed += 1
        if is_infrastructure_invalid(read_json(path)):
            infra_invalid += 1

    spares_used = 0
    for spare in registry["reserved_spares"]:
        if spare["partition"] != "TRAIN":
            continue
        if run_summary_path(
            evidence_root,
            str(spare["run_id"]),
        ).exists():
            spares_used += 1

    pid_path = control_root / "train_loop.pid"
    pid = None
    process_alive = False
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            os.kill(pid, 0)
            process_alive = True
        except (ValueError, ProcessLookupError, PermissionError):
            process_alive = False

    state = _state(control_root)
    return {
        "train_primary_total": len(primaries),
        "train_primary_accounted": completed,
        "train_primary_remaining": len(primaries) - completed,
        "infrastructure_invalid_primary": infra_invalid,
        "train_spares_used": spares_used,
        "active_run": state.get("active_run"),
        "pid": pid,
        "process_alive": process_alive,
    }


def detach() -> int:
    CONTROL_ROOT.mkdir(parents=True, exist_ok=True)
    if PID_PATH.exists():
        try:
            existing = int(PID_PATH.read_text(encoding="utf-8").strip())
            os.kill(existing, 0)
            raise RuntimeError(f"TRAIN loop already appears to be running as PID {existing}")
        except ProcessLookupError:
            pass
        except ValueError:
            pass

    log_handle = LOG_PATH.open("a", encoding="utf-8")
    process = subprocess.Popen(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--run",
        ],
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        cwd=Path.cwd(),
    )
    PID_PATH.write_text(f"{process.pid}\n", encoding="utf-8")
    return process.pid


def main() -> None:
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--run", action="store_true")
    action.add_argument("--detach", action="store_true")
    action.add_argument("--status", action="store_true")
    args = parser.parse_args()

    if args.status:
        print(json.dumps(status_snapshot(), indent=2, sort_keys=True))
        return

    if args.detach:
        pid = detach()
        print(f"detached TRAIN loop PID={pid}")
        print(f"log={LOG_PATH}")
        print(f"pid_file={PID_PATH}")
        return

    try:
        result = run_train_loop()
        print(json.dumps(result, indent=2, sort_keys=True))
    finally:
        if PID_PATH.exists():
            try:
                pid = int(PID_PATH.read_text(encoding="utf-8").strip())
                if pid == os.getpid():
                    PID_PATH.unlink()
            except ValueError:
                PID_PATH.unlink()


if __name__ == "__main__":
    main()
