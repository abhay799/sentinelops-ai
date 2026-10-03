# SentinelOps v2 RE2-OB Development Results

RE2-OB is a development suite. RE2-SS and RE2-TT remain held out and untouched.

| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Top ties | AC@1 tie | AC@1 no tie |
|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 0.211111 | 0.744444 | 0.966667 | 0.682222 | 78 | 0.153846 | 0.583333 |
| v2a | 0.844444 | 0.966667 | 1.000000 | 0.946667 | 0 | n/a | 0.844444 |
| v2b | 0.844444 | 0.966667 | 1.000000 | 0.946667 | 0 | n/a | 0.844444 |

Selected variant: **v2a**.
V2a selected because its Avg@5 is greater than V2b, or equal with the preregistered simpler-variant tie rule.

The numerical RCA weights are unchanged, but V2a/V2b unclipped anomaly strength changes the effective balance of the anomaly term relative to graph impact and primary bonus.

Paired 95% CIs are in `sentinelops_v2_results.json`; they are descriptive and do not alter the preregistered Avg@5 selection rule.
