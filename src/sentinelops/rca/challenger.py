from __future__ import annotations

from typing import Any

import polars as pl


def clamp(
    value: float,
) -> float:

    return max(
        0.0,
        min(
            1.0,
            value,
        ),
    )


def challenge_status(
    score: float,
    support_threshold: float,
    reject_threshold: float,
) -> str:

    if score >= support_threshold:
        return "supported"

    if score <= reject_threshold:
        return "rejected"

    return "weakened"


def challenge_rca_hypotheses(
    hypotheses: pl.DataFrame,
    config: dict[str, Any],
) -> pl.DataFrame:

    rows: list[
        dict[str, Any]
    ] = []

    thresholds = config[
        "thresholds"
    ]

    penalties = config[
        "penalties"
    ]

    bonuses = config[
        "bonuses"
    ]

    for incident_id in (
        hypotheses[
            "incident_id"
        ]
        .unique()
        .to_list()
    ):

        incident_rows = (
            hypotheses
            .filter(
                pl.col("incident_id")
                == incident_id
            )
            .sort("rank")
        )

        candidates = (
            incident_rows
            .to_dicts()
        )

        if not candidates:
            continue

        top_score = float(
            candidates[0][
                "rca_score"
            ]
        )

        second_score = (
            float(
                candidates[1][
                    "rca_score"
                ]
            )
            if len(candidates) > 1
            else 0.0
        )

        for candidate in candidates:

            base_score = float(
                candidate[
                    "rca_score"
                ]
            )

            challenge_score = (
                base_score
            )

            supporting: list[
                dict[str, Any]
            ] = []

            contradicting: list[
                dict[str, Any]
            ] = []

            anomaly_strength = float(
                candidate[
                    "anomaly_strength"
                ]
            )

            change_signal = float(
                candidate[
                    "change_signal"
                ]
            )

            graph_impact = float(
                candidate[
                    "graph_impact"
                ]
            )

            primary_bonus = float(
                candidate[
                    "primary_service_bonus"
                ]
            )

            # -----------------------------------------
            # Anomaly strength
            # -----------------------------------------

            if anomaly_strength >= 0.60:

                challenge_score += float(
                    bonuses[
                        "strong_anomaly"
                    ]
                )

                supporting.append(
                    {
                        "type":
                            "strong_anomaly",

                        "value":
                            float(
                                anomaly_strength
                            ),

                        "description":
                            (
                                "Candidate shows "
                                "strong anomaly evidence"
                            ),
                    }
                )

            else:

                challenge_score -= float(
                    penalties[
                        "weak_anomaly"
                    ]
                )

                contradicting.append(
                    {
                        "type":
                            "weak_anomaly",

                        "value":
                            float(
                                anomaly_strength
                            ),

                        "description":
                            (
                                "Candidate anomaly "
                                "strength is weak"
                            ),
                    }
                )

            # -----------------------------------------
            # Change evidence
            # -----------------------------------------

            if change_signal > 0:

                challenge_score += float(
                    bonuses[
                        "change_signal"
                    ]
                )

                supporting.append(
                    {
                        "type":
                            "recent_change",

                        "value":
                            float(
                                change_signal
                            ),

                        "description":
                            (
                                "Recent change aligns "
                                "with the incident"
                            ),
                    }
                )

            else:

                challenge_score -= float(
                    penalties[
                        "no_change_signal"
                    ]
                )

                contradicting.append(
                    {
                        "type":
                            "no_change_signal",

                        "value":
                            0.0,

                        "description":
                            (
                                "No recent deployment "
                                "or change evidence"
                            ),
                    }
                )

            # -----------------------------------------
            # Graph impact
            # -----------------------------------------

            if graph_impact > 0:

                challenge_score += float(
                    bonuses[
                        "graph_impact"
                    ]
                )

                supporting.append(
                    {
                        "type":
                            "graph_impact",

                        "value":
                            float(
                                graph_impact
                            ),

                        "description":
                            (
                                "Candidate can explain "
                                "upstream service impact"
                            ),
                    }
                )

            else:

                challenge_score -= float(
                    penalties[
                        "no_graph_impact"
                    ]
                )

                contradicting.append(
                    {
                        "type":
                            "no_graph_impact",

                        "value":
                            0.0,

                        "description":
                            (
                                "Candidate has no "
                                "upstream graph impact"
                            ),
                    }
                )

            # -----------------------------------------
            # Incident primary-service evidence
            # -----------------------------------------

            if primary_bonus > 0:

                challenge_score += float(
                    bonuses[
                        "primary_service"
                    ]
                )

                supporting.append(
                    {
                        "type":
                            "primary_service",

                        "value":
                            1.0,

                        "description":
                            (
                                "Candidate is the "
                                "incident primary service"
                            ),
                    }
                )

            # -----------------------------------------
            # Stronger alternative challenge
            # -----------------------------------------

            candidate_score = float(
                candidate[
                    "rca_score"
                ]
            )

            strongest_other = max(
                [
                    float(
                        other[
                            "rca_score"
                        ]
                    )
                    for other in candidates
                    if (
                        other[
                            "candidate_service"
                        ]
                        != candidate[
                            "candidate_service"
                        ]
                    )
                ],
                default=0.0,
            )

            if (
                strongest_other
                > candidate_score
            ):

                challenge_score -= float(
                    penalties[
                        "stronger_alternative"
                    ]
                )

                contradicting.append(
                    {
                        "type":
                            "stronger_alternative",

                        "value":
                            float(
                                strongest_other
                            ),

                        "description":
                            (
                                "Another RCA candidate "
                                "has stronger evidence"
                            ),
                    }
                )

            challenge_score = clamp(
                challenge_score
            )

            evidence_total = (
                len(supporting)
                + len(contradicting)
            )

            if (
                evidence_total
                < int(
                    thresholds[
                        "minimum_evidence"
                    ]
                )
            ):
                status = (
                    "inconclusive"
                )

            else:
                status = challenge_status(
                    challenge_score,
                    support_threshold=float(
                        thresholds[
                            "support"
                        ]
                    ),
                    reject_threshold=float(
                        thresholds[
                            "reject"
                        ]
                    ),
                )

            rows.append(
                {
                    "hypothesis_id":
                        candidate[
                            "hypothesis_id"
                        ],

                    "incident_id":
                        incident_id,

                    "candidate_service":
                        candidate[
                            "candidate_service"
                        ],

                    "rank":
                        int(
                            candidate[
                                "rank"
                            ]
                        ),

                    "original_rca_score":
                        candidate_score,

                    "challenge_score":
                        float(
                            round(
                                challenge_score,
                                6,
                            )
                        ),

                    "challenge_status":
                        status,

                    "supporting_evidence_count":
                        len(
                            supporting
                        ),

                    "contradicting_evidence_count":
                        len(
                            contradicting
                        ),

                    "supporting_evidence":
                        supporting,

                    "contradicting_evidence":
                        contradicting,

                    "challenger_completed":
                        True,

                    "confirmed_root_cause":
                        False,

                    "requires_human_confirmation":
                        True,

                    "top_candidate_score":
                        top_score,

                    "second_candidate_score":
                        second_score,
                }
            )

    if not rows:
        return pl.DataFrame()

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