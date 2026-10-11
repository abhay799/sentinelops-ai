# Phase C6 Run Deviations

This file was created after the C6 TRAIN start attempt. It is outside the `freeze/C-prerun-v3` manifest and records post-freeze execution deviations only. No code, config, frozen file, VALIDATION, TEST, or C7 detector-fit action is authorized by this file.

## C6-DEV-001 — Pre-injection payment reset timeout on C-TRAIN-BDR-12

- **Run:** `C-TRAIN-BDR-12`
- **Partition / scenario / seed:** TRAIN / `bad_deployment_rollback` / `681377953`
- **Registered run start:** `2026-10-11T19:00:21.070984Z`
- **Interruption record:** `2026-10-11T19:00:36.425987Z`
- **Failure point:** before `injection_start`, while the registered executor called `POST http://localhost:8103/failure-mode/reset`.
- **Observed exception:** `httpx.ReadTimeout` under the frozen executor's `httpx.AsyncClient(timeout=10.0)`.
- **Recorded classification:** `infrastructure_invalid_interrupted`, reason `executor_interrupted_or_crashed`.
- **Result visibility:** no registered algorithmic result was visible. Detection, correlation, RCA, Guard, remediation, and verification did not complete.
- **Server-side evidence:** payment-service remained live/ready. Its log records a reset request as HTTP 200 around the failure window, indicating the endpoint handler completed even though the executor did not receive the response within its client timeout.
- **Disposition:** keep the invalid run record. Do not rerun this completed/accounted registry row.

## C6-DEV-002 — Operator-triggered spare start

- **Spare:** `C-SPARE-TRAIN-BDR-01`
- **Partition / scenario / seed:** TRAIN / `bad_deployment_rollback` / `1359673832`
- **Replacement for:** `C-TRAIN-BDR-12`
- **Start:** `2026-10-11T19:00:43.252399Z`
- **Cause:** an operator-triggered second invocation of the detached TRAIN-loop start path caused the preregistered BDR spare to begin while diagnosing C6-DEV-001.
- **Stop:** SIGINT; interruption record `2026-10-11T19:01:58.810570Z`.
- **Recorded classification:** `infrastructure_invalid_interrupted`, reason `executor_interrupted_or_crashed`.
- **Spare accounting:** this spare is consumed and must not be rerun.
- **Rule from this point forward:** `--detach` is never re-invoked for this C6 execution sequence. Any future continuation requires an explicit reviewed resume decision; no implicit restart is permitted.
- **Result visibility:** no registered algorithmic result was produced by this spare.
