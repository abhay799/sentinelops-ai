from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OUT = Path("docs/evidence/phase_a/re2ob")
VARIANTS = ("v2a", "v2b")
BOOTSTRAP_SEED = 42
BOOTSTRAP_SAMPLES = 10_000


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def case_hits(ranking: list[str], truth: str) -> np.ndarray:
    return np.array([float(truth in ranking[:k]) for k in range(1, 6)])


def summary(hits: np.ndarray) -> dict[str, float]:
    ac = hits.mean(axis=0)
    return {
        **{f"AC@{k}": float(ac[k - 1]) for k in range(1, 6)},
        "Avg@5": float(ac.mean()),
    }


def tie_summary(rows: list[dict], hits: np.ndarray) -> dict[str, object]:
    tied = np.array([int(row["top_tie_count"]) > 1 for row in rows])
    ac1 = hits[:, 0]
    return {
        "top_tie_cases": int(tied.sum()),
        "no_top_tie_cases": int((~tied).sum()),
        "AC@1_with_top_tie": float(ac1[tied].mean()) if tied.any() else None,
        "AC@1_without_top_tie": (
            float(ac1[~tied].mean()) if (~tied).any() else None
        ),
    }


def distribution(values: np.ndarray) -> dict[str, float | int]:
    if not np.isfinite(values).all():
        raise ValueError("Non-finite V2a strengths found")
    result: dict[str, float | int] = {
        "count": int(values.size),
        "finite_count": int(np.isfinite(values).sum()),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "count_lt_0": int(np.sum(values < 0)),
        "fraction_lt_0": float(np.mean(values < 0)),
        "count_eq_0": int(np.sum(values == 0)),
        "fraction_eq_0": float(np.mean(values == 0)),
        "count_eq_1": int(np.sum(values == 1)),
        "fraction_eq_1": float(np.mean(values == 1)),
        "count_gt_1": int(np.sum(values > 1)),
        "fraction_gt_1": float(np.mean(values > 1)),
    }
    for name, q in (
        ("p01", 0.01), ("p05", 0.05), ("p25", 0.25),
        ("median", 0.50), ("p75", 0.75), ("p95", 0.95),
        ("p99", 0.99),
    ):
        result[name] = float(np.quantile(values, q))
    return result


def paired_ci(
    left: np.ndarray,
    right: np.ndarray,
    indices: np.ndarray,
) -> dict[str, float]:
    diff = left - right
    boot = diff[indices].mean(axis=1)
    return {
        "difference": float(diff.mean()),
        "ci_low": float(np.percentile(boot, 2.5)),
        "ci_high": float(np.percentile(boot, 97.5)),
    }


def method_contributions(hits: np.ndarray) -> dict[str, np.ndarray]:
    return {
        "AC@1": hits[:, 0],
        "AC@3": hits[:, 2],
        "AC@5": hits[:, 4],
        "Avg@5": hits.mean(axis=1),
    }


def main() -> None:
    step21 = read(OUT / "step21_cases.json")["cases"]
    ordered = sorted(step21, key=lambda row: row["case_id"])
    case_ids = [row["case_id"] for row in ordered]
    if len(case_ids) != 90:
        raise RuntimeError(f"Expected 90 cases, found {len(case_ids)}")

    rankings: dict[str, list[list[str]]] = {
        "v1": [
            row["methods"]["SentinelOps"]["e3_filtered_service_ranking"]
            for row in ordered
        ],
        "threshold": [
            row["methods"]["threshold"]["e3_filtered_service_ranking"]
            for row in ordered
        ],
    }
    variant_rows: dict[str, list[dict]] = {}
    for variant in VARIANTS:
        rows = [
            read(OUT / f"{variant}_cases" / f"{case_id}.json")
            for case_id in case_ids
        ]
        variant_rows[variant] = rows
        rankings[variant] = [row["e3_filtered_service_ranking"] for row in rows]

    truths = [row["root_cause_service"] for row in ordered]
    faults = [row["fault"] for row in ordered]
    hits = {
        method: np.vstack(
            [case_hits(ranking, truth) for ranking, truth in zip(rows, truths, strict=True)]
        )
        for method, rows in rankings.items()
    }
    overall = {method: summary(value) for method, value in hits.items()}

    v1_tie_rows = {
        row["case_id"]: row
        for row in read(OUT / "sentinelops_tie_diagnostic.json")["cases"]
    }
    v1_rows = [v1_tie_rows[case_id] for case_id in case_ids]
    ties = {
        "v1": tie_summary(v1_rows, hits["v1"]),
        "v2a": tie_summary(variant_rows["v2a"], hits["v2a"]),
        "v2b": tie_summary(variant_rows["v2b"], hits["v2b"]),
    }
    ties["v2b"]["v1_clipped_primary_group_tie_cases"] = int(
        sum(row["v1_clipped_primary_group_count"] > 1 for row in variant_rows["v2b"])
    )

    allow = {
        "adservice", "cartservice", "checkoutservice", "currencyservice",
        "emailservice", "frontend", "paymentservice", "productcatalogservice",
        "recommendationservice", "redis", "shippingservice",
    }
    all_strengths = []
    case_maxima = []
    for row in variant_rows["v2a"]:
        eligible = np.array(
            [
                float(value)
                for service, value in row["unclipped_strengths"].items()
                if service in allow
            ],
            dtype=float,
        )
        all_strengths.extend(eligible.tolist())
        case_maxima.append(float(np.max(eligible)))
    strength_distribution = {
        "all_e3_service_strengths": distribution(np.array(all_strengths)),
        "case_max_service_strengths": distribution(np.array(case_maxima)),
    }

    per_fault: dict[str, dict[str, dict[str, float]]] = {}
    for fault in sorted(set(faults)):
        mask = np.array([item == fault for item in faults])
        per_fault[fault] = {
            method: summary(value[mask]) for method, value in hits.items()
        }

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    indices = rng.integers(0, len(case_ids), size=(BOOTSTRAP_SAMPLES, len(case_ids)))
    contrib = {method: method_contributions(value) for method, value in hits.items()}
    comparisons = (
        ("v2a_minus_v1", "v2a", "v1"),
        ("v2b_minus_v1", "v2b", "v1"),
        ("v2a_minus_threshold", "v2a", "threshold"),
        ("v2b_minus_threshold", "v2b", "threshold"),
        ("v2b_minus_v2a", "v2b", "v2a"),
    )
    paired: dict[str, dict[str, dict[str, float]]] = {}
    for name, left, right in comparisons:
        paired[name] = {
            metric: paired_ci(contrib[left][metric], contrib[right][metric], indices)
            for metric in ("AC@1", "AC@3", "AC@5", "Avg@5")
        }

    if overall["v2a"]["Avg@5"] >= overall["v2b"]["Avg@5"]:
        selected = "v2a"
        selection_reason = (
            "V2a selected because its Avg@5 is greater than V2b, or equal with "
            "the preregistered simpler-variant tie rule."
        )
    else:
        selected = "v2b"
        selection_reason = "V2b selected because its Avg@5 is greater than V2a."

    result = {
        "case_count": len(case_ids),
        "development_suite": "RE2-OB",
        "held_out_suites_untouched": ["RE2-SS", "RE2-TT"],
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "samples": BOOTSTRAP_SAMPLES,
            "interval": "95% percentile paired case bootstrap",
        },
        "overall": overall,
        "tie_diagnostics": ties,
        "v2a_strength_distribution": strength_distribution,
        "per_fault": per_fault,
        "paired_differences": paired,
        "selected_variant": selected,
        "selection_reason": selection_reason,
        "selection_metric": "all-90 RE2-OB Avg@5 point estimate",
        "variant_count_lock": 2,
    }
    (OUT / "sentinelops_v2_results.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )

    lines = [
        "# SentinelOps v2 RE2-OB Development Results",
        "",
        "RE2-OB is a development suite. RE2-SS and RE2-TT remain held out and untouched.",
        "",
        "| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Top ties | AC@1 tie | AC@1 no tie |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in ("v1", "v2a", "v2b"):
        metric = overall[method]
        tie = ties[method]
        ac1_tie = (
            "n/a"
            if tie["AC@1_with_top_tie"] is None
            else f"{tie['AC@1_with_top_tie']:.6f}"
        )
        ac1_no_tie = (
            "n/a"
            if tie["AC@1_without_top_tie"] is None
            else f"{tie['AC@1_without_top_tie']:.6f}"
        )
        lines.append(
            f"| {method} | {metric['AC@1']:.6f} | {metric['AC@3']:.6f} | "
            f"{metric['AC@5']:.6f} | {metric['Avg@5']:.6f} | "
            f"{tie['top_tie_cases']} | {ac1_tie} | {ac1_no_tie} |"
        )
    lines.extend(
        [
            "",
            f"Selected variant: **{selected}**.",
            selection_reason,
            "",
            "The numerical RCA weights are unchanged, but V2a/V2b unclipped anomaly "
            "strength changes the effective balance of the anomaly term relative to "
            "graph impact and primary bonus.",
            "",
            "Paired 95% CIs are in `sentinelops_v2_results.json`; they are descriptive "
            "and do not alter the preregistered Avg@5 selection rule.",
        ]
    )
    (OUT / "SENTINELOPS_V2_RESULTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
