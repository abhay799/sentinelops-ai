import json
from pathlib import Path

import joblib
import polars as pl
import yaml
from sklearn.linear_model import LogisticRegression

from sentinelops.prediction.evaluation import (
    average_lead_events,
    choose_temporal_split,
    classification_metrics,
    validate_prediction_safety,
)

INPUT = Path(
    "data/processed/prediction/"
    "early_warning_v1.parquet"
)


with open(
    "configs/failure_prediction.yaml",
    encoding="utf-8",
) as file:

    config = yaml.safe_load(
        file
    )[
        "failure_prediction"
    ]


data = (
    pl.read_parquet(
        INPUT
    )
    .filter(
        pl.col(
            "warning_ready"
        )
        &
        (
            pl.col(
                "current_is_anomaly"
            )
            == 0
        )
    )
    .sort(
        "feature_as_of_time"
    )
)


if data.is_empty():

    raise RuntimeError(
        "No eligible prediction observations"
    )


safety_errors = (
    validate_prediction_safety(
        data
    )
)

if safety_errors:

    raise RuntimeError(
        "\n".join(
            safety_errors
        )
    )


FEATURE_COLUMNS = [
    "latency_warning_component",
    "error_warning_component",
    "request_warning_component",
    "change_warning_component",
    "history_event_count",
]


split = choose_temporal_split(
    data
)


train = data.head(
    split
)

test = data.slice(
    split
)


X_train = (
    train
    .select(
        FEATURE_COLUMNS
    )
    .to_numpy()
)

y_train = (
    train[
        "future_anomaly"
    ]
    .to_numpy()
    .astype(int)
)


X_test = (
    test
    .select(
        FEATURE_COLUMNS
    )
    .to_numpy()
)

y_test = (
    test[
        "future_anomaly"
    ]
    .to_numpy()
    .astype(int)
)


supervised = config[
    "supervised"
]


model = LogisticRegression(
    class_weight=supervised[
        "class_weight"
    ],
    max_iter=int(
        supervised[
            "max_iter"
        ]
    ),
    solver="liblinear",
    random_state=42,
)


model.fit(
    X_train,
    y_train,
)


probabilities = model.predict_proba(
    X_test
)[:, 1]


predictions = (
    probabilities >= 0.5
).astype(int)


results = (
    test
    .with_columns(
        [
            pl.Series(
                "failure_probability",
                probabilities,
            ),

            pl.Series(
                "supervised_warning",
                predictions,
            ),
        ]
    )
)


metrics = classification_metrics(
    y_test,
    predictions,
)


heuristic_metrics = (
    classification_metrics(
        y_test,
        test[
            "warning_flag"
        ]
        .to_numpy()
        .astype(int),
    )
)


metrics[
    "average_lead_events"
] = average_lead_events(
    results,
    "supervised_warning",
)


heuristic_metrics[
    "average_lead_events"
] = average_lead_events(
    test,
    "warning_flag",
)


prediction_path = Path(
    config[
        "output"
    ][
        "predictions"
    ][
        "path"
    ]
)

model_path = Path(
    config[
        "output"
    ][
        "model"
    ][
        "path"
    ]
)

evaluation_path = Path(
    config[
        "output"
    ][
        "evaluation"
    ][
        "path"
    ]
)


prediction_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

model_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)

evaluation_path.parent.mkdir(
    parents=True,
    exist_ok=True,
)


results.write_parquet(
    prediction_path
)


joblib.dump(
    {
        "model":
            model,

        "features":
            FEATURE_COLUMNS,

        "train_rows":
            train.height,

        "test_rows":
            test.height,

        "split_timestamp":
            str(
                test[
                    "feature_as_of_time"
                ][0]
            ),
    },
    model_path,
)


evaluation = {
    "training": {
        "train_rows":
            train.height,

        "test_rows":
            test.height,

        "temporal_split":
            True,

        "feature_columns":
            FEATURE_COLUMNS,
    },

    "supervised":
        metrics,

    "heuristic":
        heuristic_metrics,
}


evaluation_path.write_text(
    json.dumps(
        evaluation,
        indent=2,
    ),
    encoding="utf-8",
)


print()
print("=" * 72)
print(
    " SENTINELOPS AI - PHASE 10 FAILURE PREDICTION"
)
print("=" * 72)

print(
    "Train rows:",
    train.height,
)

print(
    "Test rows:",
    test.height,
)

print()

print(
    "Supervised precision:",
    round(
        metrics[
            "precision"
        ],
        4,
    ),
)

print(
    "Supervised recall:",
    round(
        metrics[
            "recall"
        ],
        4,
    ),
)

print(
    "Supervised F1:",
    round(
        metrics[
            "f1"
        ],
        4,
    ),
)

print(
    "Average lead events:",
    round(
        metrics[
            "average_lead_events"
        ],
        4,
    ),
)

print()

print(
    "PHASE 10 FAILURE PREDICTION: PASSED"
)
