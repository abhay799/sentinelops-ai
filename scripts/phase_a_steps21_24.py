"""Execute frozen RE2-OB Steps 21-24; never access held-out suite data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from sentinelops.evaluation.rcaeval_baselines import pagerank_ranking
from sentinelops.evaluation.rcaeval_scoring import (
    METRICS,
    a4_sentinelops_ranking,
    bootstrap_indices,
    case_hits,
    metric_values,
    paired_intervals,
    percentile_intervals,
    summarize_group,
)

OUT = Path("docs/evidence/phase_a/re2ob")
RCA_ROOT = Path("/home/dell/benchmarks/RCAEval")
RCA_REV = "259ea4167160256a74ad30004aa3d96a998c846e"
DATA_REV = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
ALLOW = set(
    "adservice cartservice checkoutservice currencyservice emailservice frontend "
    "paymentservice productcatalogservice recommendationservice redis shippingservice".split()
)
METHODS = ("SentinelOps", "threshold", "random", "PageRank", "BARO", "CIRCA", "mmBARO", "mmCIRCA")
FOLDERS = dict(
    zip(
        METHODS[:4], ("rca_cases", "threshold_cases", "random_cases", "pagerank_cases"), strict=True
    )
)
FAULTS = ("cpu", "mem", "disk", "socket", "delay", "loss")
A4_EDGES = (
    [
        ("frontend", s)
        for s in (
            "productcatalogservice",
            "currencyservice",
            "cartservice",
            "recommendationservice",
            "shippingservice",
            "checkoutservice",
            "adservice",
        )
    ]
    + [
        ("checkoutservice", s)
        for s in (
            "productcatalogservice",
            "shippingservice",
            "paymentservice",
            "emailservice",
            "currencyservice",
            "cartservice",
        )
    ]
    + [("recommendationservice", "productcatalogservice"), ("cartservice", "redis")]
)
CHANCE = 5 / 11


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def gate() -> None:
    resolution = read(OUT / "e7_gate_resolution.json")
    if resolution["status"] != "resolved_under_agreed_pre_diagnostic_rule":
        raise ValueError("E7 gate unresolved")
    for name, field in (
        ("random_multiseed_diagnostic.json", "diagnostic_sha256"),
        ("random_vs_chance_sanity.json", "seed42_sanity_sha256"),
    ):
        if sha(OUT / name) != resolution[field]:
            raise ValueError("Historical random diagnostic changed")
    if read(OUT / "random_vs_chance_sanity.json")["sanity_pass"] is not False:
        raise ValueError("Historical seed-42 sanity flag changed")
    for commit in ("bb35830", "42a148e", "b7a6bf8"):
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], check=True)
    processes = subprocess.check_output(["ps", "-eo", "args"], text=True).splitlines()
    if any("python scripts/phase_a_step20_rcaeval_baselines.py --method " in p for p in processes):
        raise ValueError("Baseline jobs still running")
    for path, expected in read(OUT / "pre_step21_fallback_validation.json")["sha256"].items():
        if sha(Path(path)) != expected:
            raise ValueError(f"Validated baseline artifact changed: {path}")


def load_cases() -> tuple[list[dict], dict]:
    hashes = {}

    def checked(path):
        hashes[str(path)] = sha(path)
        return read(path)

    ids = sorted(p.stem for p in (OUT / "rca_cases").glob("*.json"))
    if len(ids) != 90:
        raise ValueError("Expected 90 RE2-OB cases")
    folders = (
        [OUT / v for v in FOLDERS.values()]
        + [OUT / "rcaeval_baseline_cases" / m.lower() for m in METHODS[4:]]
        + [OUT / "detection_cases"]
    )
    for folder in folders:
        if sorted(p.stem for p in folder.glob("*.json")) != ids:
            raise ValueError(f"Case set mismatch: {folder}")
    cases = []
    for case_id in ids:
        detection = checked(OUT / "detection_cases" / f"{case_id}.json")
        if detection["status"] != "ok" or detection["case_id"] != case_id:
            raise ValueError("Detection evidence invalid")
        record = {"case_id": case_id, "methods": {}}
        originals = {}
        for method in METHODS:
            folder = (
                OUT / FOLDERS[method]
                if method in FOLDERS
                else (OUT / "rcaeval_baseline_cases" / method.lower())
            )
            raw = checked(folder / f"{case_id}.json")
            if raw["case_id"] != case_id or raw["status"] not in ("ok", "fallback_unranked"):
                raise ValueError(f"Invalid case record: {method} {case_id}")
            if method in FOLDERS:
                if raw["status"] != "ok" or raw["ground_truth_used_for_ranking"] is not False:
                    raise ValueError("Frozen saved ranking failed or used ground truth")
                native = [r["service"] for r in raw["ranking"]]
                pool = raw["candidate_count"]
                if len(native) != pool:
                    raise ValueError("Incomplete native ranking")
                if method == "random" and raw["master_seed"] != 42:
                    raise ValueError("Random seed changed")
            else:
                if raw["method"] != method.lower():
                    raise ValueError("Wrong baseline method")
                native = raw["native_service_ranking"]
                pool = raw["native_candidate_count_preprocess"]
                if raw["status"] == "fallback_unranked":
                    if not raw["fallback_detected"] or not raw["fallback_reason"]:
                        raise ValueError("Unexplained fallback")
                    if native or raw["raw_feature_ranking"] or raw["e3_filtered_service_ranking"]:
                        raise ValueError("Fallback contaminated scored ranking")
                elif raw["fallback_detected"]:
                    raise ValueError("Fallback mislabeled ok")
                if raw["e3_filtered_service_ranking"] != [s for s in native if s in ALLOW]:
                    raise ValueError("E3 projection differs")
            if pool < 1 or len(native) != len(set(native)):
                raise ValueError("Invalid candidate count or duplicate services")
            originals[method] = raw
            record["methods"][method] = {
                "status": raw["status"],
                "native_service_ranking": native,
                "e3_filtered_service_ranking": [s for s in native if s in ALLOW],
                "native_candidate_count": pool,
                "source": str(folder / f"{case_id}.json"),
                "fallback_signal": raw.get("fallback_signal"),
                "fallback_reason": raw.get("fallback_reason"),
                "raw_ranking_evidence": raw,
            }
        # A4 ranking receives only saved scores/strengths, never the root label.
        a4_rca = a4_sentinelops_ranking(originals["SentinelOps"]["ranking"], ALLOW, A4_EDGES)
        strengths = {
            s: float(v["fault_max_anomaly_strength"])
            for s, v in detection["per_service"].items()
            if s in ALLOW
        }
        if set(strengths) != ALLOW:
            raise ValueError("A4 missing allowlisted strengths")
        a4_pr = pagerank_ranking(ALLOW, A4_EDGES, strengths, damping=0.85)
        for name, rows in (("A4_SentinelOps", a4_rca), ("A4_PageRank", a4_pr)):
            native = [r["service"] for r in rows]
            record["methods"][name] = {
                "status": "ok",
                "native_service_ranking": native,
                "e3_filtered_service_ranking": [s for s in native if s in ALLOW],
                "native_candidate_count": len(native),
                "raw_ranking_evidence": rows,
                "fallback_signal": None,
                "fallback_reason": None,
            }
        record.update(
            {
                "root_cause_service": detection["root_cause_service"],
                "fault": detection["fault"],
                "repetition": detection["repetition"],
            }
        )
        expected_id = (
            f"re2ob_{record['root_cause_service']}_{record['fault']}_{record['repetition']}"
        )
        if case_id != expected_id or record["root_cause_service"] not in ALLOW:
            raise ValueError("Ground truth identity mismatch")
        if any(
            set(record["methods"][m]["e3_filtered_service_ranking"]) != ALLOW
            for m in (*METHODS[:4], "A4_SentinelOps", "A4_PageRank")
        ):
            raise ValueError("Incomplete frozen headline candidate set")
        cases.append(record)
    if Counter(c["fault"] for c in cases) != Counter(dict.fromkeys(FAULTS, 15)):
        raise ValueError("Unexpected RE2-OB fault cohorts")
    for m in METHODS[4:]:
        summary = checked(OUT / "rcaeval_baseline_cases" / f"{m.lower()}_summary.json")
        counts = Counter(c["methods"][m]["status"] for c in cases)
        if (
            summary["case_count_ok"] != counts["ok"]
            or (summary["case_count_fallback_unranked"] != counts["fallback_unranked"])
            or summary["case_count_failed"]
        ):
            raise ValueError("Baseline summary count mismatch")
    for m in (1, 3, 5):
        observed = (
            sum(
                case_hits(
                    c["methods"]["random"]["native_service_ranking"], c["root_cause_service"], ALLOW
                )[m - 1]
                for c in cases
            )
            / 90
        )
        historical = read(OUT / "random_vs_chance_sanity.json")["primary_filtered"][f"AC@{m}"][
            "empirical"
        ]
        if not np.isclose(observed, historical, rtol=0, atol=1e-14):
            raise ValueError("Reported random ranking differs from seed-42 sanity")
    return cases, hashes


def arrays(cases: list[dict], native: bool = False) -> tuple[dict, dict, dict]:
    hits, valid, chance = {}, {}, {}
    for method in cases[0]["methods"]:
        hits[method] = np.array(
            [
                case_hits(
                    c["methods"][method]["native_service_ranking"],
                    c["root_cause_service"],
                    set(c["methods"][method]["native_service_ranking"]) | {c["root_cause_service"]}
                    if native
                    else ALLOW,
                    c["methods"][method]["status"],
                )
                for c in cases
            ]
        )
        valid[method] = np.array([c["methods"][method]["status"] == "ok" for c in cases])
        chance[method] = np.array(
            [
                min(5, c["methods"][method]["native_candidate_count"])
                / c["methods"][method]["native_candidate_count"]
                for c in cases
            ]
        )
    return hits, valid, chance


def tables(cases: list[dict]) -> dict:
    hits, valid, _ = arrays(cases)
    result = summarize_group({m: hits[m] for m in METHODS}, {m: valid[m] for m in METHODS}, CHANCE)
    sensitivity = {
        **{m: hits[m] for m in METHODS},
        "SentinelOps": hits["A4_SentinelOps"],
        "PageRank": hits["A4_PageRank"],
    }
    result["a4_static_topology_sensitivity"] = {
        "label": "POST-HOC static-topology sensitivity",
        **summarize_group(sensitivity, {m: valid[m] for m in METHODS}, CHANCE),
    }
    native_hits, _, native_chance = arrays(cases, native=True)
    result["native_unfiltered_secondary"] = {
        m: {
            "denominator": len(cases),
            "metrics": metric_values(native_hits[m], native_chance[m]),
            "chance_policy": "mean min(5,N)/N using saved native candidate pool sizes",
        }
        for m in METHODS
    }
    return result


def uncertainty(cases: list[dict]) -> dict:
    hits, valid, _ = arrays(cases)
    indices = bootstrap_indices(len(cases))
    result = {
        "case_ids": [c["case_id"] for c in cases],
        "resample_indices_sha256": hashlib.sha256(indices.astype("<i8").tobytes()).hexdigest(),
        "primary_ci95": {},
        "valid_rankings_only_ci95": {},
        "paired_differences": {},
        "a4_static_topology_sensitivity": {
            "primary_ci95": {},
            "valid_rankings_only_ci95": {},
            "paired_differences": {},
        },
    }
    for method in METHODS:
        result["primary_ci95"][method] = percentile_intervals(hits[method], indices, CHANCE)
        selected = hits[method][valid[method]]
        ci = (
            percentile_intervals(selected, bootstrap_indices(len(selected)), CHANCE)
            if (len(selected))
            else dict.fromkeys(METRICS)
        )
        result["valid_rankings_only_ci95"][method] = {
            "denominator": len(selected),
            "case_ids": [c["case_id"] for i, c in enumerate(cases) if valid[method][i]],
            "ci95": ci,
        }
        if method != "SentinelOps":
            result["paired_differences"][method] = paired_intervals(
                hits["SentinelOps"],
                hits[method],
                indices,
            )
        variant = (
            hits["A4_SentinelOps"]
            if method == "SentinelOps"
            else (hits["A4_PageRank"] if method == "PageRank" else hits[method])
        )
        a4 = result["a4_static_topology_sensitivity"]
        a4["primary_ci95"][method] = percentile_intervals(variant, indices, CHANCE)
        a4_selected = variant[valid[method]]
        a4["valid_rankings_only_ci95"][method] = {
            "denominator": len(a4_selected),
            "ci95": percentile_intervals(
                a4_selected,
                bootstrap_indices(len(a4_selected)),
                CHANCE,
            )
            if len(a4_selected)
            else dict.fromkeys(METRICS),
        }
        if method != "SentinelOps":
            a4["paired_differences"][method] = paired_intervals(
                hits["A4_SentinelOps"],
                variant,
                indices,
            )
    return result


def provenance(step: int, started: float) -> dict:
    summaries = {}
    for name in (
        "step15_detection_summary.json",
        "step16_rca_summary.json",
        "step17_threshold_summary.json",
        "step18_random_summary.json",
        "step19_pagerank_summary.json",
    ):
        summaries[name] = read(OUT / name)
    return {
        "step": step,
        "suite": "RE2-OB",
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "exact_command": f".venv/bin/python scripts/phase_a_steps21_24.py --step {step}",
        "sentinelops_commit": head(),
        "rcaeval_revision": RCA_REV,
        "dataset_revision": DATA_REV,
        "python": platform.python_version(),
        "versions": {p: importlib.metadata.version(p) for p in ("numpy", "networkx", "polars")},
        "seeds": {"reported_random": 42, "bootstrap": 42},
        "bootstrap": {
            "resamples": 10000,
            "ci": 0.95,
            "method": "percentile",
            "quantile_interpolation": "linear",
            "cluster": "case",
            "rng": "numpy.random.default_rng(42)",
            "case_order": "lexical",
        },
        "candidate_policy": {
            "allowlist": sorted(ALLOW),
            "filter_before_top_k": True,
            "fallback_counts_as_miss": True,
            "primary_denominator": 90,
        },
        "metric_definitions": {
            "Avg@5": "mean AC@1..AC@5",
            "Lift@5": "AC@5/Chance@5",
            "Chance@5": "5/11",
        },
        "source_run_summaries": summaries,
        "a4": {
            "label": "POST-HOC static-topology sensitivity",
            "nodes": sorted(ALLOW),
            "edges": A4_EDGES,
            "graph_direction": "caller -> dependency",
            "source_revision": "38e7348eb289eb5b87c0c6e8cb19ced0449dc389",
            "source_path": "release/kubernetes-manifests.yaml",
            "original_primary_bonus_preserved": True,
            "excluded_native_graph_impact": 0.0,
            "pagerank_damping": 0.85,
        },
        "runtime_seconds": time.perf_counter() - started,
    }


def pinned_check(cases: list[dict]) -> dict:
    rev = subprocess.check_output(
        ["git", "-C", str(RCA_ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if rev != RCA_REV:
        raise ValueError("RCAEval revision changed")
    path = RCA_ROOT / "RCAEval/benchmark/evaluation.py"
    pinned = subprocess.check_output(
        ["git", "-C", str(RCA_ROOT), "show", f"{RCA_REV}:RCAEval/benchmark/evaluation.py"]
    )
    if path.read_bytes() != pinned:
        raise ValueError("Pinned evaluator changed")
    # Run the unchanged evaluator in the same dependency environment as Step 20.
    payload = {
        method: [
            {
                "ranking": [s for s in c["methods"][method]["native_service_ranking"] if s in ALLOW]
                if c["methods"][method]["status"] == "ok"
                else [],
                "answer": c["root_cause_service"],
            }
            for c in cases
        ]
        for method in (*METHODS, "A4_SentinelOps", "A4_PageRank")
    }
    check_code = """
import json, platform, sys
sys.path.insert(0, sys.argv[1])
from RCAEval.benchmark.evaluation import Evaluator
from RCAEval.classes.graph import Node
results = {}
for method, rows in json.load(sys.stdin).items():
    evaluator = Evaluator()
    for row in rows:
        evaluator.add_case([Node(s, "service") for s in row["ranking"]],
                           Node(row["answer"], "service"), n_candidates=11)
    results[method] = {
        **{f"AC@{k}": evaluator.accuracy_service(k) for k in range(1, 6)},
        "Avg@5": evaluator.average_service(5),
    }
print(json.dumps({"metrics": results, "python": platform.python_version()}))
"""
    run = subprocess.run(
        [str(RCA_ROOT / ".venv/bin/python"), "-c", check_code, str(RCA_ROOT)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
    )
    external = json.loads(run.stdout)
    for method, values in external["metrics"].items():
        expected = metric_values(
            np.array(
                [
                    case_hits(
                        c["methods"][method]["native_service_ranking"],
                        c["root_cause_service"],
                        ALLOW,
                        c["methods"][method]["status"],
                    )
                    for c in cases
                ]
            ),
            CHANCE,
        )
        for metric, value in values.items():
            if not np.isclose(value, expected[metric]):
                raise ValueError(f"Pinned service-level metric disagreement: {method} {metric}")
    return {
        "revision": rev,
        "evaluator_sha256": hashlib.sha256(pinned).hexdigest(),
        "interpreter": str(RCA_ROOT / ".venv/bin/python"),
        "python": external["python"],
        "methods_checked": len(external["metrics"]),
        "service_AC@1_to_5_and_Avg@5_match": True,
        "Lift@5": "explicit E6 ratio; pinned additive lift() deliberately unused",
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def report_and_export(cases: list[dict], overall: dict, faults: dict, intervals: dict) -> dict:
    rows, pairs, ranks = [], [], []
    groups = {"overall": overall, **faults}
    for cohort, table in groups.items():
        ci = intervals[cohort]
        for variant, section, uc in (
            ("primary_trace_topology", table, ci),
            (
                "POST-HOC static-topology sensitivity",
                table["a4_static_topology_sensitivity"],
                ci["a4_static_topology_sensitivity"],
            ),
        ):
            for sample in ("primary", "valid_rankings_only"):
                for method, r in section[sample].items():
                    bounds = (
                        uc["primary_ci95"][method]
                        if sample == "primary"
                        else (uc["valid_rankings_only_ci95"][method]["ci95"])
                    )
                    for metric, point in r["metrics"].items():
                        interval = bounds[metric]
                        rows.append(
                            {
                                "variant": variant,
                                "fault": cohort,
                                "cohort": sample,
                                "method": method,
                                "denominator": r["denominator"],
                                "metric": metric,
                                "estimate": point,
                                "ci95_lower": interval[0] if interval is not None else None,
                                "ci95_upper": interval[1] if interval is not None else None,
                            }
                        )
            for baseline, values in uc["paired_differences"].items():
                for metric, r in values.items():
                    pairs.append(
                        {
                            "variant": variant,
                            "fault": cohort,
                            "comparison": "SentinelOps minus " + baseline,
                            "denominator": 90 if cohort == "overall" else 15,
                            "metric": metric,
                            "difference": r["difference"],
                            "ci95_lower": r["ci95"][0],
                            "ci95_upper": r["ci95"][1],
                        }
                    )
    for c in cases:
        for method, r in c["methods"].items():
            for policy, ranking in (
                ("native", r["native_service_ranking"]),
                ("E3_filtered", r["e3_filtered_service_ranking"]),
            ):
                for pos, service in enumerate(ranking, 1):
                    ranks.append(
                        {
                            "case_id": c["case_id"],
                            "fault": c["fault"],
                            "method": method,
                            "status": r["status"],
                            "policy": policy,
                            "rank": pos,
                            "service": service,
                        }
                    )
    write_csv(OUT / "step24_metrics.csv", rows)
    write_csv(OUT / "step24_paired_differences.csv", pairs)
    write_csv(OUT / "step24_raw_service_rankings.csv", ranks)
    diag = read(OUT / "random_multiseed_diagnostic.json")
    random_rows = [
        {
            "metric": name,
            "reported_seed": 42,
            "seed42_AC": overall["primary"]["random"]["metrics"][name],
            "diagnostic_seed_count": 1000,
            "diagnostic_mean": r["multi_seed_mean"],
            "diagnostic_SD": r["multi_seed_sd"],
            "diagnostic_SE": r["standard_error_of_mean"],
            "analytical_chance": r["analytical_chance"],
        }
        for name, r in diag["multi_seed_ac_summary"].items()
    ]
    write_csv(OUT / "step24_random_diagnostic.csv", random_rows)
    lines = [
        "# Step 25 - RE2-OB results; stop before held-out suites",
        "",
        "Primary service-level results: E3 filtering before top-k; all 90 cases.",
        "E4 fallbacks count as misses. All methods have zero hard failures.",
        "",
        "| Method | Valid/90 | AC@1 | AC@3 | AC@5 | Avg@5 | Chance@5 | Lift@5 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method, r in overall["primary"].items():
        v = r["metrics"]
        lines.append(
            "| "
            + method
            + " | "
            + str(r["valid_ranking_count"])
            + "/90 | "
            + " | ".join(
                f"{v[k]:.6f}" for k in ("AC@1", "AC@3", "AC@5", "Avg@5", "Chance@5", "Lift@5")
            )
            + " |"
        )
    lines += ["", "## Overall 95% CIs", "", "| Method | AC@1 | AC@3 | AC@5 |", "|---|---|---|---|"]
    for method, r in intervals["overall"]["primary_ci95"].items():
        lines.append(
            "| "
            + method
            + " | "
            + " | ".join(f"[{r[k][0]:.6f}, {r[k][1]:.6f}]" for k in ("AC@1", "AC@3", "AC@5"))
            + " |"
        )
    lines += [
        "",
        "## Paired SentinelOps minus baseline",
        "",
        "Same 10,000 case resamples, seed 42; 95% percentile CIs.",
        "",
        "| Baseline | Delta AC@1 [CI] | Delta AC@3 [CI] | Delta AC@5 [CI] |",
        "|---|---|---|---|",
    ]
    for method, r in intervals["overall"]["paired_differences"].items():
        lines.append(
            "| "
            + method
            + " | "
            + " | ".join(
                f"{r[k]['difference']:.6f} [{r[k]['ci95'][0]:.6f}, {r[k]['ci95'][1]:.6f}]"
                for k in ("AC@1", "AC@3", "AC@5")
            )
            + " |"
        )
    lines += [
        "",
        "## Random seed-42 and diagnostic-only mean",
        "",
        "Historical seed-42 sanity_pass=false is unchanged.",
        "E7 resolves the agreed diagnostic gate.",
        "The 1000-seed means and SDs do not replace the reported baseline.",
        "",
        "| Metric | Seed 42 | Diagnostic mean | Across-seed SD | Chance |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in random_rows:
        lines.append(
            f"| {r['metric']} | {r['seed42_AC']:.6f} | {r['diagnostic_mean']:.6f}"
            f" | {r['diagnostic_SD']:.6f} | {r['analytical_chance']:.6f} |"
        )
    lines += [
        "",
        "## Secondary valid-rankings-only results",
        "",
        "| Method | Denominator | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method, r in overall["valid_rankings_only"].items():
        lines.append(
            "| "
            + method
            + " | "
            + str(r["denominator"])
            + " | "
            + " | ".join(
                f"{r['metrics'][k]:.6f}" if r["metrics"][k] is not None else "null"
                for k in ("AC@1", "AC@3", "AC@5", "Avg@5", "Lift@5")
            )
            + " |"
        )
    lines += [
        "",
        "## Per-fault primary results",
        "",
        "| Fault | Method | Valid/15 | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for fault, section in faults.items():
        for method, r in section["primary"].items():
            lines.append(
                "| "
                + fault
                + " | "
                + method
                + " | "
                + str(r["valid_ranking_count"])
                + "/15 | "
                + " | ".join(
                    f"{r['metrics'][k]:.6f}" for k in ("AC@1", "AC@3", "AC@5", "Avg@5", "Lift@5")
                )
                + " |"
            )
    lines += [
        "",
        "## POST-HOC static-topology sensitivity",
        "",
        "A4 is separate and never replaces the trace-derived primary result.",
        "Saved strengths and original primary-service bonuses are preserved.",
        "Only the 11 allowlisted nodes participate in the A4 graph; excluded native",
        "evidence rows have graph impact zero. A4 PageRank uses the same static graph.",
        "",
        "| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("SentinelOps", "PageRank"):
        r = overall["a4_static_topology_sensitivity"]["primary"][method]["metrics"]
        lines.append(
            "| "
            + method
            + " | "
            + " | ".join(f"{r[k]:.6f}" for k in ("AC@1", "AC@3", "AC@5", "Avg@5", "Lift@5"))
            + " |"
        )
    lines += [
        "",
        "Per-fault valid-only and A4 results, all metric CIs, raw rankings, coverage",
        "and paired differences are retained in the linked JSON/CSV evidence.",
        "",
        "- [Overall](step21_overall.json)",
        "- [Per fault](step22_per_fault.json)",
        "- [Bootstrap CIs and paired differences](step23_uncertainty.json)",
        "- [Metric CSV](step24_metrics.csv)",
        "- [Paired-difference CSV](step24_paired_differences.csv)",
        "- [Raw rankings](step21_cases.json)",
        "- [Provenance and artifact hashes](step24_manifest.json)",
        "",
        "No significance claim is made from marginal CIs. Paired intervals are",
        "unadjusted descriptive intervals; no family-wise significance is claimed.",
        "Stopped at Step 25. No RE2-SS/RE2-TT data access or push.",
        "",
    ]
    (OUT / "STEP25_RE2OB_RESULTS.md").write_text("\n".join(lines))
    return {
        "random_seed42_and_diagnostic": random_rows,
        "csv_metric_rows": len(rows),
        "csv_paired_rows": len(pairs),
        "csv_rank_rows": len(ranks),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, choices=(21, 22, 23, 24), required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    gate()
    if args.step == 21:
        cases, hashes = load_cases()
        agreement = pinned_check(cases)
        write(OUT / "step21_cases.json", {"cases": cases, "source_sha256": hashes})
        result = {
            "provenance": provenance(21, started),
            "pinned_evaluator_check": agreement,
            "overall": tables(cases),
        }
        write(OUT / "step21_overall.json", result)
        print(json.dumps(result["overall"]["primary"], indent=2), flush=True)
    else:
        snapshot = read(OUT / "step21_cases.json")
        for path, expected in snapshot["source_sha256"].items():
            if sha(Path(path)) != expected:
                raise ValueError(f"Source evidence changed: {path}")
        cases = snapshot["cases"]
        if args.step == 22:
            groups = {f: tables([c for c in cases if c["fault"] == f]) for f in FAULTS}
            write(
                OUT / "step22_per_fault.json",
                {"provenance": provenance(22, started), "faults": groups},
            )
        elif args.step == 23:
            read(OUT / "step22_per_fault.json")
            groups = {
                "overall": cases,
                **{f: [c for c in cases if c["fault"] == f] for f in FAULTS},
            }
            result = {name: uncertainty(group) for name, group in groups.items()}
            write(
                OUT / "step23_uncertainty.json",
                {"provenance": provenance(23, started), "groups": result},
            )
        else:
            overall = read(OUT / "step21_overall.json")["overall"]
            faults = read(OUT / "step22_per_fault.json")["faults"]
            intervals = read(OUT / "step23_uncertainty.json")["groups"]
            exports = report_and_export(cases, overall, faults, intervals)
            artifacts = [
                OUT / n
                for n in (
                    "step21_cases.json",
                    "step21_overall.json",
                    "step22_per_fault.json",
                    "step23_uncertainty.json",
                    "step24_metrics.csv",
                    "step24_paired_differences.csv",
                    "step24_raw_service_rankings.csv",
                    "step24_random_diagnostic.csv",
                    "STEP25_RE2OB_RESULTS.md",
                )
            ]
            write(
                OUT / "step24_manifest.json",
                {
                    "provenance": provenance(24, started),
                    "exports": exports,
                    "source_sha256": snapshot["source_sha256"],
                    "artifact_sha256": {str(p): sha(p) for p in artifacts},
                    "coverage": {
                        m: {
                            "case_count": 90,
                            "valid": sum(c["methods"][m]["status"] == "ok" for c in cases),
                            "fallback_unranked": sum(
                                c["methods"][m]["status"] == "fallback_unranked" for c in cases
                            ),
                            "failed": 0,
                        }
                        for m in METHODS
                    },
                    "method_runtimes_seconds": {
                        **{
                            m: read(OUT / n)["runtime_seconds"]
                            for m, n in (
                                ("SentinelOps", "step16_rca_summary.json"),
                                ("threshold", "step17_threshold_summary.json"),
                                ("random", "step18_random_summary.json"),
                                ("PageRank", "step19_pagerank_summary.json"),
                            )
                        },
                        **{
                            m: read(OUT / "rcaeval_baseline_cases" / f"{m.lower()}_summary.json")[
                                "runtime_seconds"
                            ]
                            for m in METHODS[4:]
                        },
                    },
                    "stop_at_step": 25,
                    "held_out_suites_accessed": False,
                    "pushed": False,
                },
            )
    print(f"Step {args.step} complete; runtime {time.perf_counter() - started:.3f}s", flush=True)


if __name__ == "__main__":
    main()
