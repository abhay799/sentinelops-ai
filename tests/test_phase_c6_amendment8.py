import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT_PATH = Path("scripts/phase_c06_train_loop.py")

spec = importlib.util.spec_from_file_location(
    "phase_c06_train_loop_a8",
    SCRIPT_PATH,
)
assert spec is not None
assert spec.loader is not None

loop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(loop)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def test_resolves_authoritative_reexecution_summary(tmp_path: Path):
    run_id = "C-SPARE-TRAIN-BDR-02"
    replacement_for = "C-TRAIN-BDR-12"

    # Historical/base record remains infrastructure-invalid.
    write_json(
        tmp_path / run_id / "run_summary.json",
        {
            "run_id": run_id,
            "replacement_for": replacement_for,
            "status": "infrastructure_invalid_interrupted",
            "registered_result_eligible": False,
            "counted_in_analysis_denominator": False,
        },
    )

    # First retry is preserved partial evidence only.
    write_json(
        tmp_path / f"{run_id}__a5_rerun" / "execution_state.json",
        {
            "run_id": run_id,
            "replacement_for": replacement_for,
            "injection_start": None,
        },
    )

    # Amendment 7 authoritative result.
    authoritative = {
        "artifact_run_id": f"{run_id}__a5_rerun_02",
        "run_id": run_id,
        "replacement_for": replacement_for,
        "seed": 300872472,
        "status": loop.RUN_FAILED_AFTER_INJECTION,
        "registered_result_eligible": True,
        "counted_in_analysis_denominator": True,
    }
    write_json(
        tmp_path
        / f"{run_id}__a5_rerun_02"
        / "run_summary.json",
        authoritative,
    )

    resolved = loop.authoritative_reexecution_summary(
        tmp_path,
        run_id,
        replacement_for=replacement_for,
    )

    assert resolved == authoritative


def test_ignores_reexecution_for_other_primary(tmp_path: Path):
    run_id = "C-SPARE-TRAIN-BDR-02"

    write_json(
        tmp_path
        / f"{run_id}__a5_rerun_02"
        / "run_summary.json",
        {
            "artifact_run_id": f"{run_id}__a5_rerun_02",
            "run_id": run_id,
            "replacement_for": "C-TRAIN-BDR-12",
            "status": loop.RUN_FAILED_AFTER_INJECTION,
            "registered_result_eligible": True,
            "counted_in_analysis_denominator": True,
        },
    )

    assert (
        loop.authoritative_reexecution_summary(
            tmp_path,
            run_id,
            replacement_for="C-TRAIN-BDR-01",
        )
        is None
    )


def test_ignores_non_registered_reexecution_summary(tmp_path: Path):
    run_id = "C-SPARE-TRAIN-BDR-02"

    write_json(
        tmp_path / f"{run_id}__attempt" / "run_summary.json",
        {
            "run_id": run_id,
            "replacement_for": "C-TRAIN-BDR-12",
            "status": "infrastructure_invalid_interrupted",
            "registered_result_eligible": False,
            "counted_in_analysis_denominator": False,
        },
    )

    assert (
        loop.authoritative_reexecution_summary(
            tmp_path,
            run_id,
            replacement_for="C-TRAIN-BDR-12",
        )
        is None
    )


def test_refuses_multiple_authoritative_reexecution_results(
    tmp_path: Path,
):
    run_id = "C-SPARE-TRAIN-BDR-02"

    for suffix in ("one", "two"):
        write_json(
            tmp_path / f"{run_id}__{suffix}" / "run_summary.json",
            {
                "artifact_run_id": f"{run_id}__{suffix}",
                "run_id": run_id,
                "replacement_for": "C-TRAIN-BDR-12",
                "status": loop.RUN_FAILED_AFTER_INJECTION,
                "registered_result_eligible": True,
                "counted_in_analysis_denominator": True,
            },
        )

    with pytest.raises(RuntimeError, match="multiple authoritative"):
        loop.authoritative_reexecution_summary(
            tmp_path,
            run_id,
            replacement_for="C-TRAIN-BDR-12",
        )
