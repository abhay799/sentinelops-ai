from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_detection import (
    calibration_ewma,
    calibration_isolation_forest,
    calibration_zscore,
    ensemble_two_of_three,
    prepare_metrics,
)


@dataclass(frozen=True)
class ServiceDetection:
    score: np.ndarray
    votes: np.ndarray
    flags: np.ndarray


@dataclass(frozen=True)
class CaseDetection:
    calibration_rows: int
    pre_injection_rows: int
    fault_rows: int
    times: np.ndarray
    services: dict[str, ServiceDetection]
    system_score: np.ndarray
    system_alert: np.ndarray
    @property
    def normal_slice(self) -> slice:
        return slice(
            self.calibration_rows,
            self.pre_injection_rows,
        )

    @property
    def fault_slice(self) -> slice:
        return slice(
            self.pre_injection_rows,
            self.pre_injection_rows + self.fault_rows,
        )


def group_metric_columns(
    columns: list[str],
) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for column in columns:
        if column == "time":
            continue
        service, _metric = column.rsplit("_", 1)
        grouped.setdefault(service, []).append(column)
    return grouped


def evaluate_detection_case(
    metrics: pl.DataFrame,
    inject_time_s: int,
) -> CaseDetection:
    prepared = prepare_metrics(metrics, inject_time_s)
    frame = prepared.frame
    grouped = group_metric_columns(frame.columns)
    outputs: dict[str, ServiceDetection] = {}
    for service, columns in sorted(grouped.items()):
        matrix = frame.select(columns).to_numpy()
        z_scores: list[np.ndarray] = []
        z_flags: list[np.ndarray] = []
        ewma_scores: list[np.ndarray] = []
        ewma_flags: list[np.ndarray] = []

        for index in range(matrix.shape[1]):
            score, flag = calibration_zscore(
                matrix[:, index],
                prepared.calibration_rows,
            )
            z_scores.append(score)
            z_flags.append(flag)
            score, flag = calibration_ewma(
                matrix[:, index],
                prepared.calibration_rows,
            )
            ewma_scores.append(score)
            ewma_flags.append(flag)

        service_z_score = np.max(
            np.column_stack(z_scores), axis=1
        )
        service_z_flag = np.max(
            np.column_stack(z_flags), axis=1
        )
        service_ewma_score = np.max(
            np.column_stack(ewma_scores), axis=1
        )
        service_ewma_flag = np.max(
            np.column_stack(ewma_flags), axis=1
        )
        iforest_score, iforest_flag = (
            calibration_isolation_forest(
                matrix,
                prepared.calibration_rows,
            )
        )
        score, votes, flags = ensemble_two_of_three(
            service_z_score,
            service_z_flag,
            service_ewma_score,
            service_ewma_flag,
            iforest_score,
            iforest_flag,
            prepared.calibration_rows,
        )
        outputs[service] = ServiceDetection(
            score=score,
            votes=votes,
            flags=flags,
        )

    service_scores = np.column_stack(
        [item.score for item in outputs.values()]
    )
    service_flags = np.column_stack(
        [item.flags for item in outputs.values()]
    )
    system_score = np.max(service_scores, axis=1)
    system_alert = (
        np.max(service_flags, axis=1) > 0
    ).astype(int)

    return CaseDetection(
        calibration_rows=prepared.calibration_rows,
        pre_injection_rows=prepared.pre_injection_rows,
        fault_rows=prepared.fault_rows,
        times=frame["time"].to_numpy(),
        services=outputs,
        system_score=system_score,
        system_alert=system_alert,
    )


def confusion_counts(
    labels: np.ndarray,
    predictions: np.ndarray,
) -> dict[str, int]:
    labels = np.asarray(labels, dtype=int)
    predictions = np.asarray(predictions, dtype=int)
    return {
        "tp": int(np.sum((labels == 1) & (predictions == 1))),
        "fp": int(np.sum((labels == 0) & (predictions == 1))),
        "tn": int(np.sum((labels == 0) & (predictions == 0))),
        "fn": int(np.sum((labels == 1) & (predictions == 0))),
    }


def metrics_from_counts(
    counts: dict[str, int],
) -> dict[str, float]:
    tp = counts["tp"]
    fp = counts["fp"]
    fn = counts["fn"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2.0 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def summarize_detection_case(
    result: CaseDetection,
    inject_time_s: int,
) -> dict[str, object]:
    normal = result.normal_slice
    fault = result.fault_slice
    normal_alert = result.system_alert[normal]
    fault_alert = result.system_alert[fault]
    predictions = np.concatenate([normal_alert, fault_alert])
    labels = np.concatenate(
        [
            np.zeros(len(normal_alert), dtype=int),
            np.ones(len(fault_alert), dtype=int),
        ]
    )
    timestamp_counts = confusion_counts(labels, predictions)
    normal_positive = int(np.any(normal_alert))
    fault_positive = int(np.any(fault_alert))
    window_counts = confusion_counts(
        np.array([0, 1]),
        np.array([normal_positive, fault_positive]),
    )
    fault_positions = np.flatnonzero(fault_alert)
    delay = (
        int(result.times[result.pre_injection_rows + fault_positions[0]])
        - inject_time_s
        if len(fault_positions)
        else None
    )
    per_service: dict[str, object] = {}
    for service, output in result.services.items():
        per_service[service] = {
            "normal_alert_rate": float(
                np.mean(output.flags[normal])
            ),
            "fault_alert_rate": float(
                np.mean(output.flags[fault])
            ),
            "fault_max_anomaly_strength": float(
                np.max(output.score[fault])
            ),
        }

    return {
        "timestamp_confusion": timestamp_counts,
        "timestamp_metrics": metrics_from_counts(timestamp_counts),
        "window_confusion": window_counts,
        "window_metrics": metrics_from_counts(window_counts),
        "normal_window_score": float(
            np.max(result.system_score[normal])
        ),
        "fault_window_score": float(
            np.max(result.system_score[fault])
        ),
        "normal_window_positive": normal_positive,
        "fault_window_positive": fault_positive,
        "detection_delay_seconds": delay,
        "per_service": per_service,
    }
