from __future__ import annotations

import hashlib
import json
from pathlib import Path

import joblib
import numpy as np

from sentinelops.anomaly.detectors import IsolationForestDetector


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fit_baseline_and_freeze(
    matrix: np.ndarray,
    artifact_path: Path,
    *,
    n_estimators: int,
    contamination: float,
    random_state: int,
) -> dict[str, object]:
    detector = IsolationForestDetector(
        n_estimators=n_estimators,
        contamination=contamination,
        random_state=random_state,
    )
    detector.fit(np.asarray(matrix, dtype=float))
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(detector, artifact_path)
    sha = sha256_file(artifact_path)
    manifest = {
        "mode": "fit_on_baseline_then_freeze",
        "artifact": str(artifact_path),
        "sha256": sha,
        "rows": int(matrix.shape[0]),
        "columns": int(matrix.shape[1]),
        "n_estimators": n_estimators,
        "contamination": contamination,
        "random_state": random_state,
    }
    artifact_path.with_suffix(artifact_path.suffix + ".manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def score_frozen(artifact_path: Path, matrix: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    detector: IsolationForestDetector = joblib.load(artifact_path)
    values = np.asarray(matrix, dtype=float)
    return detector.score(values), detector.predict(values)
