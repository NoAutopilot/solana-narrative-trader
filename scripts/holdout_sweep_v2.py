#!/usr/bin/env python3
"""
holdout_sweep_v2.py — Pre-registered holdout pipeline for feature_tape_v2.
Cold-path infra only. Does NOT modify any live collection or DB.

Usage:
  python3 scripts/holdout_sweep_v2.py --horizon 5m --output-dir reports/sweeps/v2_5m
  python3 scripts/holdout_sweep_v2.py --horizon 30m --features r_m5_micro,buy_sell_ratio_m5 --output-dir reports/sweeps/v2_30m
  python3 scripts/holdout_sweep_v2.py --dry-run --horizon 5m
"""

import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# ── Constants ─────────────────────────────────────────────────────────────────
DISCOVERY_FRACTION = 0.75
MIN_DISCOVERY_ROWS = 1500
MIN_HOLDOUT_ROWS = 500
MIN_DISCOVERY_FIRES = 50
MIN_HOLDOUT_FIRES = 15
MIN_MICRO_HOLDOUT = 350
BOOTSTRAP_N = 10_000
WINSORIZE_LO = 0.01
WINSORIZE_HI = 0.99

# Promotion gates
GATE_THRESHOLDS = {
    "G1_mean_net_proxy": 0.0,
    "G2_median_net_proxy": 0.0,
    "G3_ci_lower_mean": 0.0,
    "G4_ci_lower_median": -0.001,
    "G5_win_rate": 0.52,
    "G6_top1_share": 0.30,
    "G7_top3_share": 0.50,
    "G8_coverage": 0.70,
}

# Kill gates (reference only — for future live observer)
KILL_THRESHOLDS = {
    "K1_cum_mean_delta": -0.01,
    "K2_cum_median_delta": -0.005,
    "K3_win_rate": 0.45,
    "K4_max_drawdown": -0.05,
    "K5_consecutive_losses": 15,
    "K6_single_pair_loss": -0.20,
}

HORIZON_SECONDS = {
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
}

# Numeric feature columns eligible for sweep
SWEEP_FEATURES = [
    # Fundamentals
    "age_hours", "liquidity_usd", "vol_h1", "vol_h24", "price_usd",
    "r_m5_snap", "r_h1_snap",
    # Family A: micro-native
    "buys_m5", "sells_m5", "buys_h1", "sells_h1",
    "buy_sell_ratio_m5", "buy_sell_ratio_h1",
    "buy_count_ratio_m5", "buy_count_ratio_h1",
    "avg_trade_usd_m5", "avg_trade_usd_h1",
    "vol_accel_m5_vs_h1", "txn_accel_m5_vs_h1",
    "r_m5_micro", "rv_5m", "rv_1m", "range_5m",
    # Family A: snapshot fallback
    "buys_m5_snap", "sells_m5_snap",
    "buy_count_ratio_m5_snap", "avg_trade_usd_m5_snap",
    # Family B: route/quote
    "jup_vs_cpamm_diff_pct", "round_trip_pct",
    "impact_buy_pct", "impact_sell_pct", "impact_asymmetry_pct",
    # Family C: liquidity
    "liq_change_pct", "liq_cliff_flag",
    # Family C: market-state
    "breadth_positive_pct", "breadth_negative_pct",
    "median_pool_r_m5", "pool_dispersion_r_m5", "median_pool_rv5m",
    "pool_liquidity_median", "pool_vol_h1_median",
    "pool_size_total", "pool_size_with_micro", "coverage_ratio_micro",
]


# ── Helpers ───────────────────────────────────────────────────────────────────
def winsorize(arr, lo=WINSORIZE_LO, hi=WINSORIZE_HI):
    """Winsorize array at lo/hi percentiles."""
    low = np.nanpercentile(arr, lo * 100)
    high = np.nanpercentile(arr, hi * 100)
    return np.clip(arr, low, high)


def bootstrap_ci(arr, stat_fn, n=BOOTSTRAP_N, alpha=0.05):
    """Bootstrap confidence interval for stat_fn."""
    rng = np.random.default_rng(42)
    stats = []
    for _ in range(n):
        sample = rng.choice(arr, size=len(arr), replace=True)
        stats.append(stat_fn(sample))
    lo = np.percentile(stats, 100 * alpha / 2)
    hi = np.percentile(stats, 100 * (1 - alpha / 2))
    return lo, hi


def compute_gate_metrics(bucket_df, full_df, feature_name, n_features_tested=1):
    """Compute all 8 promotion gate metrics for a single feature's best bucket."""
    net = bucket_df["net_proxy"].dropna().values
    if len(net) == 0:
        return None

    net_w = winsorize(net)

    # Adjust CI level for multiple testing
    if n_features_tested <= 3:
        alpha = 0.05
    else:
        alpha = 0.05 / n_features_tested  # Bonferroni

    mean_net = float(np.mean(net_w))
    median_net = float(np.median(net_w))
    ci_lo_mean, ci_hi_mean = bootstrap_ci(net_w, np.mean, alpha=alpha)
    ci_lo_median, ci_hi_median = bootstrap_ci(net_w, np.median, alpha=alpha)
    win_rate = float(np.mean(net_w > 0))

    # Concentration
    abs_contributions = np.abs(net_w)
    total_abs = abs_contributions.sum()
    if total_abs > 0:
        sorted_shares = np.sort(abs_contributions / total_abs)[::-1]
        top1_share = float(sorted_shares[0])
        top3_share = float(sorted_shares[:3].sum())
    else:
        top1_share = 0.0
        top3_share = 0.0

    # Coverage: fraction of eligible rows where this feature is not NULL
    feat_vals = full_df[feature_name].values
    coverage = float(np.mean(~pd.isna(feat_vals)))

    metrics = {
        "G1_mean_net_proxy": mean_net,
        "G2_median_net_proxy": median_net,
        "G3_ci_lower_mean": float(ci_lo_mean),
        "G3_ci_upper_mean": float(ci_hi_mean),
        "G4_ci_lower_median": float(ci_lo_median),
        "G4_ci_upper_median": float(ci_hi_median),
        "G5_win_rate": win_rate,
        "G6_top1_share": top1_share,
        "G7_top3_share": top3_share,
        "G8_coverage": coverage,
        "alpha_used": alpha,
        "n_bucket": len(net),
        "n_eligible": len(full_df),
    }

    # Gate pass/fail
    gates = {}
    gates["G1"] = mean_net > GATE_THRESHOLDS["G1_mean_net_proxy"]
    gates["G2"] = median_net > GATE_THRESHOLDS["G2_median_net_proxy"]
    gates["G3"] = ci_lo_mean > GATE_THRESHOLDS["G3_ci_lower_mean"]
    gates["G4"] = ci_lo_median > GATE_THRESHOLDS["G4_ci_lower_median"]
    gates["G5"] = win_rate > GATE_THRESHOLDS["G5_win_rate"]
    gates["G6"] = top1_share < GATE_THRESHOLDS["G6_top1_share"]
    gates["G7"] = top3_share < GATE_THRESHOLDS["G7_top3_share"]
    gates["G8"] = coverage >= GATE_THRESHOLDS["G8_coverage"]
    metrics["gates"] = gates
    metrics["all_gates_pass"] = all(gates.values())

    return metrics


def bucket_and_evaluate(df, feature_name, n_buckets, n_features_tested=1):
    """Bucket feature into n_buckets, find best bucket, compute gate metrics."""
    valid = df[[feature_name, "net_proxy"]].dropna()
    if len(valid) < n_buckets * 10:
        return None, None, None

    try:
        valid["bucket"] = pd.qcut(valid[feature_name], n_buckets, labels=False, duplicates="drop")
    except ValueError:
        return None, None, None

    # Find best bucket by mean net_proxy
    bucket_means = valid.groupby("bucket")["net_proxy"].mean()
    best_bucket = bucket_means.idxmax()
    best_df = valid[valid["bucket"] == best_bucket]

    # Compute boundaries
    boundaries = {}
    for b in sorted(valid["bucket"].unique()):
        bdata = valid[valid["bucket"] == b][feature_name]
        boundaries[int(b)] = {"min": float(bdata.min()), "max": float(bdata.max())}

    metrics = compute_gate_metrics(best_df, df, feature_name, n_features_tested)
    if metrics:
        metrics["best_bucket"] = int(best_bucket)
        metrics["bucket_boundaries"] = boundaries

    return metrics, best_bucket, boundaries


def derive_forward_return(db_path, fire_epoch, candidate_mint, horizon_s):
    """
    Derive forward return from universe_snapshot.
    Looks for a snapshot within +/- 60s of (fire_epoch + horizon_s).
    Returns (r_forward, jitter_s) or (None, None).
    """
    # This is a placeholder — the actual implementation will query
    # universe_snapshot for the price at fire_epoch + horizon_s.
    # For now, returns None to indicate labels are not yet available.
    return None, None


# ── Main Pipeline ─────────────────────────────────────────────────────────────
def run_pipeline(args):
    """Execute the holdout pipeline."""
    db_path = args.db_path
    horizon = args.horizon
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dry_run = args.dry_run
    features = args.features.split(",") if args.features else SWEEP_FEATURES

    horizon_s = HORIZON_SECONDS.get(horizon)
    if horizon_s is None:
        print(f"ERROR: Unknown horizon '{horizon}'. Valid: {list(HORIZON_SECONDS.keys())}")
        sys.exit(1)

    # ── Load data ─────────────────────────────────────────────────────────
    print(f"Loading feature_tape_v2 from {db_path} ...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Primary view: eligible-only
    df = pd.read_sql_query(
        "SELECT * FROM feature_tape_v2 WHERE eligible = 1 ORDER BY fire_time_epoch, candidate_mint",
        conn,
    )
    print(f"  Loaded {len(df)} eligible rows")

    # Get fire list
    fires = df[["fire_id", "fire_time_epoch"]].drop_duplicates().sort_values("fire_time_epoch")
    n_fires = len(fires)
    print(f"  {n_fires} unique fires")

    # ── Validate sample sizes ─────────────────────────────────────────────
    split_idx = int(n_fires * DISCOVERY_FRACTION)
    discovery_fires = fires.iloc[:split_idx]["fire_id"].values
    holdout_fires = fires.iloc[split_idx:]["fire_id"].values

    disc_df = df[df["fire_id"].isin(discovery_fires)]
    hold_df = df[df["fire_id"].isin(holdout_fires)]

    validation = {
        "n_fires_total": n_fires,
        "n_fires_discovery": len(discovery_fires),
        "n_fires_holdout": len(holdout_fires),
        "n_rows_discovery": len(disc_df),
        "n_rows_holdout": len(hold_df),
        "n_micro_holdout": int((hold_df["order_flow_source"] == "microstructure_log").sum()),
    }

    checks = {
        "discovery_rows": len(disc_df) >= MIN_DISCOVERY_ROWS,
        "holdout_rows": len(hold_df) >= MIN_HOLDOUT_ROWS,
        "discovery_fires": len(discovery_fires) >= MIN_DISCOVERY_FIRES,
        "holdout_fires": len(holdout_fires) >= MIN_HOLDOUT_FIRES,
        "micro_holdout": validation["n_micro_holdout"] >= MIN_MICRO_HOLDOUT,
    }
    validation["checks"] = checks
    validation["all_valid"] = all(checks.values())

    print(f"\n  Validation:")
    for k, v in checks.items():
        status = "PASS" if v else "FAIL"
        print(f"    {k}: {status} ({validation.get('n_' + k.replace('_', '_'), '?')})")

    if not validation["all_valid"]:
        print("\n  ERROR: Sample size requirements not met. Sweep is invalid.")
        print("  Extend collection and re-run.")
        # Write validation report even on failure
        with open(output_dir / "validation_failed.json", "w") as f:
            json.dump(validation, f, indent=2)
        if not dry_run:
            sys.exit(1)

    if dry_run:
        print("\n  DRY RUN — validation complete, no sweep executed.")
        with open(output_dir / "dry_run_validation.json", "w") as f:
            json.dump(validation, f, indent=2)
        return

    # ── Label derivation ──────────────────────────────────────────────────
    # Check if forward return labels exist
    label_col = f"r_forward_{horizon}"
    if label_col not in df.columns:
        print(f"\n  Label column '{label_col}' not found in feature_tape_v2.")
        print(f"  Forward return labels must be derived from universe_snapshot.")
        print(f"  Running label derivation...")

        # Derive labels from universe_snapshot
        label_query = f"""
        SELECT
            ft.fire_id,
            ft.candidate_mint,
            ft.fire_time_epoch,
            ft.price_usd AS price_at_fire,
            (
                SELECT us.price_usd
                FROM universe_snapshot us
                WHERE us.mint = ft.candidate_mint
                  AND us.snapshot_at >= datetime(ft.fire_time_epoch + {horizon_s}, 'unixepoch')
                  AND us.snapshot_at <= datetime(ft.fire_time_epoch + {horizon_s} + 60, 'unixepoch')
                ORDER BY us.snapshot_at ASC
                LIMIT 1
            ) AS price_at_horizon
        FROM feature_tape_v2 ft
        WHERE ft.eligible = 1
        """
        try:
            labels = pd.read_sql_query(label_query, conn)
            labels["r_forward"] = (labels["price_at_horizon"] / labels["price_at_fire"]) - 1
            labels = labels[["fire_id", "candidate_mint", "r_forward"]].dropna()
            df = df.merge(labels, on=["fire_id", "candidate_mint"], how="left")
            df.rename(columns={"r_forward": label_col}, inplace=True)
            print(f"  Derived {len(labels)} forward return labels ({horizon})")
            n_labeled = df[label_col].notna().sum()
            print(f"    {n_labeled}/{len(df)} rows have labels ({n_labeled/len(df)*100:.1f}%)")
        except Exception as e:
            print(f"  ERROR deriving labels: {e}")
            print(f"  Labels may not be available yet for horizon {horizon}.")
            sys.exit(1)

    # ── Compute net-proxy ─────────────────────────────────────────────────
    df["net_proxy"] = df[label_col] - df["round_trip_pct"]

    # Re-split after label derivation
    disc_df = df[df["fire_id"].isin(discovery_fires)].copy()
    hold_df = df[df["fire_id"].isin(holdout_fires)].copy()

    # ── Discovery sweep ───────────────────────────────────────────────────
    print(f"\n  Running discovery sweep on {len(disc_df)} rows, {len(features)} features...")
    n_buckets = 5 if len(disc_df) > 2000 else 3
    n_features_tested = len(features)

    discovery_results = {}
    promoted_features = []

    for feat in features:
        metrics, best_bucket, boundaries = bucket_and_evaluate(
            disc_df, feat, n_buckets, n_features_tested
        )
        if metrics is None:
            discovery_results[feat] = {"status": "SKIP", "reason": "insufficient_data"}
            continue

        discovery_results[feat] = {
            "status": "PASS" if metrics["all_gates_pass"] else "FAIL",
            "metrics": metrics,
        }

        if metrics["all_gates_pass"]:
            promoted_features.append(feat)
            print(f"    {feat}: PROMOTED (all 8 gates pass)")
        else:
            failed = [g for g, v in metrics["gates"].items() if not v]
            print(f"    {feat}: FAIL ({', '.join(failed)})")

    print(f"\n  Discovery complete: {len(promoted_features)}/{len(features)} features promoted")

    # ── Holdout evaluation ────────────────────────────────────────────────
    holdout_results = {}
    if promoted_features:
        print(f"\n  Running holdout evaluation on {len(hold_df)} rows, {len(promoted_features)} features...")

        for feat in promoted_features:
            # Use frozen bucket boundaries from discovery
            disc_meta = discovery_results[feat]["metrics"]
            boundaries = disc_meta["bucket_boundaries"]
            best_bucket = disc_meta["best_bucket"]

            # Apply frozen boundaries to holdout
            valid = hold_df[[feat, "net_proxy"]].dropna()
            if len(valid) < 30:
                holdout_results[feat] = {"status": "SKIP", "reason": "insufficient_holdout_data"}
                continue

            # Assign buckets using discovery boundaries
            def assign_bucket(val):
                for b_id in sorted(boundaries.keys()):
                    if val <= boundaries[b_id]["max"]:
                        return b_id
                return max(boundaries.keys())

            valid["bucket"] = valid[feat].apply(assign_bucket)
            best_df = valid[valid["bucket"] == best_bucket]

            if len(best_df) < 10:
                holdout_results[feat] = {"status": "SKIP", "reason": "insufficient_best_bucket"}
                continue

            metrics = compute_gate_metrics(best_df, hold_df, feat, len(promoted_features))
            if metrics is None:
                holdout_results[feat] = {"status": "SKIP", "reason": "computation_error"}
                continue

            holdout_results[feat] = {
                "status": "PASS" if metrics["all_gates_pass"] else "FAIL",
                "metrics": metrics,
            }

            if metrics["all_gates_pass"]:
                print(f"    {feat}: HOLDOUT PASS — PROMOTED TO LIVE OBSERVER DESIGN")
            else:
                failed = [g for g, v in metrics["gates"].items() if not v]
                print(f"    {feat}: HOLDOUT FAIL ({', '.join(failed)})")
    else:
        print("\n  No features promoted from discovery. Holdout evaluation skipped.")

    # ── Write report ──────────────────────────────────────────────────────
    report_path = output_dir / "holdout_sweep_report.md"
    with open(report_path, "w") as f:
        f.write(f"# Holdout Sweep Report — {horizon}\n\n")
        f.write(f"**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"**View:** PRIMARY (eligible-only)\n")
        f.write(f"**Horizon:** {horizon} ({horizon_s}s)\n")
        f.write(f"**Fires:** {n_fires} total ({len(discovery_fires)} discovery, {len(holdout_fires)} holdout)\n")
        f.write(f"**Rows:** {len(df)} eligible ({len(disc_df)} discovery, {len(hold_df)} holdout)\n")
        f.write(f"**Buckets:** {n_buckets} ({'quintile' if n_buckets == 5 else 'tercile'})\n")
        f.write(f"**Features tested:** {len(features)}\n")
        f.write(f"**Bonferroni correction:** {'Yes' if n_features_tested > 3 else 'No'}\n\n")
        f.write("---\n\n")

        f.write("## Discovery Results\n\n")
        f.write("| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |\n")
        f.write("|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|\n")
        for feat in features:
            r = discovery_results.get(feat, {})
            if r.get("status") == "SKIP":
                f.write(f"| {feat} | SKIP | — | — | — | — | — | — |\n")
            elif "metrics" in r:
                m = r["metrics"]
                f.write(f"| {feat} | {r['status']} | {m['G1_mean_net_proxy']*100:.3f}% | {m['G2_median_net_proxy']*100:.3f}% | {m['G3_ci_lower_mean']*100:.3f}% | {m['G5_win_rate']*100:.1f}% | {m['G6_top1_share']:.3f} | {m['G8_coverage']*100:.1f}% |\n")

        if promoted_features:
            f.write(f"\n**Promoted to holdout:** {', '.join(promoted_features)}\n\n")
            f.write("## Holdout Results\n\n")
            f.write("| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |\n")
            f.write("|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|\n")
            for feat in promoted_features:
                r = holdout_results.get(feat, {})
                if r.get("status") == "SKIP":
                    f.write(f"| {feat} | SKIP ({r.get('reason', '')}) | — | — | — | — | — | — |\n")
                elif "metrics" in r:
                    m = r["metrics"]
                    f.write(f"| {feat} | {r['status']} | {m['G1_mean_net_proxy']*100:.3f}% | {m['G2_median_net_proxy']*100:.3f}% | {m['G3_ci_lower_mean']*100:.3f}% | {m['G5_win_rate']*100:.1f}% | {m['G6_top1_share']:.3f} | {m['G8_coverage']*100:.1f}% |\n")
        else:
            f.write("\n**No features promoted from discovery. Program should proceed to next option or stop.**\n")

    # ── Write JSON results ────────────────────────────────────────────────
    results_json = {
        "horizon": horizon,
        "horizon_s": horizon_s,
        "n_fires": n_fires,
        "n_discovery_fires": len(discovery_fires),
        "n_holdout_fires": len(holdout_fires),
        "n_rows_eligible": len(df),
        "n_rows_discovery": len(disc_df),
        "n_rows_holdout": len(hold_df),
        "n_buckets": n_buckets,
        "n_features_tested": n_features_tested,
        "bonferroni": n_features_tested > 3,
        "discovery_results": {k: v for k, v in discovery_results.items() if v.get("status") != "SKIP"},
        "promoted_features": promoted_features,
        "holdout_results": holdout_results,
        "validation": validation,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    with open(output_dir / "holdout_sweep_results.json", "w") as f:
        json.dump(results_json, f, indent=2, default=str)

    conn.close()
    print(f"\n  Report written to {report_path}")
    print(f"  Results JSON written to {output_dir / 'holdout_sweep_results.json'}")


# ── CLI ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Feature Tape v2 — Holdout Sweep Pipeline")
    parser.add_argument("--db-path", default="/root/solana_trader/data/solana_trader.db",
                        help="Path to SQLite database")
    parser.add_argument("--horizon", required=True, choices=["5m", "15m", "30m", "1h", "4h"],
                        help="Forward return horizon")
    parser.add_argument("--view", default="primary", choices=["primary", "secondary"],
                        help="Analysis view (default: primary = eligible-only)")
    parser.add_argument("--features", default=None,
                        help="Comma-separated feature list (default: all)")
    parser.add_argument("--output-dir", default="reports/sweeps/v2",
                        help="Output directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate only, do not run sweep")
    args = parser.parse_args()
    run_pipeline(args)
