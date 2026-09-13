from __future__ import annotations

from typing import Any

import polars as pl

REQUIRED_EVIDENCE_TYPES = {
    "anomaly",
    "correlation",
}


def validate_rca_hypotheses(
    hypotheses: pl.DataFrame,
) -> list[str]:

    errors: list[str] = []

    if hypotheses.is_empty():
        errors.append(
            "RCA hypothesis dataset is empty"
        )
        return errors

    required_columns = {
        "hypothesis_id",
        "incident_id",
        "candidate_service",
        "rank",
        "rca_score",
        "confidence",
        "evidence_count",
        "evidence",
        "confirmed_root_cause",
        "requires_challenger",
        "requires_human_confirmation",
    }

    missing = (
        required_columns
        - set(hypotheses.columns)
    )

    if missing:
        errors.append(
            "Missing RCA columns: "
            f"{sorted(missing)}"
        )
        return errors

    for row in hypotheses.to_dicts():

        evidence: list[
            dict[str, Any]
        ] = row["evidence"]

        evidence_types = {
            item["type"]
            for item in evidence
        }

        if not REQUIRED_EVIDENCE_TYPES.issubset(
            evidence_types
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                "missing minimum evidence types"
            )

        if (
            int(
                row["evidence_count"]
            )
            != len(evidence)
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                "evidence count mismatch"
            )

        if bool(
            row[
                "confirmed_root_cause"
            ]
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                "root cause prematurely confirmed"
            )

        if not bool(
            row[
                "requires_challenger"
            ]
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                "challenger requirement disabled"
            )

        if not bool(
            row[
                "requires_human_confirmation"
            ]
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                "human confirmation requirement disabled"
            )

        score = float(
            row["rca_score"]
        )

        if (
            score < 0.0
            or score > 1.0
        ):
            errors.append(
                f"{row['hypothesis_id']}: "
                f"invalid RCA score {score}"
            )

    return errors