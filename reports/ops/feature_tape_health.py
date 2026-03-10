#!/usr/bin/env python3
"""
feature_tape_health.py
======================
Prints a health report for feature_tape_v1 covering the last 24h.
Usage: python3 feature_tape_health.py
"""

import sqlite3
from datetime import datetime, timezone, timedelta

DB_PATH = "/root/solana_trader/data/solana_trader.db"

def pct(n, total):
    if not total:
        return "N/A"
    return f"{n/total*100:.1f}%"

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    rows = conn.execute("""
        SELECT * FROM feature_tape_v1
        WHERE fire_time_utc >= ?
    """, (cutoff,)).fetchall()

    if not rows:
        print("No rows in feature_tape_v1 in the last 24h.")
        conn.close()
        return

    n = len(rows)
    fires = len(set(r["fire_id"] for r in rows))

    def cov(col):
        return sum(1 for r in rows if r[col] is not None)

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  feature_tape_v1 — HEALTH REPORT (last 24h)                  ║
╠══════════════════════════════════════════════════════════════╣
║  as_of         : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'):<43}║
╚══════════════════════════════════════════════════════════════╝

  fires_processed          : {fires}
  rows_written             : {n}
  avg_candidates_per_fire  : {n/fires:.1f}

  COVERAGE (% rows with non-null value):
  ─────────────────────────────────────────────────────────────
  r_m5                     : {pct(cov('r_m5'), n)}
  buy_sell_ratio_m5        : {pct(cov('buy_sell_ratio_m5'), n)}
  signed_flow_m5           : {pct(cov('signed_flow_m5'), n)}
  txn_accel_m5_vs_h1       : {pct(cov('txn_accel_m5_vs_h1'), n)}
  vol_accel_m5_vs_h1       : {pct(cov('vol_accel_m5_vs_h1'), n)}
  avg_trade_usd_m5         : {pct(cov('avg_trade_usd_m5'), n)}
  jup_vs_cpamm_diff_pct    : {pct(cov('jup_vs_cpamm_diff_pct'), n)}
  round_trip_pct           : {pct(cov('round_trip_pct'), n)}
  impact_buy_pct           : {pct(cov('impact_buy_pct'), n)}
  liq_change_pct           : {pct(cov('liq_change_pct'), n)}
  breadth_positive_pct     : {pct(cov('breadth_positive_pct'), n)}
  median_pool_r_m5         : {pct(cov('median_pool_r_m5'), n)}
""")

    # Failures: fires with 0 rows written
    all_fires = conn.execute("""
        SELECT DISTINCT fire_id, fire_time_utc FROM feature_tape_v1
        WHERE fire_time_utc >= ?
        ORDER BY fire_time_utc
    """, (cutoff,)).fetchall()
    print(f"  FIRES SEEN: {[r['fire_time_utc'][:16] for r in all_fires]}")
    conn.close()

if __name__ == "__main__":
    main()
