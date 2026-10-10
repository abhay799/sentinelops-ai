# Phase C C4 — Frozen Detector-fit Procedure

**Status:** preregistered before any registered detector fit or registered VALIDATION/TEST run.

## Fit source

The registered detector is fit only from the baseline periods of registered TRAIN runs.

No injected period, recovery period, VALIDATION run, TEST run, dry run, optional run, ground-truth label, or future observation may enter the fit matrix.

The execution gate is:

1. complete all 36 registered TRAIN runs;
2. extract only their registered baseline feature rows using the frozen feature schema;
3. invoke `scripts/phase5_frozen_detector.py fit-baseline-freeze`;
4. save the detector artifact and sidecar manifest;
5. compute and record the detector artifact SHA-256;
6. verify the artifact hash;
7. only then may registered VALIDATION execution begin.

The artifact is not refit between VALIDATION and TEST.

## Frozen detector component

The current explicit fit/freeze path freezes the Isolation Forest detector with the values in `configs/anomaly.yaml`:

- `n_estimators: 200`
- `contamination: 0.10`
- `random_state: 42`

Scoring uses `score-frozen`, which loads the previously saved artifact and does not fit it.

The legacy `scripts/train_phase5_anomaly.py` mode remains separate and is not the registered fit path.

## Feature schema

The ordered feature schema is frozen in:

`evidence/C/C04_feature_schema.json`

Any change to feature names, order, detector parameters, fit-source run IDs, or fit semantics after a registered result is visible requires a versioned protocol and a new held-out set.
