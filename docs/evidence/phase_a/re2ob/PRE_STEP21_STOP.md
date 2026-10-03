# Pre-Step-21 validation and stop

E5 is committed as bb35830; E6 is committed as 42a148e.
Both CIRCA/mmCIRCA jobs finished. No relaunch was necessary.
All four baseline methods have exactly the same 90 case IDs, no hard
failures, and summary counts matching their case records. E3 filtering is
an order-preserving projection. Fallback flags, signals, reasons, and empty
scored rankings were verified. The machine-readable validation records
artifact hashes and counts; it computes no accuracy metrics.

| Method | Valid | Fallback unranked | Hard failures | Total |
|---|---:|---:|---:|---:|
| BARO | 90 | 0 | 0 | 90 |
| CIRCA | 86 | 4 | 0 | 90 |
| mmBARO | 90 | 0 | 0 | 90 |
| mmCIRCA | 89 | 1 | 0 | 90 |

## Unchanged stop rule

E3 states: "A disagreement beyond sampling noise remains a stop condition."
random_vs_chance_sanity.json has sanity_pass false: the seed-42 random
AC@3 has 15 hits, outside the recorded central 95% interval of 17-33.
The subsequent multi-seed diagnostic is random-only and diagnostic-only;
it does not revoke this rule. Steps 21-24 have therefore not run.
The Step-25 results presentation cannot yet be reached.

## Supplied continuation checklist

21. Overall service-level AC@1/3/5, Avg@5, Chance@5 and Lift@5 for
SentinelOps, threshold, random, PageRank, BARO, CIRCA, mmBARO and mmCIRCA.
E3 before top-k; E4 all-90 primary denominator, fallbacks as misses;
secondary valid-only table with explicit reduced denominators.
22. The same metrics for CPU, memory, disk, socket, delay and loss.
23. Case bootstrap, seed 42, 10,000 draws, 95% percentile CIs overall
and per fault; shared resamples for SentinelOps minus each baseline.
Random rankings are never redrawn.
24. JSON/CSV evidence with revisions, seeds, config, candidate policy,
raw rankings, coverage, fallback/failure counts, per-fault results,
CIs and runtimes. A4 sensitivity is separate from primary topology.
25. Stop and present the RE2-OB table before held-out suite access.

No push or RE2-SS/RE2-TT data access occurred in this continuation.
