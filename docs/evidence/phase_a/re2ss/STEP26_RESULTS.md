# Step 26 RE2-SS Held-out Results

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | OK | Fallback | Hard fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.266667 | 0.611111 | 0.888889 | 0.606667 | 1.422222 | 90 | 0 | 0 |
| v2a | 0.822222 | 0.955556 | 0.977778 | 0.928889 | 1.564444 | 90 | 0 | 0 |
| threshold | 0.811111 | 0.955556 | 0.988889 | 0.926667 | 1.582222 | 90 | 0 | 0 |
| random | 0.155556 | 0.411111 | 0.633333 | 0.413333 | 1.013333 | 90 | 0 | 0 |
| pagerank | 0.311111 | 0.666667 | 0.944444 | 0.637778 | 1.511111 | 90 | 0 | 0 |
| baro | 0.833333 | 0.977778 | 1.000000 | 0.948889 | 1.600000 | 90 | 0 | 0 |
| circa | 0.800000 | 0.955556 | 0.977778 | 0.920000 | 1.564444 | 89 | 1 | 0 |
| mmbaro | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 |
| mmcirca | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 |

Primary denominator is all 90 held-out RE2-SS cases for runnable methods.
Fallbacks and hard failures count as misses under E4/E6.
mmBARO/mmCIRCA are n/a (input unavailable), excluded from numerical comparison, and are not scored as 90 misses.
See step26_results.json for paired CIs, per-fault tables, valid-only secondary metrics, and bootstrap provenance.

RE2-TT was not accessed.

## Evidence and stop checkpoint

Frozen SentinelOps v1 remains primary. V2a is the post-hoc OB variant frozen
before SS access. All seven runnable methods have 90 saved case records.
CIRCA has one `fallback_unranked` case, `re2ss_orders_delay_1`; it counts
as a miss in the primary all-90 denominator. Its secondary valid-only
denominator is 89. All other runnable methods have 90 valid rankings.

The scorer was run only after V2a and all four CIRCA shards completed and
the workers exited. Its checksum is unchanged from `dcb02f8`.
[Prescore gate](step26_prescore_validation.json),
[scoring verification](step26_score_validation.json), and
[evidence manifest](step26_evidence_manifest.json) record coverage, hashes,
revisions, method configuration and runtime summaries. An independent
weighted-case check matched 925 numerical values/intervals and confirmed
that all 630 case files were unchanged during scoring.

The mm rows mean **n/a (outside pinned input contract)**; the official archive
does ship logts, but that modality is outside the selected frozen HF contract.
Neither mm method was run or counted as 90 misses in this cleanup.

The frozen export contains overall paired CIs and per-fault individual-method
CIs; it does not export per-fault paired CIs. No superiority or significance
claim is added here. Paired V2a-minus-threshold Avg@5 is +0.002222, with 95% CI
[-0.008889, 0.015556]; the interval includes zero.

The scorer eagerly reads the shared catalog before selecting SS rows.
"RE2-TT was not accessed" above refers to raw TT cases and TT evaluation;
it is not a claim that the shared catalog contains no TT metadata.

The four preceding changes were documentation only. No job was started or
killed by this cleanup, and no ranking algorithm, input, threshold, weight,
seed, topology, filter or scoring rule was changed. No push was performed.
Step 26 is complete and this session stops for review. Step 27 is not started.
