# Step 27 RE2-TT Held-out Results

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | OK | Fallback | Timeout | Hard fail |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.066667 | 0.311111 | 0.555556 | 0.313333 | 4.333333 | 90 | 0 | 0 | 0 |
| v2a | 0.533333 | 0.800000 | 0.877778 | 0.742222 | 6.846667 | 90 | 0 | 0 | 0 |
| threshold | 0.577778 | 0.833333 | 0.888889 | 0.780000 | 6.933333 | 90 | 0 | 0 | 0 |
| random | 0.044444 | 0.066667 | 0.133333 | 0.082222 | 1.040000 | 90 | 0 | 0 | 0 |
| pagerank | 0.000000 | 0.244444 | 0.544444 | 0.248889 | 4.246667 | 90 | 0 | 0 | 0 |
| baro | 0.677778 | 0.844444 | 0.866667 | 0.806667 | 6.760000 | 90 | 0 | 0 | 0 |
| circa | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 10 | 80 | 0 |
| mmbaro | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0 |
| mmcirca | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0 |

Primary denominator is all 90 held-out RE2-TT cases for runnable methods.
Fallbacks, timeouts, and hard failures count as misses under the frozen scoring policy.
mmBARO/mmCIRCA are n/a (outside pinned input contract), excluded from numerical comparison, and are not scored as 90 misses.
See step27_results.json for paired CIs, per-fault tables, valid-only secondary metrics, and bootstrap provenance.

RE2-TT was evaluated under the frozen Step 27 protocol.

## Methodology notes

- CIRCA used a frozen per-case timeout of 1800 seconds (30 minutes), set on 2026-10-05 before any CIRCA ranking result was inspected or used for tuning. This was a compute-budget methodology decision, not a result-dependent adjustment.
- The CIRCA run was interrupted and resumed several times. Resume is methodologically equivalent because cases are independent, the per-case RNG is independent, and already completed case JSON files are treated as cached artifacts and skipped; no completed ranking is used to alter a later case.
- Final CIRCA coverage is 0 valid rankings, 80 timeout_unranked, 10 fallback_unranked, and 0 hard_failed. All 10 fallbacks have the same recorded reason: ValueError: Data correlation matrix is singular. Cannot run fisherz test. Please check your data. The final 80/10 split is the authoritative tally from the 90 saved case files and the CIRCA run summary.
- CIRCA's zero valid rankings in this run reflect the imposed compute budget, the approximately 3.7 GiB WSL environment, and the larger Train Ticket graph under this evaluation setup; they must not be interpreted as a claim about CIRCA's algorithmic quality in general.
- Other machine workloads, including GraphShield test suites, Docker, and Redis, shared the host during parts of the CIRCA run. This is recorded as an execution-environment limitation rather than a methodological adjustment.
- mmBARO and mmCIRCA are n/a because they are outside the pinned input contract; they are excluded from numerical comparison rather than scored as misses.
