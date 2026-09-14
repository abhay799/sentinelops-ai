from __future__ import annotations

from typing import Any

from sentinelops.investigation.agents import (
    challenger_agent,
    investigator_agent,
    remediation_agent,
    verifier_agent,
)

from sentinelops.investigation.llm import (
    GroundedLLMProvider,
)


class InvestigationOrchestrator:

    def __init__(
        self,
        provider: GroundedLLMProvider,
    ) -> None:

        self.provider = provider

    def run(
        self,
        evidence: dict[str, Any],
        retrieved: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if (
            evidence.get(
                "evidence_source_count",
                0,
            )
            <= 0
        ):
            raise ValueError(
                "Cannot investigate without evidence"
            )

        source_names = [
            row["source"]
            for row in retrieved
        ]

        investigator = investigator_agent(
            evidence,
            retrieved,
        )

        challenger = challenger_agent(
            evidence
        )

        remediation = remediation_agent(
            evidence
        )

        verifier = verifier_agent(
            evidence
        )

        prompt = (
            "Explain the incident using only "
            "the supplied evidence and retrieved "
            "runbooks. Do not confirm root cause "
            "independently. Do not authorize or "
            "execute remediation."
        )

        grounded_generation = (
            self.provider.generate(
                prompt=prompt,
                evidence=evidence,
                sources=source_names,
            )
        )

        return {
            "incident_id":
                evidence[
                    "incident_id"
                ],

            "orchestration_version":
                "v1",

            "agents": {
                "investigator":
                    investigator,

                "challenger":
                    challenger,

                "remediation":
                    remediation,

                "verifier":
                    verifier,
            },

            "grounded_generation":
                grounded_generation,

            "evidence_source_count":
                evidence[
                    "evidence_source_count"
                ],

            "retrieved_sources":
                source_names,

            "safety": {
                "root_cause_confirmed_by_agent":
                    False,

                "agent_execution_authority":
                    False,

                "sentinelguard_bypass_allowed":
                    False,

                "human_approval_bypass_allowed":
                    False,

                "evidence_required":
                    True,

                "fail_closed":
                    True,
            },
        }
