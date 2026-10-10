# Phase C C4 — Prerun Amendment v2

**Status:** preregistered before registered run 1.
**Reason:** the original `freeze/C-prerun` contained the frozen registry, analysis and evidence schema but did not contain an executable registered-run orchestration path. Zero registered runs had started and zero registered results were visible when this amendment was created.

## Classification

This is a **pre-result methodology/engineering amendment** to make the already frozen C6 protocol executable. It does not change:

- the master seed;
- any registered run ID or run seed;
- TRAIN / VALIDATION / TEST membership;
- the 60-run order;
- scenario definitions or durations;
- the bad-deployment profile;
- SentinelGuard thresholds;
- remediation thresholds;
- the registered analysis metrics or bootstrap settings;
- the invalid-run replacement policy;
- the reserved spare seeds.

The original tag `freeze/C-prerun` remains immutable. This amendment is frozen under a new tag, `freeze/C-prerun-v2`.

## Registered executor

Added:

- `src/sentinelops/chaos/registered_harness.py`
- `scripts/phase_c06_run_registered.py`
- `tests/test_phase_c6_registered_harness.py`

The executor:

1. accepts only a run ID already present in the frozen registry;
2. accepts only TRAIN rows during C6;
3. performs the frozen 120 s healthy baseline;
4. applies the scenario from the frozen scenario files;
5. captures Kafka telemetry into an isolated, Git-ignored run work directory;
6. runs the existing SentinelOps Phase 4–14 pipeline scripts from that isolated run workspace;
7. records explicit detection/correlation/RCA/challenger/plan/Guard/authorization/remediation/verification evidence;
8. preserves Guard and human authorization in the remediation path;
9. uses only the existing Phase 14 local-sandbox execution path for scored rollback;
10. records emergency cleanup separately and never counts cleanup as remediation;
11. persists injection ground truth only after scored verification or emergency-cleanup verification has completed;
12. records CPU, memory, wall-clock and service-health evidence.

## TRAIN detector note

C6 TRAIN chain evidence uses the existing legacy Phase 5 detector path only as **TRAIN development-chain evidence**. It is labeled `TRAIN_legacy_development_only` and is not the registered held-out detector.

The registered anomaly detector is still fit only at C7 from registered TRAIN baseline feature rows, then frozen before any VALIDATION run, exactly as preregistered.

## Injection-end semantics

The configured scenario duration is recorded separately as the planned injection window. The injected service remains degraded while the evidence chain runs. `injection_end` is the actual time the scored rollback begins or, if no scored remediation occurs, the time emergency cleanup resets the service. This preserves the actual fault-active interval and keeps cleanup separate from scored remediation.

## Tests before registered execution

Before this amendment freeze:

- Ruff passed for all three new files.
- `tests/test_phase_c6_registered_harness.py`: 7 passed.
- No live registered run was executed by the tests.
- No C6 registered evidence file existed.

## Gate

Registered C6 run 1 may start only after:

- this amendment and the new executor are committed;
- every v2 freeze hash is recorded;
- tag `freeze/C-prerun-v2` exists and is pushed;
- a fresh clone from that tag reproduces every v2 freeze hash;
- all seven local demo services and required Kafka/core dependencies are healthy.

The first frozen registry row remains:

`C-TRAIN-BDR-12` — seed `681377953` — scenario `bad_deployment_rollback`.
