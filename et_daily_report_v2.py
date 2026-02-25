#!/usr/bin/env python3
"""
et_daily_report_v2.py — Daily shadow-live evaluation report with LIVE_CANARY_READY gate.

Column mapping (actual DB schema):
  shadow_trades: exited_at (not closed_at)
  coverage_audit: eligible_count, unique_mints_seen
  impact_gate_log: round_trip_pct_04 (for 0.04 SOL), evaluated_at
"""

import sys
import sqlite3
import argparse
import subprocess
from datetime import datetime, timezone, timedelta

sys.path.insert(0, '/root/solana_trader')
try:
    from config.config import DB_PATH
except Exception:
    DB_PATH = "/root/solana_trader/paper_trader.db"

SERVICES = ["et_universe_scanner", "et_microstructure", "et_shadow_trader", "pf_graduation_stream"]


def count_instances(name: str) -> int:
    result = subprocess.run(["pgrep", "-c", "-f", f"{name}.py"], capture_output=True, text=True)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def singleton_status():
    results = {n: count_instances(n) for n in SERVICES}
    all_ok = all(v == 1 for v in results.values())
    return all_ok, results


def run_report(hours: int = 24):
    conn = sqlite3.connect(DB_PATH)
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    print("=" * 70)
    print(f"EXISTING TOKENS LANE — DAILY SHADOW REPORT")
    print(f"Window: last {hours}h | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Universe tag: WATCHLIST_LANE_NOT_FULL_UNIVERSE")
    print("=" * 70)

    # ── SINGLETON STATUS ───────────────────────────────────────────────────────
    print("\nSINGLETON STATUS")
    sing_ok, sing_counts = singleton_status()
    for name, cnt in sing_counts.items():
        flag = "OK" if cnt == 1 else f"VIOLATION ({cnt} instances)"
        print(f"  {name:<30} {flag}")

    # ── UNIVERSE COVERAGE ──────────────────────────────────────────────────────
    print("\nUNIVERSE COVERAGE")
    try:
        cov = conn.execute("""
            SELECT COUNT(*) as scans,
                   AVG(unique_mints_seen) as avg_mints,
                   AVG(eligible_count) as avg_eligible,
                   scan_method,
                   MAX(scan_at) as last_scan
            FROM coverage_audit
            WHERE scan_at >= ?
        """, (since,)).fetchone()
        if cov and cov[0] > 0:
            print(f"  Scans in window:       {cov[0]}")
            print(f"  Avg mints seen/scan:   {(cov[1] or 0):.1f}")
            print(f"  Avg eligible/scan:     {(cov[2] or 0):.1f}")
            print(f"  Scan method:           {cov[3]}")
            print(f"  Last scan:             {cov[4]}")
        else:
            print("  No coverage_audit data in window")
        uni = conn.execute("""
            SELECT COUNT(DISTINCT mint_address) as n_mints,
                   SUM(cpamm_valid_flag) as n_cpamm
            FROM universe_snapshot
            WHERE snapshot_at >= ?
        """, (since,)).fetchone()
        if uni:
            print(f"  Unique mints (window): {uni[0]}")
            print(f"  CPAMM valid rows:      {uni[1]}")
    except Exception as e:
        print(f"  coverage error: {e}")

    # ── SHADOW TRADES ──────────────────────────────────────────────────────────
    print("\nSHADOW TRADES — ALL STRATEGIES")
    n = 0
    try:
        summary = conn.execute("""
            SELECT COUNT(*) as n,
                   AVG(shadow_pnl_pct) as avg_pnl,
                   AVG(shadow_pnl_pct_fee025) as avg_fee025,
                   AVG(shadow_pnl_pct_fee060) as avg_fee060,
                   AVG(shadow_pnl_pct_fee100) as avg_fee100,
                   SUM(CASE WHEN shadow_pnl_pct > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as win_rate,
                   MIN(shadow_pnl_pct) as worst,
                   MAX(shadow_pnl_pct) as best
            FROM shadow_trades
            WHERE exited_at >= ? AND status = 'closed'
        """, (since,)).fetchone()
        if summary and summary[0] > 0:
            n = summary[0]
            print(f"  Total trades:          {n}")
            print(f"  Win rate:              {summary[5]*100:.1f}%")
            print(f"  Avg PnL (CPAMM base):  {summary[1]*100:+.3f}%")
            print(f"  Avg PnL (fee 0.25%):   {(summary[2] or 0)*100:+.3f}%")
            print(f"  Avg PnL (fee 0.60%):   {(summary[3] or 0)*100:+.3f}%")
            print(f"  Avg PnL (fee 1.00%):   {(summary[4] or 0)*100:+.3f}%")
            print(f"  Best trade:            {summary[7]*100:+.3f}%")
            print(f"  Worst trade:           {summary[6]*100:+.3f}%")
        else:
            print("  No closed shadow trades in window")
    except Exception as e:
        print(f"  shadow_trades error: {e}")

    # ── STRATEGY BREAKDOWN ─────────────────────────────────────────────────────
    print("\nSTRATEGY BREAKDOWN")
    strategies = {}
    try:
        rows = conn.execute("""
            SELECT strategy,
                   COUNT(*) as n,
                   AVG(shadow_pnl_pct_fee060) as avg_pnl,
                   SUM(CASE WHEN shadow_pnl_pct > 0 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as win_rate,
                   SUM(shadow_pnl_pct) as total_pnl
            FROM shadow_trades
            WHERE exited_at >= ? AND status = 'closed'
            GROUP BY strategy
            ORDER BY strategy
        """, (since,)).fetchall()
        for row in rows:
            strat, cnt, avg, wr, total = row
            strategies[strat] = {"n": cnt, "avg_pnl": avg or 0, "win_rate": wr or 0}
            print(f"  [{strat:<15}] n={cnt:<5} win={wr*100:.1f}%  avg_pnl(fee060)={(avg or 0)*100:+.3f}%  total={total*100:+.3f}%")
    except Exception as e:
        print(f"  strategy breakdown error: {e}")

    # ── CONCENTRATION CHECK ────────────────────────────────────────────────────
    print("\nCONCENTRATION CHECK  (fail if top-3 > 50%)")
    top3_ok = True
    try:
        total_pnl_row = conn.execute("""
            SELECT SUM(ABS(shadow_pnl_pct)) FROM shadow_trades
            WHERE exited_at >= ? AND status = 'closed'
        """, (since,)).fetchone()
        total_abs = total_pnl_row[0] or 1

        top_trades = conn.execute("""
            SELECT token_symbol, shadow_pnl_pct
            FROM shadow_trades
            WHERE exited_at >= ? AND status = 'closed'
            ORDER BY shadow_pnl_pct DESC LIMIT 10
        """, (since,)).fetchall()

        if top_trades:
            top1 = top_trades[0][1] / total_abs * 100 if total_abs else 0
            top3 = sum(t[1] for t in top_trades[:3]) / total_abs * 100 if total_abs else 0
            top10 = sum(t[1] for t in top_trades[:10]) / total_abs * 100 if total_abs else 0
            top3_ok = top3 < 50
            print(f"  Top-1 share:  {top1:.1f}%")
            print(f"  Top-3 share:  {top3:.1f}%  {'OK' if top3 < 50 else 'FAIL (>50%)'}")
            print(f"  Top-10 share: {top10:.1f}%")
        else:
            print("  No trades to compute concentration")
    except Exception as e:
        print(f"  concentration error: {e}")

    # ── STABILITY (6h blocks) ──────────────────────────────────────────────────
    print("\nSTABILITY (6h blocks)")
    block_evs = []
    stable_ok = True
    try:
        for block_start in range(0, hours, 6):
            block_since = (datetime.now(timezone.utc) - timedelta(hours=hours - block_start)).isoformat()
            block_until = (datetime.now(timezone.utc) - timedelta(hours=hours - block_start - 6)).isoformat()
            row = conn.execute("""
                SELECT COUNT(*), AVG(shadow_pnl_pct_fee060)
                FROM shadow_trades
                WHERE exited_at >= ? AND exited_at < ? AND status = 'closed'
            """, (block_since, block_until)).fetchone()
            cnt = row[0] or 0
            avg = (row[1] or 0) * 100
            block_evs.append(avg)
            print(f"  Block {block_start:02d}-{block_start+6:02d}h: n={cnt:<4} avg_pnl(fee060)={avg:+.3f}%")

        if len(block_evs) >= 2:
            overall_avg = sum(block_evs) / len(block_evs)
            max_block = max(block_evs)
            if overall_avg != 0 and max_block > 2 * abs(overall_avg):
                stable_ok = False
                print(f"  STABILITY: FAIL — max block {max_block:+.3f}% > 2x avg {overall_avg:+.3f}%")
            else:
                print(f"  STABILITY: OK (avg={overall_avg:+.3f}%, max={max_block:+.3f}%)")
    except Exception as e:
        print(f"  stability error: {e}")

    # ── FRICTION AUDIT ─────────────────────────────────────────────────────────
    print("\nFRICTION AUDIT")
    friction_ok = True
    try:
        fric = conn.execute("""
            SELECT AVG(round_trip_pct) as avg_rt_02,
                   AVG(round_trip_pct_04) as avg_rt_04,
                   COUNT(DISTINCT mint_address) as n_pairs
            FROM impact_gate_log
            WHERE evaluated_at >= ?
        """, (since,)).fetchone()
        if fric and fric[0]:
            rt02 = fric[0]
            rt04 = fric[1] or 0
            print(f"  Avg RT friction (0.02 SOL): {rt02:.3f}%")
            print(f"  Avg RT friction (0.04 SOL): {rt04:.3f}%")
            if rt02 > 0:
                print(f"  Scale factor (04/02):       {rt04/rt02:.2f}x")
            print(f"  Pairs with data:            {fric[2]}")
            if rt04 > 3.0:
                friction_ok = False
                print(f"  FRICTION AT SIZE: FAIL — {rt04:.2f}% > 3% at 0.04 SOL")
            else:
                print(f"  FRICTION AT SIZE: OK")
        else:
            print("  No impact_gate_log data in window")
    except Exception as e:
        print(f"  friction audit error: {e}")

    # ── BASELINES ──────────────────────────────────────────────────────────────
    print("\nBASELINES")
    baseline_beat = False
    try:
        baseline_row = conn.execute("""
            SELECT COUNT(*), AVG(shadow_pnl_pct_fee060)
            FROM shadow_trades
            WHERE exited_at >= ? AND status = 'closed' AND strategy = 'baseline'
        """, (since,)).fetchone()
        baseline_n = baseline_row[0] or 0
        baseline_ev = (baseline_row[1] or 0) * 100
        print(f"  Baseline (random):  n={baseline_n:<4} avg_pnl(fee060)={baseline_ev:+.3f}%")

        for strat in ["momentum", "pullback"]:
            if strat in strategies:
                s = strategies[strat]
                ev_pct = s["avg_pnl"] * 100
                beats = ev_pct > baseline_ev
                print(f"  {strat:<15}:  n={s['n']:<4} avg_pnl(fee060)={ev_pct:+.3f}%  beats_baseline={'YES' if beats else 'NO'}")
                if beats:
                    baseline_beat = True
    except Exception as e:
        print(f"  baselines error: {e}")

    # ── SMOKE TEST ─────────────────────────────────────────────────────────────
    print("\nSMOKE TEST")
    smoke_pass = False
    try:
        smoke = conn.execute("""
            SELECT result, realized_rt_pct, expected_rt_pct, slippage_excess_pct, run_at
            FROM smoke_test_log
            ORDER BY run_at DESC LIMIT 1
        """).fetchone()
        if smoke:
            print(f"  Last run:   {smoke[4]}")
            print(f"  Result:     {smoke[0]}")
            print(f"  RT friction: expected={smoke[2]:.3f}%  realized={smoke[1]:.3f}%  excess={smoke[3]:+.3f}%")
            smoke_pass = smoke[0] == "PASS"
        else:
            print("  No smoke test run yet — required before canary")
            print("  Run: python3 live_canary.py smoke")
    except Exception as e:
        print(f"  smoke test check error: {e}")

    # ── LIVE_CANARY_READY GATE ─────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("LIVE_CANARY_READY CHECK")
    print("=" * 70)

    shadow_count_ok = n >= 150
    conc_ok = top3_ok

    criteria = [
        ("Singleton enforcement",       sing_ok,         "all services single-instance"),
        ("Shadow count >= 150",         shadow_count_ok, f"n={n}"),
        ("Beats baseline (random)",     baseline_beat,   "momentum or pullback > baseline at fee060"),
        ("Top-3 share < 50%",           conc_ok,         "concentration check"),
        ("Stability across 6h blocks",  stable_ok,       "no block > 2x avg"),
        ("Friction at 0.04 SOL < 3%",  friction_ok,     "impact scaling"),
        ("Smoke test PASS",             smoke_pass,      "live round-trip validated"),
    ]

    all_pass = True
    for name, passed, note in criteria:
        flag = "PASS" if passed else "FAIL"
        print(f"  [{flag}] {name:<35} ({note})")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print(">>> LIVE_CANARY_READY: YES <<<")
        print("    All criteria met. Proceed to live canary at 0.01 SOL.")
    else:
        failed_items = [name for name, passed, _ in criteria if not passed]
        print(">>> LIVE_CANARY_READY: NO <<<")
        print(f"    Blocking: {', '.join(failed_items)}")
        print("    Continue paper trading. Do not deploy live funds.")

    print("=" * 70)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=int, default=24)
    args = parser.parse_args()
    run_report(args.hours)
