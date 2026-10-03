from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import polars as pl

REPO = "phamquiluan/RCAEval"
REVISION = "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e"
ROOT = Path("/home/dell/datasets/rcaeval") / REVISION
OUT = Path("docs/evidence/phase_a/re2tt")
MANDATORY_FILES = {"inject_time.txt", "metrics.parquet", "traces.parquet"}
OPTIONAL_FILES = {"logs.parquet"}


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
    url = (
        f"https://huggingface.co/datasets/{REPO}/resolve/"
        f"{REVISION}/{path}?download=true"
    )
    tmp = target.with_suffix(target.suffix + ".part")
    urllib.request.urlretrieve(url, tmp)
    if tmp.stat().st_size != size:
        raise RuntimeError(
            f"Size mismatch for {path}: {tmp.stat().st_size} != {size}"
        )
    tmp.replace(target)


def main() -> None:
    catalog = pl.read_parquet(ROOT / "cases.parquet")
    tt = catalog.filter(pl.col("dataset") == "RE2-TT").sort("case")
    if tt.height != 90:
        raise RuntimeError(f"Expected 90 RE2-TT cases, found {tt.height}")

    expected: dict[str, dict[str, int]] = {}
    for case_id in tt["case"].to_list():
        entries = api_tree(str(case_id))
        files = {
            Path(item["path"]).name: int(item["size"])
            for item in entries
            if item["type"] == "file"
        }
        names = set(files)
        if not MANDATORY_FILES.issubset(names):
            raise RuntimeError(
                f"Missing mandatory files for {case_id}: "
                f"{sorted(MANDATORY_FILES - names)}"
            )
        unexpected = names - MANDATORY_FILES - OPTIONAL_FILES
        if unexpected:
            raise RuntimeError(
                f"Unexpected files for {case_id}: {sorted(unexpected)}"
            )
        expected[str(case_id)] = files

    for case_id, files in expected.items():
        for name, size in files.items():
            download(f"{case_id}/{name}", size)
        print("downloaded", case_id, flush=True)

    failures: list[str] = []
    allow = set(
        "ts-admin-basic-info-service ts-admin-order-service "
        "ts-admin-route-service ts-admin-travel-service ts-admin-user-service "
        "ts-assurance-service ts-auth-service ts-avatar-service ts-basic-service "
        "ts-cancel-service ts-config-service ts-consign-price-service "
        "ts-consign-service ts-contacts-service ts-delivery-service "
        "ts-execute-service ts-food-delivery-service ts-food-service "
        "ts-gateway-service ts-inside-payment-service ts-news-service "
        "ts-notification-service ts-order-other-service ts-order-service "
        "ts-payment-service ts-preserve-other-service ts-preserve-service "
        "ts-price-service ts-rebook-service ts-route-plan-service "
        "ts-route-service ts-seat-service ts-security-service "
        "ts-station-food-service ts-station-service ts-ticket-office-service "
        "ts-train-food-service ts-train-service ts-travel-plan-service "
        "ts-travel-service ts-travel2-service ts-user-service "
        "ts-verification-code-service ts-voucher-service ts-wait-order-service"
        .split()
    )
    roots = set(str(x) for x in tt["root_cause_service"].unique().to_list())
    if not roots.issubset(allow):
        failures.append(
            "ground-truth validity check outside frozen allowlist: "
            + ",".join(sorted(roots - allow))
        )

    for row in tt.iter_rows(named=True):
        case_id = str(row["case"])
        case_dir = ROOT / case_id
        for name, size in expected[case_id].items():
            path = case_dir / name
            if not path.exists() or path.stat().st_size != size:
                failures.append(f"{case_id}/{name}: size/presence")
        try:
            metrics = pl.read_parquet(case_dir / "metrics.parquet")
            traces = pl.read_parquet(case_dir / "traces.parquet")
            inject = int((case_dir / "inject_time.txt").read_text().strip())
        except Exception as exc:
            failures.append(
                f"{case_id}: parse {type(exc).__name__}: {exc}"
            )
            continue
        if metrics.height != int(row["n_timesteps"]):
            failures.append(f"{case_id}: metrics rows")
        if traces.height != int(row["n_traces"]):
            failures.append(f"{case_id}: trace rows")
        logs_path = case_dir / "logs.parquet"
        expected_logs = int(row["n_logs"])
        if logs_path.exists():
            try:
                logs = pl.read_parquet(logs_path)
            except Exception as exc:
                failures.append(
                    f"{case_id}: logs parse {type(exc).__name__}: {exc}"
                )
            else:
                if logs.height != expected_logs:
                    failures.append(f"{case_id}: logs rows")
        elif expected_logs != 0:
            failures.append(
                f"{case_id}: logs absent but catalog n_logs={expected_logs}"
            )
        if inject != int(row["inject_time"]):
            failures.append(f"{case_id}: inject_time")
        if "time" not in metrics.columns:
            failures.append(f"{case_id}: missing metric time")

    raw_dirs = sorted(path.name for path in ROOT.glob("re2tt_*"))
    if len(raw_dirs) != 90:
        failures.append(f"raw directory count {len(raw_dirs)} != 90")

    result = {
        "dataset": "RE2-TT",
        "revision": REVISION,
        "case_count": tt.height,
        "mandatory_files_per_case": sorted(MANDATORY_FILES),
        "optional_files": sorted(OPTIONAL_FILES),
        "expected_file_count_from_api": sum(
            len(files) for files in expected.values()
        ),
        "raw_case_directory_count": len(raw_dirs),
        "ground_truth_services_validity_check": sorted(roots),
        "faults": sorted(tt["fault"].unique().to_list()),
        "failures": failures,
        "status": "pass" if not failures else "fail",
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "step27_download_integrity.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    if failures:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
