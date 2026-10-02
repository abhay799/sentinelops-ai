from pathlib import Path

import matplotlib.pyplot as plt
import polars as pl

CASE = Path(
    "/home/dell/datasets/rcaeval/"
    "afeacb11bcc94dadfd1c8f483ee4377b2b8b614e/"
    "re2ob_checkoutservice_cpu_1"
)
OUT = Path("docs/evidence/phase_a/re2ob/plots")
METRICS = [
    "recommendationservice_mem",
    "adservice_mem",
    "productcatalogservice_latency-90",
]


def main() -> None:
    frame = pl.read_parquet(CASE / "metrics.parquet").sort("time")
    inject = int((CASE / "inject_time.txt").read_text().strip())
    pre = frame.filter(pl.col("time") < inject)
    boundary = int(pre["time"][pre.height // 2])
    OUT.mkdir(parents=True, exist_ok=True)

    for metric in METRICS:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(frame["time"].to_numpy(), frame[metric].to_numpy())
        ax.axvline(boundary, linestyle="--", label="calibration/evaluation")
        ax.axvline(inject, linestyle=":", label="inject_time")
        ax.set_title(f"{metric} — RE2-OB smoke case")
        ax.set_xlabel("Unix time (s)")
        ax.set_ylabel(metric)
        ax.legend()
        fig.tight_layout()
        fig.savefig(OUT / f"{metric}.png", dpi=150)
        plt.close(fig)

    print(f"boundary={boundary}")
    print(f"inject_time={inject}")
    for metric in METRICS:
        cal = pre[: pre.height // 2][metric]
        normal = pre[pre.height // 2 :][metric]
        print(
            metric,
            "cal_range=", (float(cal.min()), float(cal.max())),
            "normal_range=", (float(normal.min()), float(normal.max())),
        )


if __name__ == "__main__":
    main()
