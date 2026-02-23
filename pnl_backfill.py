#!/usr/bin/env python3
"""
Deferred PnL Backfill Module

Runs a background thread every 60s that backfills missing on-chain data
(sol_change, slippage) for live_trades where the initial verification
timed out before Solana finality.

Usage: import and call start_backfill_thread() from live_executor.py
"""
import os
import time
import logging
import threading
import sqlite3
import requests

logger = logging.getLogger("pnl_backfill")

_backfill_started = False
_lock = threading.Lock()


def start_backfill_thread():
    """Start the deferred backfill thread (idempotent - only starts once)."""
    global _backfill_started
    with _lock:
        if _backfill_started:
            return
        _backfill_started = True

    t = threading.Thread(target=_backfill_loop, daemon=True, name="pnl-backfill")
    t.start()
    logger.info("[BACKFILL] Deferred PnL backfill thread started (runs every 60s)")


def _backfill_loop():
    """Main loop: every 60s, find trades with missing on-chain data and fill them."""
    while True:
        try:
            time.sleep(60)
            _run_backfill_pass()
        except Exception as e:
            logger.warning(f"[BACKFILL] Loop error: {e}")
            time.sleep(60)


def _run_backfill_pass():
    """Single pass: query for missing data and fill from on-chain."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "solana_trader.db")
    rpc_url = os.environ.get("HELIUS_RPC_URL", "")
    wallet = os.environ.get("WALLET_ADDRESS", "")

    if not rpc_url:
        return

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT id, tx_signature, token_name, action, amount_sol "
            "FROM live_trades "
            "WHERE tx_signature IS NOT NULL "
            "AND tx_signature != 'ambiguous_but_confirmed' "
            "AND success = 1 "
            "AND live_fill_price_sol IS NULL "
            "ORDER BY executed_at ASC "
            "LIMIT 20"
        ).fetchall()

        if not rows:
            return

        logger.info(f"[BACKFILL] Found {len(rows)} trades with missing on-chain data")
        filled = 0

        for row_id, sig, name, action, amount_sol in rows:
            try:
                resp = requests.post(
                    rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "getTransaction",
                        "params": [
                            sig,
                            {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0},
                        ],
                    },
                    timeout=15,
                )
                result = resp.json().get("result")

                if not result:
                    continue

                meta = result.get("meta", {})
                err = meta.get("err")
                if err:
                    conn.execute("UPDATE live_trades SET success = 0 WHERE id = ?", (row_id,))
                    conn.commit()
                    logger.warning(f"[BACKFILL] {name} ({action}) TX failed on-chain: {err}")
                    continue

                pre = meta.get("preBalances", [])
                post = meta.get("postBalances", [])

                if pre and post:
                    sol_change = (post[0] - pre[0]) / 1e9
                    actual_sol = abs(sol_change)
                    expected_sol = amount_sol or 0.04
                    slippage = (
                        ((actual_sol - expected_sol) / expected_sol * 100)
                        if expected_sol > 0
                        else 0
                    )

                    conn.execute(
                        "UPDATE live_trades "
                        "SET live_fill_price_sol = ?, slippage_pct = ? "
                        "WHERE id = ?",
                        (sol_change, slippage, row_id),
                    )
                    conn.commit()
                    filled += 1
                    logger.info(
                        f"[BACKFILL] {name} ({action}): "
                        f"sol_change={sol_change:+.6f} slippage={slippage:+.1f}%"
                    )

            except Exception as e:
                logger.debug(f"[BACKFILL] Error processing {name}: {e}")
                continue

        if filled > 0:
            logger.info(f"[BACKFILL] Filled {filled}/{len(rows)} missing on-chain records")

    finally:
        conn.close()


def backfill_all_now():
    """One-shot: backfill ALL missing records immediately (for manual use)."""
    logger.info("[BACKFILL] Running one-shot backfill for all missing records...")
    _run_backfill_pass()
    logger.info("[BACKFILL] One-shot backfill complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Running one-shot backfill...")
    backfill_all_now()
