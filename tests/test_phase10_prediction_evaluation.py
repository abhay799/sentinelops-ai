import numpy as np
import polars as pl

from sentinelops.prediction.evaluation import (
    classification_metrics,
    validate_prediction_safety,
)


def test_classification_metrics_are_correct():

    y_true = np.array(
        [0, 0, 1, 1]
    )

    y_pred = np.array(
        [0, 1, 1, 1]
    )

    metrics = classification_metrics(
        y_true,
        y_pred,
    )

    assert metrics["tp"] == 2
    assert metrics["fp"] == 1
    assert metrics["tn"] == 1
    assert metrics["fn"] == 0
    assert metrics["recall"] == 1.0


def test_prediction_safety_accepts_valid_data():

    data = pl.DataFrame(
        {
            "warning_flag": [0, 1],
            "current_is_anomaly": [0, 0],
            "early_warning_score": [0.1, 0.8],
        }
    )

    errors = validate_prediction_safety(
        data
    )

    assert errors == []


def test_prediction_safety_rejects_current_anomaly_warning():

    data = pl.DataFrame(
        {
            "warning_flag": [1],
            "current_is_anomaly": [1],
            "early_warning_score": [0.9],
        }
    )

    errors = validate_prediction_safety(
        data
    )

    assert len(errors) > 0


def test_score_outside_range_fails():

    data = pl.DataFrame(
        {
            "warning_flag": [0],
            "current_is_anomaly": [0],
            "early_warning_score": [1.5],
        }
    )

    errors = validate_prediction_safety(
        data
    )

    assert len(errors) > 0
