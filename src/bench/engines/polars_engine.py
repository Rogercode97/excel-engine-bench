"""Motor 3 (S5): Polars columnar multihilo sobre Arrow.

NOTA (S15): `read_excel(engine="calamine")` usa fastexcel/calamine, el MISMO
parser Rust que el Motor 2. El I/O entre ambos debe salir parecido; lo que
este motor demuestra es la agregación columnar paralela, no un parseo distinto.
"""

from __future__ import annotations

from ._child import run_child


def load(path: str):
    import polars as pl

    return pl.read_excel(path, sheet_name="sales", engine="calamine")


def aggregate(frame) -> dict:
    out = frame.group_by("sucursal").agg(__import__("polars").col("monto").sum())
    return dict(zip(out["sucursal"].to_list(), (float(v) for v in out["monto"].to_list())))


if __name__ == "__main__":
    run_child("polars", load, aggregate)
