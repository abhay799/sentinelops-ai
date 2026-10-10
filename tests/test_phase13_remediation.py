from pathlib import Path

import polars as pl

from sentinelops.remediation.planner import (
    build_remediation_plans,
)
from sentinelops.remediation.sentinelguard import (
    SENTINELGUARD_CONFIG_PATH,
    evaluate_sentinelguard,
)

CONFIG = {
    "planner": {
        "allowed_actions": [
            "rollback",
            "traffic_shift",
            "restart",
        ],

        "minimum_causal_score":
            0.65,

        "minimum_priority_score":
            0.35,

        "minimum_net_benefit":
            0.01,
    },
}



def counterfactual():

    return pl.DataFrame(
        [
            {
                "incident_id":
                    "INC-1",

                "candidate_service":
                    "payment-service",

                "recommended_action":
                    "rollback",

                "recommended_net_benefit":
                    0.40,

                "projected_failure_risk":
                    0.25,

                "recommendation_status":
                    "simulation_recommendation",
            }
        ]
    )


def priority():

    return pl.DataFrame(
        [
            {
                "incident_id":
                    "INC-1",

                "remediation_priority_score":
                    0.90,
            }
        ]
    )


def disposition():

    return pl.DataFrame(
        [
            {
                "incident_id":
                    "INC-1",

                "candidate_service":
                    "payment-service",

                "causal_consistency_score":
                    0.90,

                "final_disposition":
                    "supported_candidate",
            }
        ]
    )


def build_plans():

    return build_remediation_plans(
        counterfactual(),
        priority(),
        disposition(),
        CONFIG,
    )


def test_planner_never_allows_execution():

    plans = build_plans()

    assert not plans[
        "execution_allowed"
    ].any()


def test_supported_plan_reaches_guard():

    plans = build_plans()

    assert plans[
        "planner_ready"
    ].all()

    assert (
        plans[
            "plan_status"
        ][0]
        == "proposed_pending_guard"
    )


def test_guard_can_mark_phase14_candidate():

    decisions = (
        evaluate_sentinelguard(
            build_plans(),
        )
    )

    assert decisions[
        "phase14_candidate"
    ].all()

    assert (
        decisions[
            "guard_decision"
        ][0]
        == "eligible_pending_human"
    )


def test_guard_still_blocks_execution():

    decisions = (
        evaluate_sentinelguard(
            build_plans(),
        )
    )

    assert not decisions[
        "execution_allowed"
    ].any()

    assert (
        decisions[
            "human_approval_status"
        ]
        == "pending"
    ).all()


def test_guard_fail_closed_on_missing_rollback():

    plans = (
        build_plans()
        .with_columns(
            pl.lit(False)
            .alias(
                "rollback_available"
            )
        )
    )

    decisions = (
        evaluate_sentinelguard(
            plans,
        )
    )

    assert not decisions[
        "guard_technical_approval"
    ].any()

    assert (
        decisions[
            "guard_decision"
        ][0]
        == "blocked"
    )


def test_guard_reads_only_canonical_config(monkeypatch):

    expected = SENTINELGUARD_CONFIG_PATH.resolve()
    original_read_text = Path.read_text
    seen: list[Path] = []

    def guarded_read_text(path: Path, *args, **kwargs):

        resolved = path.resolve()
        seen.append(resolved)

        if resolved != expected:
            raise AssertionError(
                f"SentinelGuard read non-canonical config: {resolved}"
            )

        return original_read_text(
            path,
            *args,
            **kwargs,
        )

    monkeypatch.setattr(
        Path,
        "read_text",
        guarded_read_text,
    )

    decisions = evaluate_sentinelguard(
        build_plans(),
    )

    assert decisions.height == 1
    assert seen == [expected]
