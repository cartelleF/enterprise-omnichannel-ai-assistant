"""
V6.1.8 — SQLite initialization A/B benchmark.

A: uncached JSON loading
B: cached JSON loading

Uses the production SQLite initialization logic in both variants.
Does not modify production code or datasets.
"""

import argparse
import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import src.data_access.sqlite_data_client as sqlite_module
from src.data_access.sqlite_data_client import SQLiteDataClient


def uncached_reader(path):
    records = json.loads(
        Path(path).read_text(encoding="utf-8")
    )
    return records


def percentile(values, percentage):
    values = sorted(values)
    position = (len(values) - 1) * percentage / 100
    lower = int(position)
    upper = min(lower + 1, len(values) - 1)
    weight = position - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )


def summarize(values):
    return {
        "count": len(values),
        "mean_ms": round(statistics.mean(values), 3),
        "p50_ms": round(percentile(values, 50), 3),
        "p95_ms": round(percentile(values, 95), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


def measure(variant):
    reader = (
        uncached_reader
        if variant == "A"
        else original_reader
    )

    with patch.object(sqlite_module, "_read_dataset", reader):
        client = SQLiteDataClient()

        try:
            start = time.perf_counter()
            _ = client.connection
            return (time.perf_counter() - start) * 1000
        finally:
            client.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=60)
    parser.add_argument(
        "--output",
        default="data/evaluation/sqlite_ab_v618.json",
    )
    args = parser.parse_args()

    if args.pairs < 10:
        raise ValueError("Use at least 10 measurement pairs")

    global original_reader

    original_reader = sqlite_module._read_dataset

    # Separate first-use measurements.
    sqlite_module._load_cached_records.cache_clear()

    first_a = measure("A")
    first_b = measure("B")

    # Warm the cached variant before paired measurements.
    measure("B")

    samples = {"A": [], "B": []}
    paired_differences = []

    for index in range(args.pairs):
        order = (
            ("A", "B")
            if index % 2 == 0
            else ("B", "A")
        )

        pair = {}

        for variant in order:
            elapsed = measure(variant)
            samples[variant].append(elapsed)
            pair[variant] = elapsed

        paired_differences.append(
            pair["A"] - pair["B"]
        )

    a = summarize(samples["A"])
    b = summarize(samples["B"])

    relative_change = (
        (a["p50_ms"] - b["p50_ms"])
        / a["p50_ms"] * 100
        if a["p50_ms"]
        else 0
    )

    report = {
        "benchmark": "sqlite_ab_v618",
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "pairs": args.pairs,
        "first_use": {
            "A_ms": round(first_a, 3),
            "B_ms": round(first_b, 3),
        },
        "A_uncached": a,
        "B_cached": b,
        "median_paired_saving_ms": round(
            statistics.median(paired_differences), 3
        ),
        "median_relative_change_percent": round(
            relative_change, 2
        ),
        "methodology": (
            "Alternating sequential A/B pairs, "
            "same SQLite initialization implementation, "
            "different JSON readers. "
            "First-use samples are descriptive only."
        ),
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nV6.1.8 — SQLite A/B Benchmark")
    print("=" * 62)
    print(
        f"{'Variant':<20}"
        f"{'p50 (ms)':>12}"
        f"{'p95 (ms)':>12}"
    )
    print("-" * 62)
    print(
        f"{'A — No cache':<20}"
        f"{a['p50_ms']:>12.3f}"
        f"{a['p95_ms']:>12.3f}"
    )
    print(
        f"{'B — JSON cache':<20}"
        f"{b['p50_ms']:>12.3f}"
        f"{b['p95_ms']:>12.3f}"
    )

    print(
        "\nMedian paired saving:",
        report["median_paired_saving_ms"],
        "ms",
    )
    print(
        "Relative p50 improvement:",
        report["median_relative_change_percent"],
        "%",
    )
    print(
        "First use A/B:",
        round(first_a, 3),
        "/",
        round(first_b, 3),
        "ms",
    )
    print("Report:", output)


if __name__ == "__main__":
    main()
