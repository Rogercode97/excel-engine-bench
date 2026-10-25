"""Cross-engine contract: same file -> same checksum (isolated logic, in-process)."""

from bench import generate
from bench.engines import duckdb_engine, openpyxl_engine, pandas_engine, polars_engine

ENGINES = (openpyxl_engine, pandas_engine, polars_engine, duckdb_engine)


def test_engines_agree(tmp_path):
    xlsx = str(tmp_path / "sales.xlsx")
    generate.generate(2000, 42, xlsx)
    checksums = set()
    for eng in ENGINES:
        totals = eng.aggregate(eng.load(xlsx))
        assert len(totals) == 8
        checksums.add(round(sum(totals.values()), 2))
    assert len(checksums) == 1


def test_generator_is_deterministic(tmp_path):
    a = str(tmp_path / "a.xlsx")
    b = str(tmp_path / "b.xlsx")
    ra = generate.generate(1000, 7, a)
    rb = generate.generate(1000, 7, b)
    assert ra["logical_sha256"] == rb["logical_sha256"]
