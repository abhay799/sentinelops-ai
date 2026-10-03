# Step 26 Execution-only Amendment: deterministic CIRCA sharding

Date: 2026-10-03
Status: COMMITTED BEFORE SHARDED CIRCA EXECUTION AND BEFORE ANY RE2-SS AC@k SCORING.

The frozen sequential CIRCA runner proved impractically slow during Step 26. At the time
of this amendment, only the count/runtime state was inspected: CIRCA had written 1/90
per-case ranking records. No RE2-SS AC@k, Avg@5, Lift@5, paired CI, per-fault accuracy,
or method comparison had been computed. The existing first-case ranking content was not
used to choose this change.

This amendment changes execution scheduling only. RE2-SS cases remain independent and
are assigned by the lexically sorted case list using deterministic slicing
`case_ids[shard_index::shard_count]`. All CIRCA method inputs, preprocessing, 20-minute
normal/fault window, pinned RCAEval revision, `dataset="re2-ss"`, `dk_select_useful=False`,
`n_iter=len(columns)-1`, SLI disclosure, E3 allowlist, E4 fallback handling, E6 scoring,
and bootstrap rules remain unchanged.

Existing completed case JSON is retained and validated by the resumable runner; shards
skip an already terminal (`ok`, `fallback_unranked`, or `hard_failed`) case instead of
recomputing it. Shards write disjoint case IDs and separate shard summaries. No ranking
or scoring rule changes, and no held-out outcome is used to choose a method setting.

RE2-TT remains untouched. Never push.
