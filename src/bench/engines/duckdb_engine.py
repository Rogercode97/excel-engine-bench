"""Motor 4 (S6): DuckDB embebido vía extensión `excel`.

NOTA (S15): sobre .xlsx DuckDB NO hace scan vectorizado tipo parquet; parsea
con expat SAX + minizip-ng en streaming y materializa. Se mide como tal:
I/O = read_xlsx -> TEMP TABLE (parseo + materialización);
CPU = GROUP BY sobre la tabla en memoria.
"""

from __future__ import annotations

from ._child import run_child


def load(path: str):
    import duckdb

    con = duckdb.connect()
    con.execute("INSTALL excel")
    con.execute("LOAD excel")
    con.execute(
        "CREATE TEMP TABLE sales AS "
        "SELECT sucursal, monto FROM read_xlsx(?, header => true, sheet => 'sales')",
        [path],
    )
    return con


def aggregate(con) -> dict:
    rows = con.execute("SELECT sucursal, SUM(monto) FROM sales GROUP BY sucursal").fetchall()
    con.close()
    return {str(k): float(v or 0.0) for k, v in rows}


if __name__ == "__main__":
    run_child("duckdb", load, aggregate)
