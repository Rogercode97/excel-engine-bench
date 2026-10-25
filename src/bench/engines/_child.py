"""Shared child-process harness: split I/O vs CPU, emit one JSON line (S8, S12).

Timing runs MUST use --mem-profile 0: tracemalloc perturbs the allocator and
pollutes latency. Memory runs are separate and report tracemalloc peak only;
the parent samples real RSS via psutil.
"""

from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from collections.abc import Callable
from typing import Any


def run_child(engine: str, load: Callable[[str], Any], aggregate: Callable[[Any], dict]) -> None:
    ap = argparse.ArgumentParser(description=f"isolated {engine} worker")
    ap.add_argument("--file", required=True)
    ap.add_argument("--mem-profile", type=int, default=0)
    args = ap.parse_args()

    if args.mem_profile:
        tracemalloc.start()
    t0 = time.perf_counter()
    data = load(args.file)
    t1 = time.perf_counter()
    totals = aggregate(data)
    t2 = time.perf_counter()

    current, peak = tracemalloc.get_traced_memory() if args.mem_profile else (0, 0)
    if args.mem_profile:
        tracemalloc.stop()
    checksum = round(sum(totals.values()), 2)
    print(json.dumps({
        "engine": engine,
        "io_s": t1 - t0,
        "cpu_s": t2 - t1,
        "total_s": t2 - t0,
        "groups": len(totals),
        "checksum": checksum,
        "tracemalloc_peak_mb": round(peak / 1e6, 2),
    }))
