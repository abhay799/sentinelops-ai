from pathlib import Path

import polars as pl
import yaml

from sentinelops.rca.challenger import (
    challenge_rca_hypotheses,
)

INPUT = Path(
    "data/processed/rca/"
    "rca_hypotheses_v1.parquet"
)

OUTPUT = Path(
    "data/processed/rca/"
    "rca_challenges_v1.parquet"
)


with open(
    "configs/rca_challenger.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "rca_challenger"
    ]


hypotheses = pl.read_parquet(
    INPUT
)


challenges = challenge_rca_hypotheses(
    hypotheses,
    config,
)


if challenges.is_empty():
    raise RuntimeError(
        "No RCA challenges produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

challenges.write_parquet(
    OUTPUT
)


print()
print("=" * 72)
print(
    " SENTINELOPS AI - PHASE 9 RCA CHALLENGER"
)
print("=" * 72)

print(
    challenges.select(
        [
            "incident_id",
            "rank",
            "candidate_service",
            "original_rca_score",
            "challenge_score",
            "challenge_status",
            "supporting_evidence_count",
            "contradicting_evidence_count",
            "confirmed_root_cause",
        ]
    )
)

print()
print(
    "PHASE 9 RCA CHALLENGER: PASSED"
)
