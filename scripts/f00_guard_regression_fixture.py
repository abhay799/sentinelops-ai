from __future__ import annotations

import argparse
import inspect
import json
from pathlib import Path

import polars as pl
import yaml

from sentinelops.remediation.sentinelguard import evaluate_sentinelguard

REMEDIATION_CONFIG = Path("configs/remediation.yaml")


def base_plan(index: int, **overrides: object) -> dict[str, object]:
    plan: dict[str, object] = {
        "plan_id": f"F00-{index:03d}",
        "incident_id": f"INC-F00-{index:03d}",
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
    plan.update(overrides)
    return plan


def plans() -> list[dict[str, object]]:
    cases: list[dict[str, object]] = []

    # Explicit single-check failures.
    cases.append(base_plan(1, planner_ready=False))
    cases.append(base_plan(2, recommended_action="delete_database"))
    cases.append(base_plan(3, final_rca_disposition="challenged_candidate"))
    cases.append(base_plan(4, causal_consistency_score=0.699999))
    cases.append(base_plan(5, remediation_priority_score=0.349999))
    cases.append(base_plan(6, recommended_net_benefit=0.009999))
    cases.append(base_plan(7, projected_failure_risk=0.700001))
    cases.append(base_plan(8, rollback_available=False))
    cases.append(base_plan(9, traceable_evidence=False))

    # Exact boundary values: all must pass their numeric check.
    cases.append(base_plan(10, causal_consistency_score=0.70))
    cases.append(base_plan(11, remediation_priority_score=0.35))
    cases.append(base_plan(12, recommended_net_benefit=0.01))
    cases.append(base_plan(13, projected_failure_risk=0.70))

    # Allowed-action coverage and all-pass examples.
    cases.append(base_plan(14, recommended_action="rollback"))
    cases.append(base_plan(15, recommended_action="traffic_shift"))
    cases.append(base_plan(16, recommended_action="restart"))
    cases.append(base_plan(17))
    cases.append(base_plan(18, causal_consistency_score=1.0, remediation_priority_score=1.0))
    cases.append(base_plan(19, recommended_net_benefit=1.0, projected_failure_risk=0.0))
    cases.append(
        base_plan(
            20,
            causal_consistency_score=0.70,
            remediation_priority_score=0.35,
            recommended_net_benefit=0.01,
            projected_failure_risk=0.70,
        )
    )

    # Multiple-failure combinations to lock failed_checks ordering/behavior.
    cases.append(base_plan(21, planner_ready=False, rollback_available=False))
    cases.append(base_plan(22, recommended_action="unknown", traceable_evidence=False))
    cases.append(base_plan(23, final_rca_disposition="rejected", causal_consistency_score=0.10))
    cases.append(base_plan(24, remediation_priority_score=0.10, recommended_net_benefit=-0.20))
    cases.append(base_plan(25, projected_failure_risk=0.95, rollback_available=False))
    cases.append(
        base_plan(
            26,
            planner_ready=False,
            recommended_action="unknown",
            final_rca_disposition="rejected",
        )
    )
    cases.append(
        base_plan(
            27,
            causal_consistency_score=0.0,
            remediation_priority_score=0.0,
            recommended_net_benefit=0.0,
            projected_failure_risk=1.0,
        )
    )
    cases.append(base_plan(28, rollback_available=False, traceable_evidence=False))
    cases.append(base_plan(29, planner_ready=False, traceable_evidence=False))
    cases.append(
        base_plan(
            30,
            recommended_action="delete_database",
            rollback_available=False,
            traceable_evidence=False,
        )
    )

    # Near-boundary passing values.
    cases.append(base_plan(31, causal_consistency_score=0.700001))
    cases.append(base_plan(32, remediation_priority_score=0.350001))
    cases.append(base_plan(33, recommended_net_benefit=0.010001))
    cases.append(base_plan(34, projected_failure_risk=0.699999))

    # More supported dispositions/action combinations at exact thresholds.
    cases.append(base_plan(35, recommended_action="traffic_shift", causal_consistency_score=0.70))
    cases.append(base_plan(36, recommended_action="restart", remediation_priority_score=0.35))
    cases.append(base_plan(37, recommended_action="rollback", recommended_net_benefit=0.01))
    cases.append(base_plan(38, projected_failure_risk=0.70, traceable_evidence=True))
    cases.append(base_plan(39, causal_consistency_score=0.70, projected_failure_risk=0.70))
    cases.append(base_plan(40, remediation_priority_score=0.35, recommended_net_benefit=0.01))

    # Additional fail/pass cases to exceed the minimum and stabilize combinations.
    cases.append(base_plan(41, final_rca_disposition="not_supported"))
    cases.append(base_plan(42, planner_ready=False, projected_failure_risk=0.71))
    cases.append(base_plan(43, recommended_action="traffic_shift", recommended_net_benefit=0.50))
    cases.append(base_plan(44, recommended_action="restart", projected_failure_risk=0.10))
    cases.append(
        base_plan(
            45,
            causal_consistency_score=0.70,
            remediation_priority_score=0.35,
            recommended_net_benefit=0.01,
            projected_failure_risk=0.70,
            rollback_available=True,
            traceable_evidence=True,
        )
    )

    assert len(cases) >= 40
    return cases


def evaluate(frame: pl.DataFrame) -> pl.DataFrame:
    parameters = inspect.signature(evaluate_sentinelguard).parameters
    if len(parameters) == 1:
        return evaluate_sentinelguard(frame)

    with REMEDIATION_CONFIG.open(encoding="utf-8") as file:
        config = yaml.safe_load(file)["remediation"]
    return evaluate_sentinelguard(frame, config)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    frame = pl.DataFrame(plans(), strict=False)
    decisions = evaluate(frame).sort("plan_id").to_dicts()

    payload = {
        "fixture_version": "F00-v1",
        "case_count": len(decisions),
        "decisions": decisions,
    }
    Path(args.output).write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
