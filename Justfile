set dotenv-load := false

default:
    @just --list

# Generate deterministic dataset (default 50k rows; use --rows 1000000 for full scale)
generate rows="50000" seed="42":
    uv run python -m bench.generate --rows {{rows}} --seed {{seed}} --out data/sales.xlsx

# Full benchmark: each engine in its own process, N repeats
bench repeats="5" warmup="1":
    uv run python -m bench.runner --file data/sales.xlsx --repeats {{repeats}} --warmup {{warmup}} --out results/bench.json

# Single engine (isolated subprocess, useful for profiling one motor)
bench-motor motor="polars" repeats="5" warmup="1":
    uv run python -m bench.runner --file data/sales.xlsx --motors {{motor}} --repeats {{repeats}} --warmup {{warmup}} --out results/bench-{{motor}}.json

system-info:
    uv run python -m bench.system

clean:
    rm -f data/*.xlsx results/*.json results/*.md
