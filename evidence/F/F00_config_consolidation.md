# F0 — SentinelGuard Config Consolidation

**Scope:** behavior-preserving configuration consolidation only. No guard threshold or decision rule was changed.

## Regression fixture

A deterministic synthetic fixture was created before changing guard/config behavior:

- script: `scripts/f00_guard_regression_fixture.py`
- cases: 45
- coverage: planner-not-ready, non-allowlisted action, unsupported RCA disposition, causal score below 0.70, priority below 0.35, net benefit below 0.01, projected risk above 0.70, rollback unavailable, traceable evidence absent, all-pass cases, exact threshold boundaries, near-boundary values, and multi-failure combinations.

Before consolidation:

- `evidence/F/F00_before_decisions.json`
- SHA-256: `b99d45c6c115c5f3d16f941707722a558d1742c27389c37d92afc529d3f4f888`
- 45 decisions: 24 `eligible_pending_human`, 21 `blocked`

After consolidation:

- `evidence/F/F00_after_decisions.json`
- SHA-256: `b99d45c6c115c5f3d16f941707722a558d1742c27389c37d92afc529d3f4f888`

Byte comparison:

```text
cmp -s evidence/F/F00_before_decisions.json evidence/F/F00_after_decisions.json
exit = 0
```

Therefore the before/after decision artifacts are byte-identical.

## Threshold preservation

The enforced SentinelGuard values were copied exactly from the previous `configs/remediation.yaml` guard section into the canonical `configs/sentinelguard.yaml`:

| Setting | Before | After |
|---|---:|---:|
| `fail_closed` | true | true |
| `minimum_causal_score` | 0.70 | 0.70 |
| `minimum_priority_score` | 0.35 | 0.35 |
| `minimum_net_benefit` | 0.01 | 0.01 |
| `maximum_projected_failure_risk` | 0.70 | 0.70 |
| `require_supported_rca` | true | true |
| `require_counterfactual_recommendation` | true | true |
| `require_rollback` | true | true |
| `require_human_approval` | true | true |
| `require_traceable_evidence` | true | true |

An automated comparison against `HEAD:configs/remediation.yaml` returned `all_identical True` for all enforced values.

## Config consolidation diff

Behavioral/config-source changes:

```diff
-configs/remediation.yaml
-  allowed_actions: [rollback, traffic_shift, restart]
-  sentinelguard:
-    minimum_causal_score: 0.70
-    minimum_priority_score: 0.35
-    minimum_net_benefit: 0.01
-    maximum_projected_failure_risk: 0.70
-    ...guard requirements...
-  output.guard.path: data/processed/remediation/sentinelguard_decisions_v1.parquet
+configs/remediation.yaml
+  planner:
+    allowed_actions: [rollback, traffic_shift, restart]
+    minimum_causal_score: 0.65
+    minimum_priority_score: 0.35
+    minimum_net_benefit: 0.01
+  output.plans.path: data/processed/remediation/remediation_plans_v1.parquet

+configs/sentinelguard.yaml
+  allowed_actions: [rollback, traffic_shift, restart]
+  fail_closed: true
+  minimum_causal_score: 0.70
+  minimum_priority_score: 0.35
+  minimum_net_benefit: 0.01
+  maximum_projected_failure_risk: 0.70
+  ...existing enforced requirements...
+  output.path: data/processed/remediation/sentinelguard_decisions_v1.parquet
```

The previous `sentinelguard.yaml` policy vocabulary that Phase 13 never read — including confidence bands, permissions/blast-radius/service-criticality requirements, auto-execute policy, blocked-action list, verification policy, and audit declarations — is retained under `declared_but_not_enforced`. F0 does not begin enforcing any of it.

## Guard config source

`src/sentinelops/remediation/sentinelguard.py` now owns a single canonical path:

`configs/sentinelguard.yaml`

`evaluate_sentinelguard()` no longer accepts an injected remediation config. It loads the canonical SentinelGuard file internally. `scripts/build_phase13_remediation.py` uses the canonical SentinelGuard config for the guard output path and uses `configs/remediation.yaml` only for planner settings/plan output.

`tests/test_phase13_remediation.py::test_guard_reads_only_canonical_config` intercepts config reads and fails if SentinelGuard attempts to read any path other than the canonical `configs/sentinelguard.yaml`.

## Planner-only remediation config

`configs/remediation.yaml` now contains only remediation-planner policy plus the remediation-plan output path. The planner action allowlist moved under `remediation.planner.allowed_actions`; its values are unchanged.

## Test evidence

The existing Guard + Phase 13 + Phase 14 test selection was run once after the consolidation and fixture proof:

```text
21 passed in 0.43s
```

Static test counts in that run:

- `tests/test_phase13_remediation.py`: 6
- `tests/test_phase13_validation.py`: 4
- `tests/test_phase14_execution_gate.py`: 6
- `tests/test_phase14_runtime.py`: 5
- total: 21

The Phase 13 remediation count includes the new canonical-config-path regression test.

Ruff also passed on all F0 Python files after formatting-only cleanup of the fixture script.

## Behavior-preservation conclusion

F0 changes config ownership and loading only. The fixed 45-case guard decision artifact is byte-identical before and after consolidation, all enforced threshold values are unchanged, the existing Phase 13/14 tests pass, and previously declared-but-unused policy is explicitly marked non-enforced rather than activated.
