#!/usr/bin/env python3
"""
derive_labels_v2.py
===================
Derives forward-return labels for feature_tape_v2 rows.

Horizons: +5m, +15m, +30m, +1h, +4h, +1d
For each horizon:
  gross_return_h   = (price_fwd / price_entry) - 1
  net_proxy_h      = gross_return_h - round_trip_pct
  (net_proxy is OPTIMISTIC — does not include full fees/slippage)

Source: universe_snapshot.price_usd (primary)
        microstructure_log.price_usd (fallback)

No-lookahead rule:
  entry price: latest snapshot with ts <= fire_time_epoch
  forward price: closest snapshot to fire_time_epoch + offset,
                 strictly AFTER fire_time_epoch, within ±tolerance

Run as continuous loop (polls every 60s) until all rows are labeled.
"""

import sqlite3
import time
import logging
import os
import sys
from datetime import datetime, timezone

DB_PATH  = "/root/solana_trader/data/solana_trader.db"
LOG_PATH = "/var/log/solana_trader/derive_labels_v2.log"

HORIZONS = {
    "5m":  (300,    90),   # offset_s, tolerance_s
    "15m": (900,    120),
    "30m": (1800,   180),
    "1h":  (3600,   300),
    "4h":  (14400,  600),
    "1d":  (86400,  1800),
}

os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("derive_labels_v2")

CREATE_LABELS = """
CREATE TABLE IF NOT EXISTS feature_tape_v2_labels (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    fire_id                 TEXT    NOT NULL,
    candidate_mint          TEXT    NOT NULL,
    fire_time_epoch         REAL,
    round_trip_pct          REAL,

    -- +5m
    price_entry_5m          REAL,
    price_fwd_5m            REAL,
    gross_return_5m         REAL,
    net_proxy_5m            REAL,
    label_quality_5m        TEXT,
    entry_lag_5m            REAL,
    fwd_lag_5m              REAL,

    -- +15m
    price_entry_15m         REAL,
    price_fwd_15m           REAL,
    gross_return_15m        REAL,
    net_proxy_15m           REAL,
    label_quality_15m       TEXT,
    entry_lag_15m           REAL,
    fwd_lag_15m             REAL,

    -- +30m
    price_entry_30m         REAL,
    price_fwd_30m           REAL,
    gross_return_30m        REAL,
    net_proxy_30m           REAL,
    label_quality_30m       TEXT,
    entry_lag_30m           REAL,
    fwd_lag_30m             REAL,

    -- +1h
    price_entry_1h          REAL,
    price_fwd_1h            REAL,
    gross_return_1h         REAL,
    net_proxy_1h            REAL,
    label_quality_1h        TEXT,
    entry_lag_1h            REAL,
    fwd_lag_1h              REAL,

    -- +4h
    price_entry_4h          REAL,
    price_fwd_4h            REAL,
    gross_return_4h         REAL,
    net_proxy_4h            REAL,
    label_quality_4h        TEXT,
    entry_lag_4h            REAL,
    fwd_lag_4h              REAL,

    -- +1d
    price_entry_1d          REAL,
    price_fwd_1d            REAL,
    gross_return_1d         REAL,
    net_proxy_1d            REAL,
    label_quality_1d        TEXT,
    entry_lag_1d            REAL,
    fwd_lag_1d              REAL,

    label_source            TEXT,
    created_at              TEXT,
    updated_at              TEXT,

    UNIQUE(fire_id, candidate_mint)
)
"""


def get_price(cur, mint, epoch, direction, tolerance):
    """
    Get price from universe_snapshot.
    direction='entry': latest snapshot with ts <= epoch (within 60s lookback)
    direction='fwd':   closest snapshot to epoch, strictly > epoch, within tolerance
    """
    if direction == 'entry':
        cur.execute("""
            SELECT price_usd, strftime('%s', snapshot_at)
            FROM universe_snapshot
            WHERE mint_address = ?
              AND CAST(strftime('%s', snapshot_at) AS REAL) <= ?
              AND CAST(strftime('%s', snapshot_at) AS REAL) >= ?
            ORDER BY snapshot_at DESC
            LIMIT 1
        """, (mint, epoch, epoch - 60))
    else:
        cur.execute("""
            SELECT price_usd, strftime('%s', snapshot_at)
            FROM universe_snapshot
            WHERE mint_address = ?
              AND CAST(strftime('%s', snapshot_at) AS REAL) > ?
              AND CAST(strftime('%s', snapshot_at) AS REAL) <= ?
            ORDER BY ABS(CAST(strftime('%s', snapshot_at) AS REAL) - ?)
            LIMIT 1
        """, (mint, epoch, epoch + tolerance, epoch))
    row = cur.fetchone()
    if row and row[0] is not None:
        return row[0], abs(float(row[1]) - epoch)
    return None, None


def label_quality(lag):
    if lag is None:
        return "missing"
    if lag <= 30:
        return "good"
    if lag <= 120:
        return "stale"
    return "missing"


def process_batch(con, batch_size=500):
    cur = con.cursor()

    # Get unlabeled rows (no label row yet)
    cur.execute("""
        SELECT ft.fire_id, ft.candidate_mint, ft.fire_time_epoch, ft.round_trip_pct
        FROM feature_tape_v2 ft
        LEFT JOIN feature_tape_v2_labels lbl
          ON ft.fire_id = lbl.fire_id AND ft.candidate_mint = lbl.candidate_mint
        WHERE lbl.fire_id IS NULL
        LIMIT ?
    """, (batch_size,))
    rows = cur.fetchall()

    if not rows:
        return 0

    now_utc = datetime.now(timezone.utc).isoformat()
    written = 0

    for fire_id, mint, fire_epoch, round_trip_pct in rows:
        if fire_epoch is None:
            continue

        label_row = {
            "fire_id": fire_id,
            "candidate_mint": mint,
            "fire_time_epoch": fire_epoch,
            "round_trip_pct": round_trip_pct,
            "label_source": "universe_snapshot",
            "created_at": now_utc,
            "updated_at": now_utc,
        }

        for hz, (offset, tolerance) in HORIZONS.items():
            fwd_target = fire_epoch + offset
            price_entry, entry_lag = get_price(cur, mint, fire_epoch, 'entry', 60)
            price_fwd,   fwd_lag   = get_price(cur, mint, fwd_target, 'fwd', tolerance)

            if price_entry and price_fwd and price_entry > 0:
                gross = (price_fwd / price_entry) - 1
                net   = gross - round_trip_pct if round_trip_pct is not None else None
                qual  = label_quality(fwd_lag)
            else:
                gross = net = None
                qual  = "missing"

            label_row[f"price_entry_{hz}"] = price_entry
            label_row[f"price_fwd_{hz}"]   = price_fwd
            label_row[f"gross_return_{hz}"] = gross
            label_row[f"net_proxy_{hz}"]    = net
            label_row[f"label_quality_{hz}"] = qual
            label_row[f"entry_lag_{hz}"]    = entry_lag
            label_row[f"fwd_lag_{hz}"]      = fwd_lag

        try:
            cur.execute("""
                INSERT OR REPLACE INTO feature_tape_v2_labels (
                    fire_id, candidate_mint, fire_time_epoch, round_trip_pct,
                    price_entry_5m, price_fwd_5m, gross_return_5m, net_proxy_5m, label_quality_5m, entry_lag_5m, fwd_lag_5m,
                    price_entry_15m, price_fwd_15m, gross_return_15m, net_proxy_15m, label_quality_15m, entry_lag_15m, fwd_lag_15m,
                    price_entry_30m, price_fwd_30m, gross_return_30m, net_proxy_30m, label_quality_30m, entry_lag_30m, fwd_lag_30m,
                    price_entry_1h, price_fwd_1h, gross_return_1h, net_proxy_1h, label_quality_1h, entry_lag_1h, fwd_lag_1h,
                    price_entry_4h, price_fwd_4h, gross_return_4h, net_proxy_4h, label_quality_4h, entry_lag_4h, fwd_lag_4h,
                    price_entry_1d, price_fwd_1d, gross_return_1d, net_proxy_1d, label_quality_1d, entry_lag_1d, fwd_lag_1d,
                    label_source, created_at, updated_at
                ) VALUES (
                    :fire_id, :candidate_mint, :fire_time_epoch, :round_trip_pct,
                    :price_entry_5m, :price_fwd_5m, :gross_return_5m, :net_proxy_5m, :label_quality_5m, :entry_lag_5m, :fwd_lag_5m,
                    :price_entry_15m, :price_fwd_15m, :gross_return_15m, :net_proxy_15m, :label_quality_15m, :entry_lag_15m, :fwd_lag_15m,
                    :price_entry_30m, :price_fwd_30m, :gross_return_30m, :net_proxy_30m, :label_quality_30m, :entry_lag_30m, :fwd_lag_30m,
                    :price_entry_1h, :price_fwd_1h, :gross_return_1h, :net_proxy_1h, :label_quality_1h, :entry_lag_1h, :fwd_lag_1h,
                    :price_entry_4h, :price_fwd_4h, :gross_return_4h, :net_proxy_4h, :label_quality_4h, :entry_lag_4h, :fwd_lag_4h,
                    :price_entry_1d, :price_fwd_1d, :gross_return_1d, :net_proxy_1d, :label_quality_1d, :entry_lag_1d, :fwd_lag_1d,
                    :label_source, :created_at, :updated_at
                )
            """, label_row)
            written += cur.rowcount
        except Exception as e:
            log.error(f"Insert error {fire_id}/{mint}: {e}")

    con.commit()
    return written


def main():
    log.info("derive_labels_v2 starting")
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute(CREATE_LABELS)
    con.commit()

    while True:
        written = process_batch(con)
        if written > 0:
            log.info(f"Labeled {written} rows")
        else:
            log.info("No unlabeled rows — sleeping 60s")
            time.sleep(60)


if __name__ == "__main__":
    main()
