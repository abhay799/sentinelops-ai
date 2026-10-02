from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

RCA_ROOT = Path("/home/dell/benchmarks/RCAEval")
RCA_DATA = RCA_ROOT / "data/RE2/RE2-OB"
REPO_ROOT = Path("/home/dell/work/sentinelops-ai-phase-a")
OUT_ROOT = (
    REPO_ROOT
    / "docs/evidence/phase_a/re2ob/rcaeval_baseline_cases"
)
ALLOWLIST = (
    "adservice",
    "cartservice",
    "checkoutservice",
    "currencyservice",
    "emailservice",
    "frontend",
    "paymentservice",
    "productcatalogservice",
    "recommendationservice",
    "redis",
    "shippingservice",
)
ALLOWSET = set(ALLOWLIST)
METHODS = ("baro", "circa", "mmbaro", "mmcirca")

sys.path.insert(0, str(RCA_ROOT))

from RCAEval.e2e import baro, circa, mmbaro, mmcirca  # noqa: E402
from RCAEval.io.time_series import preprocess  # noqa: E402

METHOD_FUNCS = {
    "baro": baro,
    "circa": circa,
    "mmbaro": mmbaro,
    "mmcirca": mmcirca,
}
def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )


def case_paths() -> list[Path]:
    paths = sorted(RCA_DATA.glob("*/*/simple_metrics.csv"))
    if len(paths) != 90:
        raise RuntimeError(
            f"Expected 90 native RE2-OB cases, found {len(paths)}"
        )
    return paths


def case_identity(path: Path) -> tuple[str, str, str]:
    service_fault = path.parent.parent.name
    service, fault = service_fault.rsplit("_", 1)
    repetition = path.parent.name
    return (
        f"re2ob_{service}_{fault}_{repetition}",
        service,
        fault,
    )


def native_service_ranking(
    ranks: list[str],
) -> list[str]:
    out: list[str] = []
    for item in ranks:
        service = str(item).split("_")[0].replace("-db", "")
        if service not in out:
            out.append(service)
    return out
def prepare_case(
    path: Path,
    method: str,
) -> tuple[object, int, str, int]:
    data = pd.read_csv(path)
    if "time.1" in data:
        data = data.drop(columns=["time.1"])
    data = data.loc[:, ~data.columns.str.endswith("_latency-50")]
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.ffill().fillna(0)

    inject_time = int(
        (path.parent / "inject_time.txt").read_text().strip()
    )
    length = 20
    window = length * 60 // 2
    normal = data[data["time"] < inject_time].tail(window)
    anomal = data[data["time"] >= inject_time].head(window)
    data = pd.concat([normal, anomal], ignore_index=True)

    pre_cols = preprocess(
        data.copy(),
        dataset="re2-ob",
        dk_select_useful=False,
    ).columns
    native_candidate_count = len(
        {
            col.split("_")[0].replace("-db", "")
            for col in pre_cols
            if col != "time"
        }
    )

    data = data.rename(
        columns={
            col: col.replace("_latency-90", "_latency")
            for col in data.columns
            if col.endswith("_latency-90")
        }
    )
    _case_id, service, _fault = case_identity(path)
    sli = "frontend_latency"
    if f"{service}_latency" in data:
        sli = f"{service}_latency"
    elif "frontend_1" in data:
        sli = "frontend_1"

    if method in {"mmbaro", "mmcirca"}:
        logts = pd.read_csv(path.parent / "logts.csv")
        traces_err = pd.read_csv(path.parent / "tracets_err.csv")
        traces_lat = pd.read_csv(path.parent / "tracets_lat.csv")
        logts_length = length * 4 // 2

        def window_ts(frame: pd.DataFrame) -> pd.DataFrame:
            before = frame[frame["time"] < inject_time].tail(
                logts_length
            )
            after = frame[frame["time"] >= inject_time].head(
                logts_length
            )
            return pd.concat([before, after], ignore_index=True)

        data = {
            "metric": data.copy(deep=True),
            "logts": window_ts(logts),
            "tracets_err": window_ts(traces_err),
            "tracets_lat": window_ts(traces_lat),
        }

    return data, inject_time, sli, native_candidate_count
def trace_policy(method: str) -> dict[str, object]:
    if method == "mmbaro":
        return {
            "raw_span_rows_consumed": False,
            "input": (
                "RCAEval-shipped preaggregated tracets_err.csv "
                "and tracets_lat.csv"
            ),
            "duplicate_erratum_effect": (
                "not applied at raw-span level; the pinned mmBARO "
                "API consumes preaggregated trace time series"
            ),
        }
    if method == "mmcirca":
        return {
            "raw_span_rows_consumed": False,
            "input": (
                "main-compatible data dict loads shipped trace time "
                "series, but pinned mmCIRCA uses metric and logts only"
            ),
            "duplicate_erratum_effect": (
                "none in pinned mmCIRCA implementation because "
                "trace fields are not read by mmcirca()"
            ),
        }
    return {
        "raw_span_rows_consumed": False,
        "input": "metrics only",
        "duplicate_erratum_effect": "not applicable",
    }


def run_case(
    path: Path,
    method: str,
) -> dict[str, object]:
    started = time.perf_counter()
    case_id, service, fault = case_identity(path)
    data, inject_time, sli, native_candidate_count = prepare_case(
        path,
        method,
    )
    run_args = SimpleNamespace(
        root_path=str(RCA_ROOT),
        data_path=str(path),
    )
    func = METHOD_FUNCS[method]
    out = func(
        data,
        inject_time,
        dataset="re2-ob",
        anomalies=None,
        dk_select_useful=False,
        sli=sli,
        verbose=False,
        n_iter=(
            len(data["metric"].columns) - 1
            if isinstance(data, dict)
            else len(data.columns) - 1
        ),
        args=run_args,
    )
    raw_ranks = [str(x) for x in out.get("ranks", [])]
    native_services = native_service_ranking(raw_ranks)
    filtered_services = [
        service_name
        for service_name in native_services
        if service_name in ALLOWSET
    ]
    return {
        "status": "ok",
        "case_id": case_id,
        "root_service_from_path": service,
        "fault": fault,
        "method": method,
        "inject_time": inject_time,
        "native_candidate_count_preprocess": native_candidate_count,
        "raw_feature_ranking": raw_ranks,
        "native_service_ranking": native_services,
        "e3_filtered_service_ranking": filtered_services,
        "e3_filtered_present_count": len(filtered_services),
        "e3_missing_allowlist_services": sorted(
            ALLOWSET - set(filtered_services)
        ),
        "trace_input_policy": trace_policy(method),
        "runtime_seconds": time.perf_counter() - started,
    }
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=METHODS, required=True)
    args = parser.parse_args()
    method = args.method
    case_out = OUT_ROOT / method
    case_out.mkdir(parents=True, exist_ok=True)
    paths = case_paths()

    completed = 0
    failed: list[dict[str, object]] = []
    missing_allowlist: list[dict[str, object]] = []
    started = time.perf_counter()

    for index, path in enumerate(paths, start=1):
        case_id, _service, _fault = case_identity(path)
        out_path = case_out / f"{case_id}.json"
        if out_path.exists():
            cached = json.loads(out_path.read_text())
            if cached.get("status") == "ok":
                completed += 1
                if cached.get("e3_missing_allowlist_services"):
                    missing_allowlist.append(cached)
                print(
                    f"[{index}/90] {method} {case_id} cached",
                    flush=True,
                )
                continue

        try:
            payload = run_case(path, method)
            if payload["e3_missing_allowlist_services"]:
                missing_allowlist.append(payload)
        except Exception as exc:
            payload = {
                "status": "failed",
                "case_id": case_id,
                "method": method,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }
            failed.append(payload)
        else:
            completed += 1

        write_json(out_path, payload)
        print(
            f"[{index}/90] {method} {case_id} "
            f"{payload['status']}",
            flush=True,
        )

    summary = {
        "step": 20,
        "method": method,
        "status": (
            "complete"
            if not failed
            else "completed_with_failures"
        ),
        "case_count_expected": len(paths),
        "case_count_ok": completed,
        "case_count_failed": len(failed),
        "failed_cases": failed,
        "e3_allowlist_size": len(ALLOWLIST),
        "cases_missing_allowlist_services": [
            {
                "case_id": row["case_id"],
                "missing": row["e3_missing_allowlist_services"],
            }
            for row in missing_allowlist
        ],
        "trace_input_policy": trace_policy(method),
        "runtime_seconds": time.perf_counter() - started,
    }
    write_json(
        OUT_ROOT / f"{method}_summary.json",
        summary,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if failed:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
