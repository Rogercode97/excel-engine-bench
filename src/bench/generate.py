"""Deterministic synthetic .xlsx generator (S9, S13).

One sheet `sales(id, sucursal, monto, dia)`: lognormal amounts with a fixed
anomaly budget (0.1% negative refunds, 0.1% x50 outliers). Same seed -> same bytes
modulo zip timestamps, same logical rows always.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time

import numpy as np
import xlsxwriter

SUCURSALES = ["CDMX", "MTY", "GDL", "BOG", "LIM", "SCL", "BAI", "MAD"]
HEADER = ("id", "sucursal", "monto", "dia")


def generate(rows: int, seed: int, out: str) -> dict:
    t0 = time.perf_counter()
    rng = np.random.default_rng(seed)
    suc_idx = rng.integers(0, len(SUCURSALES), size=rows)
    montos = np.round(rng.lognormal(mean=5.0, sigma=1.0, size=rows), 2)
    dias = rng.integers(1, 366, size=rows)

    n_anom = max(1, rows // 1000)  # 0.1% + 0.1%
    anom_idx = rng.choice(rows, size=min(rows, 2 * n_anom), replace=False)
    half = len(anom_idx) // 2
    montos[anom_idx[:half]] *= -1.0  # refunds (negative)
    montos[anom_idx[half:]] = np.round(montos[anom_idx[half:]] * 50.0, 2)  # outliers

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    wb = xlsxwriter.Workbook(out, {"constant_memory": True})
    ws = wb.add_worksheet("sales")
    ws.write_row(0, 0, HEADER)
    for i in range(rows):
        ws.write_row(i + 1, 0, (int(i + 1), SUCURSALES[int(suc_idx[i])], float(montos[i]), int(dias[i])))
    wb.close()

    # Logical checksum over generated vectors (independent of zip metadata).
    h = hashlib.sha256()
    h.update(suc_idx.tobytes())
    h.update(montos.tobytes())
    h.update(dias.tobytes())
    elapsed = time.perf_counter() - t0
    return {
        "rows": rows,
        "seed": seed,
        "out": out,
        "elapsed_s": round(elapsed, 3),
        "logical_sha256": h.hexdigest()[:16],
        "anomalies": int(len(anom_idx)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate deterministic sales .xlsx")
    ap.add_argument("--rows", type=int, default=50_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/sales.xlsx")
    args = ap.parse_args()
    print(json.dumps(generate(args.rows, args.seed, args.out), indent=2))


if __name__ == "__main__":
    main()
