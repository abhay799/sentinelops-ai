from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import polars as pl

from sentinelops.chaos.stage_events import write_stage_event
from sentinelops.execution.runtime import execute_local_sandbox
from sentinelops.remediation.sentinelguard import evaluate_sentinelguard


def detection_stage(run_dir: Path) -> datetime:
    return write_stage_event(run_dir, "detection", {"dry_run": True, "detected": True})


def correlation_stage(run_dir: Path) -> datetime:
    return write_stage_event(run_dir, "correlation", {"dry_run": True, "incident_created": True})


def rca_stage(run_dir: Path) -> datetime:
    return write_stage_event(run_dir, "rca", {"dry_run": True, "candidate": "payment-service"})


def challenge_stage(run_dir: Path) -> datetime:
    return write_stage_event(
        run_dir, "challenge", {"dry_run": True, "disposition": "supported_candidate"}
    )


def plan_stage(run_dir: Path) -> tuple[datetime, pl.DataFrame]:
    plan = pl.DataFrame(
        [
            {
                "plan_id": "DRY-PLAN-1",
                "incident_id": "DRY-INC-1",
                "candidate_service": "payment-service",
                "recommended_action": "rollback",
                "planner_ready": True,
                "final_rca_disposition": "supported_candidate",
                "causal_consistency_score": 0.90,
                "remediation_priority_score": 0.90,
                "recommended_net_benefit": 0.40,
                "projected_failure_risk": 0.25,
                "rollback_available": True,
                "traceable_evidence": True,
            }
        ]
    )
    timestamp = write_stage_event(run_dir, "plan", {"dry_run": True, "action": "rollback"})
    return timestamp, plan


def guard_stage(run_dir: Path, plan: pl.DataFrame) -> tuple[datetime, dict[str, Any]]:
    decision = evaluate_sentinelguard(plan).to_dicts()[0]
    timestamp = write_stage_event(
        run_dir,
        "guard_decision",
        {"dry_run": True, "guard_decision": decision["guard_decision"]},
    )
    return timestamp, decision


def human_authorization_stage(run_dir: Path) -> tuple[datetime, dict[str, str]]:
    approval = {"approval_status": "approved", "approved_by": "c03-dry-run"}
    timestamp = write_stage_event(run_dir, "human_authorization", {"dry_run": True, **approval})
    return timestamp, approval


def remediation_and_verification_stages(
    run_dir: Path,
    approval: dict[str, str],
    execution_config: dict[str, Any],
) -> tuple[datetime, datetime, dict[str, Any]]:
    request = {
        "execution_request_id": "DRY-EXEC-1",
        "plan_id": "DRY-PLAN-1",
        "incident_id": "DRY-INC-1",
        "candidate_service": "payment-service",
        "recommended_action": "rollback",
        "target_url": "http://localhost:8103",
        "preapproval_ready": True,
        "guard_passed": True,
        "rollback_available": True,
    }

    def handler(request_object: httpx.Request) -> httpx.Response:
        if request_object.url.path in {"/live", "/ready"}:
            return httpx.Response(200, json={"status": "ok"})
        if request_object.url.path == "/failure-mode/reset":
            return httpx.Response(200, json={"status": "reset"})
        return httpx.Response(404)

    remediation_time = write_stage_event(
        run_dir,
        "remediation",
        {"dry_run": True, "action": "rollback", "adapter": "/failure-mode/reset"},
    )
    result = execute_local_sandbox(
        request,
        approval,
        execution_config,
        transport=httpx.MockTransport(handler),
    )
    verification_time = write_stage_event(
        run_dir,
        "verification",
        {"dry_run": True, "recovery_verified": bool(result["recovery_verified"])},
    )
    return remediation_time, verification_time, result
