"""Motor 2 (S4): Pandas + python-calamine, migración de bajo costo.

Mismo código pandas preexistente, motor Rust (calamine) en lugar del
openpyxl por defecto. I/O = read_excel; CPU = groupby-sum en numpy.
"""

from __future__ import annotations

from ._child import run_child


def load(path: str):
    import pandas as pd

    return pd.read_excel(path, sheet_name="sales", engine="calamine")


def aggregate(df) -> dict:
    s = df.groupby("sucursal", observed=True)["monto"].sum()
    return {str(k): float(v) for k, v in s.items()}


if __name__ == "__main__":
    run_child("pandas", load, aggregate)
