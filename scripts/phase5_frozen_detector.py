from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl
import yaml

from sentinelops.anomaly.frozen_detector import fit_baseline_and_freeze, score_frozen


def load_config() -> dict:
    with Path("configs/anomaly.yaml").open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)["anomaly_detection"]


def matrix_from_parquet(path: Path, feature_columns: list[str]):
    frame = pl.read_parquet(path)
    missing = [column for column in feature_columns if column not in frame.columns]
    if missing:
        raise RuntimeError(f"Missing anomaly features: {missing}")
    return frame.select(feature_columns).fill_null(0).to_numpy().astype(float)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)

    fit = sub.add_parser("fit-baseline-freeze")
    fit.add_argument("--baseline-input", type=Path, required=True)
    fit.add_argument("--artifact", type=Path, required=True)

    score = sub.add_parser("score-frozen")
    score.add_argument("--input", type=Path, required=True)
    score.add_argument("--artifact", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)

    args = parser.parse_args()
    config = load_config()
    columns = list(config["features"])
    iforest = config["isolation_forest"]

    if args.mode == "fit-baseline-freeze":
        matrix = matrix_from_parquet(args.baseline_input, columns)
        manifest = fit_baseline_and_freeze(
            matrix,
            args.artifact,
            n_estimators=int(iforest["n_estimators"]),
            contamination=float(iforest["contamination"]),
            random_state=int(iforest["random_state"]),
        )
        print(manifest["sha256"])
        return

    matrix = matrix_from_parquet(args.input, columns)
    scores, flags = score_frozen(args.artifact, matrix)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame({"iforest_anomaly_score": scores, "iforest_anomaly": flags}).write_parquet(
        args.output
    )


if __name__ == "__main__":
    main()
