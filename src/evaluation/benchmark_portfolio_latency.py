"""
V6.1.6 — Portfolio latency benchmark.

Measures cold and warm execution latency.
No cloud calls or external telemetry.
"""

import argparse
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

from src.api.local_demo_service import LocalDemoService


SCENARIOS = {
    "ORDER": "What is the status of order ORD-10001?",
    "ORDER_RAG": "Can I return the items from order ORD-10003?",
    "RAG": "What is the standard return policy?",
}


def percentile(values, percentage):
    values = sorted(values)

    if not values:
        raise ValueError("Cannot calculate percentile of empty values")

    position = (len(values) - 1) * percentage / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return values[lower]

    weight = position - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )


def summarize(values):
    return {
        "count": len(values),
        "min_ms": round(min(values), 3),
        "mean_ms": round(statistics.mean(values), 3),
        "p50_ms": round(percentile(values, 50), 3),
        "p95_ms": round(percentile(values, 95), 3),
        "max_ms": round(max(values), 3),
    }


def benchmark(iterations):
    if iterations < 2:
        raise ValueError("At least two iterations are required")

    results = {}

    for route, question in SCENARIOS.items():
        # New service per scenario. Its SQLite connection may be
        # initialized lazily on the first query.
        service = LocalDemoService(
            multilingual_retrieval=True,
            multilingual_formatting=True,
            reference_date="2026-10-12",
        )

        samples = []
        operation_samples = {}

        for index in range(iterations):
            result = service.ask(question)

            if result["route"] != route:
                raise AssertionError(
                    f"Expected {route}, got {result['route']}"
                )

            metrics = result["performance"]
            samples.append(metrics["total_ms"])

            if index > 0:
                for name, value in metrics.items():
                    if name == "total_ms":
                        continue

                    operation_samples.setdefault(
                        name, []
                    ).append(value)

        cold = samples[0]
        warm = samples[1:]

        results[route] = {
            "question": question,
            "cold_first_request_ms": cold,
            "warm": summarize(warm),
            "warm_operations": {
                name: summarize(values)
                for name, values in operation_samples.items()
            },
        }

    return {
        "benchmark": "portfolio_latency_v616",
        "timestamp_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "iterations_per_route": iterations,
        "methodology": (
            "First request separated from subsequent requests; "
            "measurements use PerformanceTracker total_ms. "
            "Sequential single-process execution, not load testing."
        ),
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--iterations",
        type=int,
        default=101,
    )
    parser.add_argument(
        "--output",
        default="data/evaluation/portfolio_latency_v616.json",
    )

    args = parser.parse_args()

    report = benchmark(args.iterations)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\nV6.1.6 — Latency Benchmark")
    print("=" * 68)
    print(
        f"{'Route':<12}"
        f"{'First (ms)':>13}"
        f"{'Warm p50':>13}"
        f"{'Warm p95':>13}"
    )
    print("-" * 68)

    for route, data in report["results"].items():
        print(
            f"{route:<12}"
            f"{data['cold_first_request_ms']:>13.3f}"
            f"{data['warm']['p50_ms']:>13.3f}"
            f"{data['warm']['p95_ms']:>13.3f}"
        )

    print("\nReport:", output)


if __name__ == "__main__":
    main()
