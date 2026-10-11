# Phase C C6 Start Gate — Amendment 4

**Status:** pre-result methodology/engineering amendment after the first C6 start attempt. No registered algorithmic result existed when this amendment was prepared. No registered row was executed while preparing Amendment 4.

## Why Amendment 4 is required

The v3 loop treated any exception escaping the registered executor as `infrastructure_invalid_interrupted`. That was too broad: an exception after `injection_start` could be incorrectly replaced and excluded from the registered denominator. Amendment 4 changes only interruption classification and the minimum analysis handling required for that new outcome.

The frozen registry, run order, primary/spare seeds, partitions, scenario definitions/durations, Guard/remediation thresholds, C7 detector-fit rule, and all other registered analysis logic remain unchanged.

## Post-failure diagnosis

The v3 executor creates `httpx.AsyncClient(timeout=10.0)`. The first row, `C-TRAIN-BDR-12`, failed before injection at:

`run_registered_train() -> _reset_payment() -> client.post("http://localhost:8103/failure-mode/reset")`

with `httpx.ReadTimeout`.

The payment reset handler itself only resets the in-memory `FailureMode` and returns JSON. Around the failure window the payment container logged the reset handler as HTTP 200 with a middleware duration of 1273.653 ms, but the client timed out before receiving a completed response. The common HTTP middleware then synchronously awaits Kafka telemetry publication for log, metric and trace events. This makes request completion sensitive to telemetry/Kafka backpressure even when the endpoint body has already succeeded.

The payment logs also show repeated OTLP exporter failures resolving `sentinelops-otel:4318`. The observability compose file defines the collector as `sentinelops-otel`, but the collector was not running in the sampled container set. OTLP collector output is not the registered C6 evidence source: C6 records telemetry from Kafka topic `sentinelops.telemetry.raw`. The collector is therefore not required for the registered analysis chain, but leaving the services configured to export to a nonexistent collector creates retry noise and avoidable resource pressure.

### Non-registry reset probe

Exactly 30 POST resets were sent to payment-service and 30 to user-service, with each iteration spaced five seconds apart. These probes were non-registry diagnostic traffic and are not registered results.

| Service | N | Min ms | Median ms | Max ms | HTTP/client timeouts | Other transport errors |
|---|---:|---:|---:|---:|---:|---:|
| payment-service | 30 | 36.715 | 67.1445 | 5081.208 | 0 | 1 connection-closed error |
| user-service | 30 | 32.597 | 65.5135 | 1335.807 | 0 | 0 |

Payment therefore showed materially greater tail latency than the comparison service. The single payment transport error occurred at probe 8 after 2766.111 ms; it was not a 15-second timeout.

## Environment plan — not applied

Host physical RAM is `8,340,049,920` bytes (about 7.77 GiB / nominal 8 GB). WSL/Docker was exposing about 3.7 GiB to containers in the sampled stats. Because the host has only 8 GB total RAM, Amendment 4 does **not** recommend increasing WSL memory in `.wslconfig`; doing so would risk starving Windows.

For the next authorized C6 run:
- keep the seven demo services, Kafka, Redis and Postgres available;
- keep `sentinelops-otel` available if the service OTLP exporter remains configured, to eliminate DNS/retry noise even though OTLP data is not the registered evidence source;
- `sentinelops-grafana` and `sentinelops-prometheus` are not required by the registered executor/evidence chain and may be stopped to reduce resource pressure;
- do not apply these environment changes as part of this amendment. They require a separate explicit execution/preflight step.

## Corrected classification rule

The loop now records a host check when a row becomes active and the executor persists `execution_state.json` with `injection_start`, current stage and stage timestamps.

The classification is:

1. **Recorded host event:** a changed host/WSL boot ID between active-row start and interruption -> `infrastructure_invalid_host_event`; evidence is retained and the row is replaceable.
2. **No recorded injection_start:** executor exception/restart -> `infrastructure_invalid_interrupted`; replaceable according to the frozen same-cell spare policy.
3. **Recorded injection_start exists:** executor exception/restart -> `run_failed_after_injection`; traceback and stage evidence are kept, it is a registered result, it is never replaced, and it remains in the analysis denominator.

The injection boundary is persisted immediately before the fault-activation request so a failure while attempting the injection itself is classified as at/after injection rather than pre-injection.

Restart recovery uses the persisted execution/stage state plus the recorded host check. It no longer classifies solely from the fact that a process disappeared.

## Analysis handling

`run_failed_after_injection` is included in registered analysis. Its unavailable downstream binary outcomes are counted as failures and its unavailable latency/recovery values remain null. Infrastructure-invalid summaries are excluded from the registered denominator. No other metric definitions, bootstrap seed/resample count, or normal successful-run analysis path was changed.

## Preserved v3 interruption records

- `C-TRAIN-BDR-12`: pre-injection reset timeout; remains infrastructure-invalid and replaceable.
- `C-SPARE-TRAIN-BDR-01`: operator-triggered spare start stopped by SIGINT during pre-injection baseline; remains infrastructure-invalid and is already a consumed spare.

Neither preserved record is rewritten.

## Tests

Ruff passed for all Amendment 4 changed/new Python files.

The final requested combined test run passed:

- Amendment 4 classification tests: pre-injection exception; exception at injection; detection; RCA; Guard/plan; remediation; verification; recorded host event; restart classification; no-spare rule for post-injection failures; analysis denominator behavior.
- Existing C6 registered-harness and TRAIN-loop tests.
- Existing Guard/Phase 13 and Phase 14 tests.

**Final result: 44 passed, 0 failed.**

An earlier test run produced 43 passed / 1 failed because the restart test fixture used a synthetic boot ID that intentionally differed from the real host, correctly exercising the host-event override. Only the test fixture was corrected to hold the host ID constant for the restart-stage test; production logic was not weakened.

## Freeze rule

`freeze/C-prerun-v4` supersedes v3 for any future C6 execution. The v4 manifest recomputes SHA-256 for every path frozen by v3 and adds the Amendment 4 code/test/evidence files. No v3 tag or frozen file is rewritten.

No environment change, service start/stop, registered row, C7 fit, VALIDATION, or TEST execution is authorized by this amendment itself.
