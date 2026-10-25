"""Render docs/bench chart from a runner JSON (reproducible figure)."""

from __future__ import annotations

import argparse
import json

ORDER = ("openpyxl", "pandas", "polars", "duckdb")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    report = json.load(open(args.inp))
    engines = report["engines"]
    names = [e for e in ORDER if e in engines]
    io = [engines[e]["io_s"] for e in names]
    cpu = [engines[e]["cpu_s"] for e in names]
    rss = [engines[e]["peak_rss_mb"] for e in names]

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    x = range(len(names))
    ax1.bar(x, io, label="I/O (parse)")
    ax1.bar(x, cpu, bottom=io, label="CPU (aggregate)")
    ax1.set_yscale("log")
    ax1.set_xticks(list(x), names, rotation=15)
    ax1.set_ylabel("seconds (log scale, median)")
    ax1.set_title(f"Latency split — {report['file']} ({report['repeats']} reps)")
    ax1.legend()
    for i, (a, b) in enumerate(zip(io, cpu)):
        ax1.text(i, a + b, f"{a + b:.2f}s", ha="center", va="bottom", fontsize=8)

    ax2.bar(x, rss, color="tab:orange")
    ax2.set_xticks(list(x), names, rotation=15)
    ax2.set_ylabel("peak RSS (MB)")
    ax2.set_title("Peak resident memory per engine")
    for i, v in enumerate(rss):
        ax2.text(i, v, f"{v:.0f}", ha="center", va="bottom", fontsize=8)

    fig.tight_layout()
    fig.savefig(args.out, dpi=120)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
