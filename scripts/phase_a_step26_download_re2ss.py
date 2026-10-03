from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import polars as pl

REPO = "phamquiluan/RCAEval"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
ROOT = Path("/home/dell/datasets/rcaeval") / REVISION
OUT = Path("docs/evidence/phase_a/re2ss")
EXPECTED_FILES = {"inject_time.txt", "logs.parquet", "metrics.parquet"}


def api_tree(case_id: str) -> list[dict]:
    url = (
        f"https://huggingface.co/api/datasets/{REPO}/tree/{REVISION}/"
        f"{urllib.parse.quote(case_id)}?recursive=true&expand=false"
    )
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def download(path: str, size: int) -> None:
    target = ROOT / path
    if target.exists() and target.stat().st_size == size:
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    url = f"https://huggingface.co/datasets/{REPO}/resolve/{REVISION}/{path}?download=true"
    tmp = target.with_suffix(target.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    if tmp.stat().st_size != size:
        raise RuntimeError(
            f"Size mismatch for {path}: {tmp.stat().st_size} != {size}"
        )
    tmp.replace(target)


def main() -> None:
    catalog = pl.read_parquet(ROOT / "cases.parquet")
    ss = catalog.filter(pl.col("dataset") == "RE2-SS").sort("case")
    if ss.height != 90:
        raise RuntimeError(f"Expected 90 RE2-SS cases, found {ss.height}")
    if list(ROOT.glob("re2tt_*")):
        raise RuntimeError("RE2-TT raw directories unexpectedly present")

    expected: dict[str, dict[str, int]] = {}
    for case_id in ss["case"].to_list():
        entries = api_tree(case_id)
        files = {
            Path(item["path"]).name: int(item["size"])
            for item in entries
            if item["type"] == "file"
        }
        if set(files) != EXPECTED_FILES:
            raise RuntimeError(f"Unexpected files for {case_id}: {sorted(files)}")
        expected[case_id] = files

    for case_id, files in expected.items():
        for name, size in files.items():
            download(f"{case_id}/{name}", size)
        print("downloaded", case_id, flush=True)

    failures: list[str] = []
    for row in ss.iter_rows(named=True):
        case_id = str(row["case"])
        case_dir = ROOT / case_id
        for name, size in expected[case_id].items():
            path = case_dir / name
            if not path.exists() or path.stat().st_size != size:
                failures.append(f"{case_id}/{name}: size/presence")
        try:
            metrics = pl.read_parquet(case_dir / "metrics.parquet")
            logs = pl.read_parquet(case_dir / "logs.parquet")
            inject = int((case_dir / "inject_time.txt").read_text().strip())
        except Exception as exc:
            failures.append(f"{case_id}: parse {type(exc).__name__}: {exc}")
            continue
        if metrics.height != int(row["n_timesteps"]):
            failures.append(f"{case_id}: metrics rows")
        if logs.height != int(row["n_logs"]):
            failures.append(f"{case_id}: logs rows")
        if inject != int(row["inject_time"]):
            failures.append(f"{case_id}: inject_time")
        if "time" not in metrics.columns:
            failures.append(f"{case_id}: missing metric time")

    raw_dirs = sorted(path.name for path in ROOT.glob("re2ss_*"))
    if len(raw_dirs) != 90:
        failures.append(f"raw directory count {len(raw_dirs)} != 90")
    if list(ROOT.glob("re2tt_*")):
        failures.append("RE2-TT raw directories present after download")

    result = {
        "dataset": "RE2-SS",
        "revision": REVISION,
        "case_count": ss.height,
        "expected_files_per_case": sorted(EXPECTED_FILES),
        "expected_file_count": 90 * len(EXPECTED_FILES),
        "raw_case_directory_count": len(raw_dirs),
        "ground_truth_services_validity_check": sorted(
            ss["root_cause_service"].unique().to_list()
        ),
        "faults": sorted(ss["fault"].unique().to_list()),
        "re2tt_raw_directory_count": len(list(ROOT.glob("re2tt_*"))),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step26_download_integrity.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
