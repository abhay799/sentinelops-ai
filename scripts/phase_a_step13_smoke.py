from __future__ import annotations

import json
import subprocess
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
DATASET_ROOT = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
)
OUT = Path(
    "docs/evidence/phase_a/re2ob/step13_smoke.json"
)
def git_head() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()


def service_columns(
    columns: list[str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for column in columns:
        if column == "time":
            continue
        service, _metric = column.rsplit("_", 1)
        grouped.setdefault(service, []).append(column)
    return grouped


def main() -> None:
    case_dir = DATASET_ROOT / CASE_ID
    metrics = pl.read_parquet(
        case_dir / "metrics.parquet"
    )
    inject_time = int(
        (case_dir / "inject_time.txt")
        .read_text()
        .strip()
    )
    prepared = prepare_metrics(
        metrics,
        inject_time_s=inject_time,
    )
    frame = prepared.frame
    times = frame["time"].to_numpy()
    grouped = service_columns(frame.columns)
    service_outputs: dict[str, dict[str, np.ndarray]] = {}

    for service, columns in sorted(grouped.items()):
        matrix = frame.select(columns).to_numpy()
        z_scores = []
        z_flags = []
        ewma_scores = []
        ewma_flags = []
        for index in range(matrix.shape[1]):
            z_score, z_flag = calibration_zscore(
                matrix[:, index],
                prepared.calibration_rows,
            )
            e_score, e_flag = calibration_ewma(
                matrix[:, index],
                prepared.calibration_rows,
            )
            z_scores.append(z_score)
            z_flags.append(z_flag)
            ewma_scores.append(e_score)
            ewma_flags.append(e_flag)
        service_z_scores = np.max(
            np.column_stack(z_scores), axis=1
        )
        service_z_flags = np.max(
            np.column_stack(z_flags), axis=1
        )
        service_e_scores = np.max(
            np.column_stack(ewma_scores), axis=1
        )
        service_e_flags = np.max(
            np.column_stack(ewma_flags), axis=1
        )
        if_scores, if_flags = calibration_isolation_forest(
            matrix,
            prepared.calibration_rows,
        )
        scores, votes, flags = ensemble_two_of_three(
            service_z_scores,
            service_z_flags,
            service_e_scores,
            service_e_flags,
            if_scores,
            if_flags,
            prepared.calibration_rows,
        )
        service_outputs[service] = {
            "scores": scores,
            "votes": votes,
            "flags": flags,
        }

    flags_matrix = np.column_stack(
        [
            output["flags"]
            for output in service_outputs.values()
        ]
    )
    system_alert = (
        np.max(flags_matrix, axis=1) > 0
    ).astype(int)
    cal_end = prepared.calibration_rows
    pre_end = prepared.pre_injection_rows
    normal_alerts = int(
        system_alert[cal_end:pre_end].sum()
    )
    fault_alerts = int(system_alert[pre_end:].sum())
    fault_times = times[pre_end:]
    fault_flags = system_alert[pre_end:]
    positives = np.flatnonzero(fault_flags)
    first_fault_time = (
        int(fault_times[positives[0]])
        if len(positives)
        else None
    )
    delay = (
        first_fault_time - inject_time
        if first_fault_time is not None
        else None
    )

    payload = {
        "step": 13,
        "status": "runtime_smoke_only",
        "case_id": CASE_ID,
        "sentinelops_commit": git_head(),
        "dataset_revision":
            "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e",
        "command":
            "python scripts/phase_a_step13_smoke.py",
        "inject_time": inject_time,
        "calibration_rows": prepared.calibration_rows,
        "normal_evaluation_rows":
            prepared.evaluation_normal_rows,
        "fault_rows": prepared.fault_rows,
        "service_count": len(service_outputs),
        "normal_evaluation_alerts": normal_alerts,
        "fault_alerts": fault_alerts,
        "fault_alert_rate": (
            fault_alerts / prepared.fault_rows
        ),
        "first_fault_alert_time": first_fault_time,
        "detection_delay_seconds": delay,
        "note":
            "Smoke/runtime validation only; not used for tuning.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(payload, indent=2, sort_keys=True)
        + "\n"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
