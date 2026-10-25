# excel-engine-bench

[![CI](https://github.com/Rogercode97/excel-engine-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/Rogercode97/excel-engine-bench/actions/workflows/ci.yml)

Reproducible benchmark of four Excel reading strategies over a deterministic synthetic `.xlsx`:

| # | Engine | What it proves |
|---|---|---|
| 1 | OpenPyXL (`read_only=True`) | Pure-Python baseline: flat memory, worst-case latency, zero compiled deps |
| 2 | Pandas + `python-calamine` | Low-cost migration: same pandas code, Rust parser instead of the default |
| 3 | Polars (`engine="calamine"`) | Columnar multithreaded aggregation over Arrow |
| 4 | DuckDB (`excel` extension) | Embedded analytics over the same file |

## Why this design

- **Isolated processes (S11).** Every (engine, repetition) runs in its own subprocess (`bench/runner.py`).
  Python's GC does not return all memory to the kernel immediately, so in-process loops contaminate
  peak-RSS comparisons. OS page cache still applies equally to all engines; report cold vs warm.
- **I/O vs CPU split (S12).** Each child returns `io_s` (open + parse) and `cpu_s` (in-memory
  aggregation) measured with `time.perf_counter`. Lazy engines (Polars, DuckDB) only count
  materialized work — `.collect()` / `fetch_*` happens inside the timed region.
- **Timing ≠ memory runs.** `tracemalloc` perturbs the allocator, so latency runs use
  `--mem-profile 0` and memory is measured in a separate pass (child `tracemalloc` peak +
  parent `psutil` RSS sampling at 20 ms).
- **Deterministic data (S13).** `bench/generate.py` uses `numpy.default_rng(seed)`; same seed →
  same rows, amounts, branches and anomaly budget (0.1% refunds, 0.1% ×50 outliers), verified by
  `logical_sha256` and a cross-engine checksum test.
- **Known colinearity.** Polars `read_excel` has no native reader; `engine="calamine"` (default,
  via `fastexcel`) shares the same Rust parser as Motor 2. Expect similar `io_s`; the real
  comparison is aggregation. DuckDB reads `.xlsx` via the `excel` extension (streaming SAX +
  unzip), not a vectorized parquet-style scan — it is measured as such, without advantage.

## Quickstart

```bash
uv sync
just system-info
just generate              # 50k rows demo
just bench                 # all engines, 1 warmup + 5 reps
just bench-motor polars    # single engine
```

Full scale (near the 1,048,576-row `.xlsx` limit — slow and heavy by design):

```bash
just generate 1000000 && just bench
```

## Results

`just bench` writes `results/bench.json` and prints a Markdown table
(`io_s` / `cpu_s` / `total_s` medians, `peak_rss_mb`, `tracemalloc_mb`, checksum).
All engines must report the same checksum (`checksum_agreement=true`); if they
diverge, the comparison is void — fix the adapters first.

## Reproduce

```bash
uv sync --locked
just system-info > results/system.json
just generate 50000 && just bench
```

Commit your `results/bench.json` + `results/system.json` next to hardware details
(CPU, RAM, SSD/HDD, OS) or the numbers are anecdote, not evidence.

## License

MIT — see [LICENSE](LICENSE).
