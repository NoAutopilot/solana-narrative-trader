#!/usr/bin/env python3
"""
benchmark_comparator_v2.py — Compare new feature results against v1 benchmarks and no-go registry.
Cold-path infra only. Does NOT modify any live collection or DB.

Usage:
  python3 scripts/benchmark_comparator_v2.py \
      --results-json reports/sweeps/v2_5m/holdout_sweep_results.json \
      --output-dir reports/sweeps/v2_5m/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ── V1 Benchmark Ceiling ─────────────────────────────────────────────────────
V1_BENCHMARK = {
    "best_gross_mean_5m": 0.00304,       # r_m5 micro, +5m
    "best_gross_median_5m": 0.0,          # all features
    "best_net_mean_5m": 0.00051,          # median_pool_r_m5, +5m
    "best_net_median_5m": 0.0,            # all features
    "best_win_rate_5m": 0.50,             # all features
    "best_gross_mean_15m": 0.01387,       # r_m5 micro, +15m
    "best_gross_mean_30m": 0.04815,       # r_m5 micro, +30m
    "round_trip_cost_median": 0.0051,     # ~0.51%
}

# ── No-Go Registry ───────────────────────────────────────────────────────────
NO_GO_FAMILIES = {
    "momentum_direction": {
        "features": [
            "r_m5_snap", "r_m5_micro", "r_h1_snap",
            "median_pool_r_m5", "pool_dispersion_r_m5",
            "breadth_positive_pct", "breadth_negative_pct",
        ],
        "entries": ["NG-001", "NG-008", "NG-009", "NG-010"],
        "reason": "Momentum/direction family exhausted. Median = 0 at all horizons.",
    },
    "aggregated_order_flow": {
        "features": [
            "buy_sell_ratio_m5", "buy_sell_ratio_h1",
            "buy_count_ratio_m5", "buy_count_ratio_h1",
            "vol_accel_m5_vs_h1", "txn_accel_m5_vs_h1",
            "buys_m5", "sells_m5", "buys_h1", "sells_h1",
            "buys_m5_snap", "sells_m5_snap",
            "buy_count_ratio_m5_snap",
        ],
        "entries": ["NG-002", "NG-003", "NG-004"],
        "reason": "Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.",
    },
    "execution_quality": {
        "features": [
            "jup_vs_cpamm_diff_pct", "round_trip_pct",
            "impact_buy_pct", "impact_sell_pct", "impact_asymmetry_pct",
        ],
        "entries": ["NG-005"],
        "reason": "Execution quality family exhausted. Near-zero tercile differentiation.",
    },
    "static_fundamentals": {
        "features": [
            "age_hours", "liquidity_usd", "vol_h1", "vol_h24", "price_usd",
        ],
        "entries": ["NG-006", "NG-007"],
        "reason": "Static fundamentals family exhausted. Median = 0 at all horizons.",
    },
}

# ── Binding Constraints ──────────────────────────────────────────────────────
BINDING_CONSTRAINTS = {
    "C1": "Round-trip cost (~0.51%) consumes gross alpha",
    "C2": "Median is zero (outlier-driven mean)",
    "C3": "Non-random micro coverage gap (Orca/Meteora excluded)",
}


def check_novelty(feature_name):
    """Check if feature belongs to an exhausted no-go family."""
    for family_name, family in NO_GO_FAMILIES.items():
        if feature_name in family["features"]:
            return {
                "novel": False,
                "family": family_name,
                "entries": family["entries"],
                "reason": family["reason"],
            }
    return {"novel": True, "family": None, "entries": [], "reason": None}


def check_improvement(metrics, horizon="5m"):
    """Check if new result exceeds v1 benchmark ceiling."""
    h = horizon.replace("m", "m").replace("h", "h")
    bench_mean_key = f"best_net_mean_{h}" if f"best_net_mean_{h}" in V1_BENCHMARK else "best_net_mean_5m"
    bench_median_key = f"best_net_median_{h}" if f"best_net_median_{h}" in V1_BENCHMARK else "best_net_median_5m"
    bench_wr_key = f"best_win_rate_{h}" if f"best_win_rate_{h}" in V1_BENCHMARK else "best_win_rate_5m"

    bench_mean = V1_BENCHMARK[bench_mean_key]
    bench_median = V1_BENCHMARK[bench_median_key]
    bench_wr = V1_BENCHMARK[bench_wr_key]

    result = {
        "exceeds_mean": metrics["G1_mean_net_proxy"] > bench_mean,
        "exceeds_median": metrics["G2_median_net_proxy"] > bench_median,
        "exceeds_win_rate": metrics["G5_win_rate"] > bench_wr,
        "v1_bench_mean": bench_mean,
        "v1_bench_median": bench_median,
        "v1_bench_win_rate": bench_wr,
    }
    result["exceeds_all"] = all([result["exceeds_mean"], result["exceeds_median"], result["exceeds_win_rate"]])
    return result


def check_structural_distinction(metrics):
    """Check if new result addresses at least one binding constraint."""
    addresses = {}
    # C1: gross mean >> 0.51%
    gross_mean = metrics["G1_mean_net_proxy"] + V1_BENCHMARK["round_trip_cost_median"]
    addresses["C1"] = gross_mean > V1_BENCHMARK["round_trip_cost_median"] * 2  # gross > 2x cost

    # C2: positive median
    addresses["C2"] = metrics["G2_median_net_proxy"] > 0

    # C3: coverage >= 70%
    addresses["C3"] = metrics["G8_coverage"] >= 0.70

    return {
        "addresses_any": any(addresses.values()),
        "constraints": addresses,
    }


def run_comparison(args):
    """Run the benchmark comparison."""
    results_path = Path(args.results_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(results_path) as f:
        results = json.load(f)

    horizon = results["horizon"]
    comparison = {"horizon": horizon, "features": {}}

    # Compare each feature that was evaluated
    all_features = {}
    for source_key in ["discovery_results", "holdout_results"]:
        for feat, data in results.get(source_key, {}).items():
            if "metrics" in data:
                all_features[feat] = data["metrics"]

    for feat, metrics in all_features.items():
        novelty = check_novelty(feat)
        improvement = check_improvement(metrics, horizon)
        distinction = check_structural_distinction(metrics)

        comparison["features"][feat] = {
            "novelty": novelty,
            "improvement": improvement,
            "structural_distinction": distinction,
            "overall_verdict": (
                "NOVEL_AND_IMPROVED" if novelty["novel"] and improvement["exceeds_all"] and distinction["addresses_any"]
                else "NOVEL_BUT_NOT_IMPROVED" if novelty["novel"] and not improvement["exceeds_all"]
                else "NOT_NOVEL" if not novelty["novel"]
                else "IMPROVED_BUT_NOT_NOVEL"
            ),
        }

    # ── Write markdown report ─────────────────────────────────────────────
    report_path = output_dir / "benchmark_comparison.md"
    with open(report_path, "w") as f:
        f.write(f"# Benchmark Comparison — {horizon}\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n")
        f.write("---\n\n")

        f.write("## V1 Benchmark Ceiling\n\n")
        f.write("| Metric | V1 Best | Feature | Horizon |\n")
        f.write("|--------|--------:|---------|--------:|\n")
        f.write(f"| Best net mean | {V1_BENCHMARK['best_net_mean_5m']*100:.3f}% | median_pool_r_m5 | +5m |\n")
        f.write(f"| Best net median | {V1_BENCHMARK['best_net_median_5m']*100:.3f}% | all | +5m |\n")
        f.write(f"| Best win rate | {V1_BENCHMARK['best_win_rate_5m']*100:.1f}% | all | +5m |\n")
        f.write(f"| Round-trip cost | {V1_BENCHMARK['round_trip_cost_median']*100:.2f}% | median | — |\n\n")

        f.write("## Feature-Level Comparison\n\n")
        f.write("| Feature | Novel? | Exceeds V1? | Addresses Constraint? | Verdict |\n")
        f.write("|---------|--------|-------------|----------------------|--------|\n")
        for feat, comp in comparison["features"].items():
            novel = "YES" if comp["novelty"]["novel"] else f"NO ({comp['novelty']['family']})"
            exceeds = "YES" if comp["improvement"]["exceeds_all"] else "NO"
            constraints = []
            for c, v in comp["structural_distinction"]["constraints"].items():
                if v:
                    constraints.append(c)
            addr = ", ".join(constraints) if constraints else "NONE"
            f.write(f"| {feat} | {novel} | {exceeds} | {addr} | {comp['overall_verdict']} |\n")

        if any(not c["novelty"]["novel"] for c in comparison["features"].values()):
            f.write("\n### No-Go Registry Flags\n\n")
            for feat, comp in comparison["features"].items():
                if not comp["novelty"]["novel"]:
                    f.write(f"**{feat}:** {comp['novelty']['reason']}\n\n")

    # ── Write JSON ────────────────────────────────────────────────────────
    with open(output_dir / "benchmark_comparison.json", "w") as f:
        json.dump(comparison, f, indent=2, default=str)

    print(f"Benchmark comparison written to {report_path}")
    print(f"JSON written to {output_dir / 'benchmark_comparison.json'}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Comparator v2")
    parser.add_argument("--results-json", required=True, help="Path to holdout_sweep_results.json")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    args = parser.parse_args()
    run_comparison(args)
