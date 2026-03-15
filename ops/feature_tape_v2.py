#!/usr/bin/env python3
"""
feature_tape_v2.py
==================
Collects pre-fire features for every candidate at each observer fire.

Feature families:
  A) Order-flow / urgency   (from microstructure_log)
  B) Route / quote quality  (from universe_snapshot + microstructure_log)
  C) Market-state / gating  (from universe_snapshot pool-level aggregates)

No-lookahead rules:
  snapshot_at_used = MAX(snapshot_at) WHERE snapshot_at <= fire_time_epoch
  micro_ts_used    = MAX(logged_at)   WHERE logged_at <= fire_time_epoch
                                        AND logged_at >= fire_time_epoch - 60s
  All derived fields use only data at or before fire_time_epoch.

Output table: feature_tape_v2  (in data/solana_trader.db)
Run mode: fires every 15 minutes aligned to :00/:15/:30/:45 UTC
"""

import sqlite3
import time
import logging
import os
import sys
from datetime import datetime, timezone, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
DB_PATH        = "/root/solana_trader/data/solana_trader.db"
LOG_PATH       = "/var/log/solana_trader/feature_tape_v2.log"
FIRE_INTERVAL  = 900          # 15 minutes
SNAP_LOOKBACK  = 300          # max seconds before fire to find a valid snapshot
MICRO_LOOKBACK = 60           # max seconds before fire to find a valid micro row
POOL_MIN_ROWS  = 3            # min pool rows to compute pool-level aggregates

# ── Logging ──────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("feature_tape_v2")

# ── Schema ───────────────────────────────────────────────────────────────────
CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS feature_tape_v2 (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    fire_id                 TEXT    NOT NULL,
    fire_time_utc           TEXT    NOT NULL,
    fire_time_epoch         REAL    NOT NULL,
    candidate_mint          TEXT    NOT NULL,
    candidate_symbol        TEXT,
    snapshot_at_used        TEXT,
    micro_ts_used           TEXT,
    created_at              TEXT    NOT NULL,

    -- Classification
    lane                    TEXT,
    venue                   TEXT,
    pool_type               TEXT,
    pumpfun_origin          INTEGER,

    -- Fundamentals
    age_hours               REAL,
    liquidity_usd           REAL,
    vol_h1                  REAL,
    vol_h24                 REAL,

    -- A) Order-flow / urgency (from microstructure_log)
    buy_count_1m            INTEGER,
    sell_count_1m           INTEGER,
    buy_count_5m            INTEGER,
    sell_count_5m           INTEGER,
    buy_usd_1m              REAL,
    sell_usd_1m             REAL,
    buy_usd_5m              REAL,
    sell_usd_5m             REAL,
    signed_flow_1m          REAL,
    signed_flow_5m          REAL,
    buy_sell_ratio_1m       REAL,
    buy_sell_ratio_5m       REAL,
    avg_trade_usd_1m        REAL,
    avg_trade_usd_5m        REAL,
    median_trade_usd_5m     REAL,
    max_trade_usd_5m        REAL,
    txn_accel_m1_vs_h1      REAL,
    txn_accel_m5_vs_h1      REAL,
    vol_accel_m1_vs_h1      REAL,
    vol_accel_m5_vs_h1      REAL,

    -- B) Route / quote quality (from universe_snapshot)
    jup_vs_cpamm_diff_pct   REAL,
    round_trip_pct          REAL,
    impact_buy_pct          REAL,
    impact_sell_pct         REAL,
    impact_asymmetry_pct    REAL,

    -- C) Market-state / gating (pool-level aggregates from universe_snapshot)
    breadth_positive_pct    REAL,
    breadth_negative_pct    REAL,
    median_pool_r_m5        REAL,
    pool_dispersion_r_m5    REAL,
    median_pool_rv5m        REAL,
    pool_liquidity_median   REAL,
    pool_vol_h1_median      REAL,
    liq_change_pct          REAL,
    pool_size_total         INTEGER,
    pool_size_with_micro    INTEGER,
    coverage_ratio_micro    REAL,

    -- Source flags
    order_flow_source       TEXT,
    quote_source            TEXT,
    liq_source              TEXT,

    UNIQUE(fire_id, candidate_mint)
)
"""

CREATE_FIRE_LOG = """
CREATE TABLE IF NOT EXISTS feature_tape_v2_fire_log (
    fire_id         TEXT PRIMARY KEY,
    fire_time_utc   TEXT NOT NULL,
    fire_time_epoch REAL NOT NULL,
    candidates_n    INTEGER,
    rows_written    INTEGER,
    duration_s      REAL,
    created_at      TEXT NOT NULL
)
"""


def get_next_fire_time():
    """Return the next 15-minute boundary in UTC."""
    now = datetime.now(timezone.utc)
    minutes = (now.minute // 15 + 1) * 15
    if minutes >= 60:
        next_fire = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    else:
        next_fire = now.replace(minute=minutes, second=0, microsecond=0)
    return next_fire


def make_fire_id(fire_epoch: float) -> str:
    import hashlib
    return hashlib.md5(f"feature_tape_v2_{fire_epoch}".encode()).hexdigest()[:8]


def collect_fire(con: sqlite3.Connection, fire_epoch: float, fire_utc: str, fire_id: str):
    cur = con.cursor()
    t0 = time.time()

    # ── 1. Candidate universe: all mints in the latest snapshot at or before fire ──
    snap_cutoff = fire_epoch
    snap_floor  = fire_epoch - SNAP_LOOKBACK

    cur.execute("""
        SELECT DISTINCT mint_address
        FROM universe_snapshot
        WHERE strftime('%s', snapshot_at) <= ?
          AND strftime('%s', snapshot_at) >= ?
          AND eligible = 1
    """, (str(int(snap_cutoff)), str(int(snap_floor))))
    candidates = [r[0] for r in cur.fetchall()]

    if not candidates:
        log.warning(f"[{fire_id}] No eligible candidates found in snapshot window")
        return 0

    log.info(f"[{fire_id}] {len(candidates)} candidates at fire {fire_utc}")

    # ── 2. Pool-level aggregates (market-state) from universe_snapshot ──
    cur.execute("""
        SELECT
            mint_address,
            r_m5,
            vol_m5,
            liq_usd,
            vol_h1,
            buys_m5,
            sells_m5
        FROM universe_snapshot
        WHERE strftime('%s', snapshot_at) = (
            SELECT MAX(strftime('%s', snapshot_at))
            FROM universe_snapshot
            WHERE strftime('%s', snapshot_at) <= ?
        )
    """, (str(int(snap_cutoff)),))
    pool_rows = cur.fetchall()

    pool_r_m5_vals   = [r[1] for r in pool_rows if r[1] is not None]
    pool_vol_m5_vals = [r[2] for r in pool_rows if r[2] is not None]  # vol_m5 used as rv5m proxy
    pool_liq_vals    = [r[3] for r in pool_rows if r[3] is not None]
    pool_vol_h1_vals = [r[4] for r in pool_rows if r[4] is not None]

    pool_size_total = len(pool_rows)

    def safe_median(vals):
        if not vals:
            return None
        s = sorted(vals)
        n = len(s)
        return (s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2)

    def safe_pct(vals, condition):
        if not vals:
            return None
        return sum(1 for v in vals if condition(v)) / len(vals) * 100

    def safe_dispersion(vals):
        if len(vals) < 2:
            return None
        import statistics
        try:
            return statistics.stdev(vals)
        except Exception:
            return None

    breadth_positive_pct  = safe_pct(pool_r_m5_vals, lambda v: v > 0)
    breadth_negative_pct  = safe_pct(pool_r_m5_vals, lambda v: v < 0)
    median_pool_r_m5      = safe_median(pool_r_m5_vals)
    pool_dispersion_r_m5  = safe_dispersion(pool_r_m5_vals)
    median_pool_rv5m      = safe_median(pool_vol_m5_vals)  # vol_m5 proxy (rv_5m not in universe_snapshot)
    pool_liquidity_median = safe_median(pool_liq_vals)
    pool_vol_h1_median    = safe_median(pool_vol_h1_vals)

    # ── 3. Per-candidate features ──
    rows_written = 0

    for mint in candidates:
        # Latest snapshot for this mint at or before fire
        cur.execute("""
            SELECT
                snapshot_at, lane, venue, pool_type, pumpfun_origin,
                age_hours, liq_usd, vol_h1, vol_h24,
                buys_m5, sells_m5,
                buy_count_ratio_m5,
                avg_trade_usd_m5,
                jup_vs_cpamm_diff_pct, round_trip_pct,
                impact_buy_pct, impact_sell_pct,
                token_symbol
            FROM universe_snapshot
            WHERE mint_address = ?
              AND strftime('%s', snapshot_at) <= ?
              AND strftime('%s', snapshot_at) >= ?
            ORDER BY snapshot_at DESC
            LIMIT 1
        """, (mint, str(int(snap_cutoff)), str(int(snap_floor))))
        snap = cur.fetchone()

        if not snap:
            continue

        (snap_at, lane, venue, pool_type, pumpfun_origin,
         age_hours, liq_usd, vol_h1, vol_h24,
         buys_m5_snap, sells_m5_snap,
         buy_count_ratio_m5_snap,
         avg_trade_usd_m5_snap,
         jup_vs_cpamm_diff_pct, round_trip_pct,
         impact_buy_pct, impact_sell_pct,
         token_symbol) = snap
        buy_sell_ratio_m5_snap = None  # not in universe_snapshot; sourced from micro
        vol_accel_m5_snap = None       # not in universe_snapshot; sourced from micro
        txn_accel_m5_snap = None       # not in universe_snapshot; sourced from micro
        liq_change_pct_snap = None     # not in universe_snapshot; sourced from micro

        # Latest micro row for this mint within 60s before fire
        micro_floor = fire_epoch - MICRO_LOOKBACK
        cur.execute("""
            SELECT
                logged_at,
                buys_m5, sells_m5, buys_h1, sells_h1,
                buy_sell_ratio_m5, buy_sell_ratio_h1,
                buy_count_ratio_m5, buy_count_ratio_h1,
                avg_trade_usd_m5, avg_trade_usd_h1,
                vol_m5, vol_h1 AS micro_vol_h1,
                vol_accel_m5_vs_h1, txn_accel_m5_vs_h1,
                liq_usd AS micro_liq_usd,
                liq_change_pct AS micro_liq_change_pct
            FROM microstructure_log
            WHERE mint_address = ?
              AND strftime('%s', logged_at) <= ?
              AND strftime('%s', logged_at) >= ?
            ORDER BY logged_at DESC
            LIMIT 1
        """, (mint, str(int(fire_epoch)), str(int(micro_floor))))
        micro = cur.fetchone()

        if micro:
            (micro_ts, buys_m5_micro, sells_m5_micro, buys_h1_micro, sells_h1_micro,
             bsr_m5_micro, bsr_h1_micro,
             bcr_m5_micro, bcr_h1_micro,
             avg_trade_usd_m5_micro, avg_trade_usd_h1_micro,
             vol_m5_micro, vol_h1_micro,
             vol_accel_micro, txn_accel_micro,
             micro_liq_usd, micro_liq_change_pct) = micro

            # Compute derived order-flow fields
            buy_count_5m  = buys_m5_micro
            sell_count_5m = sells_m5_micro
            buy_usd_5m    = (avg_trade_usd_m5_micro * buys_m5_micro) if (avg_trade_usd_m5_micro and buys_m5_micro) else None
            sell_usd_5m   = (avg_trade_usd_m5_micro * sells_m5_micro) if (avg_trade_usd_m5_micro and sells_m5_micro) else None
            signed_flow_5m = (buy_usd_5m - sell_usd_5m) if (buy_usd_5m is not None and sell_usd_5m is not None) else None
            buy_sell_ratio_5m = bsr_m5_micro

            # 1m proxies: not directly stored — use snapshot buys_m5/sells_m5 as fallback
            buy_count_1m  = None
            sell_count_1m = None
            buy_usd_1m    = None
            sell_usd_1m   = None
            signed_flow_1m = None
            buy_sell_ratio_1m = None
            avg_trade_usd_1m = None
            median_trade_usd_5m = None   # not stored at row level
            max_trade_usd_5m    = None   # not stored at row level

            avg_trade_usd_5m   = avg_trade_usd_m5_micro
            txn_accel_m5_vs_h1 = txn_accel_micro
            vol_accel_m5_vs_h1 = vol_accel_micro
            txn_accel_m1_vs_h1 = None   # 1m not available
            vol_accel_m1_vs_h1 = None

            liq_change_pct_final = micro_liq_change_pct if micro_liq_change_pct is not None else liq_change_pct_snap
            order_flow_source = "microstructure_log"
        else:
            # Fallback to snapshot
            buys_h1_snap = None
            sells_h1_snap = None
            buy_count_5m  = buys_m5_snap
            sell_count_5m = sells_m5_snap
            buy_usd_5m    = None
            sell_usd_5m   = None
            signed_flow_5m = None
            buy_sell_ratio_5m = buy_sell_ratio_m5_snap
            avg_trade_usd_5m  = avg_trade_usd_m5_snap
            buy_count_1m = sell_count_1m = buy_usd_1m = sell_usd_1m = None
            signed_flow_1m = buy_sell_ratio_1m = avg_trade_usd_1m = None
            median_trade_usd_5m = max_trade_usd_5m = None
            txn_accel_m5_vs_h1 = txn_accel_m5_snap
            vol_accel_m5_vs_h1 = vol_accel_m5_snap
            txn_accel_m1_vs_h1 = vol_accel_m1_vs_h1 = None
            liq_change_pct_final = liq_change_pct_snap
            micro_ts = None
            order_flow_source = "universe_snapshot_fallback"

        # impact_asymmetry
        impact_asymmetry_pct = (
            (impact_buy_pct - impact_sell_pct)
            if (impact_buy_pct is not None and impact_sell_pct is not None)
            else None
        )

        # Pool size with micro coverage
        cur.execute("""
            SELECT COUNT(DISTINCT mint_address)
            FROM microstructure_log
            WHERE strftime('%s', logged_at) <= ?
              AND strftime('%s', logged_at) >= ?
        """, (str(int(fire_epoch)), str(int(micro_floor))))
        pool_size_with_micro = cur.fetchone()[0]
        coverage_ratio_micro = (
            pool_size_with_micro / pool_size_total
            if pool_size_total and pool_size_total > 0
            else None
        )

        now_utc = datetime.now(timezone.utc).isoformat()

        try:
            cur.execute("""
                INSERT OR IGNORE INTO feature_tape_v2 (
                    fire_id, fire_time_utc, fire_time_epoch,
                    candidate_mint, candidate_symbol,
                    snapshot_at_used, micro_ts_used, created_at,
                    lane, venue, pool_type, pumpfun_origin,
                    age_hours, liquidity_usd, vol_h1, vol_h24,
                    buy_count_1m, sell_count_1m,
                    buy_count_5m, sell_count_5m,
                    buy_usd_1m, sell_usd_1m,
                    buy_usd_5m, sell_usd_5m,
                    signed_flow_1m, signed_flow_5m,
                    buy_sell_ratio_1m, buy_sell_ratio_5m,
                    avg_trade_usd_1m, avg_trade_usd_5m,
                    median_trade_usd_5m, max_trade_usd_5m,
                    txn_accel_m1_vs_h1, txn_accel_m5_vs_h1,
                    vol_accel_m1_vs_h1, vol_accel_m5_vs_h1,
                    jup_vs_cpamm_diff_pct, round_trip_pct,
                    impact_buy_pct, impact_sell_pct, impact_asymmetry_pct,
                    breadth_positive_pct, breadth_negative_pct,
                    median_pool_r_m5, pool_dispersion_r_m5,
                    median_pool_rv5m, pool_liquidity_median, pool_vol_h1_median,
                    liq_change_pct, pool_size_total, pool_size_with_micro,
                    coverage_ratio_micro,
                    order_flow_source, quote_source, liq_source
                ) VALUES (
                    ?,?,?,?,?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,
                    ?,?,?,?,?,
                    ?,?,?,?,?,?,?,?,?,?,?,
                    ?,?,?
                )
            """, (
                fire_id, fire_utc, fire_epoch,
                mint, token_symbol,
                snap_at, micro_ts, now_utc,
                lane, venue, pool_type, pumpfun_origin,
                age_hours, liq_usd, vol_h1, vol_h24,
                buy_count_1m, sell_count_1m,
                buy_count_5m, sell_count_5m,
                buy_usd_1m, sell_usd_1m,
                buy_usd_5m, sell_usd_5m,
                signed_flow_1m, signed_flow_5m,
                buy_sell_ratio_1m, buy_sell_ratio_5m,
                avg_trade_usd_1m, avg_trade_usd_5m,
                median_trade_usd_5m, max_trade_usd_5m,
                txn_accel_m1_vs_h1, txn_accel_m5_vs_h1,
                vol_accel_m1_vs_h1, vol_accel_m5_vs_h1,
                jup_vs_cpamm_diff_pct, round_trip_pct,
                impact_buy_pct, impact_sell_pct, impact_asymmetry_pct,
                breadth_positive_pct, breadth_negative_pct,
                median_pool_r_m5, pool_dispersion_r_m5,
                median_pool_rv5m, pool_liquidity_median, pool_vol_h1_median,
                liq_change_pct_final, pool_size_total, pool_size_with_micro,
                coverage_ratio_micro,
                order_flow_source, "universe_snapshot", "microstructure_log"
            ))
            rows_written += cur.rowcount
        except Exception as e:
            log.error(f"[{fire_id}] Insert error for {mint}: {e}")

    con.commit()
    duration = time.time() - t0

    # Write fire log
    cur.execute("""
        INSERT OR REPLACE INTO feature_tape_v2_fire_log
        (fire_id, fire_time_utc, fire_time_epoch, candidates_n, rows_written, duration_s, created_at)
        VALUES (?,?,?,?,?,?,?)
    """, (fire_id, fire_utc, fire_epoch, len(candidates), rows_written, round(duration, 2),
          datetime.now(timezone.utc).isoformat()))
    con.commit()

    log.info(f"[{fire_id}] Wrote {rows_written}/{len(candidates)} rows in {duration:.1f}s")
    return rows_written


def main():
    log.info("feature_tape_v2 starting")
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(CREATE_TABLE)
    con.execute(CREATE_FIRE_LOG)
    con.commit()
    log.info("Schema ready")

    while True:
        next_fire = get_next_fire_time()
        wait_s = (next_fire - datetime.now(timezone.utc)).total_seconds()
        if wait_s > 0:
            log.info(f"Next fire at {next_fire.isoformat()} (in {wait_s:.0f}s)")
            time.sleep(wait_s)

        fire_epoch = next_fire.timestamp()
        fire_utc   = next_fire.strftime("%Y-%m-%dT%H:%M:%SZ")
        fire_id    = make_fire_id(fire_epoch)

        log.info(f"FIRE {fire_id} at {fire_utc}")
        try:
            collect_fire(con, fire_epoch, fire_utc, fire_id)
        except Exception as e:
            log.error(f"[{fire_id}] Unhandled error: {e}", exc_info=True)

        # Sleep a few seconds past the fire boundary to avoid double-fire
        time.sleep(5)


if __name__ == "__main__":
    main()
