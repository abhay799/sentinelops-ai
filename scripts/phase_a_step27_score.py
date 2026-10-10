from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import polars as pl

DATA_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2tt")
ALLOW = {
    "ts-admin-basic-info-service",
    "ts-admin-order-service",
    "ts-admin-route-service",
    "ts-admin-travel-service",
    "ts-admin-user-service",
    "ts-assurance-service",
    "ts-auth-service",
    "ts-avatar-service",
    "ts-basic-service",
    "ts-cancel-service",
    "ts-config-service",
    "ts-consign-price-service",
    "ts-consign-service",
    "ts-contacts-service",
    "ts-delivery-service",
    "ts-execute-service",
    "ts-food-delivery-service",
    "ts-food-service",
    "ts-gateway-service",
    "ts-inside-payment-service",
    "ts-news-service",
    "ts-notification-service",
    "ts-order-other-service",
    "ts-order-service",
    "ts-payment-service",
    "ts-preserve-other-service",
    "ts-preserve-service",
    "ts-price-service",
    "ts-rebook-service",
    "ts-route-plan-service",
    "ts-route-service",
    "ts-seat-service",
    "ts-security-service",
    "ts-station-food-service",
    "ts-station-service",
    "ts-ticket-office-service",
    "ts-train-food-service",
    "ts-train-service",
    "ts-travel-plan-service",
    "ts-travel-service",
    "ts-travel2-service",
    "ts-user-service",
    "ts-verification-code-service",
    "ts-voucher-service",
    "ts-wait-order-service",
}
METHODS = (
    "v1",
    "v2a",
    "threshold",
    "random",
    "pagerank",
    "baro",
    "circa",
)
UNAVAILABLE_METHODS = {
    "mmbaro": "n/a (outside pinned input contract)",
    "mmcirca": "n/a (outside pinned input contract)",
}
FAULTS = ("cpu", "mem", "disk", "socket", "delay", "loss")
BOOTSTRAP_SEED = 42
BOOTSTRAP_SAMPLES = 10_000
EFFECTIVE_E3_COUNT = 39
CHANCE_AT_5 = 5 / EFFECTIVE_E3_COUNT


def read(path: Path) -> dict:
    return json.loads(path.read_text())


def write(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def case_hits(ranking: list[str], truth: str, status: str) -> np.ndarray:
    if status != "ok":
        return np.zeros(5, dtype=float)
    return np.array(
        [float(truth in ranking[:k]) for k in range(1, 6)],
        dtype=float,
    )


def metrics(hits: np.ndarray) -> dict[str, float]:
    ac = hits.mean(axis=0)
    return {
        "AC@1": float(ac[0]),
        "AC@2": float(ac[1]),
        "AC@3": float(ac[2]),
        "AC@4": float(ac[3]),
        "AC@5": float(ac[4]),
        "Avg@5": float(ac.mean()),
        "Chance@5": CHANCE_AT_5,
        "Lift@5": float(ac[4] / CHANCE_AT_5),
    }


def contrib(hits: np.ndarray, metric: str) -> np.ndarray:
    if metric == "AC@1":
        return hits[:, 0]
    if metric == "AC@3":
        return hits[:, 2]
    if metric == "AC@5":
        return hits[:, 4]
    if metric == "Avg@5":
        return hits.mean(axis=1)
    if metric == "Lift@5":
        return hits[:, 4] / CHANCE_AT_5
    raise KeyError(metric)


def percentile_ci(
    hits: np.ndarray,
    indices: np.ndarray,
) -> dict[str, list[float] | None]:
    result: dict[str, list[float] | None] = {}
    for name in ("AC@1", "AC@3", "AC@5", "Avg@5", "Lift@5"):
        values = contrib(hits, name)
        boot = values[indices].mean(axis=1)
        result[name] = [
            float(np.percentile(boot, 2.5)),
            float(np.percentile(boot, 97.5)),
        ]
    result["Chance@5"] = [CHANCE_AT_5, CHANCE_AT_5]
    return result


def paired_ci(
    left: np.ndarray,
    right: np.ndarray,
    indices: np.ndarray,
) -> dict[str, dict[str, float | list[float]]]:
    result: dict[str, dict[str, float | list[float]]] = {}
    for name in ("AC@1", "AC@3", "AC@5", "Avg@5"):
        diff = contrib(left, name) - contrib(right, name)
        boot = diff[indices].mean(axis=1)
        result[name] = {
            "difference": float(diff.mean()),
            "ci95": [
                float(np.percentile(boot, 2.5)),
                float(np.percentile(boot, 97.5)),
            ],
        }
    return result


def strength_distribution(values: np.ndarray) -> dict[str, float | int]:
    if values.ndim != 1 or values.size == 0:
        raise ValueError("Strength distribution requires a non-empty 1D array")
    if not np.isfinite(values).all():
        raise ValueError("Non-finite V2a strengths found in held-out evidence")
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
        ("p01", 0.01),
        ("p05", 0.05),
        ("p25", 0.25),
        ("median", 0.50),
        ("p75", 0.75),
        ("p95", 0.95),
        ("p99", 0.99),
    ):
        result[name] = float(np.quantile(values, q))
    return result


def main() -> None:
    catalog = pl.read_parquet(DATA_ROOT / "cases.parquet")
    tt = catalog.filter(pl.col("dataset") == "RE2-TT").sort("case")
    if tt.height != 90:
        raise RuntimeError(f"Expected 90 RE2-TT catalog rows, found {tt.height}")
    case_rows = tt.select(
        "case", "root_cause_service", "fault"
    ).to_dicts()
    case_ids = [str(row["case"]) for row in case_rows]

    if any(str(row["root_cause_service"]) not in ALLOW for row in case_rows):
        raise RuntimeError("Frozen TT allowlist does not cover ground-truth labels")
    if Counter(str(row["fault"]) for row in case_rows) != Counter(
        {fault: 15 for fault in FAULTS}
    ):
        raise RuntimeError("Unexpected RE2-TT fault cohort sizes")

    saved: dict[str, list[dict]] = {}
    for method in METHODS:
        folder = OUT / "cases" / method
        paths = [folder / f"{case_id}.json" for case_id in case_ids]
        if not all(path.exists() for path in paths):
            missing = [path.stem for path in paths if not path.exists()]
            raise RuntimeError(
                f"{method} incomplete: {len(missing)} missing cases"
            )
        saved[method] = [read(path) for path in paths]

    hits: dict[str, np.ndarray] = {}
    coverage: dict[str, dict[str, object]] = {}
    for method in METHODS:
        rows = saved[method]
        if any(
            row["case_id"] != case_id
            for row, case_id in zip(rows, case_ids, strict=True)
        ):
            raise RuntimeError(f"{method} case ordering mismatch")
        statuses = Counter(str(row["status"]) for row in rows)
        for row in rows:
            if row.get("ground_truth_used_for_ranking") is not False:
                raise RuntimeError(f"{method} ranking used ground truth")
            ranking = [
                str(x) for x in row.get("e3_filtered_service_ranking", [])
            ]
            if len(ranking) != len(set(ranking)):
                raise RuntimeError(f"{method} duplicate filtered services")
            if not set(ranking).issubset(ALLOW):
                raise RuntimeError(f"{method} ranking outside frozen allowlist")

        hits[method] = np.vstack(
            [
                case_hits(
                    [
                        str(x)
                        for x in row.get(
                            "e3_filtered_service_ranking", []
                        )
                    ],
                    str(meta["root_cause_service"]),
                    str(row["status"]),
                )
                for row, meta in zip(rows, case_rows, strict=True)
            ]
        )
        coverage[method] = {
            "case_count": 90,
            "ok": statuses["ok"],
            "fallback_unranked": statuses["fallback_unranked"],
            "timeout_unranked": statuses["timeout_unranked"],
            "hard_failed": statuses["hard_failed"],
            "input_unavailable": 0,
            "other_statuses": {
                key: value
                for key, value in statuses.items()
                if key not in {
                    "ok",
                    "fallback_unranked",
                    "timeout_unranked",
                    "hard_failed",
                }
            },
            "valid_fraction": statuses["ok"] / 90,
            "excluded_from_numerical_comparison": False,
        }

    for method, status in UNAVAILABLE_METHODS.items():
        coverage[method] = {
            "case_count": 90,
            "ok": 0,
            "fallback_unranked": 0,
            "timeout_unranked": 0,
            "hard_failed": 0,
            "input_unavailable": 90,
            "other_statuses": {},
            "valid_fraction": 0.0,
            "excluded_from_numerical_comparison": True,
            "status": status,
        }

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    overall_indices = rng.integers(
        0, 90, size=(BOOTSTRAP_SAMPLES, 90)
    )
    overall = {}
    primary_ci = {}
    valid_only = {}
    for method in METHODS:
        overall[method] = metrics(hits[method])
        primary_ci[method] = percentile_ci(hits[method], overall_indices)
        valid_mask = np.array(
            [row["status"] == "ok" for row in saved[method]],
            dtype=bool,
        )
        valid_hits = hits[method][valid_mask]
        if len(valid_hits):
            valid_rng = np.random.default_rng(BOOTSTRAP_SEED)
            valid_indices = valid_rng.integers(
                0,
                len(valid_hits),
                size=(BOOTSTRAP_SAMPLES, len(valid_hits)),
            )
            valid_only[method] = {
                "denominator": int(len(valid_hits)),
                "metrics": metrics(valid_hits),
                "ci95": percentile_ci(valid_hits, valid_indices),
            }
        else:
            valid_only[method] = {
                "denominator": 0,
                "metrics": None,
                "ci95": None,
            }

    pairs: list[tuple[str, str, str]] = [
        ("v2a_minus_v1", "v2a", "v1"),
    ]
    for focal in ("v1", "v2a"):
        for baseline in (
            "threshold",
            "random",
            "pagerank",
            "baro",
            "circa",
        ):
            pairs.append(
                (f"{focal}_minus_{baseline}", focal, baseline)
            )
    paired = {
        name: paired_ci(hits[left], hits[right], overall_indices)
        for name, left, right in pairs
    }

    per_fault: dict[str, object] = {}
    for fault in FAULTS:
        mask = np.array(
            [str(row["fault"]) == fault for row in case_rows],
            dtype=bool,
        )
        n = int(mask.sum())
        fault_rng = np.random.default_rng(BOOTSTRAP_SEED)
        fault_indices = fault_rng.integers(
            0, n, size=(BOOTSTRAP_SAMPLES, n)
        )
        per_fault[fault] = {
            method: {
                "denominator": n,
                "metrics": metrics(hits[method][mask]),
                "ci95": percentile_ci(
                    hits[method][mask], fault_indices
                ),
            }
            for method in METHODS
        }

    v2a_all_strengths: list[float] = []
    v2a_case_maxima: list[float] = []
    for row in saved["v2a"]:
        strengths = row.get("unclipped_strengths")
        if not isinstance(strengths, dict):
            raise RuntimeError("V2a case missing unclipped_strengths")
        eligible = np.array(
            [
                float(value)
                for service, value in strengths.items()
                if str(service) in ALLOW
            ],
            dtype=float,
        )
        if len(eligible) != EFFECTIVE_E3_COUNT:
            raise RuntimeError(
                "V2a strength evidence does not contain the frozen 39 "
                "metric-visible E3 candidates"
            )
        v2a_all_strengths.extend(eligible.tolist())
        v2a_case_maxima.append(float(np.max(eligible)))
    v2a_strength_distribution = {
        "all_e3_service_strengths": strength_distribution(
            np.asarray(v2a_all_strengths, dtype=float)
        ),
        "case_max_service_strengths": strength_distribution(
            np.asarray(v2a_case_maxima, dtype=float)
        ),
    }

    result = {
        "suite": "RE2-TT",
        "held_out": True,
        "case_count": 90,
        "allowlist": sorted(ALLOW),
        "chance": {
            "N": EFFECTIVE_E3_COUNT,
            "frozen_allowlist_N": len(ALLOW),
            "metric_visible_allowlisted_N": EFFECTIVE_E3_COUNT,
            "Chance@5": CHANCE_AT_5,
            "ChanceAvg@5": 15 / (5 * EFFECTIVE_E3_COUNT),
        },
        "bootstrap": {
            "seed": BOOTSTRAP_SEED,
            "samples": BOOTSTRAP_SAMPLES,
            "ci": "95% percentile",
            "case_order": "lexical",
            "overall_indices_sha256": hashlib.sha256(
                overall_indices.astype("<i8").tobytes()
            ).hexdigest(),
        },
        "coverage": coverage,
        "unavailable_methods": UNAVAILABLE_METHODS,
        "v2a_strength_distribution": v2a_strength_distribution,
        "overall_primary_all_90": overall,
        "primary_ci95": primary_ci,
        "valid_rankings_only_secondary": valid_only,
        "paired_differences": paired,
        "per_fault": per_fault,
        "re2tt_accessed": True,
    }
    write(OUT / "step27_results.json", result)

    lines = [
        "# Step 27 RE2-TT Held-out Results",
        "",
        "| Method | AC@1 | AC@3 | AC@5 | Avg@5 | Lift@5 | OK | Fallback | Timeout | Hard fail |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for method in METHODS:
        m = overall[method]
        c = coverage[method]
        lines.append(
            f"| {method} | {m['AC@1']:.6f} | {m['AC@3']:.6f} | "
            f"{m['AC@5']:.6f} | {m['Avg@5']:.6f} | "
            f"{m['Lift@5']:.6f} | {c['ok']} | "
            f"{c['fallback_unranked']} | {c['timeout_unranked']} | "
            f"{c['hard_failed']} |"
        )
    for method in UNAVAILABLE_METHODS:
        lines.append(
            f"| {method} | n/a | n/a | n/a | n/a | n/a | 0 | 0 | 0 | 0 |"
        )
    lines.extend(
        [
            "",
            "Primary denominator is all 90 held-out RE2-TT cases for runnable methods.",
            "Fallbacks, timeouts, and hard failures count as misses under the frozen scoring policy.",
            "mmBARO/mmCIRCA are n/a (outside pinned input contract), excluded from numerical "
            "comparison, and are not scored as 90 misses.",
            "See step27_results.json for paired CIs, per-fault tables, "
            "valid-only secondary metrics, and bootstrap provenance.",
            "",
            "RE2-TT was evaluated under the frozen Step 27 protocol.",
        ]
    )
    (OUT / "STEP27_RESULTS.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
