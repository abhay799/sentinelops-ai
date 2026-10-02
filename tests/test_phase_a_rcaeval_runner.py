import numpy as np
import polars as pl

from sentinelops.evaluation.rcaeval_runner import (
    confusion_counts,
    evaluate_detection_case,
    metrics_from_counts,
)


def test_post_injection_data_cannot_change_calibration():
    base = {
        "time": [1, 2, 3, 4, 5, 6, 7, 8],
        "svc_cpu": [1.0, 1.1, 0.9, 1.0, 1.1, 0.9, 5.0, 6.0],
        "svc_mem": [2.0, 2.1, 1.9, 2.0, 2.1, 1.9, 8.0, 9.0],
    }
    changed = {
        **base,
        "svc_cpu": base["svc_cpu"][:6] + [5000.0, 6000.0],
        "svc_mem": base["svc_mem"][:6] + [8000.0, 9000.0],
    }

    first = evaluate_detection_case(pl.DataFrame(base), 7)
    second = evaluate_detection_case(pl.DataFrame(changed), 7)

    assert first.calibration_rows == second.calibration_rows
    c = first.calibration_rows
    np.testing.assert_allclose(
        first.services["svc"].score[:c],
        second.services["svc"].score[:c],
    )
    np.testing.assert_array_equal(
        first.services["svc"].flags[:c],
        second.services["svc"].flags[:c],
    )
    np.testing.assert_allclose(
        first.system_score[:c],
        second.system_score[:c],
    )


def test_confusion_and_metrics():
    labels = np.array([0, 0, 1, 1])
    predictions = np.array([0, 1, 1, 0])
    counts = confusion_counts(labels, predictions)
    assert counts == {"tp": 1, "fp": 1, "tn": 1, "fn": 1}
    metrics = metrics_from_counts(counts)
    assert metrics == {
        "precision": 0.5,
        "recall": 0.5,
        "f1": 0.5,
    }
