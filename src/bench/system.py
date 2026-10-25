"""Hardware/software fingerprint for reproducible reports."""

from __future__ import annotations

import importlib.metadata
import json
import platform
import sys

import psutil

PACKAGES = ("openpyxl", "pandas", "python-calamine", "polars",
            "fastexcel", "duckdb", "xlsxwriter", "numpy", "psutil")


def fingerprint() -> dict:
    versions = {}
    for pkg in PACKAGES:
        try:
            versions[pkg] = importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError:
            versions[pkg] = "missing"
    vm = psutil.virtual_memory()
    return {
        "os": f"{platform.system()} {platform.release()}",
        "cpu": platform.processor() or platform.machine(),
        "cpu_count_logical": psutil.cpu_count(logical=True),
        "cpu_count_physical": psutil.cpu_count(logical=False),
        "ram_gb": round(vm.total / 1e9, 2),
        "python": sys.version.split()[0],
        "packages": versions,
    }


def main() -> None:
    print(json.dumps(fingerprint(), indent=2))


if __name__ == "__main__":
    main()
