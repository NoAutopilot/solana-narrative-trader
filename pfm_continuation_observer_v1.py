#!/usr/bin/env python3
"""
pfm_continuation_observer_v1.py
================================
READ-ONLY sidecar observer. No trades. No state changes. No wallet access.
No private keys required. Only reads from main DB + calls Jupiter QUOTE endpoint.
Hypothesis:
  pumpfun_mature continuation (r_m5 > 0) beats matched pumpfun_mature controls
  (r_m5 <= 0) on executable net forward markout at +5m using Jupiter quotes.
Preregistered rules (FROZEN — do not modify):
  - Signal:  top-1 candidate per fire with MAX(entry_r_m5), lane=pumpfun_mature, r_m5>0
  - Control: nearest match from same fire with r_m5<=0, deterministic distance metric
  - Horizons: +1m, +5m, +15m, +30m
  - Quote source: Jupiter Ultra API, fixed 0.01 SOL notional, slippageBps=50
  - Primary metric: mean signal-minus-control net_fee100 at +5m
Eval rules (FROZEN — do not modify):
  - Data-quality checks:
      entry quote coverage >= 95%
      conditional +5m coverage >= 95%
      row_valid = 100%
      timing jitter within same bounds as LCR observer
    If these fail → classify as INVALID / INFRA FAILURE (NOT strategy).
  - Hypothesis verdict evaluated ONLY after n >= 50 signals (minimum n >= 30):
      Primary:  mean(signal-control) net markout at +5m
      Report:   mean, median, % > 0, 95% CI (bootstrap)
  - Do NOT stop early based on n < 30 performance.
  - Do NOT tune gates, thresholds, or control-matching budgets.
Implementation Clarifications:
  - Skipped fires must be logged (no_signal / no_control).
  - Primary analysis inclusion: signal & control entry_quote_ok=1 AND fwd_quote_ok_5m=1.
"""
import sqlite3
import uuid
import time
import math
import logging
import sys
import os
import json
import hashlib
import requests
from datetime import datetime, timezone

# ── CONFIG (frozen) ──────────────────────────────────────────────────────────
VERSION             = "pfm_continuation_observer_v1"
DB_PATH             = "/root/solana_trader/data/solana_trader.db"
OBS_DB_PATH         = "/root/solana_trader/data/observer_pfm_cont_v1.db"
FIRE_INTERVAL_SEC   = 900          # 15-minute cadence
MICRO_WINDOW_SEC    = 120          # microstructure must be within 120s of fire_time
FIXED_NOTIONAL_SOL  = 0.01
LAMPORTS_IN         = 10_000_000   # 0.01 SOL in lamports
WSOL_MINT           = "So11111111111111111111111111111111111111112"
SLIPPAGE_BPS        = 50
JUP_QUOTE_URL       = "https://lite-api.jup.ag/swap/v1/quote"
JUP_TIMEOUT_SEC     = 10
JUP_RETRY_DELAYS    = [2, 5, 10]
JUP_API_KEY         = os.environ.get("JUPITER_API_KEY", "")
FEE_RATE            = 0.01         # 1% fee
HORIZONS            = [60, 300, 900, 1800]
HORIZON_LABELS      = ["1m", "5m", "15m", "30m"]
_TX_KEYS            = {"transaction", "tx", "signedTransaction", "serializedTransaction"}

LCR_MIN_AGE_H       = 24 * 30
PF_MATURE_MIN_AGE_H = 24.0

RUN_ID = str(uuid.uuid4())[:8]

# ── LOGGING ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(VERSION)

# ── HELPERS ───────────────────────────────────────────────────────────────────
def age_bucket(age_seconds: float) -> str:
    h = age_seconds / 3600.0
    if h < 1:      return "<1h"
    if h < 4:      return "1-4h"
    if h < 24:     return "4h-24h"
    if h < 168:    return "1-7d"
    return "7d+"

def liq_bucket(liq_usd: float) -> str:
    if liq_usd < 10_000:   return "<10k"
    if liq_usd < 50_000:   return "10k-50k"
    if liq_usd < 200_000:  return "50k-200k"
    return "200k+"

def vol_h1_bucket(vol_h1: float) -> str:
    if vol_h1 < 1000:      return "<1k"
    if vol_h1 < 10000:     return "1k-10k"
    if vol_h1 < 100000:    return "10k-100k"
    return "100k+"

def classify_lane(age_h: float, pumpfun_origin: int, venue: str) -> str:
    venue_l = (venue or "").lower()
    on_pumpswap = "pumpswap" in venue_l
    if pumpfun_origin:
        return "pumpfun_mature" if age_h >= PF_MATURE_MIN_AGE_H else "pumpfun_early"
    if on_pumpswap and age_h >= PF_MATURE_MIN_AGE_H:
        return "mature_pumpswap"
    if on_pumpswap:
        return "pumpfun_early"
    if age_h >= LCR_MIN_AGE_H:
        return "large_cap_ray"
    return "non_pumpfun_mature"

def venue_family(venue: str) -> str:
    v = (venue or "").lower()
    if "meteora" in v: return "meteora"
    if "raydium" in v: return "raydium"
    if "orca"    in v: return "orca"
    if "pumpswap" in v: return "pumpswap"
    return v.split("_")[0] if v else "unknown"

# ── DB SETUP ──────────────────────────────────────────────────────────────────
def init_observer_db():
    con = sqlite3.connect(OBS_DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS observer_pfm_cont_v1 (
        candidate_id                TEXT    PRIMARY KEY,
        run_id                      TEXT    NOT NULL,
        signal_fire_id              TEXT    NOT NULL,
        candidate_type              TEXT    NOT NULL,
        control_for_signal_id       TEXT,
        fire_time_epoch             INTEGER NOT NULL,
        fire_time_iso               TEXT    NOT NULL,
        snapshot_at_iso             TEXT,
        mint                        TEXT    NOT NULL,
        symbol                      TEXT,
        lane                        TEXT,
        venue                       TEXT,
        venue_family                TEXT,
        pumpfun_origin              INTEGER,
        age_seconds                 REAL,
        age_bucket                  TEXT,
        liquidity_usd               REAL,
        liquidity_bucket            TEXT,
        entry_vol_h1                REAL,
        vol_h1_bucket               TEXT,
        entry_r_m5                  REAL,
        entry_rv5m                  REAL,
        entry_range_5m              REAL,
        control_match_distance      REAL,
        quote_source                TEXT    DEFAULT 'Jupiter',
        fixed_notional_sol          REAL    DEFAULT 0.01,
        slippage_bps                INTEGER DEFAULT 50,
        entry_quote_ok              INTEGER,
        entry_out_amount_raw        INTEGER,
        entry_price_ref             REAL,
        entry_price_impact_pct      REAL,
        entry_quote_err             TEXT,
        entry_quote_ts_epoch        INTEGER,
        fwd_quote_ok_1m             INTEGER,
        fwd_sol_out_lamports_1m     INTEGER,
        fwd_gross_markout_1m        REAL,
        fwd_net_fee100_1m           REAL,
        fwd_quote_err_1m            TEXT,
        fwd_due_epoch_1m            INTEGER,
        fwd_exec_epoch_1m           INTEGER,
        fwd_quote_ts_epoch_1m       INTEGER,
        fwd_quote_ok_5m             INTEGER,
        fwd_sol_out_lamports_5m     INTEGER,
        fwd_gross_markout_5m        REAL,
        fwd_net_fee100_5m           REAL,
        fwd_quote_err_5m            TEXT,
        fwd_due_epoch_5m            INTEGER,
        fwd_exec_epoch_5m            INTEGER,
        fwd_quote_ts_epoch_5m       INTEGER,
        fwd_quote_ok_15m            INTEGER,
        fwd_sol_out_lamports_15m    INTEGER,
        fwd_gross_markout_15m       REAL,
        fwd_net_fee100_15m          REAL,
        fwd_quote_err_15m           TEXT,
        fwd_due_epoch_15m           INTEGER,
        fwd_exec_epoch_15m          INTEGER,
        fwd_quote_ts_epoch_15m      INTEGER,
        fwd_quote_ok_30m            INTEGER,
        fwd_sol_out_lamports_30m    INTEGER,
        fwd_gross_markout_30m       REAL,
        fwd_net_fee100_30m          REAL,
        fwd_quote_err_30m           TEXT,
        fwd_due_epoch_30m           INTEGER,
        fwd_exec_epoch_30m          INTEGER,
        fwd_quote_ts_epoch_30m      INTEGER,
        created_at_iso              TEXT    NOT NULL,
        updated_at_iso              TEXT    NOT NULL,
        row_valid                   INTEGER DEFAULT 1,
        invalid_reason              TEXT
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_obs_fire_type
        ON observer_pfm_cont_v1(run_id, signal_fire_id, candidate_type);
    CREATE INDEX IF NOT EXISTS idx_obs_run_fire
        ON observer_pfm_cont_v1(run_id, fire_time_epoch);
    CREATE TABLE IF NOT EXISTS observer_fire_log (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id          TEXT    NOT NULL,
        signal_fire_id  TEXT    NOT NULL,
        fire_time_epoch INTEGER NOT NULL,
        fire_time_iso   TEXT    NOT NULL,
        outcome         TEXT    NOT NULL,
        note            TEXT,
        created_at_iso  TEXT    NOT NULL
    );
    """)
    con.commit()
    con.close()
    log.info(f"Observer DB initialized: {OBS_DB_PATH}")

# ── CANDIDATE POOL ────────────────────────────────────────────────────────────
def get_candidate_pool(fire_epoch: int) -> list[dict]:
    fire_iso = datetime.fromtimestamp(fire_epoch, tz=timezone.utc).isoformat()
    micro_lo  = fire_epoch - MICRO_WINDOW_SEC
    micro_hi  = fire_epoch
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("""
        SELECT MAX(snapshot_at) AS snap_at
        FROM universe_snapshot
        WHERE snapshot_at <= ?
    """, (fire_iso,))
    row = cur.fetchone()
    snap_at = row["snap_at"] if row else None
    if not snap_at:
        con.close()
        return []
    cur.execute("""
        SELECT u.mint_address, u.token_symbol, u.venue, u.age_hours,
               u.liq_usd, u.vol_h1, u.pool_type, u.spam_flag
        FROM universe_snapshot u
        WHERE u.snapshot_at = ?
          AND u.eligible = 1
    """, (snap_at,))
    snap_rows = cur.fetchall()
    candidates = []
    for s in snap_rows:
        age_h      = s["age_hours"] or 0.0
        mint       = s["mint_address"]
        cur.execute("""
            SELECT m.r_m5, m.rv_5m, m.range_5m, m.vol_h1, m.liq_usd,
                   m.pumpfun_origin, m.venue, m.logged_at
            FROM microstructure_log m
            WHERE m.mint_address = ?
              AND m.logged_at <= ?
              AND m.logged_at >= ?
            ORDER BY m.logged_at DESC
            LIMIT 1
        """, (mint, fire_iso,
              datetime.fromtimestamp(micro_lo, tz=timezone.utc).isoformat()))
        micro = cur.fetchone()
        if not micro: continue
        pf_origin  = micro["pumpfun_origin"] or 0
        venue_str  = micro["venue"] or s["venue"] or ""
        r_m5       = micro["r_m5"]
        if r_m5 is None: continue
        lane = classify_lane(age_h, pf_origin, venue_str)
        if lane != "pumpfun_mature": continue
        candidates.append({
            "mint": mint, "symbol": s["token_symbol"], "lane": lane,
            "venue": venue_str, "venue_family": venue_family(venue_str),
            "pumpfun_origin": pf_origin, "age_seconds": age_h * 3600.0,
            "liquidity_usd": micro["liq_usd"] or s["liq_usd"] or 0.0,
            "entry_vol_h1": micro["vol_h1"] or s["vol_h1"] or 0.0,
            "entry_r_m5": r_m5, "entry_rv5m": micro["rv_5m"],
            "entry_range_5m": micro["range_5m"], "snapshot_at_iso": snap_at,
            "liquidity_bucket": liq_bucket(micro["liq_usd"] or s["liq_usd"] or 0.0),
            "vol_h1_bucket": vol_h1_bucket(micro["vol_h1"] or s["vol_h1"] or 0.0),
            "age_bucket": age_bucket(age_h * 3600.0)
        })
    con.close()
    return candidates

# ── MATCHING LOGIC ────────────────────────────────────────────────────────────
def select_signal(pool: list[dict]) -> dict | None:
    signal_pool = [c for c in pool if c["entry_r_m5"] > 0]
    if not signal_pool: return None
    signal_pool.sort(key=lambda x: (-x["entry_r_m5"], x["mint"]))
    return signal_pool[0]

def select_control(pool: list[dict], signal: dict) -> dict | None:
    control_pool = [c for c in pool if c["entry_r_m5"] <= 0]
    if not control_pool: return None
    best_c = None
    min_dist = float('inf')
    s_vol_log = math.log10(max(1.0, signal["entry_vol_h1"]))
    s_liq_log = math.log10(max(1.0, signal["liquidity_usd"]))
    s_age_log = math.log10(max(1.0, signal["age_seconds"]))
    for c in control_pool:
        c_vol_log = math.log10(max(1.0, c["entry_vol_h1"]))
        c_liq_log = math.log10(max(1.0, c["liquidity_usd"]))
        c_age_log = math.log10(max(1.0, c["age_seconds"]))
        dist = math.sqrt(
            2.0 * (s_vol_log - c_vol_log)**2 +
            1.0 * (s_liq_log - c_liq_log)**2 +
            1.0 * (s_age_log - c_age_log)**2
        )
        if dist < min_dist:
            min_dist = dist
            best_c = c
        elif abs(dist - min_dist) < 1e-9:
            if best_c is None or c["mint"] < best_c["mint"]:
                best_c = c
    if best_c: best_c["_match_distance"] = min_dist
    return best_c

# ── JUPITER QUOTES ────────────────────────────────────────────────────────────
def _jup_quote_get(input_mint: str, output_mint: str, amount: int) -> dict:
    headers  = ({"x-api-key": JUP_API_KEY} if JUP_API_KEY else {})
    params   = {"inputMint": input_mint, "outputMint": output_mint, "amount": amount}
    last_err = ""
    for attempt, delay in enumerate([0] + JUP_RETRY_DELAYS):
        if delay: time.sleep(delay)
        try:
            r = requests.get(JUP_QUOTE_URL, params=params, headers=headers, timeout=JUP_TIMEOUT_SEC)
            if r.status_code == 200:
                data = r.json()
                for k in _TX_KEYS:
                    if data.get(k) is not None:
                        return {"ok": False, "data": None, "err": f"tx_present_readonly_violation: {k}"}
                return {"ok": True, "data": data, "err": None}
            last_err = f"HTTP {r.status_code}: {r.text[:120]}"
            if r.status_code in (429, 500, 502, 503): continue
            return {"ok": False, "data": None, "err": last_err}
        except Exception as e: last_err = str(e)[:200]
    return {"ok": False, "data": None, "err": last_err}

def jup_buy_quote(mint: str) -> dict:
    ts = int(time.time())
    res = _jup_quote_get(WSOL_MINT, mint, LAMPORTS_IN)
    if not res["ok"]:
        return {"ok": 0, "out_amount": None, "price_impact": None, "price_ref": None, "quote_ts_epoch": ts, "err": res["err"]}
    data = res["data"]
    out_amount = int(data.get("outAmount", 0))
    impact = float(data.get("priceImpactPct", 0) or 0)
    price_ref = LAMPORTS_IN / out_amount if out_amount > 0 else None
    return {"ok": 1, "out_amount": out_amount, "price_impact": impact, "price_ref": price_ref, "quote_ts_epoch": ts, "err": None}

def jup_sell_quote(mint: str, token_amount: int) -> dict:
    ts = int(time.time())
    res = _jup_quote_get(mint, WSOL_MINT, token_amount)
    if not res["ok"]:
        return {"ok": 0, "sol_out": None, "quote_ts_epoch": ts, "err": res["err"]}
    sol_out = int(res["data"].get("outAmount", 0))
    return {"ok": 1, "sol_out": sol_out, "quote_ts_epoch": ts, "err": None}

def compute_markout(sol_out_lamports: int | None) -> tuple[float | None, float | None]:
    if sol_out_lamports is None: return None, None
    gross = (sol_out_lamports / LAMPORTS_IN) - 1.0
    net   = gross - FEE_RATE
    return gross, net

# ── DB WRITE ──────────────────────────────────────────────────────────────────
def upsert_candidate(row: dict):
    con = sqlite3.connect(OBS_DB_PATH)
    cur = con.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("""
        INSERT INTO observer_pfm_cont_v1 (
            candidate_id, run_id, signal_fire_id, candidate_type, control_for_signal_id,
            fire_time_epoch, fire_time_iso, snapshot_at_iso,
            mint, symbol, lane, venue, venue_family, pumpfun_origin,
            age_seconds, age_bucket, liquidity_usd, liquidity_bucket,
            entry_vol_h1, vol_h1_bucket,
            entry_r_m5, entry_rv5m, entry_range_5m,
            control_match_distance,
            quote_source, fixed_notional_sol, slippage_bps,
            entry_quote_ok, entry_out_amount_raw, entry_price_ref,
            entry_price_impact_pct, entry_quote_err,
            entry_quote_ts_epoch,
            created_at_iso, updated_at_iso
        ) VALUES (
            :candidate_id, :run_id, :signal_fire_id, :candidate_type, :control_for_signal_id,
            :fire_time_epoch, :fire_time_iso, :snapshot_at_iso,
            :mint, :symbol, :lane, :venue, :venue_family, :pumpfun_origin,
            :age_seconds, :age_bucket, :liquidity_usd, :liquidity_bucket,
            :entry_vol_h1, :vol_h1_bucket,
            :entry_r_m5, :entry_rv5m, :entry_range_5m,
            :control_match_distance,
            :quote_source, :fixed_notional_sol, :slippage_bps,
            :entry_quote_ok, :entry_out_amount_raw, :entry_price_ref,
            :entry_price_impact_pct, :entry_quote_err,
            :entry_quote_ts_epoch,
            :created_at_iso, :updated_at_iso
        )
        ON CONFLICT(run_id, signal_fire_id, candidate_type) DO UPDATE SET
            updated_at_iso = excluded.updated_at_iso
    """, {
        "candidate_id": row.get("candidate_id"),
        "run_id": row.get("run_id"),
        "signal_fire_id": row.get("signal_fire_id"),
        "candidate_type": row.get("candidate_type"),
        "control_for_signal_id": row.get("control_for_signal_id"),
        "fire_time_epoch": row.get("fire_time_epoch"),
        "fire_time_iso": row.get("fire_time_iso"),
        "snapshot_at_iso": row.get("snapshot_at_iso"),
        "mint": row.get("mint"),
        "symbol": row.get("symbol"),
        "lane": row.get("lane"),
        "venue": row.get("venue"),
        "venue_family": row.get("venue_family"),
        "pumpfun_origin": row.get("pumpfun_origin"),
        "age_seconds": row.get("age_seconds"),
        "age_bucket": row.get("age_bucket"),
        "liquidity_usd": row.get("liquidity_usd"),
        "liquidity_bucket": row.get("liquidity_bucket"),
        "entry_vol_h1": row.get("entry_vol_h1"),
        "vol_h1_bucket": row.get("vol_h1_bucket"),
        "entry_r_m5": row.get("entry_r_m5"),
        "entry_rv5m": row.get("entry_rv5m"),
        "entry_range_5m": row.get("entry_range_5m"),
        "control_match_distance": row.get("control_match_distance"),
        "quote_source": row.get("quote_source", "Jupiter"),
        "fixed_notional_sol": row.get("fixed_notional_sol", 0.01),
        "slippage_bps": row.get("slippage_bps", 50),
        "entry_quote_ok": row.get("entry_quote_ok"),
        "entry_out_amount_raw": row.get("entry_out_amount_raw"),
        "entry_price_ref": row.get("entry_price_ref"),
        "entry_price_impact_pct": row.get("entry_price_impact_pct"),
        "entry_quote_err": row.get("entry_quote_err"),
        "entry_quote_ts_epoch": row.get("entry_quote_ts_epoch"),
        "created_at_iso": now_iso,
        "updated_at_iso": now_iso
    })
    con.commit()
    con.close()

def update_fwd_quote(candidate_id: str, label: str, sol_out: int | None,
                     gross: float | None, net: float | None,
                     ok: int, err: str | None,
                     due_epoch: int, exec_epoch: int, quote_ts_epoch: int):
    con = sqlite3.connect(OBS_DB_PATH)
    cur = con.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    row_valid = 1
    invalid_reason = None
    if ok and gross is not None and net is not None:
        expected_net = gross - FEE_RATE
        if abs(net - expected_net) > 1e-6:
            row_valid = 0
            invalid_reason = f"net_invariant_fail_{label}"
    cur.execute(f"""
        UPDATE observer_pfm_cont_v1 SET
            fwd_quote_ok_{label}          = ?,
            fwd_sol_out_lamports_{label}  = ?,
            fwd_gross_markout_{label}     = ?,
            fwd_net_fee100_{label}        = ?,
            fwd_quote_err_{label}         = ?,
            fwd_due_epoch_{label}         = ?,
            fwd_exec_epoch_{label}        = ?,
            fwd_quote_ts_epoch_{label}    = ?,
            row_valid                     = CASE WHEN ? = 0 THEN 0 ELSE row_valid END,
            invalid_reason                = CASE WHEN ? IS NOT NULL THEN ? ELSE invalid_reason END,
            updated_at_iso                = ?
        WHERE candidate_id = ?
    """, (ok, sol_out, gross, net, err, due_epoch, exec_epoch, quote_ts_epoch, row_valid, invalid_reason, invalid_reason, now_iso, candidate_id))
    con.commit()
    con.close()

def log_fire(signal_fire_id: str, fire_epoch: int, fire_iso: str, outcome: str, note: str = ""):
    con = sqlite3.connect(OBS_DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO observer_fire_log
            (run_id, signal_fire_id, fire_time_epoch, fire_time_iso, outcome, note, created_at_iso)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (RUN_ID, signal_fire_id, fire_epoch, fire_iso, outcome, note, datetime.now(timezone.utc).isoformat()))
    con.commit()
    con.close()

# ── FORWARD QUOTE SCHEDULER ───────────────────────────────────────────────────
_pending_fwd: list[tuple[int, str, str, int, str, int]] = []

def schedule_fwd_quotes(candidate_id: str, mint: str, token_amount: int, fire_epoch: int):
    for sec, label in zip(HORIZONS, HORIZON_LABELS):
        due_epoch = fire_epoch + sec
        _pending_fwd.append((due_epoch, candidate_id, mint, token_amount, label, due_epoch))

def process_pending_fwd(now_epoch: int):
    still_pending = []
    for (target, cid, mint, amount, label, due_epoch) in _pending_fwd:
        if now_epoch >= target:
            exec_epoch = int(time.time())
            q = jup_sell_quote(mint, amount)
            gross, net = compute_markout(q["sol_out"])
            update_fwd_quote(cid, label, q["sol_out"], gross, net, q["ok"], q["err"], due_epoch, exec_epoch, q["quote_ts_epoch"])
            log.info(f"  fwd_{label} | {mint[:8]} | ok={q['ok']} | gross={gross} | net={net} | jitter={exec_epoch - due_epoch}s")
        else:
            still_pending.append((target, cid, mint, amount, label, due_epoch))
    _pending_fwd.clear()
    _pending_fwd.extend(still_pending)

# ── RUN FIRE ──────────────────────────────────────────────────────────────────
def run_fire(fire_epoch: int):
    fire_iso = datetime.fromtimestamp(fire_epoch, tz=timezone.utc).isoformat()
    signal_fire_id = hashlib.md5(f"{fire_epoch}_{VERSION}".encode()).hexdigest()[:8]
    log.info(f"Fire {signal_fire_id} @ {fire_iso}")
    pool = get_candidate_pool(fire_epoch)
    if not pool:
        log_fire(signal_fire_id, fire_epoch, fire_iso, "no_pool", "Empty candidate pool")
        return
    signal = select_signal(pool)
    if not signal:
        log_fire(signal_fire_id, fire_epoch, fire_iso, "no_signal", "No candidate with r_m5 > 0")
        return
    control = select_control(pool, signal)
    if not control:
        log_fire(signal_fire_id, fire_epoch, fire_iso, "no_control", "No candidate with r_m5 <= 0")
        return
    signal_id = str(uuid.uuid4())[:8]
    control_id = str(uuid.uuid4())[:8]
    sq = jup_buy_quote(signal["mint"])
    cq = jup_buy_quote(control["mint"])
    log.info(f"  Entry: sig_ok={sq['ok']} | ctl_ok={cq['ok']}")
    upsert_candidate({**signal, "candidate_id": signal_id, "run_id": RUN_ID, "signal_fire_id": signal_fire_id, "candidate_type": "signal", "control_for_signal_id": None, "fire_time_epoch": fire_epoch, "fire_time_iso": fire_iso, "control_match_distance": None, "entry_quote_ok": sq["ok"], "entry_out_amount_raw": sq["out_amount"], "entry_price_ref": sq.get("price_ref"), "entry_price_impact_pct": sq.get("price_impact"), "entry_quote_err": sq["err"], "entry_quote_ts_epoch": sq["quote_ts_epoch"]})
    upsert_candidate({**control, "candidate_id": control_id, "run_id": RUN_ID, "signal_fire_id": signal_fire_id, "candidate_type": "control", "control_for_signal_id": signal_id, "fire_time_epoch": fire_epoch, "fire_time_iso": fire_iso, "control_match_distance": control.get("_match_distance"), "entry_quote_ok": cq["ok"], "entry_out_amount_raw": cq["out_amount"], "entry_price_ref": cq.get("price_ref"), "entry_price_impact_pct": cq.get("price_impact"), "entry_quote_err": cq["err"], "entry_quote_ts_epoch": cq["quote_ts_epoch"]})
    if sq["ok"] and sq["out_amount"]: schedule_fwd_quotes(signal_id, signal["mint"], sq["out_amount"], fire_epoch)
    if cq["ok"] and cq["out_amount"]: schedule_fwd_quotes(control_id, control["mint"], cq["out_amount"], fire_epoch)
    log_fire(signal_fire_id, fire_epoch, fire_iso, "ok", f"sig={signal['mint'][:8]} ctl={control['mint'][:8]}")

def main():
    init_observer_db()
    log.info(f"PFM Observer {VERSION} run_id={RUN_ID} ready.")
    last_fire_epoch = 0
    while True:
        now_epoch = int(time.time())
        process_pending_fwd(now_epoch)
        current_bucket = (now_epoch // FIRE_INTERVAL_SEC) * FIRE_INTERVAL_SEC
        if current_bucket > last_fire_epoch:
            try:
                run_fire(current_bucket)
                last_fire_epoch = current_bucket
            except Exception as e:
                log.error(f"Fire error: {e}", exc_info=True)
        time.sleep(10)

if __name__ == "__main__":
    main()
