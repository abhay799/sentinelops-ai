# Phase A Step 13 — Suspicious Smoke Diagnosis

**Date:** 2026-10-02  
**Case:** `re2ob_checkoutservice_cpu_1`  
**SentinelOps commit used for final rerun:** `cefe94d18398852210b157a5f87f9f1f5c56f3c8`

## Commands

```bash
python scripts/phase_a_step13_smoke.py
python scripts/phase_a_step13_diagnose.py
```

## Final smoke result

- Calibration rows: 360
- Normal evaluation rows: 360
- Normal evaluation alerts: 350 / 360 (97.22%)
- Fault rows: 721
- Fault alerts: 721 / 721 (100%)
- Detection delay: 0 seconds
- Services: 12
## Implementation issue found and fixed

The first diagnostic exposed a floating-point artifact in the EWMA
constant-calibration path. A mathematically constant metric could produce
residuals around `4.44e-16`, causing a tiny nonzero calibration residual
standard deviation and false flags.

The implementation now detects an exactly constant calibration input and
applies the frozen constant-vs-change rule directly. No threshold, alpha,
ensemble rule, or benchmark-tuned parameter was changed.

Focused detector tests after the fix: 13 passed.
Full repository tests after the fix: 115 passed, 1 skipped.
Ruff: passed.
## Why the suspicious result remains

After the numerical fix, the normal system alert rate remains 97.22%.

The high rate is not produced by the removed floating-point artifact alone.
Several services have substantial anomaly rates in the second pre-injection
half under the frozen detector definitions. Examples from the final diagnostic:

- recommendationservice ensemble normal rate: 71.11%
- adservice ensemble normal rate: 56.11%
- shippingservice ensemble normal rate: 43.61%
- productcatalogservice ensemble normal rate: 43.06%
- emailservice ensemble normal rate: 41.39%

The frozen system-level rule marks a timestamp positive when any service has
an ensemble anomaly. Across 12 services, these service-level alerts combine
to 350 of 360 normal-evaluation timestamps.
## Pre-injection distribution evidence

The diagnostic also found pre-injection distribution movement between the
calibration half and the normal-evaluation half. Examples:

- `recommendationservice_mem`: z-score normal flag rate 64.7%
- `adservice_mem`: z-score normal flag rate 71.4%
- `emailservice_mem`: z-score normal flag rate 72.2%
- `productcatalogservice_latency-50`: z-score normal flag rate 34.7%
- `productcatalogservice_latency-90`: z-score normal flag rate 33.9%

These measurements are diagnostic observations only. They were not used to
change thresholds, features, weights, graph settings, or hyperparameters.

## Stop decision

The requested sanity policy explicitly treats 100% detection as suspicious
and requires a stop when a suspicious result appears. The final smoke still
has 100% fault-window detection and 97.22% normal-window alerting.

Therefore Phase A remains stopped at Step 13. Steps 14–25 were not run.
RE2-SS and RE2-TT were not touched.
