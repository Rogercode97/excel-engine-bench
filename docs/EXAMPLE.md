# Example run — 50,000 rows, seed 42

Machine: Linux 7.2.9-2-cachyos, x86_64, 12 logical / 6 physical cores, 12.39 GB RAM.
Python 3.12.15. Packages: openpyxl 3.1.5, pandas 3.1.0, python-calamine 0.9.0,
polars 2.0.0, fastexcel 0.21.0, duckdb 2.0.0, xlsxwriter 3.3.0, numpy 2.5.4.

Dataset: `just generate 50000` → 50,000 rows, 100 anomalies,
`logical_sha256=57bb447323b105d7`, generated in 0.657 s.

Command: `just bench` (1 warmup + 5 repetitions, medians reported).

| engine | io_s (med) | cpu_s (med) | total_s (med) | peak_rss_mb | tracemalloc_mb | checksum |
|---|---|---|---|---|---|---|
| openpyxl | 0.8356 | 0.0072 | 0.8429 | 100.47 | 27.25 | 12872903.22 |
| pandas | 0.3092 | 0.0026 | 0.3118 | 184.10 | 51.31 | 12872903.22 |
| polars | 0.1309 | 0.0033 | 0.1342 | 207.44 | 14.45 | 12872903.22 |
| duckdb | 0.1574 | 0.0061 | 0.1635 | 131.17 | 7.45 | 12872903.22 |

`checksum_agreement=true` — all four engines computed the same total.

## Readings

- **I/O dominates everywhere** (20–100× the aggregation cost). The benchmark
  behaves as an I/O benchmark with a group-by attached — which is exactly what
  Excel ingestion is in practice.
- **Shared parser, different materialization.** Pandas and Polars both parse
  through calamine, yet Polars I/O is ~2.4× faster here: the XML parsing is
  shared, frame construction (Arrow-direct vs numpy/DataFrame) is not.
- **DuckDB shows no vectorized-scan advantage over `.xlsx`** (0.157 s vs
  Polars 0.131 s): the `excel` extension streams and materializes before any
  analytics happen. Its value would appear against CSV/Parquet, not here.
- **tracemalloc underreports native engines.** Polars reports 14.45 MB and
  DuckDB 7.45 MB at both 5k and 50k rows — Rust/C++ allocations bypass the
  Python allocator. Compare engines on `peak_rss_mb`, never on
  `tracemalloc_mb` across runtimes.
- **Aggregation is noise at this scale** (3–7 ms). To benchmark the CPU side,
  grow the group-by cardinality (more branches, wider keys), not just rows.
