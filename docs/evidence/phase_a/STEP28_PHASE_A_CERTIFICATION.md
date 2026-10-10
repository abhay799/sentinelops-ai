# Step 28 — Phase A Final Evaluation Certification

**Status:** COMPLETE
**Decision:** CERTIFIED WITH CAVEATS
**Scope:** internal local/synthetic experimental certification only

## 1. Scope and evidence order

Phase A evaluates SentinelOps AI detection and deterministic root-cause analysis under the frozen RCAEval protocol.

Evaluation order:

1. RE2-OB — development/pilot
2. RE2-SS — held-out
3. RE2-TT — held-out

Primary protocol:

`docs/evidence/PHASE_A_EVALUATION_SPEC.md`

Revision chain actually used:

- pre-existing core detector/RCA reference: `9fd8b0967fbf94607e5e2b5213a7895669d07a4e`
- V2 development freeze/selection: `d840a5a23197fde54b3e8c2586a3fecb7eba41fc`
- RE2-TT runner/scorer freeze: `c4c42241ed9f89ff05b923798078846c57de5e56`
- audited Step 27 producing scripts: `05dc014c08278eb48c0f361456f35ee17b04e788`
- certification closeout revision: this commit; the exact SHA cannot be embedded in its own content-addressed commit without changing that SHA, so the final Git hash is reported externally at closeout
- RCAEval: `259ea4167160256a74ad30004aa3d96a998c846e`
- RCAEval dataset: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`
- bootstrap/random seed: `42`
- bootstrap resamples: `10000`
- interval: 95% percentile case bootstrap

The pre-existing core detector/RCA diff `d840a5a..9fd8b09` is empty for `src/sentinelops/anomaly/detectors.py` and the core `src/sentinelops/rca/` implementation. The Phase A evaluation-specific detector/ranking layer (`src/sentinelops/evaluation/rcaeval_*.py` and related Phase A scripts) postdates `9fd8b09`, so the broader evaluation-layer diff is not empty.

This is not an external, regulatory, production, safety, or security certification.

## 2. Seven-method benchmark matrix

All headline rows use the suite's frozen primary all-case denominator. A non-`ok` runnable result counts as a miss.

### RE2-OB — development

Chance@5 = 5/11 = 0.454545.

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | Valid |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 0.211111 | 0.744444 | 0.966667 | 0.682222 | 2.126667 | 90/90 |
| V2a | 0.844444 | 0.966667 | 1.000000 | 0.946667 | 2.200000 | 90/90 |
| threshold | 0.866667 | 0.966667 | 1.000000 | 0.955556 | 2.200000 | 90/90 |
| random | 0.033333 | 0.166667 | 0.422222 | 0.213333 | 0.928889 | 90/90 |
| PageRank | 0.200000 | 0.655556 | 0.977778 | 0.611111 | 2.151111 | 90/90 |
| BARO | 0.144444 | 0.877778 | 0.944444 | 0.742222 | 2.077778 | 90/90 |
| CIRCA | 0.666667 | 0.877778 | 0.900000 | 0.833333 | 1.980000 | 86/90 |

V2a is the RE2-OB-selected variant, frozen before held-out suite access.

### RE2-SS — held-out

Chance@5 = 5/8 = 0.625000.

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | Valid |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 0.266667 | 0.611111 | 0.888889 | 0.606667 | 1.422222 | 90/90 |
| V2a | 0.822222 | 0.955556 | 0.977778 | 0.928889 | 1.564444 | 90/90 |
| threshold | 0.811111 | 0.955556 | 0.988889 | 0.926667 | 1.582222 | 90/90 |
| random | 0.155556 | 0.411111 | 0.633333 | 0.413333 | 1.013333 | 90/90 |
| PageRank | 0.311111 | 0.666667 | 0.944444 | 0.637778 | 1.511111 | 90/90 |
| BARO | 0.833333 | 0.977778 | 1.000000 | 0.948889 | 1.600000 | 90/90 |
| CIRCA | 0.800000 | 0.955556 | 0.977778 | 0.920000 | 1.564444 | 89/90 |

### RE2-TT — held-out

Chance@5 = 5/39 = 0.128205.

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | Valid |
|---|---:|---:|---:|---:|---:|---:|
| v1 | 0.066667 | 0.311111 | 0.555556 | 0.313333 | 4.333333 | 90/90 |
| V2a | 0.533333 | 0.800000 | 0.877778 | 0.742222 | 6.846667 | 90/90 |
| threshold | 0.577778 | 0.833333 | 0.888889 | 0.780000 | 6.933333 | 90/90 |
| random | 0.044444 | 0.066667 | 0.133333 | 0.082222 | 1.040000 | 90/90 |
| PageRank | 0.000000 | 0.244444 | 0.544444 | 0.248889 | 4.246667 | 90/90 |
| BARO | 0.677778 | 0.844444 | 0.866667 | 0.806667 | 6.760000 | 90/90 |
| CIRCA | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0/90 |

CIRCA's RE2-TT all-90 row is a compute-budget outcome: 80 timeouts and 10 fallbacks, with no valid rankings.

## 3. Cross-suite generalization

### Avg@5 by suite

| Method | RE2-OB | RE2-SS | RE2-TT | SS -> TT change |
|---|---:|---:|---:|---:|
| v1 | 0.682222 | 0.606667 | 0.313333 | -0.293334 |
| V2a | 0.946667 | 0.928889 | 0.742222 | -0.186667 |
| threshold | 0.955556 | 0.926667 | 0.780000 | -0.146667 |
| random | 0.213333 | 0.413333 | 0.082222 | -0.331111 |
| PageRank | 0.611111 | 0.637778 | 0.248889 | -0.388889 |
| BARO | 0.742222 | 0.948889 | 0.806667 | -0.142222 |
| CIRCA | 0.833333 | 0.920000 | 0.000000 | -0.920000 |

Raw top-k accuracy is lower on RE2-TT than RE2-SS for the methods with valid rankings, but the suites are not directly comparable because RE2-TT has a much larger effective candidate set: 39 versus 8, with Chance@5 0.128205 versus 0.625000. Lift@5 therefore provides necessary context beside raw AC@5:

| Method | SS AC@5 | SS Lift@5 | TT AC@5 | TT Lift@5 |
|---|---:|---:|---:|---:|
| v1 | 0.888889 | 1.422222 | 0.555556 | 4.333333 |
| V2a | 0.977778 | 1.564444 | 0.877778 | 6.846667 |
| threshold | 0.988889 | 1.582222 | 0.888889 | 6.933333 |
| random | 0.633333 | 1.013333 | 0.133333 | 1.040000 |
| PageRank | 0.944444 | 1.511111 | 0.544444 | 4.246667 |
| BARO | 1.000000 | 1.600000 | 0.866667 | 6.760000 |
| CIRCA | 0.977778 | 1.564444 | 0.000000 | 0.000000* |

`*` CIRCA has 0/90 valid RE2-TT rankings, so its TT raw score and lift are compute-budget outcomes rather than an accuracy comparison.

V2a addresses the v1 saturation/tie pathology seen in RE2-OB: v1 had 78 top-score ties, while V2a had 0. The V2a strength audit records all 90 case maxima above 1.0 and 774/990 E3 service strengths above 1.0, preserving information that v1 clipping had collapsed.

The held-out pattern is consistent with that development diagnosis: V2a retains substantially higher Avg@5 than v1 on both SS and TT. Its held-out results are comparable to the threshold baseline on SS and somewhat lower on TT. BARO has higher Avg@5 than V2a on TT.

## 4. Confidence intervals and paired differences

Bootstrap settings: 10,000 case resamples, seed 42, 95% percentile intervals.

### RE2-SS primary Avg@5 95% CIs

| Method | Avg@5 | 95% CI |
|---|---:|---|
| v1 | 0.606667 | [0.533333, 0.675556] |
| V2a | 0.928889 | [0.886667, 0.964444] |
| threshold | 0.926667 | [0.886667, 0.962222] |
| random | 0.413333 | [0.335556, 0.491111] |
| PageRank | 0.637778 | [0.571111, 0.702222] |
| BARO | 0.948889 | [0.917778, 0.975556] |
| CIRCA | 0.920000 | [0.877778, 0.957778] |

### RE2-TT primary Avg@5 95% CIs

| Method | Avg@5 | 95% CI |
|---|---:|---|
| v1 | 0.313333 | [0.244444, 0.384444] |
| V2a | 0.742222 | [0.666667, 0.811111] |
| threshold | 0.780000 | [0.708889, 0.846667] |
| random | 0.082222 | [0.035556, 0.135556] |
| PageRank | 0.248889 | [0.191111, 0.311111] |
| BARO | 0.806667 | [0.733333, 0.875556] |
| CIRCA | 0.000000 | [0.000000, 0.000000] |

The V2a RE2-OB development artifact exports paired CIs but not a standalone V2a primary CI; Step 28 does not introduce a post-hoc recomputation.

### Paired Avg@5 differences

| Suite | Pair | Difference | 95% CI |
|---|---|---:|---|
| OB | V2a - v1 | +0.264444 | [0.213333, 0.317778] |
| OB | V2a - threshold | -0.008889 | [-0.026667, 0.006667] |
| SS | V2a - v1 | +0.322222 | [0.253333, 0.395556] |
| SS | V2a - threshold | +0.002222 | [-0.008889, 0.015556] |
| SS | V2a - BARO | -0.020000 | [-0.051111, 0.006667] |
| TT | V2a - v1 | +0.428889 | [0.328889, 0.524444] |
| TT | V2a - threshold | -0.037778 | [-0.080000, ~0.000000] |
| TT | V2a - BARO | -0.064444 | [-0.122222, -0.006667] |

These are descriptive paired intervals under the frozen scorer. No family-wise significance claim is made.

## 5. Per-fault Avg@5

Each fault has 15 cases per suite.

### RE2-OB

| Fault | v1 | V2a | threshold | random | PageRank | BARO | CIRCA |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU | 0.666667 | 0.946667 | 0.973333 | 0.120000 | 0.600000 | 0.640000 | 0.760000 |
| Delay | 0.760000 | 0.893333 | 0.893333 | 0.306667 | 0.626667 | 0.666667 | 0.706667 |
| Disk | 0.760000 | 0.973333 | 0.973333 | 0.146667 | 0.573333 | 0.813333 | 0.866667 |
| Loss | 0.546667 | 0.920000 | 0.920000 | 0.226667 | 0.586667 | 0.800000 | 0.853333 |
| Memory | 0.640000 | 1.000000 | 1.000000 | 0.240000 | 0.626667 | 0.866667 | 0.960000 |
| Socket | 0.720000 | 0.946667 | 0.973333 | 0.240000 | 0.653333 | 0.666667 | 0.853333 |

### RE2-SS

| Fault | v1 | V2a | threshold | random | PageRank | BARO | CIRCA |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU | 0.666667 | 0.960000 | 0.933333 | 0.440000 | 0.680000 | 1.000000 | 0.986667 |
| Delay | 0.666667 | 0.853333 | 0.866667 | 0.480000 | 0.720000 | 0.880000 | 0.800000 |
| Disk | 0.680000 | 0.933333 | 0.946667 | 0.453333 | 0.640000 | 0.973333 | 0.893333 |
| Loss | 0.440000 | 0.960000 | 0.960000 | 0.280000 | 0.586667 | 0.946667 | 0.906667 |
| Memory | 0.600000 | 0.986667 | 1.000000 | 0.320000 | 0.666667 | 0.986667 | 0.986667 |
| Socket | 0.586667 | 0.880000 | 0.853333 | 0.506667 | 0.533333 | 0.906667 | 0.946667 |

### RE2-TT

| Fault | v1 | V2a | threshold | random | PageRank | BARO | CIRCA |
|---|---:|---:|---:|---:|---:|---:|---:|
| CPU | 0.253333 | 0.626667 | 0.680000 | 0.080000 | 0.253333 | 0.720000 | 0.000000 |
| Delay | 0.266667 | 0.693333 | 0.786667 | 0.160000 | 0.186667 | 0.640000 | 0.000000 |
| Disk | 0.240000 | 0.986667 | 1.000000 | 0.000000 | 0.226667 | 1.000000 | 0.000000 |
| Loss | 0.346667 | 0.546667 | 0.560000 | 0.053333 | 0.253333 | 0.653333 | 0.000000 |
| Memory | 0.386667 | 0.920000 | 0.866667 | 0.053333 | 0.266667 | 0.986667 | 0.000000 |
| Socket | 0.386667 | 0.680000 | 0.786667 | 0.146667 | 0.306667 | 0.840000 | 0.000000 |

## 6. Coverage, fallback, and timeout accounting

| Suite | Method | Valid | Fallback | Timeout | Hard fail |
|---|---|---:|---:|---:|---:|
| OB | CIRCA | 86/90 | 4/90 (4.44%) | 0 | 0 |
| SS | CIRCA | 89/90 | 1/90 (1.11%) | 0 | 0 |
| TT | CIRCA | 0/90 | 10/90 (11.11%) | 80/90 (88.89%) | 0 |

All other methods in the seven-method matrix have 90/90 valid rankings and zero fallback/timeout/hard-failure counts in these final suite artifacts.

For TT, all 10 CIRCA fallbacks record the same reason: `ValueError: Data correlation matrix is singular. Cannot run fisherz test. Please check your data.`

mmBARO/mmCIRCA are not included in the seven-method cross-suite matrix because they are unavailable under the pinned SS/TT input contract. They are n/a in held-out suites, excluded from numerical comparison, and are not converted into misses. Their OB evidence remains preserved separately.

## 7. CIRCA RE2-TT compute-budget disclosure

The fixed CIRCA per-case timeout is 1800 seconds (30 minutes), set on 2026-10-05 before any CIRCA ranking result was inspected or used for tuning.

The run was interrupted and resumed several times. Resume is equivalent under this protocol because each case is independent, the per-case RNG is independent, and terminal cached case JSON files are skipped without using their outcomes to alter later cases.

Final TT CIRCA coverage:

- valid rankings: 0/90
- `timeout_unranked`: 80/90
- `fallback_unranked`: 10/90
- hard failures: 0/90

This reflects the imposed compute budget, the approximately 3.7 GiB WSL environment, and the larger Train Ticket graph under this setup. It is not a claim about CIRCA's algorithmic quality in general.

Other host workloads, including GraphShield test suites, Docker, and Redis, shared the machine during parts of the CIRCA run. This is an execution-environment limitation, not a methodological adjustment.

## 8. Methodology audit

| Gate | Result | Evidence/interpretation |
|---|---|---|
| Evaluation order | PASS | OB development -> SS held-out -> TT held-out |
| Held-out tuning | PASS | V2a frozen after OB and before SS access; no SS/TT outcome-driven tuning |
| Ground-truth leakage into ranking | PASS | frozen evaluator-only ground truth; ranking artifacts record ground truth not used for ranking |
| Scoring denominator | PASS | runnable methods use all 90 cases; non-`ok` outcomes count as misses |
| Bootstrap | PASS | seed 42, 10,000 case resamples, 95% percentile intervals |
| Candidate universes | PASS | OB N=11, SS N=8, TT metric-visible N=39; TT frozen allowlist N=45 |
| Topology | PASS WITH DISCLOSURE | OB trace-derived primary topology; A4 static topology remains post-hoc sensitivity only; SS/TT topology frozen by preflight |
| Fixed faults | PASS | CPU, memory, disk, delay, loss, socket |
| mm methods | PASS WITH N/A | mmBARO/mmCIRCA excluded on SS/TT by pinned input contract, not scored as misses |
| CIRCA TT runtime policy | PASS WITH CAVEAT | 1800-second limit set pre-result; 80 timeouts and 10 fallbacks explicitly retained |
| Script integrity | PASS | post-run diff audit found execution/status/reporting changes only; ranking logic and scoring math unchanged |

## 9. Step 27 script-integrity note

Integrity record:

`docs/evidence/phase_a/STEP27_SCRIPT_INTEGRITY.md`

Commit recording the scripts that produced Step 27 results:

`05dc014c08278eb48c0f361456f35ee17b04e788`

Recorded SHA-256:

- `scripts/phase_a_step27_score.py`: `3ca8cc77aa6dae0f55885db77e6a3b6c465462a5c8d120ae60e20d16d2b16bb2`
- `scripts/phase_a_step27_rcaeval_run.py`: `fdee1bc33ba59a9d70a9cfa566f461110fcb20ebdb5fc9fc81983dbe30ffb9f3`

Classification:

- runner: fixed 1800-second timeout policy, Queue-to-Pipe result-transport fix, explicit timeout resume/status accounting
- scorer: explicit timeout coverage/reporting
- no ranking algorithm, candidate filter, topology, model parameter, metric formula, bootstrap math, or valid-only rule was changed

Backup snapshots remain intentionally untracked and are listed with hashes in the integrity record.

## 10. Certification decision

### CERTIFIED WITH CAVEATS

Phase A is certified internally under the frozen local/synthetic evaluation protocol, with the runtime and input-contract caveats above.

Permitted claim text:

> SentinelOps Phase A shows that V2a removes the v1 saturation/tie pathology diagnosed on the RE2-OB development suite and retains substantially higher Avg@5 than v1 on both held-out suites. On RE2-SS, V2a and the frozen threshold baseline are comparable on Avg@5: the paired V2a-minus-threshold difference is +0.002222 with 95% CI [-0.008889, 0.015556], so the evidence does not support a superiority claim. On RE2-TT, V2a has a lower Avg@5 point estimate than threshold (difference -0.037778; paired 95% CI approximately [-0.080000, 0.000000]) and is below BARO on Avg@5 (difference -0.064444; 95% CI [-0.122222, -0.006667]). Raw top-k accuracy is lower on RE2-TT, but RE2-TT has a much larger effective candidate set than RE2-SS (39 versus 8; Chance@5 0.128205 versus 0.625000), so the suites are not directly comparable; for V2a, AC@5/Lift@5 is 0.977778/1.564444 on SS versus 0.877778/6.846667 on TT. CIRCA's RE2-TT values are excluded from accuracy interpretation because the run produced zero valid rankings. mmBARO/mmCIRCA are n/a under the pinned held-out input contract.

Additional certification caveats:

- run-summary JSON files do not embed runner SHA-256 values; runner provenance is established by the freeze/integrity records rather than by a per-summary embedded hash;
- BARO and CIRCA ran through `scripts/phase_a_step27_rcaeval_run.py`, while v1, V2a, threshold, random, and PageRank ran through `scripts/phase_a_step27_run.py`.

Not permitted:

- claims of production readiness
- claims of external/security/regulatory certification
- claims that TT CIRCA zeros measure CIRCA's general algorithmic quality
- claims that unavailable mm methods failed
- claims that held-out outcomes were used for tuning
- any wording that claims general baseline superiority
