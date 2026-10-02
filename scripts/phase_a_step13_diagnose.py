from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_detection import (
    calibration_ewma,
    calibration_isolation_forest,
    calibration_zscore,
    ensemble_two_of_three,
    prepare_metrics,
)

CASE_ID = "re2ob_checkoutservice_cpu_1"
ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path(
    "docs/evidence/phase_a/re2ob/"
    "step13_suspicious_diagnostic.json"
)
def grouped_columns(
    columns: list[str],
) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for column in columns:
        if column == "time":
            continue
        service, _metric = column.rsplit("_", 1)
        result.setdefault(service, []).append(column)
    return result


def count_rate(
    values: np.ndarray,
    start: int,
    end: int,
) -> dict[str, float | int]:
    count = int(values[start:end].sum())
    total = int(end - start)
    return {
        "count": count,
        "total": total,
        "rate": count / total if total else 0.0,
    }


def main() -> None:
    case = ROOT / CASE_ID
    metrics = pl.read_parquet(case / "metrics.parquet")
    inject = int(
        (case / "inject_time.txt").read_text().strip()
    )
    prepared = prepare_metrics(metrics, inject)
    frame = prepared.frame
    grouped = grouped_columns(frame.columns)
    c = prepared.calibration_rows
    p = prepared.pre_injection_rows
    n = frame.height
    per_service: dict[str, object] = {}
    all_ensemble: list[np.ndarray] = []
    for service, columns in sorted(grouped.items()):
        matrix = frame.select(columns).to_numpy()
        z_scores_list: list[np.ndarray] = []
        z_flags_list: list[np.ndarray] = []
        e_scores_list: list[np.ndarray] = []
        e_flags_list: list[np.ndarray] = []
        constant_calibration_metrics = 0

        for idx in range(matrix.shape[1]):
            if np.std(matrix[:c, idx], ddof=0) == 0.0:
                constant_calibration_metrics += 1
            zs, zf = calibration_zscore(
                matrix[:, idx], c
            )
            es, ef = calibration_ewma(
                matrix[:, idx], c
            )
            z_scores_list.append(zs)
            z_flags_list.append(zf)
            e_scores_list.append(es)
            e_flags_list.append(ef)

        z_scores = np.max(
            np.column_stack(z_scores_list), axis=1
        )
        z_flags = np.max(
            np.column_stack(z_flags_list), axis=1
        )
        e_scores = np.max(
            np.column_stack(e_scores_list), axis=1
        )
        e_flags = np.max(
            np.column_stack(e_flags_list), axis=1
        )
        i_scores, i_flags = calibration_isolation_forest(
            matrix, c
        )
        _scores, votes, ensemble_flags = (
            ensemble_two_of_three(
                z_scores,
                z_flags,
                e_scores,
                e_flags,
                i_scores,
                i_flags,
                c,
            )
        )
        all_ensemble.append(ensemble_flags)
        per_service[service] = {
            "metric_count": len(columns),
            "constant_calibration_metrics":
                constant_calibration_metrics,
            "z_calibration": count_rate(z_flags, 0, c),
            "z_normal": count_rate(z_flags, c, p),
            "z_fault": count_rate(z_flags, p, n),
            "ewma_calibration": count_rate(e_flags, 0, c),
            "ewma_normal": count_rate(e_flags, c, p),
            "ewma_fault": count_rate(e_flags, p, n),
            "iforest_calibration": count_rate(
                i_flags, 0, c
            ),
            "iforest_normal": count_rate(i_flags, c, p),
            "iforest_fault": count_rate(i_flags, p, n),
            "ensemble_normal": count_rate(
                ensemble_flags, c, p
            ),
            "ensemble_fault": count_rate(
                ensemble_flags, p, n
            ),
            "normal_vote_histogram": {
                str(v): int(
                    np.sum(votes[c:p] == v)
                )
                for v in range(4)
            },
        }
    system = (
        np.max(np.column_stack(all_ensemble), axis=1) > 0
    ).astype(int)
    ranked = sorted(
        (
            (
                service,
                data["ensemble_normal"]["rate"],
            )
            for service, data in per_service.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    payload = {
        "case_id": CASE_ID,
        "calibration_rows": c,
        "normal_rows": p - c,
        "fault_rows": n - p,
        "system_normal": count_rate(system, c, p),
        "system_fault": count_rate(system, p, n),
        "services_by_normal_ensemble_rate": ranked,
        "per_service": per_service,
        "interpretation":
            "Diagnostic only; no threshold or parameter changes.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True)
        + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
