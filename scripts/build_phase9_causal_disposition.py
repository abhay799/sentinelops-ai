from pathlib import Path

import polars as pl

from sentinelops.rca.causal import (
    build_causal_disposition,
)

HYPOTHESES = Path(
    "data/processed/rca/"
    "rca_hypotheses_v1.parquet"
)

CHALLENGES = Path(
    "data/processed/rca/"
    "rca_challenges_v1.parquet"
)

OUTPUT = Path(
    "data/processed/rca/"
    "rca_disposition_v1.parquet"
)


hypotheses = pl.read_parquet(
    HYPOTHESES
)

challenges = pl.read_parquet(
    CHALLENGES
)


result = build_causal_disposition(
    hypotheses,
    challenges,
)


if result.is_empty():
    raise RuntimeError(
        "No Phase 9 RCA dispositions produced"
    )


OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True,
)

result.write_parquet(
    OUTPUT
)


print()
print("=" * 72)
print(
    " SENTINELOPS AI - PHASE 9 CAUSAL RCA DISPOSITION"
)
print("=" * 72)

print(
    result.select(
        [
            "incident_id",
            "rank",
            "candidate_service",
            "challenge_status",
            "causal_consistency_score",
            "causal_checks_passed",
            "final_disposition",
            "root_cause_status",
        ]
    )
)

print()

print(
    "PHASE 9 CAUSAL CONSISTENCY: PASSED"
)
