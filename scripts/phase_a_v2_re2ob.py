from __future__ import annotations

import argparse
import json
import multiprocessing
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import polars as pl

from sentinelops.evaluation.rcaeval_rca import graph_from_edges
from sentinelops.evaluation.rcaeval_v2 import (
    Variant,
    compute_v2_strengths,
    sentinelops_v2_ranking,
)

ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ob")
ALLOW = set(
    "adservice cartservice checkoutservice currencyservice emailservice frontend "
    "paymentservice productcatalogservice recommendationservice redis shippingservice".split()
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def case_ids() -> list[str]:
    frame = pl.read_parquet(ROOT / "cases.parquet")
    return (
        frame.filter(pl.col("dataset") == "RE2-OB")
        .sort("case")["case"]
        .to_list()
    )


def suite_graph():
    payload = json.loads((OUT / "re2ob_suite_graph.json").read_text())
    return graph_from_edges(
        payload["nodes"],
        [(str(a), str(b)) for a, b in payload["edges"]],
    )


def run_case(case_id: str, variant: Variant) -> dict[str, object]:
    started = time.perf_counter()
    case = ROOT / case_id
    metrics = pl.read_parquet(case / "metrics.parquet")
    inject = int((case / "inject_time.txt").read_text().strip())
    strengths = compute_v2_strengths(metrics, inject)
    ranking, primary_service = sentinelops_v2_ranking(
        strengths, suite_graph(), variant
    )
    e3 = [
        str(row["service"])
        for row in ranking
        if str(row["service"]) in ALLOW
    ]
    eligible_raw = {
        service: value
        for service, value in strengths.unclipped.items()
        if service in ALLOW
    }
    eligible_clipped = {
        service: value
        for service, value in strengths.clipped.items()
        if service in ALLOW
    }
    max_raw = max(eligible_raw.values())
    top_tied = sorted(
        service for service, value in eligible_raw.items() if value == max_raw
    )
    max_clipped = max(eligible_clipped.values())
    clipped_primary_group = sorted(
        service
        for service, value in eligible_clipped.items()
        if value == max_clipped
    )
    return {
        "case_id": case_id,
        "variant": variant,
        "status": "ok",
        "ground_truth_used_for_ranking": False,
        "candidate_count": len(ranking),
        "ranking": ranking,
        "e3_filtered_service_ranking": e3,
        "primary_service": primary_service,
        "unclipped_strengths": strengths.unclipped,
        "clipped_v1_strengths": strengths.clipped,
        "top_tied_services": top_tied,
        "top_tie_count": len(top_tied),
        "v1_clipped_primary_group": clipped_primary_group,
        "v1_clipped_primary_group_count": len(clipped_primary_group),
        "runtime_seconds": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--variant", required=True, choices=("v2a", "v2b"))
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    variant: Variant = args.variant
    ids = case_ids()
    if len(ids) != 90:
        raise RuntimeError(f"Expected 90 RE2-OB cases, found {len(ids)}")
    case_out = OUT / f"{variant}_cases"
    case_out.mkdir(parents=True, exist_ok=True)

    with ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as pool:
        futures = {
            pool.submit(run_case, case_id, variant): case_id for case_id in ids
        }
        for future in as_completed(futures):
            payload = future.result()
            write_json(case_out / f"{payload['case_id']}.json", payload)
            print(variant, payload["case_id"], "ok", flush=True)

    missing = [case_id for case_id in ids if not (case_out / f"{case_id}.json").exists()]
    if missing:
        raise RuntimeError(f"Missing {variant} outputs: {missing}")
    write_json(
        OUT / f"{variant}_run_summary.json",
        {
            "variant": variant,
            "case_count": len(ids),
            "workers": args.workers,
            "status": "complete",
            "exact_command": (
                f".venv/bin/python scripts/phase_a_v2_re2ob.py "
                f"--variant {variant} --workers {args.workers}"
            ),
        },
    )


if __name__ == "__main__":
    main()
