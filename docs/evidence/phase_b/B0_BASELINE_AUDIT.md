# Phase B Step B0 — Baseline Audit

**Status:** COMPLETE
**Purpose:** record the pre-Phase-B failure-prediction baseline before any Phase B experiment or registered TEST scoring.

## Repository state

Phase A certification HEAD before this B0 freeze:

`90b33d76ddf6a6ff4e053ffe6e4f9576c3605a80`

No Phase B experiment, model training, threshold search, or registered TEST scoring was run during B0.

## Baseline source hashes

| Path | SHA-256 |
|---|---|
| `configs/failure_prediction.yaml` | `2e0bad04e73e79fda13bd0e69dabfd1a6de948258062d54f2e876a5b46659bb9` |
| `scripts/build_phase10_early_warning.py` | `f705e260c1347a7a01e72a750c26b1d48394b3190f39e7e4e49fb28b5715b75a` |
| `scripts/train_phase10_predictor.py` | `ee388752e176298b20150a36374324ef38708dc2ca20c92e02bb6bd9a02f1fb3` |
| `src/sentinelops/prediction/early_warning.py` | `cbfc7c2d90e2c8b3d3356e7b34096c669dab563c19b00e22bc56639d0f62d1d3` |
| `src/sentinelops/prediction/evaluation.py` | `5d9f995ea28693449643aaea397d17e83629e3bd0d1dfc6a4d56d478b378dfc4` |
| `scripts/train_phase5_anomaly.py` | `41ee6538b96a0a8e32d3c5a9f4a9d9410f60aceddd062a9ec5c5f224e6f91a1e` |
| `tests/test_phase10_early_warning.py` | `29657b88eeff4a5d24516d87a7d1f12ffe71d153e9a786b41a6fc953adb6a557` |

## Existing Phase 10 baseline

Current configuration:

- lookahead: 3 observations
- minimum history: 3
- history window: 20
- heuristic threshold: 0.55
- supervised model: logistic regression
- supervised decision threshold: 0.5
- class weighting: balanced
- model random state: 42
- configured train fraction: 0.70
- label: `future_anomaly`
- lead proxy: `lead_events`

Current positive property:

- `test_risk_score_does_not_use_future_values` verifies that changing a future latency value does not alter an earlier early-warning score.

## Findings that must be resolved before registered Phase B TEST scoring

### 1. Upstream anomaly fit is not chronology-safe for registered evaluation

`scripts/train_phase5_anomaly.py` fits Isolation Forest on the entire temporal feature matrix and scores the same matrix.

Because its anomaly output contributes to `is_anomaly`, and `is_anomaly` is later used to construct `future_anomaly`, the current Phase 10 target is not acceptable as-is for a registered held-out Phase B evaluation.

Resolution required in B1/B2: fit any learned upstream detector on TRAIN-only history, or replace the label source with an independent frozen failure-onset target.

### 2. Current temporal split selection inspects labels

`choose_temporal_split()` evaluates several candidate split fractions and selects one based on class presence, including whether the future/test side contains positives.

Resolution required: replace this for Phase B registered evaluation with a predetermined episode-grouped chronological 60/20/20 split whose boundary is independent of held-out labels.

### 3. Existing lead time is event-based only

The current pipeline computes `lead_events`; it does not preserve an independent fault-onset timestamp in the Phase 10 prediction dataset.

Resolution required: build episode provenance containing failure onset timestamps before any wall-clock lead-time claim.

### 4. Current operating thresholds are development defaults

The heuristic 0.55 and supervised 0.5 thresholds are not Phase B registered operating points.

Resolution required: threshold selection on VALIDATION only under the frozen Phase B utility, then freeze before TEST.

## B0 decision

The existing Phase 10 implementation is retained as a baseline and source of reusable code, but its historical metrics are **not** promoted to Phase B certification evidence.

No baseline code was modified during Step B0.

The frozen methodology is:

`docs/evidence/phase_b/PHASE_B_EVALUATION_SPEC.md`

## Next step

**B1 — data/provenance audit and episode chronology.**

B1 must determine whether the existing captured telemetry can support independent failure-onset timestamps and episode grouping. It must not train or score the registered TEST set.
