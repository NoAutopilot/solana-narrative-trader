#!/usr/bin/env python3
"""
generate_final_recommendation.py — Generate the final recommendation memo
after all sweeps and benchmark comparisons are complete.

Cold-path only. Does NOT modify any live collection or DB.

The memo chooses exactly one of:
  1) ONE NEW LIVE OBSERVER CANDIDATE APPROVED
  2) NO NEW LIVE OBSERVER — CONTINUE FEATURE ACQUISITION
  3) NO NEW LIVE OBSERVER — STOP PROGRAM

Usage:
  python3 scripts/generate_final_recommendation.py \
      --sweep-base reports/synthesis/sweeps_full_sample \
      --horizons 5m,15m,30m,1h,4h \
      --output reports/synthesis/feature_family_sweep_v2_final_recommendation.md
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_results(sweep_base, horizons):
    """Load all sweep results and benchmark comparisons."""
    all_results = {}
    all_benchmarks = {}

    for h in horizons:
        results_path = Path(sweep_base) / f"v2_{h}" / "holdout_sweep_results.json"
        if results_path.exists():
            with open(results_path) as f:
                all_results[h] = json.load(f)

        bench_path = Path(sweep_base) / f"v2_{h}" / "benchmark_comparison.json"
        if bench_path.exists():
            with open(bench_path) as f:
                all_benchmarks[h] = json.load(f)

    return all_results, all_benchmarks


def determine_verdict(all_results, all_benchmarks):
    """
    Determine the final verdict based on holdout results and benchmark comparisons.

    Decision logic:
    1. If any feature passes ALL 8 holdout gates at ANY horizon AND
       is NOVEL (not in no-go registry) AND
       addresses at least one binding constraint:
       → VERDICT 1: ONE NEW LIVE OBSERVER CANDIDATE APPROVED

    2. If no feature passes holdout but there are novel features that
       passed discovery (suggesting more data or a different approach might help):
       → VERDICT 2: NO NEW LIVE OBSERVER — CONTINUE FEATURE ACQUISITION

    3. If no feature passes discovery, or all passing features are in the
       no-go registry:
       → VERDICT 3: NO NEW LIVE OBSERVER — STOP PROGRAM
    """
    approved_candidates = []
    novel_discovery_passes = []
    any_discovery_pass = False

    for h, results in all_results.items():
        promoted = results.get("promoted_features", [])
        benchmarks = all_benchmarks.get(h, {}).get("features", {})

        # Check holdout results
        for feat in promoted:
            holdout = results.get("holdout_results", {}).get(feat, {})
            if holdout.get("status") == "PASS":
                # Check benchmark
                bench = benchmarks.get(feat, {})
                is_novel = bench.get("novelty", {}).get("novel", False)
                addresses_constraint = bench.get("structural_distinction", {}).get("addresses_any", False)

                if is_novel and addresses_constraint:
                    approved_candidates.append({
                        "feature": feat,
                        "horizon": h,
                        "holdout_metrics": holdout.get("metrics", {}),
                        "benchmark": bench,
                    })
                elif is_novel:
                    novel_discovery_passes.append({
                        "feature": feat,
                        "horizon": h,
                        "reason": "Passes holdout but does not address binding constraint",
                    })

        # Check discovery passes (even if not promoted to holdout)
        for feat, data in results.get("discovery_results", {}).items():
            if data.get("status") == "PASS":
                any_discovery_pass = True
                bench = benchmarks.get(feat, {})
                if bench.get("novelty", {}).get("novel", False):
                    novel_discovery_passes.append({
                        "feature": feat,
                        "horizon": h,
                        "reason": "Passes discovery, novel",
                    })

    if approved_candidates:
        # Sort by mean net proxy descending
        approved_candidates.sort(
            key=lambda x: x["holdout_metrics"].get("G1_mean_net_proxy", 0),
            reverse=True,
        )
        return 1, approved_candidates, novel_discovery_passes
    elif novel_discovery_passes:
        return 2, approved_candidates, novel_discovery_passes
    else:
        return 3, approved_candidates, novel_discovery_passes


def write_memo(output_path, verdict_num, approved, novel_passes, all_results, all_benchmarks, horizons):
    """Write the final recommendation memo."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    verdict_labels = {
        1: "ONE NEW LIVE OBSERVER CANDIDATE APPROVED",
        2: "NO NEW LIVE OBSERVER — CONTINUE FEATURE ACQUISITION",
        3: "NO NEW LIVE OBSERVER — STOP PROGRAM",
    }

    with open(output_path, "w") as f:
        f.write("# Feature Tape v2 — Final Recommendation Memo\n\n")
        f.write(f"**Date:** {now}\n")
        f.write(f"**View:** PRIMARY (eligible-only)\n")
        f.write(f"**Horizons evaluated:** {', '.join(['+' + h for h in horizons])}\n")
        f.write(f"**+1d:** EXCLUDED from primary decision (deferred)\n\n")
        f.write("---\n\n")

        # Verdict
        f.write(f"## VERDICT: {verdict_labels[verdict_num]}\n\n")

        if verdict_num == 1:
            f.write("At least one feature passed all 8 holdout gates, is novel (not in the no-go registry), ")
            f.write("and addresses at least one binding constraint from v1.\n\n")

            f.write("### Approved Candidate(s)\n\n")
            f.write("| Feature | Horizon | Mean Net | Median Net | Win Rate | CI Lower (Mean) |\n")
            f.write("|---------|---------|--------:|----------:|--------:|----------------:|\n")
            for c in approved:
                m = c["holdout_metrics"]
                f.write(f"| {c['feature']} | +{c['horizon']} | "
                        f"{m.get('G1_mean_net_proxy', 0)*100:.3f}% | "
                        f"{m.get('G2_median_net_proxy', 0)*100:.3f}% | "
                        f"{m.get('G5_win_rate', 0)*100:.1f}% | "
                        f"{m.get('G3_ci_lower_mean', 0)*100:.3f}% |\n")

            f.write("\n### Recommended Next Step\n\n")
            best = approved[0]
            f.write(f"Design a live observer for **{best['feature']}** at **+{best['horizon']}** horizon.\n")
            f.write("The observer must implement all 6 kill gates (K1-K6) from the holdout pipeline spec.\n")
            f.write("Do NOT deploy without a paper-trading phase of at least 48 hours.\n\n")

        elif verdict_num == 2:
            f.write("No feature passed all 8 holdout gates with novelty and structural distinction. ")
            f.write("However, some novel features showed promise in discovery, suggesting that ")
            f.write("additional data collection or a different feature engineering approach may help.\n\n")

            if novel_passes:
                f.write("### Promising Discovery Results\n\n")
                f.write("| Feature | Horizon | Reason |\n")
                f.write("|---------|---------|--------|\n")
                seen = set()
                for p in novel_passes:
                    key = f"{p['feature']}_{p['horizon']}"
                    if key not in seen:
                        f.write(f"| {p['feature']} | +{p['horizon']} | {p['reason']} |\n")
                        seen.add(key)

            f.write("\n### Recommended Next Step\n\n")
            f.write("Continue feature acquisition with a focus on:\n\n")
            f.write("1. Trade-by-trade order flow features (not yet available in aggregated form)\n")
            f.write("2. Cross-venue flow imbalance features\n")
            f.write("3. Longer collection window (192+ fires) for better statistical power\n\n")
            f.write("Do NOT re-test features from the no-go registry.\n")
            f.write("Do NOT launch any live observer.\n\n")

        elif verdict_num == 3:
            f.write("No feature passed discovery gates, or all passing features are in the no-go registry. ")
            f.write("The signal is fundamentally weak across all tested features and horizons.\n\n")

            f.write("### Evidence Summary\n\n")
            total_features = 0
            total_pass = 0
            total_novel = 0
            for h in horizons:
                r = all_results.get(h, {})
                for feat, data in r.get("discovery_results", {}).items():
                    total_features += 1
                    if data.get("status") == "PASS":
                        total_pass += 1
                        b = all_benchmarks.get(h, {}).get("features", {}).get(feat, {})
                        if b.get("novelty", {}).get("novel", False):
                            total_novel += 1

            f.write(f"- Features tested: {total_features}\n")
            f.write(f"- Discovery passes: {total_pass}\n")
            f.write(f"- Novel discovery passes: {total_novel}\n\n")

            f.write("### Recommended Next Step\n\n")
            f.write("**Stop the feature_tape_v2 program.**\n\n")
            f.write("The current feature space has been exhaustively tested. Options:\n\n")
            f.write("1. **Pivot to a fundamentally different data source** (e.g., on-chain transaction-level data, ")
            f.write("social sentiment, cross-chain flow)\n")
            f.write("2. **Pivot to a different market** (e.g., established tokens with deeper liquidity)\n")
            f.write("3. **Accept that the edge does not exist** in the current market microstructure and stop\n\n")
            f.write("Do NOT re-run the same features with minor parameter changes.\n")
            f.write("Do NOT launch any live observer.\n\n")

        # ── Horizon-level summary ─────────────────────────────────────────
        f.write("---\n\n## Horizon-Level Summary\n\n")
        f.write("| Horizon | Features Tested | Discovery Pass | Holdout Pass | Novel + Constraint |\n")
        f.write("|---------|----------------:|---------------:|-------------:|-------------------:|\n")

        for h in horizons:
            r = all_results.get(h, {})
            n_tested = len(r.get("discovery_results", {}))
            n_disc_pass = sum(1 for d in r.get("discovery_results", {}).values() if d.get("status") == "PASS")
            promoted = r.get("promoted_features", [])
            n_hold_pass = sum(1 for feat in promoted
                             if r.get("holdout_results", {}).get(feat, {}).get("status") == "PASS")
            n_novel_constraint = 0
            for feat in promoted:
                hr = r.get("holdout_results", {}).get(feat, {})
                if hr.get("status") == "PASS":
                    b = all_benchmarks.get(h, {}).get("features", {}).get(feat, {})
                    if (b.get("novelty", {}).get("novel", False) and
                            b.get("structural_distinction", {}).get("addresses_any", False)):
                        n_novel_constraint += 1
            f.write(f"| +{h} | {n_tested} | {n_disc_pass} | {n_hold_pass} | {n_novel_constraint} |\n")

        # ── Safety confirmation ───────────────────────────────────────────
        f.write("\n---\n\n## Safety Confirmation\n\n")
        f.write("- Collector NOT stopped\n")
        f.write("- Live tape NOT mutated\n")
        f.write("- No live observer started\n")
        f.write("- No scanner/strategy changes made\n")
        f.write("- +1d horizon EXCLUDED from primary decision\n")

    print(f"  Final recommendation: {output_path}")
    print(f"  Verdict: {verdict_labels[verdict_num]}")


def main():
    parser = argparse.ArgumentParser(description="Generate Final Recommendation Memo")
    parser.add_argument("--sweep-base", required=True, help="Base directory of sweep results")
    parser.add_argument("--horizons", default="5m,15m,30m,1h,4h", help="Comma-separated horizons")
    parser.add_argument("--output", required=True, help="Output path for recommendation memo")
    args = parser.parse_args()

    horizons = args.horizons.split(",")
    all_results, all_benchmarks = load_results(args.sweep_base, horizons)

    if not all_results:
        print("ERROR: No sweep results found. Run the sweeps first.")
        sys.exit(1)

    verdict_num, approved, novel_passes = determine_verdict(all_results, all_benchmarks)
    write_memo(args.output, verdict_num, approved, novel_passes, all_results, all_benchmarks, horizons)


if __name__ == "__main__":
    main()
