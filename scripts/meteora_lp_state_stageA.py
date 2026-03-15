#!/usr/bin/env python3
"""
Meteora LP State Study — Stage A Analysis
Program: meteora_lp_state_stageA
Date: 2026-03-15

Data sources:
- Meteora DLMM API: current pool state (fees, volume, TVL, fee/TVL ratio)
- GeckoTerminal API: historical OHLCV hourly for each pool

LP proxy = fee_proxy - il_proxy - operational_friction
"""

import requests
import json
import time
import math
import random
import statistics
import csv
from datetime import datetime, timezone

# ─── CONFIG ─────────────────────────────────────────────────────────────────
METEORA_BASE = "https://dlmm-api.meteora.ag"
GT_BASE = "https://api.geckoterminal.com/api/v2"
HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

# Universe filters
MIN_FEES_24H = 50.0        # USD
MIN_LIQUIDITY = 5000.0     # USD
SOL_MINT = "So11111111111111111111111111111111111111112"

# LP proxy parameters
OPERATIONAL_FRICTION = 0.0006   # 0.06% per deployment

# Event study parameters
N_BOOTSTRAP = 1000
MIN_SAMPLE_SIZE = 30
TOP1_THRESHOLD = 0.25
TOP3_THRESHOLD = 0.50

# Hypothesis thresholds
H1_FEE_TVL_H1_THRESHOLD = 0.01    # 1% fee yield per hour
H2_TOXIC_MOVE_THRESHOLD = 0.05    # 5% price move = toxic
H3_BASE_FEE_MIN = 2.0             # 2% base fee = launch type
H3_MAX_FEE_MIN = 5.0              # 5% max fee = launch type

# ─── STEP 1: FETCH POOL UNIVERSE ────────────────────────────────────────────
def fetch_pool_universe():
    print("Fetching Meteora DLMM pool universe...")
    r = requests.get(f"{METEORA_BASE}/pair/all", headers=HEADERS, timeout=60)
    r.raise_for_status()
    all_pools = r.json()
    print(f"Total pools: {len(all_pools)}")

    # Filter to active SOL-quote pools
    working = []
    for p in all_pools:
        if p.get('is_blacklisted') or p.get('hide'):
            continue
        # Must have SOL as one of the tokens
        if p.get('mint_x') != SOL_MINT and p.get('mint_y') != SOL_MINT:
            continue
        fees_24h = float(p.get('fees_24h') or 0)
        liquidity = float(p.get('liquidity') or 0)
        if fees_24h < MIN_FEES_24H:
            continue
        if liquidity < MIN_LIQUIDITY:
            continue
        working.append(p)

    print(f"Working universe (active SOL-quote pools): {len(working)}")
    return working

# ─── STEP 2: CLASSIFY POOL TYPES ────────────────────────────────────────────
def classify_pool(p):
    base_fee = float(p.get('base_fee_percentage') or 0)
    max_fee = float(p.get('max_fee_percentage') or 0)
    if base_fee >= H3_BASE_FEE_MIN and max_fee >= H3_MAX_FEE_MIN:
        return 'launch'
    elif base_fee >= 1.0:
        return 'elevated'
    else:
        return 'standard'

# ─── STEP 3: FETCH OHLCV FROM GECKOTERMINAL ─────────────────────────────────
def fetch_ohlcv(pool_address, limit=500):
    """Fetch hourly OHLCV from GeckoTerminal. Returns list of [ts, o, h, l, c, vol_usd]."""
    url = f"{GT_BASE}/networks/solana/pools/{pool_address}/ohlcv/hour"
    try:
        r = requests.get(url, params={"limit": limit, "currency": "usd"},
                         headers=HEADERS, timeout=15)
        if r.status_code == 404:
            return None
        if r.status_code == 429:
            time.sleep(2)
            r = requests.get(url, params={"limit": limit, "currency": "usd"},
                             headers=HEADERS, timeout=15)
        r.raise_for_status()
        d = r.json()
        ohlcv = d['data']['attributes']['ohlcv_list']
        # Sort by timestamp ascending
        ohlcv.sort(key=lambda x: x[0])
        return ohlcv
    except Exception as e:
        return None

# ─── STEP 4: BUILD EVENTS ────────────────────────────────────────────────────
def compute_il_proxy(price_return):
    """IL proxy = 0.5 * r^2 for small moves, capped at 50%."""
    r = abs(price_return)
    il = 0.5 * r * r
    return min(il, 0.50)

def compute_fee_proxy(base_fee_pct, vol_usd, tvl_usd, n_bars):
    """
    Fee proxy for n_bars of holding.
    fee_proxy = base_fee_pct * vol_per_bar / tvl
    Accumulated over n_bars.
    """
    if tvl_usd <= 0:
        return 0.0
    fee_rate = base_fee_pct / 100.0
    fee_per_bar = fee_rate * vol_usd / tvl_usd
    return fee_per_bar * n_bars

def build_events(pool, ohlcv, pool_type, fee_tvl_h1):
    """
    Build LP deployment events from hourly OHLCV bars.
    Each bar is a potential event.
    Returns list of event dicts with LP proxy at each horizon.
    """
    if not ohlcv or len(ohlcv) < 10:
        return []

    base_fee = float(pool.get('base_fee_percentage') or 0)
    tvl_usd = float(pool.get('liquidity') or 0)

    events = []
    n = len(ohlcv)

    for i in range(n - 4):  # Need at least 4 bars ahead for +4h
        bar = ohlcv[i]
        ts, o, h, l, c, vol = bar[0], bar[1], bar[2], bar[3], bar[4], bar[5]

        if o <= 0 or vol <= 0:
            continue

        # H1 state: fee/TVL elevated
        h1_state = (fee_tvl_h1 >= H1_FEE_TVL_H1_THRESHOLD)

        # H2 state: will be determined by forward price move (computed below)

        # H3 state: launch pool
        h3_state = (pool_type == 'launch')

        # Forward returns at +15m (use next bar's close, ~1h resolution, so +1 bar ≈ +1h)
        # Note: We have hourly bars. +15m is not directly available.
        # We use: +1 bar = +1h, +4 bars = +4h
        # +15m is approximated as 25% of the first bar's move (linear interpolation)
        # This is a proxy limitation — documented in data doc.

        # +1h forward (next bar close)
        if i + 1 < n:
            c_1h = ohlcv[i+1][4]
            ret_1h = (c_1h - c) / c if c > 0 else 0.0
        else:
            ret_1h = None

        # +4h forward (4 bars ahead close)
        if i + 4 < n:
            c_4h = ohlcv[i+4][4]
            ret_4h = (c_4h - c) / c if c > 0 else 0.0
        else:
            ret_4h = None

        # +15m approximation: use high/low range of current bar as proxy
        # IL for 15m ≈ 25% of 1h IL (conservative)
        # Fee for 15m = 0.25 * fee for 1h
        if ret_1h is not None:
            ret_15m_proxy = ret_1h * 0.25  # linear interpolation proxy

        # Build LP proxy for each horizon
        lp_proxies = {}

        for horizon, ret, n_bars_fee in [
            ('15m', ret_15m_proxy if ret_1h is not None else None, 0.25),
            ('1h', ret_1h, 1.0),
            ('4h', ret_4h, 4.0),
        ]:
            if ret is None:
                lp_proxies[horizon] = None
                continue

            fee_p = compute_fee_proxy(base_fee, vol, tvl_usd, n_bars_fee)
            il_p = compute_il_proxy(ret)
            net = fee_p - il_p - OPERATIONAL_FRICTION
            lp_proxies[horizon] = {
                'fee_proxy': fee_p,
                'il_proxy': il_p,
                'net_lp_proxy': net,
                'price_return': ret,
            }

        events.append({
            'pool_address': pool['address'],
            'pool_name': pool['name'],
            'pool_type': pool_type,
            'ts': ts,
            'dt': datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
            'open_price': o,
            'vol_usd': vol,
            'tvl_usd': tvl_usd,
            'base_fee_pct': base_fee,
            'fee_tvl_h1': fee_tvl_h1,
            'h1_state': h1_state,
            'h3_state': h3_state,
            'lp_15m': lp_proxies.get('15m'),
            'lp_1h': lp_proxies.get('1h'),
            'lp_4h': lp_proxies.get('4h'),
        })

    return events

# ─── STEP 5: EVENT STUDY ANALYSIS ───────────────────────────────────────────
def winsorize(values, lower=0.05, upper=0.95):
    if not values:
        return []
    lo = sorted(values)[int(len(values) * lower)]
    hi = sorted(values)[int(len(values) * upper)]
    return [max(lo, min(hi, v)) for v in values]

def bootstrap_ci(values, n=1000, stat_fn=statistics.mean, alpha=0.05):
    if len(values) < 2:
        return (None, None)
    samples = []
    for _ in range(n):
        sample = [random.choice(values) for _ in range(len(values))]
        try:
            samples.append(stat_fn(sample))
        except:
            pass
    if not samples:
        return (None, None)
    samples.sort()
    lo_idx = int(len(samples) * alpha / 2)
    hi_idx = int(len(samples) * (1 - alpha / 2))
    return (samples[lo_idx], samples[hi_idx])

def analyze_events(events, horizon_key, condition_key=None):
    """
    Analyze LP proxy values for a set of events at a given horizon.
    condition_key: if set, filter to events where this key is True.
    """
    filtered = events
    if condition_key:
        filtered = [e for e in events if e.get(condition_key)]

    values = []
    for e in filtered:
        lp = e.get(horizon_key)
        if lp is not None and lp.get('net_lp_proxy') is not None:
            values.append(lp['net_lp_proxy'])

    if not values:
        return None

    n = len(values)
    mean_val = statistics.mean(values)
    median_val = statistics.median(values)
    wins = winsorize(values)
    wins_mean = statistics.mean(wins) if wins else None
    pct_pos = sum(1 for v in values if v > 0) / n

    ci_mean = bootstrap_ci(values, n=N_BOOTSTRAP, stat_fn=statistics.mean)
    ci_median = bootstrap_ci(values, n=N_BOOTSTRAP, stat_fn=statistics.median)

    # Concentration
    sorted_vals = sorted(values, reverse=True)
    total = sum(abs(v) for v in values) if values else 1
    top1_share = abs(sorted_vals[0]) / total if total > 0 and sorted_vals else 0
    top3_share = sum(abs(v) for v in sorted_vals[:3]) / total if total > 0 else 0

    # Gate checks
    g1 = n >= MIN_SAMPLE_SIZE
    g2 = wins_mean is not None and wins_mean > 0
    g3 = median_val > 0
    g4 = ci_mean[0] is not None and ci_mean[0] > 0
    g5 = top1_share < TOP1_THRESHOLD
    g6 = top3_share < TOP3_THRESHOLD
    all_pass = all([g1, g2, g3, g4, g5, g6])

    return {
        'n': n,
        'mean': mean_val,
        'median': median_val,
        'wins_mean': wins_mean,
        'pct_pos': pct_pos,
        'ci_mean_lo': ci_mean[0],
        'ci_mean_hi': ci_mean[1],
        'ci_median_lo': ci_median[0],
        'ci_median_hi': ci_median[1],
        'top1_share': top1_share,
        'top3_share': top3_share,
        'g1_n': g1,
        'g2_wins_mean': g2,
        'g3_median': g3,
        'g4_ci_lower': g4,
        'g5_top1': g5,
        'g6_top3': g6,
        'all_pass': all_pass,
    }

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    random.seed(42)

    # Step 1: Fetch universe
    pools = fetch_pool_universe()

    # Limit to top 60 pools by fees_24h for tractability
    pools.sort(key=lambda p: float(p.get('fees_24h') or 0), reverse=True)
    pools = pools[:60]
    print(f"Working with top {len(pools)} pools by fees_24h")

    # Step 2: Classify and fetch OHLCV
    all_events = []
    pool_stats = []
    failed_pools = 0
    
    for i, pool in enumerate(pools):
        pool_type = classify_pool(pool)
        fee_tvl_ratio = pool.get('fee_tvl_ratio', {})
        fee_tvl_h1 = float(fee_tvl_ratio.get('hour_1', 0) if isinstance(fee_tvl_ratio, dict) else 0)
        
        print(f"  [{i+1}/{len(pools)}] {pool['name']} ({pool_type}) fee_tvl_h1={fee_tvl_h1:.4f} fees24h=${float(pool.get('fees_24h',0)):.0f}")
        
        ohlcv = fetch_ohlcv(pool['address'], limit=500)
        time.sleep(0.3)  # Rate limit
        
        if not ohlcv or len(ohlcv) < 10:
            print(f"    -> No OHLCV data")
            failed_pools += 1
            continue
        
        n_bars = len(ohlcv)
        oldest_ts = ohlcv[0][0]
        newest_ts = ohlcv[-1][0]
        days_coverage = (newest_ts - oldest_ts) / 86400
        
        pool_stats.append({
            'address': pool['address'],
            'name': pool['name'],
            'pool_type': pool_type,
            'n_bars': n_bars,
            'days_coverage': days_coverage,
            'oldest': datetime.fromtimestamp(oldest_ts, tz=timezone.utc).isoformat(),
            'newest': datetime.fromtimestamp(newest_ts, tz=timezone.utc).isoformat(),
            'fees_24h': float(pool.get('fees_24h') or 0),
            'liquidity': float(pool.get('liquidity') or 0),
            'fee_tvl_h1': fee_tvl_h1,
            'base_fee_pct': float(pool.get('base_fee_percentage') or 0),
        })
        
        events = build_events(pool, ohlcv, pool_type, fee_tvl_h1)
        all_events.extend(events)
        print(f"    -> {n_bars} bars ({days_coverage:.1f} days), {len(events)} events")

    print(f"\nTotal events: {len(all_events)}")
    print(f"Failed pools (no OHLCV): {failed_pools}")

    # Save pool stats
    with open('/home/ubuntu/meteora_pool_stats.json', 'w') as f:
        json.dump(pool_stats, f, indent=2)

    # Step 3: Run event study
    print("\n=== EVENT STUDY RESULTS ===")
    
    results = []
    
    # H1: Elevated fee/TVL state
    print("\nH1 — Volatility-Fee State (fee_tvl_h1 >= 0.01):")
    for horizon in ['lp_15m', 'lp_1h', 'lp_4h']:
        r = analyze_events(all_events, horizon, condition_key='h1_state')
        label = horizon.replace('lp_', '+')
        if r:
            print(f"  {label}: N={r['n']} wins_mean={r['wins_mean']:.4f} median={r['median']:.4f} "
                  f"pct_pos={r['pct_pos']:.1%} CI_lo={r['ci_mean_lo']:.4f} PASS={r['all_pass']}")
            results.append({'hypothesis': 'H1', 'horizon': label, **r})
        else:
            print(f"  {label}: NO DATA")
            results.append({'hypothesis': 'H1', 'horizon': label, 'n': 0, 'all_pass': False})

    # H1 null: All events (no state filter)
    print("\nH1 NULL — All events (no state filter):")
    for horizon in ['lp_15m', 'lp_1h', 'lp_4h']:
        r = analyze_events(all_events, horizon, condition_key=None)
        label = horizon.replace('lp_', '+')
        if r:
            print(f"  {label}: N={r['n']} wins_mean={r['wins_mean']:.4f} median={r['median']:.4f} "
                  f"pct_pos={r['pct_pos']:.1%} CI_lo={r['ci_mean_lo']:.4f} PASS={r['all_pass']}")
            results.append({'hypothesis': 'H1_null', 'horizon': label, **r})

    # H2: Toxic flow filter — events where |price_return_1h| > 5%
    print("\nH2 — Toxic Flow Filter (|ret_1h| > 5%):")
    toxic_events = []
    non_toxic_events = []
    for e in all_events:
        lp_1h = e.get('lp_1h')
        if lp_1h is not None:
            ret = abs(lp_1h.get('price_return', 0))
            if ret > H2_TOXIC_MOVE_THRESHOLD:
                toxic_events.append(e)
            else:
                non_toxic_events.append(e)
    
    print(f"  Toxic events (|ret_1h| > 5%): {len(toxic_events)}")
    print(f"  Non-toxic events: {len(non_toxic_events)}")
    
    for label, evts in [('toxic', toxic_events), ('non_toxic', non_toxic_events)]:
        for horizon in ['lp_15m', 'lp_1h', 'lp_4h']:
            r = analyze_events(evts, horizon)
            h_label = horizon.replace('lp_', '+')
            if r:
                print(f"  {label} {h_label}: N={r['n']} wins_mean={r['wins_mean']:.4f} median={r['median']:.4f} "
                      f"pct_pos={r['pct_pos']:.1%} PASS={r['all_pass']}")
                results.append({'hypothesis': f'H2_{label}', 'horizon': h_label, **r})

    # H3: Launch pools
    print("\nH3 — Launch/Bootstrap Toxicity (base_fee >= 2%, max_fee >= 5%):")
    launch_events = [e for e in all_events if e.get('h3_state')]
    standard_events = [e for e in all_events if not e.get('h3_state')]
    print(f"  Launch events: {len(launch_events)}")
    print(f"  Standard events: {len(standard_events)}")
    
    for label, evts in [('launch', launch_events), ('standard', standard_events)]:
        for horizon in ['lp_15m', 'lp_1h', 'lp_4h']:
            r = analyze_events(evts, horizon)
            h_label = horizon.replace('lp_', '+')
            if r:
                print(f"  {label} {h_label}: N={r['n']} wins_mean={r['wins_mean']:.4f} median={r['median']:.4f} "
                      f"pct_pos={r['pct_pos']:.1%} PASS={r['all_pass']}")
                results.append({'hypothesis': f'H3_{label}', 'horizon': h_label, **r})

    # Save results
    with open('/home/ubuntu/meteora_stageA_results.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Save results CSV
    if results:
        keys = ['hypothesis', 'horizon', 'n', 'mean', 'median', 'wins_mean', 'pct_pos',
                'ci_mean_lo', 'ci_mean_hi', 'ci_median_lo', 'ci_median_hi',
                'top1_share', 'top3_share', 'g1_n', 'g2_wins_mean', 'g3_median',
                'g4_ci_lower', 'g5_top1', 'g6_top3', 'all_pass']
        with open('/home/ubuntu/meteora_stageA_results.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(results)

    # Summary
    passing = [r for r in results if r.get('all_pass')]
    print(f"\n=== SUMMARY ===")
    print(f"Total combinations tested: {len(results)}")
    print(f"Combinations passing all gates: {len(passing)}")
    if passing:
        for p in passing:
            print(f"  PASS: {p['hypothesis']} {p['horizon']} N={p['n']} wins_mean={p['wins_mean']:.4f}")
        verdict = "GO"
    else:
        verdict = "NO-GO"
    print(f"VERDICT: {verdict}")

    # Save summary stats
    summary = {
        'total_pools_fetched': len(pool_stats),
        'failed_pools': failed_pools,
        'total_events': len(all_events),
        'h1_elevated_events': sum(1 for e in all_events if e.get('h1_state')),
        'h2_toxic_events': len(toxic_events),
        'h2_non_toxic_events': len(non_toxic_events),
        'h3_launch_events': len(launch_events),
        'h3_standard_events': len(standard_events),
        'combinations_tested': len(results),
        'combinations_passing': len(passing),
        'verdict': verdict,
    }
    with open('/home/ubuntu/meteora_stageA_summary_stats.json', 'w') as f:
        json.dump(summary, f, indent=2)

    print("\nDone. Output files:")
    print("  /home/ubuntu/meteora_pool_stats.json")
    print("  /home/ubuntu/meteora_stageA_results.json")
    print("  /home/ubuntu/meteora_stageA_results.csv")
    print("  /home/ubuntu/meteora_stageA_summary_stats.json")

if __name__ == '__main__':
    main()
