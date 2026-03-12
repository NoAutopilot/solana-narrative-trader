#!/usr/bin/env python3
"""
horizon_sweep.py — Feature-family sweep at +15m and +30m horizons.

Uses existing feature_tape_v1_labels columns: r_forward_15m, r_forward_30m.
Net-proxy formula: r_forward_Xm - round_trip_pct  (same cost as +5m sweep).
No new collection logic.
"""

import sqlite3
import random
import os
from datetime import datetime, timezone

DB      = os.environ.get('SOLANA_TRADER_DB', '/root/solana_trader/data/solana_trader.db')
OUT_DIR = '/root/solana_trader/reports/synthesis'
N_BOOT  = 10000
SEED    = 42
random.seed(SEED)

TRACK_A = [
    'median_pool_r_m5', 'breadth_positive_pct', 'impact_buy_pct',
    'impact_sell_pct', 'round_trip_pct', 'liquidity_usd',
    'pool_dispersion_r_m5', 'vol_h1', 'age_hours', 'jup_vs_cpamm_diff_pct',
]
TRACK_B = [
    'r_m5', 'vol_accel_m5_vs_h1', 'txn_accel_m5_vs_h1',
    'liq_change_pct', 'avg_trade_usd_m5', 'buy_sell_ratio_m5', 'signed_flow_m5',
]

def log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f'{ts} [horizon_sweep] {msg}', flush=True)

def winsorize(vals, pct=0.01):
    """Winsorize at pct and (1-pct) quantiles."""
    v = sorted(x for x in vals if x is not None)
    if len(v) < 3: return v
    lo_idx = max(0, int(len(v) * pct))
    hi_idx = min(len(v) - 1, int(len(v) * (1 - pct)))
    lo_val = v[lo_idx]
    hi_val = v[hi_idx]
    return [max(lo_val, min(hi_val, x)) for x in v]

def mean(vals):
    v = [x for x in vals if x is not None]
    return sum(v) / len(v) if v else None

def median(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if n == 0: return None
    return v[n // 2] if n % 2 == 1 else (v[n // 2 - 1] + v[n // 2]) / 2

def pct_positive(vals):
    v = [x for x in vals if x is not None]
    if not v: return None
    return sum(1 for x in v if x > 0) / len(v)

def bootstrap_ci(vals, stat_fn, n_boot=N_BOOT, alpha=0.05):
    v = [x for x in vals if x is not None]
    if len(v) < 5:
        return None, None
    boot_stats = []
    for _ in range(n_boot):
        sample = [random.choice(v) for _ in range(len(v))]
        s = stat_fn(sample)
        if s is not None:
            boot_stats.append(s)
    boot_stats.sort()
    lo = boot_stats[int(alpha / 2 * len(boot_stats))]
    hi = boot_stats[int((1 - alpha / 2) * len(boot_stats))]
    return lo, hi

def top_contributor_share(vals, k=1):
    v = [x for x in vals if x is not None]
    if not v: return None
    total_abs = sum(abs(x) for x in v)
    if total_abs == 0: return 0.0
    top_k = sorted([abs(x) for x in v], reverse=True)[:k]
    return sum(top_k) / total_abs

def outlier_count(vals, z=3.0):
    v = [x for x in vals if x is not None]
    if len(v) < 3: return 0
    m = mean(v)
    s = (sum((x - m) ** 2 for x in v) / len(v)) ** 0.5
    if s == 0: return 0
    return sum(1 for x in v if abs(x - m) > z * s)

def fmt(v, pct=True, decimals=3):
    if v is None: return 'N/A'
    if pct:
        return f'{v*100:+.{decimals}f}%'
    return f'{v:.{decimals}f}'

def tercile_split(rows, feat_col):
    valid = [r for r in rows if r.get(feat_col) is not None]
    valid.sort(key=lambda r: r[feat_col])
    n = len(valid)
    if n < 3: return [], [], []
    s = n // 3
    return valid[:s], valid[s:2*s], valid[2*s:]

def analyze_feature(rows, feat_col, label_col, net_col, total_rows, winsor=False):
    valid = [r for r in rows if r.get(feat_col) is not None and r.get(label_col) is not None and r.get(net_col) is not None]
    coverage = len(valid) / total_rows if total_rows else 0

    bot, mid, top = tercile_split(valid, feat_col)
    # best bucket = highest mean gross
    buckets = [(bot, 'bot'), (mid, 'mid'), (top, 'top')]
    best_bucket, best_label = max(buckets, key=lambda b: mean([r[label_col] for r in b[0]]) or -999)

    gross_vals_raw = [r[label_col] for r in best_bucket]
    net_vals_raw   = [r[net_col]   for r in best_bucket]

    if winsor:
        gross_vals = winsorize(gross_vals_raw)
        net_vals   = winsorize(net_vals_raw)
    else:
        gross_vals = gross_vals_raw
        net_vals   = net_vals_raw

    mean_gross   = mean(gross_vals)
    mean_net     = mean(net_vals)
    med_gross    = median(gross_vals)
    med_net      = median(net_vals)
    pct_pos_net  = pct_positive(net_vals)
    ci_mean_lo, ci_mean_hi = bootstrap_ci(net_vals, mean)
    ci_med_lo,  ci_med_hi  = bootstrap_ci(net_vals, median)
    out_count    = outlier_count(net_vals)
    top1_share   = top_contributor_share(net_vals, k=1)
    top3_share   = top_contributor_share(net_vals, k=3)

    # tercile diff (top - bot gross mean)
    bot_mean = mean([r[label_col] for r in bot])
    top_mean = mean([r[label_col] for r in top])
    tercile_diff = (top_mean - bot_mean) if (top_mean is not None and bot_mean is not None) else None

    # recommendation
    rec = 'CANDIDATE' if (
        mean_net is not None and mean_net > 0 and
        med_net  is not None and med_net  > 0 and
        ci_mean_lo is not None and ci_mean_lo > 0 and
        top1_share is not None and top1_share < 0.30
    ) else 'SKIP'

    return {
        'feature': feat_col,
        'coverage': coverage,
        'n_valid': len(valid),
        'best_bucket': best_label,
        'mean_gross': mean_gross,
        'mean_net': mean_net,
        'med_gross': med_gross,
        'med_net': med_net,
        'pct_pos_net': pct_pos_net,
        'tercile_diff': tercile_diff,
        'ci_mean_lo': ci_mean_lo,
        'ci_mean_hi': ci_mean_hi,
        'ci_med_lo': ci_med_lo,
        'ci_med_hi': ci_med_hi,
        'outlier_count': out_count,
        'top1_share': top1_share,
        'top3_share': top3_share,
        'rec': rec,
    }

def write_md_report(horizon_label, track_a_results, track_b_results, total_rows_a, total_rows_b, out_path):
    lines = []
    lines.append(f'# Feature Family Sweep — {horizon_label} Horizon (96 fires)')
    lines.append('')
    lines.append(f'Generated: {datetime.now(timezone.utc).isoformat()}')
    lines.append('')
    lines.append('## Net-Proxy Formula')
    lines.append('')
    lines.append('```')
    lines.append(f'net_proxy = r_forward_{horizon_label.lower().replace("+","")} - round_trip_pct')
    lines.append('```')
    lines.append('')
    lines.append('`round_trip_pct` = impact_buy_pct + impact_sell_pct (CPAMM-based, same cost as +5m sweep).')
    lines.append('Bootstrap: 10,000 resamples, 95% CI, seed=42.')
    lines.append('')

    for track_label, results, total_rows, subset_note in [
        ('Track A — Full-Sample Features', track_a_results, total_rows_a, False),
        ('Track B — Micro-Derived Features (SUBSET-ONLY)', track_b_results, total_rows_b, True),
    ]:
        lines.append(f'## {track_label}')
        lines.append('')
        if subset_note:
            lines.append('> **SUBSET-ONLY**: Non-random missingness. Orca/Meteora pools excluded (~21-29% missing). Do NOT generalise to full universe.')
            lines.append('')

        lines.append('| Feature | Coverage | Mean Gross | Mean Net | Med Gross | Med Net | %Pos Net | Tercile Diff | CI Mean Net | CI Med Net | Outliers | Top-1 | Top-3 | Rec |')
        lines.append('|---------|----------|------------|----------|-----------|---------|----------|--------------|-------------|------------|----------|-------|-------|-----|')
        for r in results:
            ci_str  = f"[{fmt(r['ci_mean_lo'])} → {fmt(r['ci_mean_hi'])}]"
            cim_str = f"[{fmt(r['ci_med_lo'])} → {fmt(r['ci_med_hi'])}]"
            lines.append(
                f"| {r['feature']} | {r['coverage']*100:.1f}% | {fmt(r['mean_gross'])} | {fmt(r['mean_net'])} | "
                f"{fmt(r['med_gross'])} | {fmt(r['med_net'])} | {fmt(r['pct_pos_net'], pct=True, decimals=1) if r['pct_pos_net'] is not None else 'N/A'} | "
                f"{fmt(r['tercile_diff'])} | {ci_str} | {cim_str} | "
                f"{r['outlier_count']} | {fmt(r['top1_share'], pct=False)} | {fmt(r['top3_share'], pct=False)} | {r['rec']} |"
            )
        lines.append('')

        candidates = [r for r in results if r['rec'] == 'CANDIDATE']
        if candidates:
            lines.append(f'**CANDIDATES**: {", ".join(r["feature"] for r in candidates)}')
        else:
            lines.append('**No candidates passed all gates.**')
        lines.append('')

    # Decision
    all_results = track_a_results + track_b_results
    candidates = [r for r in all_results if r['rec'] == 'CANDIDATE']
    lines.append('## Decision')
    lines.append('')
    if candidates:
        lines.append(f'**CANDIDATE(S) FOUND**: {", ".join(r["feature"] for r in candidates)}')
        lines.append('')
        lines.append('At least one feature passes all gates (positive mean net, positive median net, CI lower > 0, acceptable concentration).')
        lines.append('Recommend further evaluation for new live observer.')
    else:
        lines.append('**NO NEW LIVE OBSERVER — CURRENT PUBLIC-DATA LONG-ONLY SELECTION LINE FAILED ACROSS HORIZONS**')
        lines.append('')
        lines.append('No feature passes all gates at this horizon.')

    with open(out_path, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    log(f'Written: {out_path}')

def write_csv(results, out_path):
    import csv
    fields = ['feature', 'coverage', 'n_valid', 'best_bucket', 'mean_gross', 'mean_net',
              'med_gross', 'med_net', 'pct_pos_net', 'tercile_diff',
              'ci_mean_lo', 'ci_mean_hi', 'ci_med_lo', 'ci_med_hi',
              'outlier_count', 'top1_share', 'top3_share', 'rec']
    with open(out_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(results)
    log(f'Written: {out_path}')

def main():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row

    # Load joined dataset
    rows_raw = con.execute("""
        SELECT ft.*, lbl.r_forward_5m, lbl.r_forward_15m, lbl.r_forward_30m,
               lbl.label_quality, lbl.label_source
        FROM feature_tape_v1 ft
        JOIN feature_tape_v1_labels lbl
          ON lbl.fire_id = ft.fire_id AND lbl.candidate_mint = ft.candidate_mint
        WHERE lbl.label_quality NOT IN ('missing', 'missing_disk_gap')
          AND ft.round_trip_pct IS NOT NULL
    """).fetchall()
    con.close()

    rows = []
    for r in rows_raw:
        d = dict(r)
        d['net_proxy_5m']  = (d['r_forward_5m']  - d['round_trip_pct']) if (d['r_forward_5m']  is not None and d['round_trip_pct'] is not None) else None
        d['net_proxy_15m'] = (d['r_forward_15m'] - d['round_trip_pct']) if (d['r_forward_15m'] is not None and d['round_trip_pct'] is not None) else None
        d['net_proxy_30m'] = (d['r_forward_30m'] - d['round_trip_pct']) if (d['r_forward_30m'] is not None and d['round_trip_pct'] is not None) else None
        rows.append(d)

    total = len(rows)
    log(f'Rows loaded: {total}')

    os.makedirs(OUT_DIR, exist_ok=True)

    for horizon, label_col, net_col, out_md, out_csv in [
        ('+15m', 'r_forward_15m', 'net_proxy_15m',
         f'{OUT_DIR}/feature_family_sweep_15m.md',
         f'{OUT_DIR}/feature_family_sweep_15m.csv'),
        ('+30m', 'r_forward_30m', 'net_proxy_30m',
         f'{OUT_DIR}/feature_family_sweep_30m.md',
         f'{OUT_DIR}/feature_family_sweep_30m.csv'),
    ]:
        log(f'Running {horizon} sweep...')
        # For coverage denominator, use rows that have this label
        rows_h = [r for r in rows if r.get(label_col) is not None]
        total_h = len(rows_h)
        log(f'  {horizon} rows with label: {total_h}')

        track_a = []
        for feat in TRACK_A:
            res = analyze_feature(rows_h, feat, label_col, net_col, total_h)
            res['track'] = 'A'
            track_a.append(res)
            log(f'  {horizon} A {feat}: cov={res["coverage"]*100:.1f}%  mean_net={fmt(res["mean_net"])}  med_net={fmt(res["med_net"])}  rec={res["rec"]}')

        track_b = []
        for feat in TRACK_B:
            res = analyze_feature(rows_h, feat, label_col, net_col, total_h)
            res['track'] = 'B'
            track_b.append(res)
            log(f'  {horizon} B {feat}: cov={res["coverage"]*100:.1f}%  mean_net={fmt(res["mean_net"])}  med_net={fmt(res["med_net"])}  rec={res["rec"]}')

        write_md_report(horizon, track_a, track_b, total_h, total_h, out_md)
        write_csv(track_a + track_b, out_csv)

        # Also run winsorized version
        log(f'Running {horizon} sweep (winsorized p1/p99)...')
        track_a_w = []
        for feat in TRACK_A:
            res = analyze_feature(rows_h, feat, label_col, net_col, total_h, winsor=True)
            res['track'] = 'A'
            track_a_w.append(res)
            log(f'  {horizon} A(w) {feat}: mean_net={fmt(res["mean_net"])}  med_net={fmt(res["med_net"])}  rec={res["rec"]}')
        track_b_w = []
        for feat in TRACK_B:
            res = analyze_feature(rows_h, feat, label_col, net_col, total_h, winsor=True)
            res['track'] = 'B'
            track_b_w.append(res)
            log(f'  {horizon} B(w) {feat}: mean_net={fmt(res["mean_net"])}  med_net={fmt(res["med_net"])}  rec={res["rec"]}')
        out_md_w  = out_md.replace('.md', '_winsorized.md')
        out_csv_w = out_csv.replace('.csv', '_winsorized.csv')
        write_md_report(f'{horizon} (Winsorized p1/p99)', track_a_w, track_b_w, total_h, total_h, out_md_w)
        write_csv(track_a_w + track_b_w, out_csv_w)

    log('Horizon sweep complete.')

if __name__ == '__main__':
    main()
