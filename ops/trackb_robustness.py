#!/usr/bin/env python3
"""
trackb_robustness.py — Final robustness check for Track B candidates.

Candidates: r_m5, vol_accel_m5_vs_h1
For each candidate's best bucket:
  - n, mean gross, mean net-proxy, median gross, median net-proxy
  - bootstrap 95% CI for mean net-proxy
  - bootstrap 95% CI for median net-proxy
  - top contributor share, top 3 contributor share
  - venue split: PumpSwap-only, Raydium-only
"""

import sqlite3
import random
import math
import os
from datetime import datetime, timezone

DB      = os.environ.get('SOLANA_TRADER_DB', '/root/solana_trader/data/solana_trader.db')
OUT_DIR = '/root/solana_trader/reports/synthesis'
OUT_MD  = os.path.join(OUT_DIR, 'trackb_robustness_report.md')
N_BOOT  = 10000
SEED    = 42

random.seed(SEED)

def log(msg):
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    print(f'{ts} [trackb_robustness] {msg}', flush=True)

def mean(vals):
    v = [x for x in vals if x is not None]
    return sum(v) / len(v) if v else None

def median(vals):
    v = sorted(x for x in vals if x is not None)
    n = len(v)
    if n == 0: return None
    return v[n // 2] if n % 2 == 1 else (v[n // 2 - 1] + v[n // 2]) / 2

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

def fmt(v, pct=True, decimals=3):
    if v is None: return 'N/A'
    if pct:
        return f'{v*100:+.{decimals}f}%'
    return f'{v:.{decimals}f}'

def best_bucket_rows(rows, feat_col, n_buckets=3):
    """Return rows in the top tercile by feat_col."""
    valid = [r for r in rows if r[feat_col] is not None]
    valid.sort(key=lambda r: r[feat_col])
    size = len(valid) // n_buckets
    # top tercile
    top = valid[2 * size:]
    return top

def analyze_candidate(rows, feat_col, label_gross='r_forward_5m', label_net='net_proxy'):
    log(f'Analyzing {feat_col}...')
    bucket = best_bucket_rows(rows, feat_col)
    gross_vals = [r[label_gross] for r in bucket if r[label_gross] is not None]
    net_vals   = [r[label_net]   for r in bucket if r[label_net]   is not None]

    n = len(bucket)
    mean_gross  = mean(gross_vals)
    mean_net    = mean(net_vals)
    med_gross   = median(gross_vals)
    med_net     = median(net_vals)

    ci_mean_lo, ci_mean_hi = bootstrap_ci(net_vals, mean)
    ci_med_lo,  ci_med_hi  = bootstrap_ci(net_vals, median)

    top1_share = top_contributor_share(net_vals, k=1)
    top3_share = top_contributor_share(net_vals, k=3)

    # Venue split
    venue_results = {}
    for venue_label, venue_filter in [
        ('PumpSwap', lambda r: r.get('pool_type') == 'PumpSwap' or
                               (r.get('pumpfun_origin') == 1 and r.get('pool_type') not in ('Raydium', 'Orca', 'Meteora'))),
        ('Raydium',  lambda r: r.get('pool_type') == 'Raydium'),
    ]:
        v_rows = [r for r in bucket if venue_filter(r)]
        v_net  = [r[label_net]   for r in v_rows if r[label_net]   is not None]
        v_gross= [r[label_gross] for r in v_rows if r[label_gross] is not None]
        if len(v_net) >= 5:
            vci_lo, vci_hi = bootstrap_ci(v_net, mean)
            venue_results[venue_label] = {
                'n': len(v_rows),
                'mean_gross': mean(v_gross),
                'mean_net':   mean(v_net),
                'med_gross':  median(v_gross),
                'med_net':    median(v_net),
                'ci_mean_lo': vci_lo,
                'ci_mean_hi': vci_hi,
                'top1_share': top_contributor_share(v_net, k=1),
                'top3_share': top_contributor_share(v_net, k=3),
            }
        else:
            venue_results[venue_label] = {'n': len(v_rows), 'note': 'insufficient sample (n<5)'}

    # Feat range of best bucket
    feat_vals = [r[feat_col] for r in bucket if r[feat_col] is not None]
    feat_min = min(feat_vals) if feat_vals else None
    feat_max = max(feat_vals) if feat_vals else None

    return {
        'feature': feat_col,
        'n': n,
        'feat_min': feat_min,
        'feat_max': feat_max,
        'mean_gross': mean_gross,
        'mean_net': mean_net,
        'med_gross': med_gross,
        'med_net': med_net,
        'ci_mean_lo': ci_mean_lo,
        'ci_mean_hi': ci_mean_hi,
        'ci_med_lo': ci_med_lo,
        'ci_med_hi': ci_med_hi,
        'top1_share': top1_share,
        'top3_share': top3_share,
        'venue': venue_results,
    }

def write_report(results):
    os.makedirs(OUT_DIR, exist_ok=True)
    lines = []
    lines.append('# Track B Robustness Report — Final (96 fires)')
    lines.append('')
    lines.append(f'Generated: {datetime.now(timezone.utc).isoformat()}')
    lines.append('')
    lines.append('> **SUBSET-ONLY**: Track B results reflect non-random missingness.')
    lines.append('> Missing rows = Orca/Meteora micro scope gap (~21-29%).')
    lines.append('> Do NOT generalise to full universe.')
    lines.append('')
    lines.append('## Net-Proxy Formula')
    lines.append('')
    lines.append('```')
    lines.append('net_proxy = r_forward_5m - round_trip_pct')
    lines.append('```')
    lines.append('')
    lines.append('Bootstrap: 10,000 resamples, 95% CI, seed=42.')
    lines.append('')

    for r in results:
        lines.append(f"## {r['feature']} — Best Bucket (Top Tercile)")
        lines.append('')
        lines.append(f"Feature range in bucket: [{fmt(r['feat_min'], pct=False)} → {fmt(r['feat_max'], pct=False)}]")
        lines.append('')
        lines.append('| Metric | Value |')
        lines.append('|--------|-------|')
        lines.append(f"| n | {r['n']} |")
        lines.append(f"| Mean gross | {fmt(r['mean_gross'])} |")
        lines.append(f"| Mean net-proxy | {fmt(r['mean_net'])} |")
        lines.append(f"| Median gross | {fmt(r['med_gross'])} |")
        lines.append(f"| Median net-proxy | {fmt(r['med_net'])} |")
        lines.append(f"| Bootstrap 95% CI — mean net | [{fmt(r['ci_mean_lo'])} → {fmt(r['ci_mean_hi'])}] |")
        lines.append(f"| Bootstrap 95% CI — median net | [{fmt(r['ci_med_lo'])} → {fmt(r['ci_med_hi'])}] |")
        lines.append(f"| Top-1 contributor share | {fmt(r['top1_share'], pct=False)} |")
        lines.append(f"| Top-3 contributor share | {fmt(r['top3_share'], pct=False)} |")
        lines.append('')

        lines.append('### Venue Split')
        lines.append('')
        for venue, vr in r['venue'].items():
            lines.append(f'**{venue}** (n={vr["n"]})')
            if 'note' in vr:
                lines.append(f'  {vr["note"]}')
            else:
                lines.append(f'| Metric | Value |')
                lines.append(f'|--------|-------|')
                lines.append(f"| Mean gross | {fmt(vr['mean_gross'])} |")
                lines.append(f"| Mean net-proxy | {fmt(vr['mean_net'])} |")
                lines.append(f"| Median gross | {fmt(vr['med_gross'])} |")
                lines.append(f"| Median net-proxy | {fmt(vr['med_net'])} |")
                lines.append(f"| Bootstrap 95% CI — mean net | [{fmt(vr['ci_mean_lo'])} → {fmt(vr['ci_mean_hi'])}] |")
                lines.append(f"| Top-1 contributor share | {fmt(vr['top1_share'], pct=False)} |")
                lines.append(f"| Top-3 contributor share | {fmt(vr['top3_share'], pct=False)} |")
            lines.append('')

    # Decision
    lines.append('## Final Decision')
    lines.append('')
    approved = []
    for r in results:
        mean_net_pos = r['mean_net'] is not None and r['mean_net'] > 0
        med_net_pos  = r['med_net']  is not None and r['med_net']  > 0
        ci_lo_pos    = r['ci_mean_lo'] is not None and r['ci_mean_lo'] > 0
        conc_ok      = r['top1_share'] is not None and r['top1_share'] < 0.30
        if mean_net_pos and conc_ok:
            approved.append((r['feature'], mean_net_pos, med_net_pos, ci_lo_pos, conc_ok))

    if approved:
        lines.append('**CANDIDATES PASSED ROBUSTNESS GATE:**')
        for feat, mn, mdn, ci, conc in approved:
            lines.append(f'  - {feat}: mean_net>0={mn}, median_net>0={mdn}, CI_lo>0={ci}, conc_ok={conc}')
        lines.append('')
        lines.append('However: median net-proxy must also be > 0 for a YES recommendation.')
        any_med_pos = any(mdn for _, _, mdn, _, _ in approved)
        if any_med_pos:
            lines.append('')
            lines.append('**RECOMMENDATION: CONSIDER NEW LIVE OBSERVER**')
            lines.append('At least one candidate has positive mean AND positive median net-proxy.')
        else:
            lines.append('')
            lines.append('**RECOMMENDATION: NO NEW LIVE OBSERVER**')
            lines.append('Mean net-proxy is positive but median is zero or negative.')
            lines.append('Effect is mean-driven by tail events. Not robust enough for live deployment.')
    else:
        lines.append('**RECOMMENDATION: NO NEW LIVE OBSERVER**')
        lines.append('No candidate has positive mean net-proxy with acceptable concentration.')

    with open(OUT_MD, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    log(f'Written: {OUT_MD}')

def main():
    con = sqlite3.connect(DB, timeout=30)
    con.row_factory = sqlite3.Row

    rows = con.execute("""
        SELECT ft.*, lbl.r_forward_5m, lbl.label_quality, lbl.label_source
        FROM feature_tape_v1 ft
        JOIN feature_tape_v1_labels lbl
          ON lbl.fire_id = ft.fire_id AND lbl.candidate_mint = ft.candidate_mint
        WHERE lbl.label_quality NOT IN ('missing', 'missing_disk_gap')
          AND lbl.r_forward_5m IS NOT NULL
          AND ft.round_trip_pct IS NOT NULL
    """).fetchall()

    rows_dict = []
    for r in rows:
        d = dict(r)
        d['net_proxy'] = d['r_forward_5m'] - d['round_trip_pct'] if (d['r_forward_5m'] is not None and d['round_trip_pct'] is not None) else None
        rows_dict.append(d)

    log(f'Rows loaded: {len(rows_dict)}')
    con.close()

    results = []
    for feat in ['r_m5', 'vol_accel_m5_vs_h1']:
        res = analyze_candidate(rows_dict, feat)
        results.append(res)
        log(f'  {feat}: n={res["n"]}  mean_net={fmt(res["mean_net"])}  med_net={fmt(res["med_net"])}  CI=[{fmt(res["ci_mean_lo"])} → {fmt(res["ci_mean_hi"])}]')

    write_report(results)

if __name__ == '__main__':
    main()
