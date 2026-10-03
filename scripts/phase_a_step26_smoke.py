from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_adapter import metric_services_from_columns
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

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ss")
ALLOW = {
    "front-end", "carts", "catalogue", "orders", "payment",
    "queue-master", "shipping", "user",
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
SMOKE_CASES = ("re2ss_carts_cpu_1", "re2ss_carts_cpu_2")


def filtered_services(rows: list[dict[str, object]]) -> list[str]:
    return [str(row["service"]) for row in rows if str(row["service"]) in ALLOW]


def main() -> None:
    results: list[dict[str, object]] = []
    for case_id in SMOKE_CASES:
        case = ROOT / case_id
        metrics = pl.read_parquet(case / "metrics.parquet")
        inject = int((case / "inject_time.txt").read_text().strip())
        services = sorted(metric_services_from_columns(metrics.columns))
        graph = graph_from_edges(services, EDGES)

        detection = evaluate_detection_case(metrics, inject)
        detection_summary = summarize_detection_case(detection, inject)
        v1_strengths = {
            service: float(values["fault_max_anomaly_strength"])
            for service, values in detection_summary["per_service"].items()
        }
        if not all(np.isfinite(value) for value in v1_strengths.values()):
            raise RuntimeError(f"non-finite v1 strengths in {case_id}")
        v1 = sentinelops_continuous_ranking(
            v1_strengths,
            graph,
            max_candidates=len(v1_strengths),
        )

        v2_strengths = compute_v2_strengths(metrics, inject)
        v2, _primary = sentinelops_v2_ranking(v2_strengths, graph, "v2a")
        if not all(np.isfinite(value) for value in v2_strengths.unclipped.values()):
            raise RuntimeError(f"non-finite V2a strengths in {case_id}")

        threshold = static_threshold_ranking(metrics, inject, threshold=2.5)
        candidates = [str(row["service"]) for row in threshold]
        random_ranking, derived_seed = deterministic_random_ranking(
            candidates,
            case_id=case_id,
            master_seed=42,
        )
        pagerank = pagerank_ranking(
            services=v1_strengths,
            edges=list(EDGES),
            service_strengths=v1_strengths,
            damping=0.85,
        )

        outputs = {
            "v1": filtered_services(v1),
            "v2a": filtered_services(v2),
            "threshold": filtered_services(threshold),
            "random": [
                str(row["service"])
                for row in random_ranking
                if str(row["service"]) in ALLOW
            ],
            "pagerank": [str(row["service"]) for row in pagerank if str(row["service"]) in ALLOW],
        }
        if any(not ranking for ranking in outputs.values()):
            raise RuntimeError(f"empty filtered smoke ranking in {case_id}")
        results.append(
            {
                "case_id": case_id,
                "metric_shape": [metrics.height, metrics.width],
                "metric_service_count": len(services),
                "frozen_allowlist_present": sorted(ALLOW & set(services)),
                "static_topology_edge_count": len(EDGES),
                "v1_service_strength_count": len(v1_strengths),
                "v2a_service_strength_count": len(v2_strengths.unclipped),
                "v2a_strengths_all_finite": True,
                "threshold_candidate_count": len(candidates),
                "random_derived_seed": derived_seed,
                "filtered_ranking_lengths": {
                    method: len(ranking) for method, ranking in outputs.items()
                },
                "ground_truth_read_for_smoke": False,
                "accuracy_computed": False,
            }
        )

    mm_input_contract = {
        "pinned_hf_case_files": ["inject_time.txt", "logs.parquet", "metrics.parquet"],
        "rcaeval_mm_required_preprocessed_input": "logts.csv",
        "official_pinned_raw_to_logts_transform_found": False,
        "action": (
            "do not invent held-out log preprocessing; record mmBARO/mmCIRCA "
            "as unavailable/hard-failed under the frozen input contract"
        ),
    }
    payload = {
        "status": "pass",
        "smoke_case_selection": "first two lexically sorted RE2-SS case IDs, frozen before outputs",
        "smoke_case_count": len(results),
        "cases": results,
        "ground_truth_read_for_smoke": False,
        "accuracy_computed": False,
        "settings_changed_from_smoke": False,
        "mm_input_contract": mm_input_contract,
        "re2tt_accessed": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step26_smoke.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
