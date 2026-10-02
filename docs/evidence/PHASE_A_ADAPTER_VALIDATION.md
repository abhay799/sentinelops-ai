# Phase A — RCAEval Adapter Validation

**Date:** 2026-10-02  
**Purpose:** Pre-benchmark schema/runtime validation only. No benchmark scores or tuning were produced.

## Frozen inputs

- RCAEval revision: `259ea4167160256a74ad30004aa3d96a998c846e`
- Hugging Face RCAEval dataset revision: `afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`
- Suite inspected: `RE2-OB`
- Total downloaded RE2-OB case directories: `90`

## Smoke cases inspected

1. `re2ob_checkoutservice_cpu_1`
2. `re2ob_emailservice_loss_1`
3. `re2ob_recommendationservice_socket_3`

These smoke cases were used only for adapter/schema validation and not for threshold, feature, weight, or hyperparameter tuning.

## Timestamp observations

For `re2ob_checkoutservice_cpu_1`:

- `metrics.parquet.time` is Unix seconds.
- `inject_time.txt` is Unix seconds.
- `traces.parquet.startTimeMillis` is Unix milliseconds.
- `traces.parquet.startTime` is Unix microseconds.
- Metrics contain `1441` rows.
- Rows before injection: `720`.
- Rows at or after injection: `721`.
- Metric timestamps were monotonically increasing.
- Duplicate metric timestamps: `0`.

## Trace schema observations

The trace data provides:

- `traceID`
- `spanID`
- `parentSpanID`
- `serviceName`
- `startTimeMillis`
- `startTime`

For the first smoke case:

- Trace rows: `391997`.
- Duplicate `(traceID, spanID)` pairs: `0`.
- Null `parentSpanID`: `23968`.

## Service-name normalization

Metric service vocabulary uses `frontend`.

Trace service vocabulary uses `frontendservice`.

The frozen adapter normalization is therefore:

1. If the trace service name exactly matches a metric service name, keep it.
2. Otherwise, if the trace service name ends in `service`, remove only that suffix.
3. Accept the stripped value only if it exactly matches a metric service name.
4. Otherwise fail the case rather than guessing.

Observed mapping:

`frontendservice -> frontend`

All other trace services in the three smoke cases matched metric service names directly.

No unresolved trace service names were observed in the three smoke cases.

## Metric-only graph nodes

The smoke cases contained metric services not represented by pre-injection trace spans:

- `adservice`
- `cartservice`
- `frontend-external`
- `redis`
- `shippingservice`

These services remain graph nodes but receive no invented trace-derived edges.

## Parent-span integrity

Observed unresolved pre-injection parent references:

- `re2ob_checkoutservice_cpu_1`: `7`
- `re2ob_emailservice_loss_1`: `0`
- `re2ob_recommendationservice_socket_3`: `18`

For both affected cases, every unresolved parent span was also absent from the full trace file. Therefore the unresolved references are not caused by the pre-injection cutoff.

Adapter policy:

- Resolve edges only when both child and parent spans are present.
- If a referenced parent span is absent from the full trace data, record the unresolved count and skip that edge.
- Never synthesize or infer a missing parent edge.
- Duplicate `(traceID, spanID)` identifiers are a hard failure.
- Unresolvable trace service names are a hard failure.
- Only pre-injection trace relationships may contribute topology.

## Benchmark status

No SentinelOps RCA score, RCAEval baseline score, detection metric, ranking metric, or benchmark comparison has been produced at this stage.
