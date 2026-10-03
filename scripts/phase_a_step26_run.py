from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_baselines import (
    deterministic_random_ranking,
    pagerank_ranking,
    static_threshold_ranking,
)
from sentinelops.evaluation.rcaeval_rca import (
    graph_from_edges,
    sentinelops_continuous_ranking,
)
from sentinelops.evaluation.rcaeval_runner import (
    evaluate_detection_case,
    summarize_detection_case,
)
from sentinelops.evaluation.rcaeval_v2 import (
    compute_v2_strengths,
    sentinelops_v2_ranking,
)

DATA_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ss")
ALLOW = {
    "front-end",
    "carts",
    "catalogue",
    "orders",
    "payment",
    "queue-master",
    "shipping",
    "user",
}
EDGES = (
    ("front-end", "carts"),
    ("orders", "carts"),
    ("front-end", "catalogue"),
    ("front-end", "orders"),
    ("orders", "payment"),
    ("orders", "shipping"),
    ("front-end", "user"),
    ("orders", "user"),
    ("shipping", "rabbitmq"),
    ("queue-master", "rabbitmq"),
    ("carts", "carts-db"),
    ("catalogue", "catalogue-db"),
    ("orders", "orders-db"),
    ("user", "user-db"),
)
METHODS = ("v1", "v2a", "threshold", "random", "pagerank", "mmbaro", "mmcirca")


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def case_ids() -> list[str]:
    frame = pl.read_parquet(DATA_ROOT / "cases.parquet")
    ids = (
        frame.filter(pl.col("dataset") == "RE2-SS")
        .sort("case")["case"]
        .to_list()
    )
    if len(ids) != 90:
        raise RuntimeError(f"Expected 90 RE2-SS cases, found {len(ids)}")
    return ids


def filter_rows(rows: list[dict[str, object]]) -> list[str]:
    return [
        str(row["service"])
        for row in rows
        if str(row["service"]) in ALLOW
    ]


def local_ranking(case_id: str, method: str) -> dict[str, object]:
    case = DATA_ROOT / case_id
    metrics = pl.read_parquet(case / "metrics.parquet")
    inject = int((case / "inject_time.txt").read_text().strip())
    services = sorted(
        {
            column.rsplit("_", 1)[0]
            for column in metrics.columns
            if column != "time" and "_" in column
        }
    )
    graph = graph_from_edges(services, EDGES)

    v1_strengths: dict[str, float] | None = None
    if method in {"v1", "pagerank"}:
        detection = summarize_detection_case(
            evaluate_detection_case(metrics, inject), inject
        )
        v1_strengths = {
            service: float(values["fault_max_anomaly_strength"])
            for service, values in detection["per_service"].items()
        }
        if not all(np.isfinite(value) for value in v1_strengths.values()):
            raise ValueError("non-finite v1 service strength")

    if method == "v1":
        assert v1_strengths is not None
        rows = sentinelops_continuous_ranking(
            v1_strengths,
            graph,
            max_candidates=len(v1_strengths),
        )
    elif method == "v2a":
        strengths = compute_v2_strengths(metrics, inject)
        rows, _primary = sentinelops_v2_ranking(strengths, graph, "v2a")
    elif method == "threshold":
        rows = static_threshold_ranking(metrics, inject, threshold=2.5)
    elif method == "random":
        source = static_threshold_ranking(metrics, inject, threshold=2.5)
        candidates = [str(row["service"]) for row in source]
        rows, derived_seed = deterministic_random_ranking(
            candidates,
            case_id=case_id,
            master_seed=42,
        )
    elif method == "pagerank":
        assert v1_strengths is not None
        rows = pagerank_ranking(
            services=v1_strengths,
            edges=list(EDGES),
            service_strengths=v1_strengths,
            damping=0.85,
        )
    else:
        raise ValueError(f"Unsupported local method: {method}")

    payload: dict[str, object] = {
        "status": "ok",
        "case_id": case_id,
        "method": method,
        "ranking": rows,
        "e3_filtered_service_ranking": filter_rows(rows),
        "ground_truth_used_for_ranking": False,
        "candidate_count": len(rows),
    }
    if method == "random":
        payload["master_seed"] = 42
        payload["derived_seed"] = derived_seed
    if method == "pagerank":
        payload["damping"] = 0.85
        payload["personalization_source"] = (
            "continuous v1 fault-window anomaly strength"
        )
    return payload


def unavailable_mm(case_id: str, method: str) -> dict[str, object]:
    return {
        "status": "hard_failed",
        "case_id": case_id,
        "method": method,
        "error_type": "FrozenInputUnavailable",
        "error": (
            "Pinned RE2-SS case provides raw logs.parquet but pinned RCAEval "
            f"{method} requires preprocessed logts.csv; no pinned official "
            "raw-to-logts transform was found, and held-out preprocessing "
            "will not be invented."
        ),
        "missing_required_inputs": ["logts.csv"],
        "ground_truth_used_for_ranking": False,
        "e3_filtered_service_ranking": [],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    args = parser.parse_args()
    method = args.method
    started = time.perf_counter()
    out_dir = OUT / "cases" / method
    out_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    failures = 0
    ids = case_ids()

    for case_id in ids:
        path = out_dir / f"{case_id}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("status") in {"ok", "hard_failed"}:
                completed += 1
                failures += int(cached.get("status") == "hard_failed")
                continue
        try:
            if method in {"mmbaro", "mmcirca"}:
                payload = unavailable_mm(case_id, method)
            else:
                payload = local_ranking(case_id, method)
        except Exception as exc:
            payload = {
                "status": "hard_failed",
                "case_id": case_id,
                "method": method,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "ground_truth_used_for_ranking": False,
                "e3_filtered_service_ranking": [],
            }
        write_json(path, payload)
        completed += 1
        failures += int(payload["status"] == "hard_failed")
        print(method, case_id, payload["status"], flush=True)

    summary = {
        "method": method,
        "case_count_expected": len(ids),
        "case_count_written_or_cached": completed,
        "hard_failed": failures,
        "fallback_unranked": 0,
        "runtime_seconds": time.perf_counter() - started,
        "resumable": True,
        "ground_truth_used_for_ranking": False,
        "re2tt_accessed": False,
    }
    write_json(OUT / f"step26_{method}_run_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
