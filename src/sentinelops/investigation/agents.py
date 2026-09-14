from __future__ import annotations

from typing import Any


def investigator_agent(
    evidence: dict[str, Any],
    retrieved: list[dict[str, Any]],
) -> dict[str, Any]:

    rca = evidence.get(
        "rca",
        [],
    )

    top_candidate = None
    causal_score = None
    disposition = None

    if rca:

        sorted_rca = sorted(
            rca,
            key=lambda row: row.get(
                "rank",
                999,
            ),
        )

        top = sorted_rca[0]

        top_candidate = top.get(
            "candidate_service"
        )

        causal_score = top.get(
            "causal_consistency_score"
        )

        disposition = top.get(
            "final_disposition"
        )

    return {
        "agent":
            "investigator",

        "incident_id":
            evidence[
                "incident_id"
            ],

        "leading_candidate":
            top_candidate,

        "causal_consistency_score":
            causal_score,

        "candidate_disposition":
            disposition,

        "evidence_source_count":
            evidence[
                "evidence_source_count"
            ],

        "retrieved_sources":
            [
                item["source"]
                for item in retrieved
            ],

        "root_cause_status":
            "not_confirmed_by_agent",

        "execution_authority":
            False,
    }


def challenger_agent(
    evidence: dict[str, Any],
) -> dict[str, Any]:

    rca = evidence.get(
        "rca",
        [],
    )

    supported = []

    rejected = []

    inconclusive = []

    for row in rca:

        disposition = row.get(
            "final_disposition"
        )

        service = row.get(
            "candidate_service"
        )

        if (
            disposition
            == "supported_candidate"
        ):
            supported.append(
                service
            )

        elif (
            disposition
            == "rejected_candidate"
        ):
            rejected.append(
                service
            )

        else:
            inconclusive.append(
                service
            )

    return {
        "agent":
            "challenger",

        "supported_candidates":
            supported,

        "rejected_candidates":
            rejected,

        "inconclusive_candidates":
            inconclusive,

        "root_cause_confirmed":
            False,

        "execution_authority":
            False,
    }


def remediation_agent(
    evidence: dict[str, Any],
) -> dict[str, Any]:

    remediation = evidence.get(
        "remediation",
        [],
    )

    recommendations = []

    for row in remediation:

        recommendations.append(
            {
                "plan_id":
                    row.get(
                        "plan_id"
                    ),

                "action":
                    row.get(
                        "recommended_action"
                    ),

                "guard_decision":
                    row.get(
                        "guard_decision"
                    ),

                "phase14_candidate":
                    row.get(
                        "phase14_candidate"
                    ),

                "human_approval_status":
                    row.get(
                        "human_approval_status"
                    ),
            }
        )

    return {
        "agent":
            "remediation",

        "recommendations":
            recommendations,

        "can_bypass_sentinelguard":
            False,

        "execution_authority":
            False,
    }


def verifier_agent(
    evidence: dict[str, Any],
) -> dict[str, Any]:

    verification = evidence.get(
        "verification",
        [],
    )

    verified = any(
        bool(
            row.get(
                "recovery_verified",
                False,
            )
        )
        for row in verification
    )

    statuses = [
        row.get(
            "execution_status"
        )
        for row
        in verification
    ]

    return {
        "agent":
            "verifier",

        "recovery_verified":
            verified,

        "execution_statuses":
            statuses,

        "execution_authority":
            False,
    }
