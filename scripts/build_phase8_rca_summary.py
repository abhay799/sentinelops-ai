from pathlib import Path

import polars as pl

from sentinelops.rca.validation import (
    validate_rca_hypotheses,
)

INPUT = Path(
    "data/processed/rca/"
    "rca_hypotheses_v1.parquet"
)

OUTPUT = Path(
    "data/processed/rca/"
    "rca_summary_v1.parquet"
)


hypotheses = pl.read_parquet(
    INPUT
)


errors = validate_rca_hypotheses(
    hypotheses
)

if errors:
    raise RuntimeError(
        "RCA validation failed:\n"
        + "\n".join(errors)
    )


rows = []

for incident_id in (
    hypotheses[
        "incident_id"
    ]
    .unique()
    .to_list()
):

    incident_hypotheses = (
        hypotheses
        .filter(
            pl.col("incident_id")
            == incident_id
        )
        .sort("rank")
    )

    candidates = (
        incident_hypotheses
        .to_dicts()
    )

    top = candidates[0]

    alternatives = [
        {
            "rank":
                int(
                    candidate[
                        "rank"
                    ]
                ),

            "candidate_service":
                candidate[
                    "candidate_service"
                ],

            "rca_score":
                float(
                    candidate[
                        "rca_score"
                    ]
                ),

            "confidence":
                candidate[
                    "confidence"
                ],
        }
        for candidate
        in candidates[1:]
    ]

    rows.append(
        {
            "incident_id":
                incident_id,

            "top_candidate":
                top[
                    "candidate_service"
                ],

            "top_candidate_score":
                float(
                    top[
                        "rca_score"
                    ]
                ),

            "top_candidate_confidence":
                top[
                    "confidence"
                ],

            "candidate_count":
                len(candidates),

            "alternative_count":
                len(alternatives),

            "alternatives":
                alternatives,

            "root_cause_status":
                "unconfirmed",

            "challenger_required":
                True,

            "human_confirmation_required":
                True,
        }
    )


summary = pl.DataFrame(
    rows
)


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

summary.write_parquet(
    OUTPUT
)


print()
print("=" * 70)
print(
    " SENTINELOPS AI - PHASE 8 RCA SUMMARY"
)
print("=" * 70)

print(
    summary.select(
        [
            "incident_id",
            "top_candidate",
            "top_candidate_score",
            "top_candidate_confidence",
            "candidate_count",
            "alternative_count",
            "root_cause_status",
        ]
    )
)

print()
print(
    "PHASE 8 RCA VALIDATION: PASSED"
)
