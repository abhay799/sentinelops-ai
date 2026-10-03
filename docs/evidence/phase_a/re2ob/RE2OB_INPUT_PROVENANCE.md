# RE2-OB metric input provenance

Date: 2026-10-03
Scope: documentation only; no change to inputs, rankings, code or scoring.

## Inputs actually used

Pinned HF root:
`/home/dell/datasets/rcaeval/afeacb11bcc94dadfd1c8f483ee4377b2b8b614e`

Native RCAEval root:
`/home/dell/benchmarks/RCAEval/data/RE2/RE2-OB`

| OB method | Metric input |
|---|---|
| SentinelOps v1 | HF `<case>/metrics.parquet`; saved continuous strengths from Step 15 used by Step 16 |
| SentinelOps V2a / V2b | HF `<case>/metrics.parquet` |
| Static threshold | HF `<case>/metrics.parquet` |
| PageRank | Saved v1 detection strengths originating in HF `metrics.parquet`; no native CSV read by its ranking runner |
| Random | Candidate names from saved v1 case evidence; no metric values read by its ranking function |
| Harness BARO / CIRCA | Native `<service>_<fault>/<repeat>/simple_metrics.csv` |
| Harness mmBARO / mmCIRCA | Same native `simple_metrics.csv`, plus shipped preaggregated modalities documented in Step 20 |
| Native CLI BARO / mmBARO | Native archive `simple_metrics.csv` in their pinned native worktrees |

Source references: `scripts/phase_a_step15_detection.py`,
`phase_a_step16_rca.py`, `phase_a_step17_threshold.py`,
`phase_a_step18_random.py`, `phase_a_step19_pagerank.py`,
`phase_a_v2_re2ob.py`, and `phase_a_step20_rcaeval_baselines.py`.
The HF and native archive metric inputs must not be described as identical
for all 90 cases.

## Previously reported 90-case comparison

The comparison supplied for this correction is:
- 81/90 exact matches;
- 7/90 null-versus-NaN representation differences;
- 2/90 row-count differences.

The native harness converts NaN/inf to missing and forward-fills, then fills
leading missing values with zero. The SentinelOps path applies its frozen
missing-value preprocessing; representation-only null/NaN differences must
not be confused with an algorithm change. The 81/7 elementwise classification
is recorded from the prior comparison, not independently recomputed while
CIRCA/V2a are running. No claim of complete byte identity is made.

A lightweight recheck of Parquet footers and native CSV row counts independently
identifies the two row-count differences:

| Case | HF rows | Native CSV rows | Saved native-harness CIRCA status |
|---|---:|---:|---|
| `re2ob_checkoutservice_cpu_2` | 930 | 1186 | fallback_unranked |
| `re2ob_checkoutservice_mem_2` | 1004 | 1262 | ok |

## CIRCA fallback interpretation

The CPU case is one of the two mismatches. Its saved evidence
`rcaeval_baseline_cases/circa/re2ob_checkoutservice_cpu_2.json` explicitly
reports a singular correlation matrix in the Fisher-Z test, followed by the
unranked-column-order fallback. The memory case also has a row-count mismatch
but completed with a valid ranking.

The row-count differences are therefore a plausible input-comparability
factor, **not an established causal explanation** for the CPU fallback.
No CIRCA rerun with substituted HF inputs has been performed by this
documentation cleanup, and no claim is made that replacing inputs would
remove the singularity. The archived native run and its E4 fallback miss
remain unchanged. Causality is unresolved; overlap alone does not prove it.

No job is started or killed and no method is fixed or retuned. This note does
not authorize rerunning OB or the SS mm methods. Never push.
