"""Runner: un subproceso aislado por (motor, repetición) (S11, S12, S7, S8).

Fase 1 (tiempos): hijos con --mem-profile 0; el padre mide wall con
perf_counter y muestrea el pico RSS del hijo con psutil en un hilo.
Fase 2 (memoria): una corrida extra por motor con tracemalloc dentro del hijo.
Warmup descartado, se reporta mediana de I/O, CPU y total.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import threading
import time

import psutil

MOTORS = ("openpyxl", "pandas", "polars", "duckdb")


def run_isolated(motor: str, path: str, mem_profile: int) -> dict:
    cmd = [sys.executable, "-m", f"bench.engines.{motor}_engine",
           "--file", path, "--mem-profile", str(mem_profile)]
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    peak_rss = 0
    stop = False

    def sample() -> None:
        nonlocal peak_rss
        try:
            p = psutil.Process(proc.pid)
            while not stop and proc.poll() is None:
                try:
                    peak_rss = max(peak_rss, p.memory_info().rss)
                except psutil.NoSuchProcess:
                    break
                time.sleep(0.02)
        except psutil.NoSuchProcess:
            pass

    th = threading.Thread(target=sample, daemon=True)
    th.start()
    out, err = proc.communicate()
    stop = True
    th.join(timeout=2.0)
    wall = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"[{motor}] child failed: {err.strip()[-2000:]}")
    payload = json.loads(out.strip().splitlines()[-1])
    payload["wall_s"] = wall
    payload["peak_rss_mb"] = round(peak_rss / 1e6, 2)
    return payload


def median(xs: list[float]) -> float:
    return round(statistics.median(xs), 4)


def main() -> None:
    ap = argparse.ArgumentParser(description="Isolated multi-engine benchmark")
    ap.add_argument("--file", required=True)
    ap.add_argument("--motors", default=",".join(MOTORS))
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmup", type=int, default=1)
    ap.add_argument("--out", default="results/bench.json")
    args = ap.parse_args()

    motors = [m.strip() for m in args.motors.split(",") if m.strip()]
    report: dict = {"file": args.file, "repeats": args.repeats,
                    "warmup": args.warmup, "engines": {}}
    for motor in motors:
        reps = [run_isolated(motor, args.file, 0)
                for _ in range(args.warmup + args.repeats)][args.warmup:]
        mem = run_isolated(motor, args.file, 1)
        report["engines"][motor] = {
            "io_s": median([r["io_s"] for r in reps]),
            "cpu_s": median([r["cpu_s"] for r in reps]),
            "total_s": median([r["total_s"] for r in reps]),
            "peak_rss_mb": max([r["peak_rss_mb"] for r in reps] + [mem["peak_rss_mb"]]),
            "tracemalloc_peak_mb": mem["tracemalloc_peak_mb"],
            "checksum": reps[0]["checksum"],
            "groups": reps[0]["groups"],
        }

    checksums = {v["checksum"] for v in report["engines"].values()}
    report["checksum_agreement"] = len(checksums) == 1

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2)

    print("| engine | io_s (med) | cpu_s (med) | total_s (med) | peak_rss_mb | tracemalloc_mb | checksum |")
    print("|---|---|---|---|---|---|---|")
    for motor, e in report["engines"].items():
        print(f"| {motor} | {e['io_s']} | {e['cpu_s']} | {e['total_s']} | "
              f"{e['peak_rss_mb']} | {e['tracemalloc_peak_mb']} | {e['checksum']} |")
    print(f"\nchecksum_agreement={report['checksum_agreement']} -> {args.out}")


if __name__ == "__main__":
    main()
