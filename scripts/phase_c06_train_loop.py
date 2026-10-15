from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
import traceback as traceback_module

import httpx
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
RUN_FAILED_AFTER_INJECTION = "run_failed_after_injection"
HARNESS_DEFECT = "harness_defect"


def utc_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def host_check() -> dict[str, Any]:
    boot_id_path = Path("/proc/sys/kernel/random/boot_id")
    uptime_path = Path("/proc/uptime")
    return {
        "timestamp_utc": utc_iso(),
        "boot_id": (
            boot_id_path.read_text(encoding="utf-8").strip()
            if boot_id_path.exists()
            else None
        ),
        "uptime_seconds": (
            float(uptime_path.read_text(encoding="utf-8").split()[0])
            if uptime_path.exists()
            else None
        ),
    }


def _host_event_reason(
    start_check: dict[str, Any] | None,
    current_check: dict[str, Any],
) -> str | None:
    if not start_check:
        return None
    start_boot = start_check.get("boot_id")
    current_boot = current_check.get("boot_id")
    if start_boot and current_boot and start_boot != current_boot:
        return "host_boot_id_changed"
    return None


def is_environmental_exception(exc: BaseException | None) -> bool:
    if exc is None:
        return False
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.ConnectError,
        ),
    )


def _execution_state(
    evidence_root: Path,
    run_id: str,
) -> dict[str, Any]:
    path = evidence_root / run_id / "execution_state.json"
    if not path.exists():
        return {}
    return read_json(path)


def classify_interruption(
    active: dict[str, Any],
    *,
    evidence_root: Path,
    current_host_check: dict[str, Any] | None = None,
    exception: BaseException | None = None,
) -> tuple[str, str, dict[str, Any], dict[str, Any]]:
    current_check = current_host_check or host_check()
    host_reason = _host_event_reason(active.get("host_check"), current_check)
    state = _execution_state(evidence_root, str(active["run_id"]))
    if host_reason:
        return (
            "infrastructure_invalid_host_event",
            host_reason,
            state,
            current_check,
        )
    if exception is not None and not is_environmental_exception(exception):
        return (
            HARNESS_DEFECT,
            f"non_environmental_exception:{type(exception).__name__}",
            state,
            current_check,
        )
    if state.get("injection_start"):
        return (
            RUN_FAILED_AFTER_INJECTION,
            "executor_failed_at_or_after_injection_start",
            state,
            current_check,
        )
    return (
        "infrastructure_invalid_interrupted",
        "executor_failed_before_injection_start",
        state,
        current_check,
    )


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


def finalize_orphaned_post_injection_attempt(
    attempt_dir: Path,
    *,
    failure_reason: str,
) -> Path:
    state_path = attempt_dir / "execution_state.json"
    if not state_path.is_file():
        raise RuntimeError(
            f"missing execution_state.json for orphaned attempt: {attempt_dir}"
        )

    summary_path = attempt_dir / "run_summary.json"
    if summary_path.exists():
        raise RuntimeError(
            f"run_summary.json already exists for orphaned attempt: {attempt_dir}"
        )

    state = read_json(state_path)
    injection_start = state.get("injection_start")
    if injection_start is None:
        raise RuntimeError(
            "orphaned attempt is not post-injection: injection_start is null"
        )

    summary: dict[str, Any] = {
        "classification": "registered",
        "partition": state["partition"],
        "run_id": state["run_id"],
        "artifact_run_id": attempt_dir.name,
        "scenario": state["scenario"],
        "seed": state["seed"],
        "replacement_for": state.get("replacement_for"),
        "status": RUN_FAILED_AFTER_INJECTION,
        "invalid_reason": None,
        "failure_reason": failure_reason,
        "interruption_record": None,
        "execution_state": state,
        "traceback": None,
        "registered_result_eligible": True,
        "counted_in_analysis_denominator": True,
        "harness_defect_reason": None,
        "run_record": {
            "run_id": state["run_id"],
            "seed": state["seed"],
            "scenario": state["scenario"],
            "approver": None,
            "injection_start": injection_start,
            "injection_end": None,
            "recovery_time": None,
            "detection_time": None,
            "rca_output_time": None,
            "guard_decision_time": None,
            "remediation_time": None,
            "verification_time": None,
        },
    }

    write_json(summary_path, summary)
    return summary_path


def run_summary_path(evidence_root: Path, run_id: str) -> Path:
    return evidence_root / run_id / "run_summary.json"


def preexecutor_launcher_retry_eligible(
    evidence_root: Path,
    run_id: str,
) -> bool:
    run_dir = evidence_root / run_id
    summary_path = run_dir / "run_summary.json"

    if not summary_path.is_file():
        return False

    if (run_dir / "execution_state.json").exists():
        return False

    summary = read_json(summary_path)

    if summary.get("status") != HARNESS_DEFECT:
        return False

    if summary.get("registered_result_eligible") is not False:
        return False

    if summary.get("counted_in_analysis_denominator") is not False:
        return False

    traceback_text = str(summary.get("traceback") or "")

    required_fragments = (
        "result = executor(entry, replacement_for)",
        "TypeError: run_registered_train() takes 1 positional argument but 2 were given",
    )

    return all(
        fragment in traceback_text
        for fragment in required_fragments
    )


def authoritative_reexecution_summary(
    evidence_root: Path,
    run_id: str,
    *,
    replacement_for: str,
) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []

    for summary_path in sorted(
        evidence_root.glob(f"{run_id}__*/run_summary.json")
    ):
        summary = read_json(summary_path)

        if summary.get("run_id") != run_id:
            continue

        if summary.get("replacement_for") != replacement_for:
            continue

        if summary.get("registered_result_eligible") is not True:
            continue

        if summary.get("counted_in_analysis_denominator") is not True:
            continue

        matches.append(summary)

    if len(matches) > 1:
        raise RuntimeError(
            "multiple authoritative reexecution summaries found for "
            f"{run_id} replacing {replacement_for}"
        )

    return matches[0] if matches else None


def is_infrastructure_invalid(summary: dict[str, Any]) -> bool:
    return str(summary.get("status", "")).startswith(INFRASTRUCTURE_INVALID_PREFIX)


def is_harness_defect(summary: dict[str, Any]) -> bool:
    return summary.get("status") == HARNESS_DEFECT


def harness_defect_reexecution_eligible(
    summary: dict[str, Any],
) -> bool:
    if summary.get("status") != HARNESS_DEFECT:
        return False

    if summary.get("registered_result_eligible") is True:
        return False

    state = summary.get("execution_state") or {}
    return state.get("injection_start") is None


def harness_defect_reexecution_dir(
    evidence_root: Path,
    run_id: str,
) -> Path:
    path = evidence_root / f"{run_id}__a5_rerun"

    if path.exists():
        raise RuntimeError(
            f"harness-defect reexecution directory already exists: {path}"
        )

    return path


ENVIRONMENTAL_HTTPX_EXCEPTION_NAMES = {
    "ReadTimeout",
    "ConnectTimeout",
    "ConnectError",
}


def preinjection_environmental_retry_eligible(
    attempt_dir: Path,
    *,
    exception_name: str,
) -> bool:
    if exception_name not in ENVIRONMENTAL_HTTPX_EXCEPTION_NAMES:
        return False

    state_path = attempt_dir / "execution_state.json"
    if not state_path.is_file():
        return False

    state = read_json(state_path)

    return state.get("injection_start") is None


def environmental_retry_dir(
    evidence_root: Path,
    run_id: str,
    *,
    attempt_label: str,
) -> Path:
    path = evidence_root / f"{run_id}__{attempt_label}"

    if path.exists():
        raise RuntimeError(
            f"environmental retry directory already exists: {path}"
        )

    return path


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
        "host_check": host_check(),
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
    traceback_text: str | None = None,
    current_host_check: dict[str, Any] | None = None,
    exception: BaseException | None = None,
) -> Path:
    timestamp = utc_iso()
    safe_stamp = timestamp.replace(":", "").replace("-", "")
    status, classified_reason, execution_state, current_check = classify_interruption(
        active,
        evidence_root=evidence_root,
        current_host_check=current_host_check,
        exception=exception,
    )
    record = {
        "classification": "registered_control_record",
        "event": "interruption",
        "timestamp_utc": timestamp,
        "reason": reason,
        "classified_status": status,
        "classified_reason": classified_reason,
        "run": active,
        "execution_state": execution_state,
        "host_check_at_interruption": current_check,
        "traceback": traceback_text,
        "registered_result": status == RUN_FAILED_AFTER_INJECTION,
    }
    interruption_path = (
        control_root
        / "interruptions"
        / f"{safe_stamp}_{active['run_id']}.json"
    )
    write_json(interruption_path, record)

    summary_path = run_summary_path(
        evidence_root,
        str(active["run_id"]),
    )
    if not summary_path.exists():
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary: dict[str, Any] = {
            "classification": "registered",
            "partition": active["partition"],
            "run_id": active["run_id"],
            "scenario": active["scenario"],
            "seed": active["seed"],
            "replacement_for": active.get("replacement_for"),
            "status": status,
            "invalid_reason": (
                classified_reason
                if status.startswith(INFRASTRUCTURE_INVALID_PREFIX)
                else None
            ),
            "failure_reason": (
                reason if status == RUN_FAILED_AFTER_INJECTION else None
            ),
            "interruption_record": str(interruption_path),
            "execution_state": execution_state,
            "traceback": traceback_text,
            "registered_result_eligible": status == RUN_FAILED_AFTER_INJECTION,
            "counted_in_analysis_denominator": status == RUN_FAILED_AFTER_INJECTION,
            "harness_defect_reason": (
                classified_reason if status == HARNESS_DEFECT else None
            ),
        }
        if status == RUN_FAILED_AFTER_INJECTION:
            summary["run_record"] = {
                "run_id": active["run_id"],
                "seed": active["seed"],
                "scenario": active["scenario"],
                "approver": None,
                "injection_start": execution_state.get("injection_start"),
                "injection_end": None,
                "recovery_time": None,
                "detection_time": None,
                "rca_output_time": None,
                "guard_decision_time": None,
                "remediation_time": None,
                "verification_time": None,
            }
        write_json(summary_path, summary)
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
    *,
    attempt_label: str | None = None,
) -> Path:
    return await run_registered_train(
        str(entry["run_id"]),
        replacement_for=replacement_for,
        attempt_label=attempt_label,
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
    attempt_label: str | None = None,
) -> dict[str, Any]:
    artifact_run_id = (
        f"{entry['run_id']}__{attempt_label}"
        if attempt_label
        else str(entry["run_id"])
    )

    summary_path = run_summary_path(
        evidence_root,
        artifact_run_id,
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
                    attempt_label=attempt_label,
                )
            )
        else:
            result = executor(entry, replacement_for)
            if hasattr(result, "__await__"):
                asyncio.run(result)
    except BaseException as exc:
        traceback_text = traceback_module.format_exc()
        state = _state(control_root)
        active = state.get("active_run")
        if active:
            _record_interruption(
                active=active,
                evidence_root=evidence_root,
                control_root=control_root,
                reason="executor_interrupted_or_crashed",
                traceback_text=traceback_text,
                exception=exc,
            )
        _clear_active(control_root)
        raise

    _clear_active(control_root)

    if not summary_path.exists():
        raise RuntimeError(f"executor returned without run_summary.json for {entry['run_id']}")
    return read_json(summary_path)


def registered_spares_exhausted_for_primary(
    primary: dict[str, Any],
    registry: dict[str, Any],
    *,
    evidence_root: Path,
) -> bool:
    spares = train_spares(
        registry,
        str(primary["scenario"]),
    )

    if not spares:
        return False

    for spare in spares:
        summary_path = run_summary_path(
            evidence_root,
            str(spare["run_id"]),
        )

        if not summary_path.exists():
            return False

        summary = read_json(summary_path)

        if summary.get("replacement_for") == str(primary["run_id"]):
            return False

    return True


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

        authoritative = authoritative_reexecution_summary(
            evidence_root,
            str(spare["run_id"]),
            replacement_for=str(primary["run_id"]),
        )
        if authoritative is not None:
            return authoritative

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

        if (
            is_harness_defect(summary)
            and preexecutor_launcher_retry_eligible(
                evidence_root,
                str(primary["run_id"]),
            )
        ):
            attempt_label = "launcher_retry_01"
            retry_summary_path = run_summary_path(
                evidence_root,
                f"{primary['run_id']}__{attempt_label}",
            )

            if retry_summary_path.exists():
                summary = read_json(retry_summary_path)
            else:
                summary = _execute_once(
                    primary,
                    replacement_for=None,
                    evidence_root=evidence_root,
                    control_root=control_root,
                    executor=executor,
                    attempt_label=attempt_label,
                )

        if is_harness_defect(summary):
            raise RuntimeError(
                "STOP: harness_defect requires harness correction before "
                f"continuing; run_id={primary['run_id']}"
            )

        if is_infrastructure_invalid(summary):
            if registered_spares_exhausted_for_primary(
                primary,
                registry,
                evidence_root=evidence_root,
            ):
                continue

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
