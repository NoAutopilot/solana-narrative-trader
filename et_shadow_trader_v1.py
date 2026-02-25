#!/usr/bin/env python3
"""
et_shadow_trader_v1.py — ET v1 Paper Trading Harness

Spec:
  - TRADE_SIZE_SOL = 0.01
  - MAX_OPEN_POSITIONS_PER_STRATEGY = 1  (hard cap per strategy, not global)
  - UNIFIED exit policy across all strategies: TP +4%, SL -2%, timeout 12min
  - Friction gate: Jupiter quote-based RT estimate <= 1.0%; abort if no route
  - Baseline: matched-time (fires whenever momentum OR pullback enters, on a
    randomly chosen eligible token from the same scan cycle)
  - Fee scenarios: fee025 / fee060 / fee100 reported at close
  - Singleton: lockfile guard at /tmp/et_shadow_trader_v1.lock
"""

import os
import sys
import fcntl
import logging
import random
import sqlite3
import time
import uuid
import requests
from datetime import datetime, timezone

# ── SINGLETON GUARD ──────────────────────────────────────────────────────────
_LOCK_PATH = "/tmp/et_shadow_trader_v1.lock"
_lockfile_fd = open(_LOCK_PATH, "w")
try:
    fcntl.flock(_lockfile_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    _lockfile_fd.write(str(os.getpid()))
    _lockfile_fd.flush()
except BlockingIOError:
    print("[singleton] Another instance is running (lock held). Exiting.", flush=True)
    sys.exit(0)

# ── IMPORTS ───────────────────────────────────────────────────────────────────
sys.path.insert(0, "/root/solana_trader")
from config.config import DB_PATH, LOGS_DIR, JUPITER_API_KEY, JUPITER_BASE_URL
from cpamm_math import cpamm_round_trip, k_lp_cliff

os.makedirs(LOGS_DIR, exist_ok=True)
logger = logging.getLogger("et_shadow_trader_v1")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s [shadow_v1] %(levelname)s: %(message)s")
    fh = logging.FileHandler(os.path.join(LOGS_DIR, "et_shadow_trader_v1.log"))
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)

# ── CONSTANTS ─────────────────────────────────────────────────────────────────
POLL_INTERVAL_SEC           = 15
TRADE_SIZE_SOL              = 0.01
MAX_OPEN_PER_STRATEGY       = 1        # hard cap: 1 open trade per strategy at a time
LP_CLIFF_THRESHOLD          = 0.05     # 5% k-drop triggers liq_cliff exit
FRICTION_GATE_MAX_RT        = 0.010    # 1.0% max total RT friction (Jupiter-quoted)
DEXSCREENER_TIMEOUT         = 12
WSOL_MINT                   = "So11111111111111111111111111111111111111112"
LAMPORTS_PER_SOL            = 1_000_000_000

# ── UNIFIED EXIT POLICY (identical across all strategies) ─────────────────────
EXIT_TAKE_PROFIT_PCT        = 4.0      # +4.0% gross
EXIT_STOP_LOSS_PCT          = -2.0     # -2.0% gross
EXIT_MAX_HOLD_MINUTES       = 12
EXIT_LIQ_CLIFF              = True

# ── STRATEGY ENTRY CONDITIONS ─────────────────────────────────────────────────
STRATEGIES = {
    "momentum": {
        "entry_r_m5_min":               2.0,
        "entry_buy_count_ratio_min":    0.60,
        "entry_vol_accel_min":          1.5,
    },
    "pullback": {
        "entry_r_h1_min":               3.0,
        "entry_r_m5_max":              -0.5,
        "entry_buy_count_ratio_min":    0.55,
    },
    # baseline has no entry conditions — it is matched-time only
    "baseline": {},
}

# ── DB HELPERS ────────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_tables():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS shadow_trades_v1 (
        trade_id                TEXT    PRIMARY KEY,
        strategy                TEXT    NOT NULL,
        mint_address            TEXT    NOT NULL,
        token_symbol            TEXT,
        pair_address            TEXT,
        entered_at              TEXT    NOT NULL,
        entry_price_usd         REAL,
        entry_price_native      REAL,
        entry_liq_usd           REAL,
        entry_liq_quote_sol     REAL,
        entry_liq_base          REAL,
        entry_k_invariant       REAL,
        entry_impact_buy_pct    REAL,
        entry_impact_sell_pct   REAL,
        entry_round_trip_pct    REAL,
        entry_jup_rt_pct        REAL,   -- Jupiter-quoted RT friction at entry
        entry_r_m5              REAL,
        entry_r_h1              REAL,
        entry_buy_count_ratio   REAL,
        entry_vol_accel         REAL,
        baseline_trigger_id     TEXT,   -- trade_id of the strategy trade that triggered this baseline
        exited_at               TEXT,
        exit_price_usd          REAL,
        exit_price_native       REAL,
        exit_liq_usd            REAL,
        exit_liq_base           REAL,
        exit_k_invariant        REAL,
        exit_impact_sell_pct    REAL,
        exit_round_trip_pct     REAL,
        exit_reason             TEXT,
        gross_pnl_pct           REAL,
        shadow_pnl_pct          REAL,
        shadow_pnl_sol          REAL,
        shadow_pnl_pct_fee025   REAL,
        shadow_pnl_pct_fee060   REAL,
        shadow_pnl_pct_fee100   REAL,
        status                  TEXT    DEFAULT 'open'
    )
    """)
    c.execute("CREATE INDEX IF NOT EXISTS idx_sv1_strategy ON shadow_trades_v1(strategy, entered_at)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_sv1_status   ON shadow_trades_v1(status)")
    conn.commit()
    conn.close()
    logger.info("Table initialized: shadow_trades_v1")

def count_open_by_strategy(strategy: str) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "SELECT COUNT(*) FROM shadow_trades_v1 WHERE strategy = ? AND status = 'open'",
        (strategy,)
    )
    n = c.fetchone()[0]
    conn.close()
    return n

def get_open_trades() -> list[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM shadow_trades_v1 WHERE status = 'open'")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_latest_microstructure() -> list[dict]:
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT m.*
        FROM microstructure_log m
        INNER JOIN (
            SELECT mint_address, MAX(logged_at) as max_at
            FROM microstructure_log
            WHERE logged_at >= datetime('now', '-2 minutes')
              AND spam_flag = 0
            GROUP BY mint_address
        ) latest ON m.mint_address = latest.mint_address AND m.logged_at = latest.max_at
        INNER JOIN universe_snapshot u ON m.mint_address = u.mint_address
            AND u.snapshot_at = (SELECT MAX(snapshot_at) FROM universe_snapshot)
            AND u.eligible = 1 AND u.cpamm_valid_flag = 1
        ORDER BY m.vol_h24 DESC
    """)
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ── JUPITER FRICTION GATE ─────────────────────────────────────────────────────
def get_jupiter_rt_estimate(mint: str) -> float | None:
    """
    Get round-trip friction estimate from Jupiter quotes.
    Returns total RT fraction (e.g. 0.008 = 0.8%) or None if no route.
    Aborts entry if None (route risk).
    """
    sol_in_lamports = int(TRADE_SIZE_SOL * LAMPORTS_PER_SOL)
    try:
        # Buy quote: SOL -> token
        r_buy = requests.get(
            f"{JUPITER_BASE_URL}/v6/quote",
            params={
                "inputMint":   WSOL_MINT,
                "outputMint":  mint,
                "amount":      str(sol_in_lamports),
                "slippageBps": "50",
            },
            headers={"Authorization": f"Bearer {JUPITER_API_KEY}"},
            timeout=8,
        )
        buy_q = r_buy.json()
        if "outAmount" not in buy_q:
            return None  # no route
        tokens_out = int(buy_q["outAmount"])
        if tokens_out <= 0:
            return None

        # Sell quote: token -> SOL
        r_sell = requests.get(
            f"{JUPITER_BASE_URL}/v6/quote",
            params={
                "inputMint":   mint,
                "outputMint":  WSOL_MINT,
                "amount":      str(tokens_out),
                "slippageBps": "50",
            },
            headers={"Authorization": f"Bearer {JUPITER_API_KEY}"},
            timeout=8,
        )
        sell_q = r_sell.json()
        if "outAmount" not in sell_q:
            return None  # no sell route
        sol_back_lamports = int(sell_q["outAmount"])

        rt_friction = 1.0 - (sol_back_lamports / sol_in_lamports)
        return max(0.0, rt_friction)

    except Exception as e:
        logger.warning(f"Jupiter RT estimate failed for {mint[:8]}: {e}")
        return None

# ── PRICE FETCH ───────────────────────────────────────────────────────────────
def fetch_current_price(mint: str) -> dict | None:
    try:
        url = f"https://api.dexscreener.com/latest/dex/tokens/{mint}"
        r = requests.get(url, timeout=DEXSCREENER_TIMEOUT)
        data = r.json()
        pairs = data.get("pairs") or []
        if not pairs:
            return None
        # Pick highest-liquidity SOL pair
        sol_pairs = [p for p in pairs if (p.get("quoteToken", {}).get("symbol") or "").upper() == "SOL"]
        if not sol_pairs:
            sol_pairs = pairs
        best = max(sol_pairs, key=lambda p: float(p.get("liquidity", {}).get("usd") or 0))
        price_usd    = float(best.get("priceUsd") or 0)
        price_native = float(best.get("priceNative") or 0)
        liq_usd      = float(best.get("liquidity", {}).get("usd") or 0)
        liq_base     = float(best.get("liquidity", {}).get("base") or 0)
        liq_quote    = float(best.get("liquidity", {}).get("quote") or 0)
        k = liq_base * liq_quote if liq_base > 0 and liq_quote > 0 else None
        return {
            "price_usd":    price_usd,
            "price_native": price_native,
            "liq_usd":      liq_usd,
            "liq_base":     liq_base,
            "liq_quote_sol": liq_quote,
            "k_invariant":  k,
        }
    except Exception:
        return None

# ── ENTRY LOGIC ───────────────────────────────────────────────────────────────
def should_enter_momentum(row: dict) -> bool:
    p = STRATEGIES["momentum"]
    return (
        (row.get("r_m5") or 0)               >= p["entry_r_m5_min"] and
        (row.get("buy_count_ratio_m5") or 0)  >= p["entry_buy_count_ratio_min"] and
        (row.get("vol_accel_m5_vs_h1") or 0)  >= p["entry_vol_accel_min"]
    )

def should_enter_pullback(row: dict) -> bool:
    p = STRATEGIES["pullback"]
    return (
        (row.get("r_h1") or 0)               >= p["entry_r_h1_min"] and
        (row.get("r_m5") or 0)               <= p["entry_r_m5_max"] and
        (row.get("buy_count_ratio_m5") or 0)  >= p["entry_buy_count_ratio_min"]
    )

def open_trade(strategy: str, row: dict, baseline_trigger_id: str | None = None) -> str | None:
    """
    Open a shadow trade. Returns trade_id on success, None if blocked.
    Checks:
      1. Per-strategy cap (MAX_OPEN_PER_STRATEGY)
      2. Jupiter friction gate (<= 1.0% RT)
    """
    # Cap check
    if count_open_by_strategy(strategy) >= MAX_OPEN_PER_STRATEGY:
        logger.debug(f"SKIP {strategy}: already at MAX_OPEN_PER_STRATEGY={MAX_OPEN_PER_STRATEGY}")
        return None

    mint = row["mint_address"]

    # Jupiter friction gate
    jup_rt = get_jupiter_rt_estimate(mint)
    if jup_rt is None:
        logger.info(f"SKIP {strategy} {mint[:8]}: no Jupiter route (route risk)")
        return None
    if jup_rt > FRICTION_GATE_MAX_RT:
        logger.info(f"SKIP {strategy} {mint[:8]}: Jupiter RT {jup_rt*100:.2f}% > gate {FRICTION_GATE_MAX_RT*100:.1f}%")
        return None

    # CPAMM model (for logging/reporting, not gating)
    liq_b = row.get("liq_base") or 0
    liq_q = row.get("liq_quote_sol") or 0
    rt = cpamm_round_trip(TRADE_SIZE_SOL, liq_b, liq_q)
    k = liq_b * liq_q if liq_b > 0 and liq_q > 0 else None

    trade_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    conn = get_conn()
    conn.execute("""
        INSERT INTO shadow_trades_v1
        (trade_id, strategy, mint_address, token_symbol, pair_address,
         entered_at, entry_price_usd, entry_price_native,
         entry_liq_usd, entry_liq_quote_sol, entry_liq_base, entry_k_invariant,
         entry_impact_buy_pct, entry_impact_sell_pct, entry_round_trip_pct,
         entry_jup_rt_pct,
         entry_r_m5, entry_r_h1, entry_buy_count_ratio, entry_vol_accel,
         baseline_trigger_id, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        trade_id, strategy, mint,
        row.get("token_symbol"), row.get("pair_address"),
        now,
        row.get("price_usd"), row.get("price_native"),
        row.get("liq_usd"), liq_q, liq_b, k,
        round(rt["buy_slippage"], 6), round(rt["sell_slippage"], 6),
        round(rt["total_friction"], 6),
        round(jup_rt, 6),
        row.get("r_m5"), row.get("r_h1"),
        row.get("buy_count_ratio_m5"), row.get("vol_accel_m5_vs_h1"),
        baseline_trigger_id,
        "open",
    ))
    conn.commit()
    conn.close()

    logger.info(
        f"OPEN {strategy} {row.get('token_symbol','?')} ({mint[:8]}...) "
        f"jup_rt={jup_rt*100:.2f}% cpamm_rt={rt['total_friction']*100:.2f}%"
        + (f" [triggered_by={baseline_trigger_id[:8]}]" if baseline_trigger_id else "")
    )
    return trade_id

# ── EXIT LOGIC ────────────────────────────────────────────────────────────────
def close_trade(trade: dict, current: dict, reason: str):
    entry_price = trade["entry_price_usd"]
    exit_price  = current["price_usd"]
    if entry_price <= 0 or exit_price <= 0:
        return

    liq_b = current["liq_base"]
    liq_q = current["liq_quote_sol"]
    rt = cpamm_round_trip(TRADE_SIZE_SOL, liq_b, liq_q)

    gross_pnl_pct  = (exit_price / entry_price) - 1.0
    shadow_pnl_pct = gross_pnl_pct - rt["total_friction"]
    shadow_pnl_sol = shadow_pnl_pct * TRADE_SIZE_SOL

    # Fee scenarios: impact is fixed; fee component varies
    impact_only = rt["buy_slippage"] + rt["sell_slippage"]
    pnl_fee025  = gross_pnl_pct - (impact_only + 0.0025)
    pnl_fee060  = gross_pnl_pct - (impact_only + 0.006)
    pnl_fee100  = gross_pnl_pct - (impact_only + 0.01)

    now = datetime.now(timezone.utc).isoformat()
    conn = get_conn()
    conn.execute("""
        UPDATE shadow_trades_v1 SET
            exited_at               = ?,
            exit_price_usd          = ?,
            exit_price_native       = ?,
            exit_liq_usd            = ?,
            exit_liq_base           = ?,
            exit_k_invariant        = ?,
            exit_impact_sell_pct    = ?,
            exit_round_trip_pct     = ?,
            exit_reason             = ?,
            gross_pnl_pct           = ?,
            shadow_pnl_pct          = ?,
            shadow_pnl_sol          = ?,
            shadow_pnl_pct_fee025   = ?,
            shadow_pnl_pct_fee060   = ?,
            shadow_pnl_pct_fee100   = ?,
            status                  = 'closed'
        WHERE trade_id = ?
    """, (
        now,
        exit_price, current["price_native"],
        current["liq_usd"], liq_b, current.get("k_invariant"),
        round(rt["sell_slippage"], 6), round(rt["total_friction"], 6),
        reason,
        round(gross_pnl_pct, 6), round(shadow_pnl_pct, 6), round(shadow_pnl_sol, 6),
        round(pnl_fee025, 6), round(pnl_fee060, 6), round(pnl_fee100, 6),
        trade["trade_id"],
    ))
    conn.commit()
    conn.close()

    logger.info(
        f"CLOSE {trade['strategy']} {trade.get('token_symbol','?')} "
        f"reason={reason} gross={gross_pnl_pct*100:+.2f}% "
        f"fee060={pnl_fee060*100:+.2f}%"
    )

def check_exits(open_trades: list[dict]):
    for trade in open_trades:
        mint = trade["mint_address"]
        current = fetch_current_price(mint)
        if not current:
            continue
        entry_price = trade["entry_price_usd"]
        if entry_price <= 0:
            continue

        gross_pnl_pct = (current["price_usd"] / entry_price - 1.0) * 100
        entered_at = datetime.fromisoformat(trade["entered_at"])
        hold_min = (datetime.now(timezone.utc) - entered_at).total_seconds() / 60

        # Unified exit policy
        if hold_min >= EXIT_MAX_HOLD_MINUTES:
            close_trade(trade, current, "timeout")
            continue
        if gross_pnl_pct >= EXIT_TAKE_PROFIT_PCT:
            close_trade(trade, current, "tp")
            continue
        if gross_pnl_pct <= EXIT_STOP_LOSS_PCT:
            close_trade(trade, current, "sl")
            continue
        if EXIT_LIQ_CLIFF:
            entry_k = trade.get("entry_k_invariant")
            exit_k  = current.get("k_invariant")
            if entry_k and exit_k:
                cliff = k_lp_cliff(entry_k, exit_k, LP_CLIFF_THRESHOLD)
                if cliff["lp_removal_flag"]:
                    close_trade(trade, current, "lp_removal")
                    continue

        time.sleep(0.1)

# ── MAIN LOOP ─────────────────────────────────────────────────────────────────
def run():
    logger.info("=" * 65)
    logger.info("Shadow Trader v1 starting")
    logger.info(f"  Trade size:            {TRADE_SIZE_SOL} SOL")
    logger.info(f"  Max open/strategy:     {MAX_OPEN_PER_STRATEGY}")
    logger.info(f"  Exit TP/SL/timeout:    +{EXIT_TAKE_PROFIT_PCT}% / {EXIT_STOP_LOSS_PCT}% / {EXIT_MAX_HOLD_MINUTES}min")
    logger.info(f"  Friction gate (Jup):   <= {FRICTION_GATE_MAX_RT*100:.1f}% RT")
    logger.info(f"  LP cliff threshold:    {LP_CLIFF_THRESHOLD*100:.0f}% k-drop")
    logger.info(f"  Baseline:              matched-time (fires on each strategy entry)")
    logger.info("=" * 65)

    init_tables()

    # Wait for microstructure data
    for _ in range(20):
        rows = get_latest_microstructure()
        if rows:
            logger.info(f"Microstructure ready: {len(rows)} tokens")
            break
        logger.info("Waiting for microstructure data...")
        time.sleep(15)

    while True:
        loop_start = time.time()
        try:
            # 1. Check exits on all open trades
            open_trades = get_open_trades()
            if open_trades:
                check_exits(open_trades)

            # 2. Get fresh microstructure snapshot
            rows = get_latest_microstructure()
            if not rows:
                time.sleep(max(2, POLL_INTERVAL_SEC - (time.time() - loop_start)))
                continue

            # 3. Evaluate entry conditions for each token
            for row in rows:
                mint = row.get("mint_address")
                if not mint:
                    continue

                strategy_entered = None  # track which strategy (if any) entered this token

                if should_enter_momentum(row):
                    tid = open_trade("momentum", row)
                    if tid:
                        strategy_entered = tid

                if should_enter_pullback(row):
                    tid = open_trade("pullback", row)
                    if tid:
                        strategy_entered = tid

                # 4. Matched-time baseline: fires whenever momentum or pullback enters
                #    on a randomly chosen eligible token from the same scan cycle
                if strategy_entered is not None:
                    if count_open_by_strategy("baseline") < MAX_OPEN_PER_STRATEGY:
                        # Pick a random eligible token (can be same or different mint)
                        baseline_row = random.choice(rows)
                        open_trade("baseline", baseline_row, baseline_trigger_id=strategy_entered)

        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)

        elapsed = time.time() - loop_start
        time.sleep(max(2, POLL_INTERVAL_SEC - elapsed))

if __name__ == "__main__":
    run()
