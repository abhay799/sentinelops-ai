from __future__ import annotations

from typing import Any

import polars as pl


def build_causal_disposition(
    hypotheses: pl.DataFrame,
    challenges: pl.DataFrame,
) -> pl.DataFrame:

    challenge_fields = challenges.select(
        [
            "hypothesis_id",
            "incident_id",
            "candidate_service",
            "rank",
            "challenge_score",
            "challenge_status",
            "supporting_evidence_count",
            "contradicting_evidence_count",
            "challenger_completed",
        ]
    )

    joined = hypotheses.join(
        challenge_fields,
        on=[
            "hypothesis_id",
            "incident_id",
            "candidate_service",
            "rank",
        ],
        how="inner",
    )

    if joined.is_empty():
        return pl.DataFrame()

    rows: list[dict[str, Any]] = []

    for row in joined.to_dicts():

        anomaly_strength = float(
            row["anomaly_strength"]
        )

        change_signal = float(
            row["change_signal"]
        )

        graph_impact = float(
            row["graph_impact"]
        )

        challenge_score = float(
            row["challenge_score"]
        )

        challenge_status = row[
            "challenge_status"
        ]

        checks = {
            "strong_anomaly":
                anomaly_strength >= 0.60,

            "change_temporally_aligned":
                change_signal > 0.0,

            "graph_can_explain_impact":
                graph_impact > 0.0,

            "challenger_survived":
                challenge_status == "supported",
        }

        passed_checks = sum(
            1
            for value in checks.values()
            if value
        )

        graph_component = min(
            graph_impact * 3.0,
            1.0,
        )

        causal_score = (
            0.35 * challenge_score
            + 0.30 * anomaly_strength
            + 0.20 * change_signal
            + 0.15 * graph_component
        )

        causal_score = max(
            0.0,
            min(
                causal_score,
                1.0,
            ),
        )

        if challenge_status == "rejected":
            disposition = "rejected_candidate"

        elif (
            challenge_status == "supported"
            and causal_score >= 0.70
            and passed_checks >= 3
        ):
            disposition = "supported_candidate"

        elif causal_score >= 0.50:
            disposition = "weakened_candidate"

        else:
            disposition = "inconclusive"

        rows.append(
            {
                "hypothesis_id":
                    row["hypothesis_id"],

                "incident_id":
                    row["incident_id"],

                "rank":
                    int(row["rank"]),

                "candidate_service":
                    row["candidate_service"],

                "original_rca_score":
                    float(
                        row["rca_score"]
                    ),

                "challenge_score":
                    challenge_score,

                "causal_consistency_score":
                    round(
                        causal_score,
                        6,
                    ),

                "causal_checks_passed":
                    passed_checks,

                "causal_checks_total":
                    len(checks),

                "causal_checks":
                    checks,

                "challenge_status":
                    challenge_status,

                "final_disposition":
                    disposition,

                "root_cause_status":
                    "unconfirmed",

                "confirmed_root_cause":
                    False,

                "challenger_completed":
                    bool(
                        row[
                            "challenger_completed"
                        ]
                    ),

                "requires_human_confirmation":
                    True,
            }
        )

    return (
        pl.DataFrame(
            rows,
            strict=False,
        )
        .sort(
            [
                "incident_id",
                "rank",
            ]
        )
    )
