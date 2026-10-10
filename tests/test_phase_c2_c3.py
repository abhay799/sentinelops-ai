from __future__ import annotations

import ast
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

from sentinelops.anomaly.frozen_detector import fit_baseline_and_freeze, score_frozen
from sentinelops.chaos.schema import ChaosRunRecord


def valid_record() -> dict:
    t0 = datetime(2026, 10, 11, 10, 0, 0, tzinfo=timezone.utc)
    return {
        "run_id": "C03-TEST-1",
        "seed": 42,
        "scenario": "latency",
        "injection_start": t0,
        "detection_time": t0 + timedelta(seconds=1),
        "rca_output_time": t0 + timedelta(seconds=2),
        "guard_decision_time": t0 + timedelta(seconds=3),
        "remediation_time": t0 + timedelta(seconds=4),
        "injection_end": t0 + timedelta(seconds=4),
        "verification_time": t0 + timedelta(seconds=5),
        "recovery_time": t0 + timedelta(seconds=5),
    }


def test_run_record_accepts_ordered_utc_timestamps():
    record = ChaosRunRecord(**valid_record())
    assert record.run_id == "C03-TEST-1"


def test_run_record_rejects_non_utc_timestamp():
    payload = valid_record()
    payload["detection_time"] = datetime(
        2026, 10, 11, 15, 30, tzinfo=timezone(timedelta(hours=5, minutes=30))
    )
    with pytest.raises(ValidationError, match="must be UTC"):
        ChaosRunRecord(**payload)


def test_run_record_rejects_naive_timestamp():
    payload = valid_record()
    payload["rca_output_time"] = datetime(2026, 10, 11, 10, 0, 2)
    with pytest.raises(ValidationError, match="timezone-aware UTC"):
        ChaosRunRecord(**payload)


def test_run_record_rejects_out_of_order_timestamp():
    payload = valid_record()
    payload["guard_decision_time"] = payload["detection_time"] - timedelta(seconds=1)
    with pytest.raises(ValidationError, match="out of order"):
        ChaosRunRecord(**payload)


def test_run_record_rejects_missing_required_timestamp():
    payload = valid_record()
    del payload["injection_end"]
    with pytest.raises(ValidationError):
        ChaosRunRecord(**payload)


def test_run_record_rejects_missing_nullable_stage_field():
    payload = valid_record()
    del payload["detection_time"]
    with pytest.raises(ValidationError):
        ChaosRunRecord(**payload)


def test_pipeline_modules_do_not_read_or_import_injection_ground_truth():
    paths = [
        Path("src/sentinelops/anomaly/detectors.py"),
        Path("src/sentinelops/incidents/correlator.py"),
        Path("src/sentinelops/rca/engine.py"),
        Path("src/sentinelops/rca/challenger.py"),
        Path("src/sentinelops/remediation/sentinelguard.py"),
    ]
    forbidden = {
        "sentinelops.chaos.ground_truth",
        "_ground_truth_injection_only",
        "write_injection_record",
    }
    for path in paths:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        haystack = source + "\n" + "\n".join(imports)
        hits = sorted(item for item in forbidden if item in haystack)
        assert not hits, f"{path} accesses injection ground truth: {hits}"


def test_frozen_detector_fit_then_score_roundtrip(tmp_path: Path):
    rng = np.random.default_rng(42)
    baseline = rng.normal(size=(40, 3))
    score_matrix = rng.normal(size=(10, 3))
    artifact = tmp_path / "detector.joblib"
    manifest = fit_baseline_and_freeze(
        baseline,
        artifact,
        n_estimators=20,
        contamination=0.10,
        random_state=42,
    )
    assert artifact.exists()
    assert len(str(manifest["sha256"])) == 64
    scores_a, flags_a = score_frozen(artifact, score_matrix)
    scores_b, flags_b = score_frozen(artifact, score_matrix)
    np.testing.assert_array_equal(scores_a, scores_b)
    np.testing.assert_array_equal(flags_a, flags_b)
    saved = json.loads(artifact.with_suffix(".joblib.manifest.json").read_text())
    assert saved["mode"] == "fit_on_baseline_then_freeze"
