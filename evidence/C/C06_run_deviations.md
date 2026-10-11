# Phase C6 Registered-Run Deviations

This file is post-freeze operational evidence created after `freeze/C-prerun-v3`.
It is outside the v3 manifest. It records execution deviations only and does
not modify any frozen code, configuration, registry, scenario, analysis, or
detector-fit artifact.

## C6-DEV-001 — Pre-injection payment reset timeout

- **Run:** `C-TRAIN-BDR-12`
- **Partition / scenario:** `TRAIN / bad_deployment_rollback`
- **Seed:** `681377953`
- **Run start recorded by loop:** `2026-10-11T19:00:21.070984Z`
- **Interruption record time:** `2026-10-11T19:00:36.425987Z`
- **Failure location:** the registered executor's initial
  `POST http://localhost:8103/failure-mode/reset`, before Kafka consumer
  start, baseline workload, and `injection_start`.
- **Observed exception:** `httpx.ReadTimeout`.
- **Executor timeout:** `httpx.AsyncClient(timeout=10.0)`.
- **Recorded status:** `infrastructure_invalid_interrupted`.
- **Reason:** `executor_interrupted_or_crashed`.
- **Result visibility:** no registered algorithmic result was visible. The run
  directory contained preflight health plus the infrastructure-invalid summary;
  no injection, detection, RCA, Guard, remediation, verification, or resource
  result was completed.
- **Treatment:** keep the invalid run record. Do not delete, rewrite, or rerun
  the completed invalid primary row.

## C6-DEV-002 — Operator-triggered spare start

- **Run:** `C-SPARE-TRAIN-BDR-01`
- **Replacement for:** `C-TRAIN-BDR-12`
- **Partition / scenario:** `TRAIN / bad_deployment_rollback`
- **Seed:** `1359673832`
- **Start recorded by loop:** `2026-10-11T19:00:43.252399Z`
- **Interruption record time:** `2026-10-11T19:01:58.810570Z`
- **Cause:** during post-failure diagnosis, an operator-triggered second
  `--detach` invocation started the preregistered replacement spare after the
  first detached process had already exited.
- **Stop:** the spare was stopped by operator `SIGINT` immediately after the
  unintended start was identified.
- **Recorded status:** `infrastructure_invalid_interrupted`.
- **Accounting:** the spare is preserved and counted as a consumed TRAIN
  bad-deployment spare. It is not deleted or rerun.
- **Result visibility:** no registered algorithmic result was completed.
- **Operational rule from this point:** `--detach` is never re-invoked during
  C6 diagnosis or status checking. Any future restart requires an explicit
  authorized restart decision after diagnosis, using the frozen resumable loop
  semantics and without rerunning completed rows.

No C7 detector fit, VALIDATION run, or TEST run was started by either deviation.
