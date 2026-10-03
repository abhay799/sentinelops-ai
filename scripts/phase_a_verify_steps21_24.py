"""Independent artifact reconciliation; uses no production scoring helpers."""

import csv
import hashlib
import json
from pathlib import Path

import networkx as nx
import numpy as np

OUT = Path("docs/evidence/phase_a/re2ob")


def read(name):
    return json.loads((OUT / name).read_text())


manifest = read("step24_manifest.json")
for path, digest in {**manifest["source_sha256"], **manifest["artifact_sha256"]}.items():
    assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == digest, path
cases = read("step21_cases.json")["cases"]
overall = read("step21_overall.json")["overall"]
faults = read("step22_per_fault.json")["faults"]
uncertainty = read("step23_uncertainty.json")["groups"]
methods = ("SentinelOps", "threshold", "random", "PageRank", "BARO", "CIRCA", "mmBARO", "mmCIRCA")
allow = set(manifest["provenance"]["candidate_policy"]["allowlist"])
chance = 5 / 11
groups = {
    "overall": cases,
    **{
        f: [c for c in cases if c["fault"] == f]
        for f in ("cpu", "mem", "disk", "socket", "delay", "loss")
    },
}
tables = {"overall": overall, **faults}
checks = 0


def direct_hits(group, method):
    return np.array(
        [
            [
                int(
                    c["root_cause_service"]
                    in [s for s in c["methods"][method]["native_service_ranking"] if s in allow][:k]
                )
                if c["methods"][method]["status"] == "ok"
                else 0
                for k in range(1, 6)
            ]
            for c in group
        ],
        dtype=float,
    )


def direct_metrics(ac):
    return {
        **{f"AC@{k}": float(ac[k - 1]) for k in range(1, 6)},
        "Avg@5": float(sum(ac) / 5),
        "Chance@5": chance,
        "Lift@5": float(ac[4] / chance),
    }


def close(left, right):
    assert np.allclose(left, right, rtol=0, atol=1e-13), (left, right)


for cohort, group in groups.items():
    assert len(group) == (90 if cohort == "overall" else 15)
    indices = np.random.default_rng(42).integers(0, len(group), size=(10000, len(group)))
    assert (
        hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest()
        == uncertainty[cohort]["resample_indices_sha256"]
    )
    for variant in ("primary", "a4"):
        section = (
            tables[cohort]
            if variant == "primary"
            else tables[cohort]["a4_static_topology_sensitivity"]
        )
        bounds = (
            uncertainty[cohort]
            if variant == "primary"
            else uncertainty[cohort]["a4_static_topology_sensitivity"]
        )
        matrices = {
            m: direct_hits(
                group, "A4_" + m if variant == "a4" and m in ("SentinelOps", "PageRank") else m
            )
            for m in methods
        }
        for method, hits in matrices.items():
            point = direct_metrics(hits.mean(axis=0))
            for name, want in point.items():
                close(section["primary"][method]["metrics"][name], want)
                checks += 1
            assert section["primary"][method]["denominator"] == len(group)
            valid = np.array([c["methods"][method]["status"] == "ok" for c in group])
            assert section["primary"][method]["valid_ranking_count"] == int(valid.sum())
            assert section["primary"][method]["fallback_unranked_count"] == int((~valid).sum())
            assert section["valid_rankings_only"][method]["denominator"] == int(valid.sum())
            if valid.sum():
                point = direct_metrics(hits[valid].mean(axis=0))
                for name, want in point.items():
                    close(section["valid_rankings_only"][method]["metrics"][name], want)
                    checks += 1
            for _sample, selected, draws, stored in (
                ("primary", hits, indices, bounds["primary_ci95"][method]),
                (
                    "valid",
                    hits[valid],
                    np.random.default_rng(42).integers(
                        0, int(valid.sum()), size=(10000, int(valid.sum()))
                    )
                    if valid.sum()
                    else None,
                    bounds["valid_rankings_only_ci95"][method]["ci95"],
                ),
            ):
                if len(selected):
                    ac = selected[draws].mean(axis=1)
                    values = {
                        **{f"AC@{k}": ac[:, k - 1] for k in range(1, 6)},
                        "Avg@5": ac.mean(axis=1),
                        "Chance@5": np.full(10000, chance),
                        "Lift@5": ac[:, 4] / chance,
                    }
                    for name, values_for_metric in values.items():
                        want = np.percentile(values_for_metric, [2.5, 97.5], method="linear")
                        close(stored[name], want)
                        checks += 1
                else:
                    assert all(v is None for v in stored.values())
            if method != "SentinelOps":
                differences = matrices["SentinelOps"] - hits
                ac = differences[indices].mean(axis=1)
                for k in (1, 3, 5):
                    stored = bounds["paired_differences"][method][f"AC@{k}"]
                    close(stored["difference"], differences[:, k - 1].mean())
                    close(stored["ci95"], np.percentile(ac[:, k - 1], [2.5, 97.5], method="linear"))
                    checks += 2

# Independent A4 graph-impact/formula check, retaining original bonuses.
graph = nx.DiGraph()
graph.add_nodes_from(allow)
graph.add_edges_from(manifest["provenance"]["a4"]["edges"])
assert set(graph) == allow
for c in cases:
    before = c["methods"]["SentinelOps"]["raw_ranking_evidence"]["ranking"]
    after = c["methods"]["A4_SentinelOps"]["raw_ranking_evidence"]
    original = {r["service"]: r for r in before}
    for row in after:
        service = row["service"]
        old = original[service]
        impact = len(nx.ancestors(graph, service)) / 10 if service in allow else 0
        close(row["graph_impact"], impact)
        assert row["anomaly_strength"] == old["anomaly_strength"]
        assert row["change_signal"] == old["change_signal"]
        assert row["primary_service_bonus"] == old["primary_service_bonus"]
        close(
            row["rca_score"],
            round(
                0.45 * old["anomaly_strength"]
                + 0.25 * old["change_signal"]
                + 0.20 * impact
                + 0.10 * old["primary_service_bonus"],
                6,
            ),
        )
    assert after == sorted(after, key=lambda r: (-r["rca_score"], r["service"]))
    strengths = {r["service"]: r["anomaly_strength"] for r in before if r["service"] in allow}
    total = sum(strengths.values())
    personalize = (
        {s: v / total for s, v in strengths.items()} if total else {s: 1 / 11 for s in allow}
    )
    scores = nx.pagerank(graph, alpha=0.85, personalization=personalize)
    for row in c["methods"]["A4_PageRank"]["raw_ranking_evidence"]:
        close(row["score"], scores[row["service"]])

# Every exported estimate/interval and paired difference reconciles with JSON.
with (OUT / "step24_metrics.csv").open() as f:
    metric_rows = list(csv.DictReader(f))
for row in metric_rows:
    cohort = row["fault"]
    method = row["method"]
    metric = row["metric"]
    sample = row["cohort"]
    table = tables[cohort]
    bounds = uncertainty[cohort]
    if row["variant"] != "primary_trace_topology":
        table = table["a4_static_topology_sensitivity"]
        bounds = bounds["a4_static_topology_sensitivity"]
    assert int(row["denominator"]) == table[sample][method]["denominator"]
    point = table[sample][method]["metrics"][metric]
    ci = (
        bounds["primary_ci95"][method][metric]
        if sample == "primary"
        else bounds["valid_rankings_only_ci95"][method]["ci95"][metric]
    )
    if point is None:
        assert row["estimate"] == row["ci95_lower"] == row["ci95_upper"] == ""
    else:
        close(float(row["estimate"]), point)
        close([float(row["ci95_lower"]), float(row["ci95_upper"])], ci)
with (OUT / "step24_paired_differences.csv").open() as f:
    pair_rows = list(csv.DictReader(f))
for row in pair_rows:
    bounds = uncertainty[row["fault"]]
    if row["variant"] != "primary_trace_topology":
        bounds = bounds["a4_static_topology_sensitivity"]
    value = bounds["paired_differences"][row["comparison"].removeprefix("SentinelOps minus ")][
        row["metric"]
    ]
    close(float(row["difference"]), value["difference"])
    close([float(row["ci95_lower"]), float(row["ci95_upper"])], value["ci95"])
assert len(metric_rows) == 1792
assert len(pair_rows) == 294
assert read("random_vs_chance_sanity.json")["sanity_pass"] is False
diag = read("random_multiseed_diagnostic.json")
for name, r in diag["multi_seed_ac_summary"].items():
    stored = next(
        r for r in manifest["exports"]["random_seed42_and_diagnostic"] if r["metric"] == name
    )
    close(stored["diagnostic_mean"], r["multi_seed_mean"])
    close(stored["diagnostic_SD"], r["multi_seed_sd"])
    close(stored["seed42_AC"], overall["primary"]["random"]["metrics"][name])
result = {
    "status": "pass",
    "source_and_artifact_sha256_verified": True,
    "all_methods_and_faults_reconciled": True,
    "independent_point_and_interval_comparisons": checks,
    "A4_strengths_bonus_formula_and_pagerank_verified": True,
    "CSV_metrics_rows": len(metric_rows),
    "CSV_paired_rows": len(pair_rows),
    "seed42_historical_sanity_unchanged": False
    if read("random_vs_chance_sanity.json")["sanity_pass"]
    else True,
    "held_out_data_accessed": False,
}
(OUT / "step24_validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result, indent=2), flush=True)
