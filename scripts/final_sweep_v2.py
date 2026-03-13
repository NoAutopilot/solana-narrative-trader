#!/usr/bin/env python3
"""
final_sweep_v2.py — Orchestrate holdout sweeps across all 5 horizons and generate
a unified report. Cold-path infra only. Does NOT modify any live collection or DB.

Usage:
  python3 scripts/final_sweep_v2.py --db-path /root/solana_trader/data/solana_trader.db
  python3 scripts/final_sweep_v2.py --dry-run
  python3 scripts/final_sweep_v2.py --horizons 5m,15m --features r_m5_micro,buy_sell_ratio_m5

Prerequisites:
  - feature_tape_v2 collection complete (96+ fires)
  - 10-fire health checkpoint passed
  - Forward return labels available for all requested horizons
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HORIZONS = ["5m", "15m", "30m", "1h", "4h"]
SCRIPT_DIR = Path(__file__).parent
HOLDOUT_SCRIPT = SCRIPT_DIR / "holdout_sweep_v2.py"
COMPARATOR_SCRIPT = SCRIPT_DIR / "benchmark_comparator_v2.py"


def run_horizon(horizon, db_path, features, output_base, dry_run=False):
    """Run holdout sweep + benchmark comparison for a single horizon."""
    output_dir = output_base / f"v2_{horizon}"
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Holdout sweep ─────────────────────────────────────────────────────
    cmd = [
        sys.executable, str(HOLDOUT_SCRIPT),
        "--db-path", db_path,
        "--horizon", horizon,
        "--output-dir", str(output_dir),
    ]
    if features:
        cmd.extend(["--features", features])
    if dry_run:
        cmd.append("--dry-run")

    print(f"\n{'='*60}")
    print(f"  HORIZON: +{horizon}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=False)
    if result.returncode != 0:
        print(f"  WARNING: Holdout sweep for +{horizon} exited with code {result.returncode}")
        return {"horizon": horizon, "status": "FAILED", "returncode": result.returncode}

    if dry_run:
        return {"horizon": horizon, "status": "DRY_RUN"}

    # ── Benchmark comparison ──────────────────────────────────────────────
    results_json = output_dir / "holdout_sweep_results.json"
    if results_json.exists():
        cmd2 = [
            sys.executable, str(COMPARATOR_SCRIPT),
            "--results-json", str(results_json),
            "--output-dir", str(output_dir),
        ]
        subprocess.run(cmd2, capture_output=False)

    return {"horizon": horizon, "status": "COMPLETE"}


def generate_unified_report(output_base, horizons):
    """Generate a unified report across all horizons."""
    report_path = output_base / "unified_sweep_report.md"
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    with open(report_path, "w") as f:
        f.write("# Unified Feature Sweep Report — All Horizons\n\n")
        f.write(f"**Date:** {now}\n")
        f.write(f"**View:** PRIMARY (eligible-only)\n")
        f.write(f"**Horizons:** {', '.join(['+' + h for h in horizons])}\n\n")
        f.write("---\n\n")

        # Collect results from each horizon
        all_promoted = {}
        for h in horizons:
            results_path = output_base / f"v2_{h}" / "holdout_sweep_results.json"
            if not results_path.exists():
                f.write(f"## +{h} — NO RESULTS\n\n")
                continue

            with open(results_path) as rf:
                results = json.load(rf)

            n_fires = results.get("n_fires", "?")
            n_disc = results.get("n_rows_discovery", "?")
            n_hold = results.get("n_rows_holdout", "?")
            promoted = results.get("promoted_features", [])

            f.write(f"## +{h}\n\n")
            f.write(f"Fires: {n_fires} | Discovery: {n_disc} rows | Holdout: {n_hold} rows\n\n")

            if promoted:
                f.write(f"**Promoted features:** {', '.join(promoted)}\n\n")
                all_promoted[h] = promoted

                # Holdout results table
                f.write("| Feature | Mean Net | Median Net | CI Lower | Win Rate | Top-1 | Verdict |\n")
                f.write("|---------|--------:|----------:|--------:|--------:|------:|--------|\n")
                for feat in promoted:
                    hr = results.get("holdout_results", {}).get(feat, {})
                    if "metrics" in hr:
                        m = hr["metrics"]
                        f.write(f"| {feat} | {m['G1_mean_net_proxy']*100:.3f}% | {m['G2_median_net_proxy']*100:.3f}% | {m['G3_ci_lower_mean']*100:.3f}% | {m['G5_win_rate']*100:.1f}% | {m['G6_top1_share']:.3f} | {hr['status']} |\n")
                    else:
                        f.write(f"| {feat} | — | — | — | — | — | {hr.get('status', 'SKIP')} |\n")
            else:
                f.write("**No features promoted from discovery.**\n\n")

            f.write("\n")

        # Summary
        f.write("---\n\n## Summary\n\n")
        if all_promoted:
            f.write("| Horizon | Promoted Features |\n")
            f.write("|---------|------------------|\n")
            for h, feats in all_promoted.items():
                f.write(f"| +{h} | {', '.join(feats)} |\n")
            f.write("\n")
        else:
            f.write("**No features were promoted at any horizon.**\n\n")
            f.write("This is the expected outcome if the signal is fundamentally weak. ")
            f.write("Proceed to the next option in the decision tree or stop.\n\n")

        # Benchmark comparison summaries
        f.write("---\n\n## Benchmark Comparison Summaries\n\n")
        for h in horizons:
            comp_path = output_base / f"v2_{h}" / "benchmark_comparison.json"
            if not comp_path.exists():
                continue
            with open(comp_path) as cf:
                comp = json.load(cf)
            novel_count = sum(1 for feat in comp.get("features", {}).values() if feat["novelty"]["novel"])
            total = len(comp.get("features", {}))
            f.write(f"**+{h}:** {novel_count}/{total} features are novel (not in no-go registry)\n\n")

    print(f"\nUnified report written to {report_path}")


def main():
    parser = argparse.ArgumentParser(description="Final Sweep v2 — All Horizons")
    parser.add_argument("--db-path", default="/root/solana_trader/data/solana_trader.db",
                        help="Path to SQLite database")
    parser.add_argument("--horizons", default=None,
                        help="Comma-separated horizons (default: all 5)")
    parser.add_argument("--features", default=None,
                        help="Comma-separated feature list (default: all)")
    parser.add_argument("--output-base", default="reports/sweeps",
                        help="Base output directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate only, do not run sweeps")
    args = parser.parse_args()

    horizons = args.horizons.split(",") if args.horizons else HORIZONS
    output_base = Path(args.output_base)
    output_base.mkdir(parents=True, exist_ok=True)

    print(f"Final Sweep v2 — {len(horizons)} horizons")
    print(f"DB: {args.db_path}")
    print(f"Output: {output_base}")
    if args.dry_run:
        print("MODE: DRY RUN")

    statuses = []
    for h in horizons:
        status = run_horizon(h, args.db_path, args.features, output_base, args.dry_run)
        statuses.append(status)

    if not args.dry_run:
        generate_unified_report(output_base, horizons)

    # Summary
    print(f"\n{'='*60}")
    print("  FINAL SWEEP COMPLETE")
    print(f"{'='*60}")
    for s in statuses:
        print(f"  +{s['horizon']}: {s['status']}")


if __name__ == "__main__":
    main()
