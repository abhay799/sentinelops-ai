from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

RCA_ROOT = Path("/home/dell/benchmarks/RCAEval")
DATA_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("/home/dell/work/sentinelops-ai-phase-a/docs/evidence/phase_a/re2tt")
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
METHODS = ("baro", "circa")

sys.path.insert(0, str(RCA_ROOT))
from RCAEval.e2e import baro, circa  # noqa: E402

FUNCS = {"baro": baro, "circa": circa}


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


def case_ids() -> list[str]:
    ids = sorted(path.name for path in DATA_ROOT.glob("re2tt_*") if path.is_dir())
    if len(ids) != 90:
        raise RuntimeError(f"Expected 90 RE2-TT cases, found {len(ids)}")
    return ids


def native_service_ranking(ranks: list[str]) -> list[str]:
    out: list[str] = []
    for item in ranks:
        service = str(item).split("_")[0].replace("-db", "")
        if service not in out:
            out.append(service)
    return out


def prepare_case(case_id: str) -> tuple[pd.DataFrame, int]:
    case = DATA_ROOT / case_id
    data = pd.read_parquet(case / "metrics.parquet")
    data = data.loc[:, ~data.columns.str.endswith("_latency-50")]
    data = data.replace([np.inf, -np.inf], np.nan).ffill().fillna(0)
    inject = int((case / "inject_time.txt").read_text().strip())
    window = 20 * 60 // 2
    normal = data[data["time"] < inject].tail(window)
    anomal = data[data["time"] >= inject].head(window)
    data = pd.concat([normal, anomal], ignore_index=True)
    data = data.rename(
        columns={
            col: col.replace("_latency-90", "_latency")
            for col in data.columns
            if col.endswith("_latency-90")
        }
    )
    return data, inject


def run_case(case_id: str, method: str) -> dict[str, object]:
    data, inject = prepare_case(case_id)
    stderr = io.StringIO()
    with contextlib.redirect_stderr(stderr):
        out = FUNCS[method](
            data.copy(deep=True),
            inject,
            dataset="re2-tt",
            anomalies=None,
            dk_select_useful=False,
            sli="ts-ui-dashboard_latency",
            verbose=False,
            n_iter=len(data.columns) - 1,
            args=SimpleNamespace(
                root_path=str(RCA_ROOT),
                data_path=str(DATA_ROOT / case_id / "metrics.parquet"),
            ),
        )
    warning = stderr.getvalue()
    raw_ranks = [str(value) for value in out.get("ranks", [])]
    fallback = "returning the unranked column order" in warning
    if fallback:
        return {
            "status": "fallback_unranked",
            "case_id": case_id,
            "method": method,
            "fallback_detected": True,
            "fallback_reason": warning.strip(),
            "fallback_returned_feature_order": raw_ranks,
            "ground_truth_used_for_ranking": False,
            "e3_filtered_service_ranking": [],
        }

    native = native_service_ranking(raw_ranks)
    return {
        "status": "ok",
        "case_id": case_id,
        "method": method,
        "raw_feature_ranking": raw_ranks,
        "native_service_ranking": native,
        "e3_filtered_service_ranking": [service for service in native if service in ALLOW],
        "fallback_detected": False,
        "rcaeval_stderr": warning,
        "ground_truth_used_for_ranking": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--shard-index", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    args = parser.parse_args()
    method = args.method
    if args.shard_count < 1 or not 0 <= args.shard_index < args.shard_count:
        raise ValueError("Invalid shard configuration")
    started = time.perf_counter()
    out_dir = OUT / "cases" / method
    out_dir.mkdir(parents=True, exist_ok=True)
    completed = 0
    failures = 0
    fallbacks = 0

    selected_ids = case_ids()[args.shard_index :: args.shard_count]
    for case_id in selected_ids:
        path = out_dir / f"{case_id}.json"
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("status") in {"ok", "fallback_unranked", "hard_failed"}:
                completed += 1
                failures += int(cached.get("status") == "hard_failed")
                fallbacks += int(cached.get("status") == "fallback_unranked")
                continue
        try:
            payload = run_case(case_id, method)
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
        fallbacks += int(payload["status"] == "fallback_unranked")
        print(method, case_id, payload["status"], flush=True)

    summary = {
        "method": method,
        "shard_index": args.shard_index,
        "shard_count": args.shard_count,
        "case_count_expected": len(selected_ids),
        "case_count_written_or_cached": completed,
        "hard_failed": failures,
        "fallback_unranked": fallbacks,
        "runtime_seconds": time.perf_counter() - started,
        "resumable": True,
        "ground_truth_used_for_ranking": False,
        "re2tt_accessed": True,
    }
    suffix = (
        ""
        if args.shard_count == 1
        else f"_shard{args.shard_index}of{args.shard_count}"
    )
    write_json(OUT / f"step27_{method}_run_summary{suffix}.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
