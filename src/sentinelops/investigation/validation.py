from __future__ import annotations

from typing import Any


def validate_final_investigation(
    report: dict[str, Any],
) -> list[str]:

    errors: list[str] = []

    if (
        report.get(
            "evidence_source_count",
            0,
        )
        <= 0
    ):
        errors.append(
            "Investigation has no traceable evidence"
        )

    safety = report.get(
        "safety",
        {},
    )

    forbidden_true_fields = [
        "root_cause_confirmed_by_agent",
        "agent_execution_authority",
        "sentinelguard_bypass_allowed",
        "human_approval_bypass_allowed",
    ]

    for field in forbidden_true_fields:

        if bool(
            safety.get(
                field,
                False,
            )
        ):
            errors.append(
                f"Unsafe capability enabled: {field}"
            )

    if not bool(
        safety.get(
            "evidence_required",
            False,
        )
    ):
        errors.append(
            "Evidence requirement disabled"
        )

    if not bool(
        safety.get(
            "fail_closed",
            False,
        )
    ):
        errors.append(
            "Final investigation is not fail-closed"
        )

    generation = report.get(
        "grounded_generation",
        {},
    )

    if generation.get(
        "root_cause_confirmed"
    ):
        errors.append(
            "LLM provider confirmed root cause"
        )

    if generation.get(
        "execution_authority"
    ):
        errors.append(
            "LLM provider has execution authority"
        )

    if not generation.get(
        "source_references"
    ):
        errors.append(
            "Grounded generation has no source references"
        )

    agents = report.get(
        "agents",
        {},
    )

    for agent_name, agent in agents.items():

        if agent.get(
            "execution_authority"
        ):
            errors.append(
                f"{agent_name} has execution authority"
            )

    return errors
