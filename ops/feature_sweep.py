#!/usr/bin/env python3
"""
feature_sweep.py — Final retrospective feature family sweep for feature_tape_v1.

Labels:
  GROSS:     r_forward_5m
  NET-PROXY: r_forward_5m - round_trip_pct
             (round_trip_pct = impact_buy_pct + impact_sell_pct, stored in feature_tape_v1
              as the CPAMM-based round-trip cost at the time of the fire snapshot.
              This is a proxy only — actual execution cost depends on venue, size, and timing.)

Exclusions:
  label_quality IN ('missing', 'missing_disk_gap') are excluded from all denominators.

Usage:
  python3 ops/feature_sweep.py                  # runs sweep, writes reports
  python3 ops/feature_sweep.py --dry-run        # prints stats, writes nothing
  python3 ops/feature_sweep.py --min-fires 96  # only run if >= 96 fires collected (default)
"""

import sqlite3
import csv
import os
import sys
import argparse
import math
from datetime import datetime, timezone

DB      = os.environ.get('SOLANA_TRADER_DB', '/root/solana_trader/data/solana_trader.db')
OUT_DIR = '/root/solana_trader/reports/synthesis'

TRACK_A = [
    'jup_vs_cpamm_diff_pct',
    'round_trip_pct',
    'impact_buy_pct',
    'impact_sell_pct',
    'breadth_positive_pct',
    'median_pool_r_m5',
    'pool_dispersion_r_m5',
    'age_hours',
    'liquidity_usd',
    'vol_h1',
]

TRACK_B = [
    'r_m5',
    'buy_sell_ratio_m5',
    'signed_flow_m5',
    'txn_accel_m5_vs_h1',
    'vol_accel_m5_vs_h1',
    'avg_trade_usd_m5',
    'liq_change_pct',
]

# Outlier threshold: top contributor share > this fraction is flagged
OUTLIER_CONC_THRESHOLD = 0.30

def log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f'{ts} [feature_sweep] {msg}', flush=True)

def mean(vals):
    v = [x for x in vals if x is not None]
    return sum(v) / len(v) if v else None

def median(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if n == 0: return None
    if n % 2 == 1: return v[n // 2]
    return (v[n // 2 - 1] + v[n // 2]) / 2

def stdev(vals):
    v = [x for x in vals if x is not None]
    if len(v) < 2: return None
    m = sum(v) / len(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))

def top_contributor_share(vals):
    """Fraction of total absolute return attributable to the single largest absolute value."""
    v = [x for x in vals if x is not None]
    if not v: return None
    total_abs = sum(abs(x) for x in v)
    if total_abs == 0: return 0.0
    return max(abs(x) for x in v) / total_abs

def bucket_stats(rows, feature_col, label_col, n_buckets=3):
    """
    Split rows into n_buckets equal-size buckets by feature value.
    Returns list of dicts with bucket stats.
    """
    valid = [(r[feature_col], r[label_col]) for r in rows
             if r[feature_col] is not None and r[label_col] is not None]
    if len(valid) < n_buckets * 2:
        return None
    valid.sort(key=lambda x: x[0])
    size = len(valid) // n_buckets
    buckets = []
    for i in range(n_buckets):
        start = i * size
        end = (i + 1) * size if i < n_buckets - 1 else len(valid)
        chunk = valid[start:end]
        feat_vals = [x[0] for x in chunk]
        lbl_vals  = [x[1] for x in chunk]
        buckets.append({
            'bucket': i + 1,
            'n': len(chunk),
            'feat_min': min(feat_vals),
            'feat_max': max(feat_vals),
            'feat_mean': mean(feat_vals),
            'label_mean': mean(lbl_vals),
            'label_median': median(lbl_vals),
            'label_stdev': stdev(lbl_vals),
            'top_contributor_share': top_contributor_share(lbl_vals),
        })
    return buckets

def quintile_stats(rows, feature_col, label_col):
    """Top vs bottom quintile comparison."""
    valid = [(r[feature_col], r[label_col]) for r in rows
             if r[feature_col] is not None and r[label_col] is not None]
    if len(valid) < 20:
        return None, None
    valid.sort(key=lambda x: x[0])
    q_size = len(valid) // 5
    bottom = [x[1] for x in valid[:q_size]]
    top    = [x[1] for x in valid[-q_size:]]
    return mean(top), mean(bottom)

def analyze_feature(rows, feature_col, label_gross_col, label_net_col, track):
    """Full analysis for one feature against both label targets."""
    total = len(rows)
    present = sum(1 for r in rows if r[feature_col] is not None)
    coverage_pct = round(100 * present / total, 1) if total > 0 else 0

    # Gross label analysis
    gross_buckets = bucket_stats(rows, feature_col, label_gross_col, n_buckets=3)
    net_buckets   = bucket_stats(rows, feature_col, label_net_col,   n_buckets=3)

    gross_q_top, gross_q_bot = quintile_stats(rows, feature_col, label_gross_col)
    net_q_top,   net_q_bot   = quintile_stats(rows, feature_col, label_net_col)

    # Best bucket = highest mean gross return
    best_bucket_gross = None
    best_bucket_net   = None
    if gross_buckets:
        best_bucket_gross = max(gross_buckets, key=lambda b: b['label_mean'] or -999)
    if net_buckets:
        best_bucket_net   = max(net_buckets,   key=lambda b: b['label_mean'] or -999)

    # Outlier risk
    all_gross = [r[label_gross_col] for r in rows if r[feature_col] is not None and r[label_gross_col] is not None]
    outlier_share = top_contributor_share(all_gross)
    outlier_risk = 'HIGH' if (outlier_share or 0) > OUTLIER_CONC_THRESHOLD else 'LOW'

    # Top-bottom tercile diff
    tercile_diff_gross = None
    tercile_diff_net   = None
    if gross_buckets and len(gross_buckets) >= 3:
        g_top = gross_buckets[-1]['label_mean']
        g_bot = gross_buckets[0]['label_mean']
        tercile_diff_gross = round(g_top - g_bot, 6) if (g_top is not None and g_bot is not None) else None
    if net_buckets and len(net_buckets) >= 3:
        n_top = net_buckets[-1]['label_mean']
        n_bot = net_buckets[0]['label_mean']
        tercile_diff_net = round(n_top - n_bot, 6) if (n_top is not None and n_bot is not None) else None

    # Recommendation logic
    best_gross_mean = best_bucket_gross['label_mean'] if best_bucket_gross else None
    best_net_mean   = best_bucket_net['label_mean']   if best_bucket_net   else None
    best_gross_med  = best_bucket_gross['label_median'] if best_bucket_gross else None

    rec = 'SKIP'
    if (best_net_mean is not None and best_net_mean > 0 and
        best_gross_med is not None and best_gross_med >= 0 and
        outlier_risk == 'LOW' and
        coverage_pct >= 70):
        rec = 'CANDIDATE'
    elif best_net_mean is not None and best_net_mean > 0:
        rec = 'WEAK_CANDIDATE'

    return {
        'feature': feature_col,
        'track': track,
        'total_rows': total,
        'present': present,
        'coverage_pct': coverage_pct,
        'best_bucket_gross_mean': round(best_gross_mean, 6) if best_gross_mean is not None else None,
        'best_bucket_net_mean':   round(best_net_mean,   6) if best_net_mean   is not None else None,
        'best_bucket_gross_median': round(best_gross_med, 6) if best_gross_med is not None else None,
        'tercile_diff_gross': tercile_diff_gross,
        'tercile_diff_net':   tercile_diff_net,
        'quintile_top_gross': round(gross_q_top, 6) if gross_q_top is not None else None,
        'quintile_bot_gross': round(gross_q_bot, 6) if gross_q_bot is not None else None,
        'quintile_top_net':   round(net_q_top,   6) if net_q_top   is not None else None,
        'quintile_bot_net':   round(net_q_bot,   6) if net_q_bot   is not None else None,
        'outlier_top_share':  round(outlier_share, 4) if outlier_share is not None else None,
        'outlier_risk': outlier_risk,
        'recommendation': rec,
        'gross_buckets': gross_buckets,
        'net_buckets':   net_buckets,
    }

def format_pct(v):
    if v is None: return 'N/A'
    return f'{v*100:+.3f}%'

def format_val(v, decimals=4):
    if v is None: return 'N/A'
    return f'{v:.{decimals}f}'

def write_md(results, track_label, out_path, subset_note=''):
    lines = []
    lines.append(f'# Feature Family Sweep — {track_label}')
    lines.append(f'')
    lines.append(f'Generated: {datetime.now(timezone.utc).isoformat()}')
    lines.append(f'')
    if subset_note:
        lines.append(f'> **{subset_note}**')
        lines.append(f'')
    lines.append(f'## Net-Proxy Formula')
    lines.append(f'')
    lines.append(f'```')
    lines.append(f'net_proxy = r_forward_5m - round_trip_pct')
    lines.append(f'')
    lines.append(f'Where:')
    lines.append(f'  r_forward_5m   = (price_at_fire_plus_5m / price_at_fire) - 1')
    lines.append(f'                   Source: universe_snapshot.price_usd')
    lines.append(f'                   Entry:  latest snapshot with ts <= fire_time_epoch')
    lines.append(f'                   Forward: closest snapshot to fire_time_epoch + 300s,')
    lines.append(f'                            strictly after fire, within ±60s tolerance')
    lines.append(f'')
    lines.append(f'  round_trip_pct = impact_buy_pct + impact_sell_pct')
    lines.append(f'                   = CPAMM-based round-trip cost at fire snapshot time')
    lines.append(f'                   Source: feature_tape_v1.round_trip_pct')
    lines.append(f'                   PROXY ONLY: actual execution cost varies by venue,')
    lines.append(f'                   size, and timing. Does not include fees or slippage.')
    lines.append(f'```')
    lines.append(f'')
    lines.append(f'## Exclusions')
    lines.append(f'')
    lines.append(f'Rows with `label_quality IN (missing, missing_disk_gap)` are excluded')
    lines.append(f'from all denominators. These correspond to the 20 fires missed during')
    lines.append(f'the 11:15–15:45 UTC disk-full gap on 2026-03-11.')
    lines.append(f'')
    lines.append(f'## Ranked Summary Table')
    lines.append(f'')
    lines.append(f'| Feature | Coverage | Best Bucket Gross | Best Bucket Net | Gross Median | Tercile Diff (Gross) | Outlier Risk | Recommendation |')
    lines.append(f'|---------|----------|-------------------|-----------------|--------------|----------------------|--------------|----------------|')
    for r in sorted(results, key=lambda x: x['best_bucket_net_mean'] or -999, reverse=True):
        lines.append(
            f"| {r['feature']} "
            f"| {r['coverage_pct']}% "
            f"| {format_pct(r['best_bucket_gross_mean'])} "
            f"| {format_pct(r['best_bucket_net_mean'])} "
            f"| {format_pct(r['best_bucket_gross_median'])} "
            f"| {format_pct(r['tercile_diff_gross'])} "
            f"| {r['outlier_risk']} "
            f"| {r['recommendation']} |"
        )
    lines.append(f'')
    lines.append(f'## Per-Feature Detail')
    lines.append(f'')
    for r in results:
        lines.append(f"### {r['feature']}")
        lines.append(f'')
        lines.append(f'- **Coverage**: {r["present"]}/{r["total_rows"]} ({r["coverage_pct"]}%)')
        lines.append(f'- **Outlier risk**: {r["outlier_risk"]} (top contributor share: {format_val(r["outlier_top_share"])})')
        lines.append(f'- **Best bucket gross mean**: {format_pct(r["best_bucket_gross_mean"])}')
        lines.append(f'- **Best bucket net mean**: {format_pct(r["best_bucket_net_mean"])}')
        lines.append(f'- **Best bucket gross median**: {format_pct(r["best_bucket_gross_median"])}')
        lines.append(f'- **Tercile diff (gross)**: {format_pct(r["tercile_diff_gross"])}')
        lines.append(f'- **Tercile diff (net)**: {format_pct(r["tercile_diff_net"])}')
        lines.append(f'- **Quintile top/bot (gross)**: {format_pct(r["quintile_top_gross"])} / {format_pct(r["quintile_bot_gross"])}')
        lines.append(f'- **Quintile top/bot (net)**: {format_pct(r["quintile_top_net"])} / {format_pct(r["quintile_bot_net"])}')
        lines.append(f'- **Recommendation**: {r["recommendation"]}')
        lines.append(f'')
        if r['gross_buckets']:
            lines.append(f'**Tercile buckets (gross label):**')
            lines.append(f'')
            lines.append(f'| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |')
            lines.append(f'|--------|---|----------|----------|------------|--------------|-------------|')
            for b in r['gross_buckets']:
                lines.append(
                    f"| {b['bucket']} | {b['n']} "
                    f"| {format_val(b['feat_min'])} | {format_val(b['feat_max'])} "
                    f"| {format_pct(b['label_mean'])} | {format_pct(b['label_median'])} "
                    f"| {format_val(b['label_stdev'])} |"
                )
            lines.append(f'')
        if r['net_buckets']:
            lines.append(f'**Tercile buckets (net-proxy label):**')
            lines.append(f'')
            lines.append(f'| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |')
            lines.append(f'|--------|---|----------|----------|----------|------------|')
            for b in r['net_buckets']:
                lines.append(
                    f"| {b['bucket']} | {b['n']} "
                    f"| {format_val(b['feat_min'])} | {format_val(b['feat_max'])} "
                    f"| {format_pct(b['label_mean'])} | {format_pct(b['label_median'])} |"
                )
            lines.append(f'')

    lines.append(f'## Decision')
    lines.append(f'')
    candidates = [r for r in results if r['recommendation'] == 'CANDIDATE']
    weak = [r for r in results if r['recommendation'] == 'WEAK_CANDIDATE']
    if candidates:
        lines.append(f'**CANDIDATE FEATURES FOUND**: {", ".join(r["feature"] for r in candidates)}')
        lines.append(f'')
        lines.append(f'At least one feature shows positive net-proxy mean, non-negative median,')
        lines.append(f'acceptable outlier risk, and sufficient coverage.')
        lines.append(f'Recommend further evaluation for new live observer.')
    elif weak:
        lines.append(f'**WEAK CANDIDATES ONLY**: {", ".join(r["feature"] for r in weak)}')
        lines.append(f'')
        lines.append(f'Positive net-proxy mean but fails one or more quality gates.')
        lines.append(f'Do not recommend new live observer without additional validation.')
    else:
        lines.append(f'**NO NEW LIVE OBSERVER — FAMILY SWEEP NEGATIVE**')
        lines.append(f'')
        lines.append(f'No feature shows positive net-proxy mean in the best bucket with')
        lines.append(f'acceptable coverage, non-negative median, and low outlier risk.')

    with open(out_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    log(f'Written: {out_path}')

def write_csv(results, out_path):
    fields = [
        'feature', 'track', 'total_rows', 'present', 'coverage_pct',
        'best_bucket_gross_mean', 'best_bucket_net_mean', 'best_bucket_gross_median',
        'tercile_diff_gross', 'tercile_diff_net',
        'quintile_top_gross', 'quintile_bot_gross',
        'quintile_top_net', 'quintile_bot_net',
        'outlier_top_share', 'outlier_risk', 'recommendation',
    ]
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(results)
    log(f'Written: {out_path}')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-fires', type=int, default=96)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row

    fires = con.execute('SELECT COUNT(DISTINCT fire_id) FROM feature_tape_v1').fetchone()[0]
    log(f'Fires collected: {fires}/{args.min_fires}')
    if fires < args.min_fires:
        log(f'Not enough fires yet. Exiting.')
        con.close()
        sys.exit(0)

    # Mark disk-gap rows in labels table
    log('Marking disk-gap rows as missing_disk_gap...')
    gap_count = con.execute("""
        UPDATE feature_tape_v1_labels
        SET label_quality = 'missing_disk_gap'
        WHERE label_quality = 'missing'
        AND fire_id IN (
            SELECT DISTINCT fire_id FROM feature_tape_v1
            WHERE fire_time_utc >= '2026-03-11T11:00' AND fire_time_utc <= '2026-03-11T16:00'
        )
    """).rowcount
    con.commit()
    log(f'Marked {gap_count} rows as missing_disk_gap')

    # Load joined dataset: feature_tape + labels, excluding missing/missing_disk_gap
    log('Loading joined dataset...')
    rows = con.execute("""
        SELECT ft.*, lbl.r_forward_5m, lbl.label_quality, lbl.label_source
        FROM feature_tape_v1 ft
        JOIN feature_tape_v1_labels lbl
          ON lbl.fire_id = ft.fire_id AND lbl.candidate_mint = ft.candidate_mint
        WHERE lbl.label_quality NOT IN ('missing', 'missing_disk_gap')
          AND lbl.r_forward_5m IS NOT NULL
          AND ft.round_trip_pct IS NOT NULL
    """).fetchall()
    log(f'Rows in analysis dataset: {len(rows)}')

    # Compute net-proxy label for each row
    # net_proxy = r_forward_5m - round_trip_pct
    rows_dict = []
    for r in rows:
        d = dict(r)
        d['net_proxy'] = d['r_forward_5m'] - d['round_trip_pct'] if (d['r_forward_5m'] is not None and d['round_trip_pct'] is not None) else None
        rows_dict.append(d)

    log(f'Net-proxy rows: {sum(1 for r in rows_dict if r["net_proxy"] is not None)}')

    if args.dry_run:
        log('DRY RUN — no files written.')
        con.close()
        return

    os.makedirs(OUT_DIR, exist_ok=True)

    # Track A
    log('Running Track A analysis...')
    track_a_results = []
    for feat in TRACK_A:
        res = analyze_feature(rows_dict, feat, 'r_forward_5m', 'net_proxy', 'A')
        track_a_results.append(res)
        log(f'  {feat}: coverage={res["coverage_pct"]}%  best_net={format_pct(res["best_bucket_net_mean"])}  rec={res["recommendation"]}')

    write_md(track_a_results, 'Track A — Full-Sample Features',
             os.path.join(OUT_DIR, 'feature_family_sweep_full_sample.md'))
    write_csv(track_a_results,
              os.path.join(OUT_DIR, 'feature_family_sweep_full_sample.csv'))

    # Track B
    log('Running Track B analysis...')
    track_b_results = []
    for feat in TRACK_B:
        res = analyze_feature(rows_dict, feat, 'r_forward_5m', 'net_proxy', 'B')
        track_b_results.append(res)
        log(f'  {feat}: coverage={res["coverage_pct"]}%  best_net={format_pct(res["best_bucket_net_mean"])}  rec={res["recommendation"]}')

    write_md(track_b_results, 'Track B — Micro-Derived Features (SUBSET-ONLY — non-random missingness)',
             os.path.join(OUT_DIR, 'feature_family_sweep_subset_micro.md'),
             subset_note='SUBSET-ONLY: Track B results reflect non-random missingness (Orca/Meteora micro scope gap). Do not generalise to full universe.')
    write_csv(track_b_results,
              os.path.join(OUT_DIR, 'feature_family_sweep_subset_micro.csv'))

    # Combined ranked summary
    all_results = track_a_results + track_b_results
    summary_path = os.path.join(OUT_DIR, 'feature_family_sweep_ranked_summary.csv')
    write_csv(all_results, summary_path)

    log('Sweep complete.')
    log(f'Track A candidates: {[r["feature"] for r in track_a_results if r["recommendation"] == "CANDIDATE"]}')
    log(f'Track B candidates: {[r["feature"] for r in track_b_results if r["recommendation"] == "CANDIDATE"]}')

    con.close()

if __name__ == '__main__':
    main()
