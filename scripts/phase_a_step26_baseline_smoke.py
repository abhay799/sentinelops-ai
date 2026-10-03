from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

RCA_ROOT = Path("/home/dell/benchmarks/RCAEval")
DATA_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path("docs/evidence/phase_a/re2ss")
SMOKE_CASES = ("re2ss_carts_cpu_1", "re2ss_carts_cpu_2")
METHODS = ("baro", "circa")

sys.path.insert(0, str(RCA_ROOT))
from RCAEval.e2e import baro, circa  # noqa: E402

FUNCS = {"baro": baro, "circa": circa}


def prepare(case_id: str) -> tuple[pd.DataFrame, int]:
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


def main() -> None:
    rows = []
    for case_id in SMOKE_CASES:
        data, inject = prepare(case_id)
        for method in METHODS:
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                out = FUNCS[method](
                    data.copy(deep=True),
                    inject,
                    dataset="re2-ss",
                    anomalies=None,
                    dk_select_useful=False,
                    sli="front-end_latency",
                    verbose=False,
                    n_iter=len(data.columns) - 1,
                    args=SimpleNamespace(
                        root_path=str(RCA_ROOT),
                        data_path=str(DATA_ROOT / case_id / "metrics.parquet"),
                    ),
                )
            warning = stderr.getvalue()
            ranks = [str(value) for value in out.get("ranks", [])]
            fallback = "returning the unranked column order" in warning
            rows.append(
                {
                    "case_id": case_id,
                    "method": method,
                    "status": "fallback_unranked" if fallback else "ok",
                    "rank_count": 0 if fallback else len(ranks),
                    "fallback_detected": fallback,
                    "stderr": warning,
                    "ground_truth_read_for_smoke": False,
                    "accuracy_computed": False,
                }
            )
    payload = {
        "status": "pass",
        "cases": rows,
        "ground_truth_read_for_smoke": False,
        "accuracy_computed": False,
        "settings_changed_from_smoke": False,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step26_baseline_smoke.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
