# Phase C C6 Run Deviations

This file is post-freeze operational evidence. It is outside the `freeze/C-prerun-v3` manifest. It records C6 execution deviations without rewriting any v3-frozen file.

## C6-DEV-001 — Pre-injection reset timeout on C-TRAIN-BDR-12

- **Run:** `C-TRAIN-BDR-12`
- **Scenario / seed:** `bad_deployment_rollback` / `681377953`
- **Interruption record time (UTC):** `2026-10-11T19:00:36.425987Z`
- **Point of failure:** before `injection_start`, during the executor's initial `POST http://localhost:8103/failure-mode/reset`.
- **Executor HTTP timeout:** `httpx.AsyncClient(timeout=10.0)`.
- **Observed exception:** `httpx.ReadTimeout`.
- **Result visibility:** no registered algorithmic result was visible. No injection, detection, RCA, Guard, remediation, verification, or persisted ground-truth result was completed for this row.
- **Preserved classification:** `infrastructure_invalid_interrupted`; under Amendment 4 this remains a pre-injection infrastructure-invalid run and is replaceable under the frozen spare rule.
- **Diagnostic evidence:** payment-service logged the reset handler as HTTP 200 around the failure window, while the client still timed out. The service middleware awaits Kafka telemetry publication after the handler and before request completion. The same window also contained telemetry/exporter instability. The non-registry probe later showed substantial latency variance and one payment transport connection-close error, supporting an environmental/request-path problem rather than failure-mode state mutation logic.

## C6-DEV-002 — Operator-triggered C-SPARE-TRAIN-BDR-01 start

- **Run:** `C-SPARE-TRAIN-BDR-01`
- **Scenario / seed:** `bad_deployment_rollback` / `1359673832`
- **Start time (UTC):** `2026-10-11T19:00:43.252399Z`
- **Stop/interruption time (UTC):** `2026-10-11T19:01:58.810570Z`
- **Cause:** an operator diagnostic invocation unintentionally reached the already-frozen `--detach` action after the primary loop process had exited.
- **Action:** the spare process was stopped with SIGINT as soon as it was identified.
- **Accounting:** the preserved spare is counted as consumed. It is not deleted, rewritten, or rerun.
- **Stage:** pre-injection. Only preflight evidence and the interruption summary exist; the 120-second baseline had not completed and no `injection_start` evidence exists.
- **Preserved classification:** `infrastructure_invalid_interrupted`; under Amendment 4 it remains pre-injection infrastructure-invalid.
- **Control rule:** `--detach` is never re-invoked as part of diagnosis or monitoring. A future authorized restart must be a deliberate execution action after the applicable freeze/start gate.

## C6-DEV-003 — Interruption classification flaw fixed by Amendment 4

- **Discovery:** post-failure audit showed that the v3 loop mapped every exception escaping the executor to `infrastructure_invalid_interrupted`, regardless of whether the exception occurred before or after `injection_start`.
- **Risk:** a failure after fault injection could therefore have been incorrectly replaced and excluded from the registered analysis denominator.
- **Registered-result state at discovery:** no registered algorithmic result existed. The two preserved interruption records above were both pre-injection and remain infrastructure-invalid under the corrected rule.
- **Amendment 4 rule:** failures before `injection_start` are infrastructure-invalid and replaceable; failures at or after the recorded `injection_start` are `run_failed_after_injection`, retain traceback/stage evidence, are registered results, are never replaced, and remain in the analysis denominator. A recorded host-level boot change overrides this and is infrastructure-invalid with host-check evidence.
- **Restart rule:** an unfinished run is classified from the persisted execution/stage state and recorded host check rather than from the mere fact that the loop restarted.


## C6-DEV-004 — Pre-resume environment adjustment after v4 freeze

- **Change window (UTC):** OpenTelemetry collector start initiated at approximately `2026-10-11T20:26:16Z` and reached a stable running state by approximately `2026-10-11T20:27:23Z`; Grafana was stopped at approximately `2026-10-11T20:28:20Z`.
- **Reason:** reduce nonessential resource pressure for the registered C6 TRAIN chain while restoring the configured OTLP endpoint so service exporters no longer repeatedly fail DNS resolution for `sentinelops-otel`.
- **Started:** `sentinelops-otel`. No collector configuration was edited. Final status sample showed `sentinelops-otel` Up, exposing ports 4317-4318.
- **Stopped:** `sentinelops-grafana`. Grafana is not required by the registered executor/evidence chain.
- **Left stopped:** `sentinelops-prometheus`. Prometheus is not required by the registered executor/evidence chain.
- **Required chain left running:** the seven demo services, Kafka, Postgres, and Redis.
- **Post-change readiness:** all seven service `/ready` endpoints returned HTTP 200 with `status=ready` and `telemetry=connected`.
- **Resource check:** three `docker stats --no-stream` samples were taken about 30 seconds apart. Kafka CPU was 10.10%, 35.08%, and 13.30%; Kafka memory was approximately 217.9-218.2 MiB. OTEL remained approximately 190.1 MiB and 0.10-0.25% CPU. WSL `MemAvailable` was 1,998,748 kB at the post-change sample.
- **Methodology:** this is an environment-only operational change. No registered row was started, `--detach` was not invoked, and no code, config, frozen v4 file, registry row, C7 fit, VALIDATION, or TEST execution was changed or started.
