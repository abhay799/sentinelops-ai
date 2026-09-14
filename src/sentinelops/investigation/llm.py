from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class GroundedLLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        prompt: str,
        evidence: dict[str, Any],
        sources: list[str],
    ) -> dict[str, Any]:
        raise NotImplementedError


class DeterministicGroundedProvider(
    GroundedLLMProvider
):

    provider_name = "deterministic-grounded-v1"

    def generate(
        self,
        prompt: str,
        evidence: dict[str, Any],
        sources: list[str],
    ) -> dict[str, Any]:

        incident_id = evidence.get(
            "incident_id"
        )

        rca_rows = evidence.get(
            "rca",
            [],
        )

        candidate = None
        disposition = None

        if rca_rows:

            top = sorted(
                rca_rows,
                key=lambda row: row.get(
                    "rank",
                    999,
                ),
            )[0]

            candidate = top.get(
                "candidate_service"
            )

            disposition = top.get(
                "final_disposition"
            )

        return {
            "provider":
                self.provider_name,

            "incident_id":
                incident_id,

            "summary":
                (
                    f"Incident {incident_id} has "
                    f"leading candidate {candidate} "
                    f"with disposition "
                    f"{disposition}. "
                    "This remains evidence-grounded "
                    "and is not independently "
                    "confirmed by the language model."
                ),

            "source_references":
                sources,

            "root_cause_confirmed":
                False,

            "execution_authority":
                False,

            "prompt_used":
                prompt,
        }
