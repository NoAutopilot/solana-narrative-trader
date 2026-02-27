#!/usr/bin/env python3
"""
diag_status.py — One-command health snapshot for the shadow trader.

Usage:
    python3 diag_status.py

Prints:
  - Current run_id, signature, commit
  - Last tick: timestamp, eligible/tradeable/opened, reason, best_token, best_block_reason
  - What-if gate counters for the last tick (NULL = not computed)
  - Last trade entered_at / last trade exited_at
  - n_closed_pairs for the CURRENT signature (so you can see if scanning is broken
    vs market is quiet vs a gate is too tight)

No arguments required. Always reads from the live DB.
"""

import sqlite3
import sys
from datetime import datetime, timezone

DB = "/root/solana_trader/data/solana_trader.db"

def fmt(val, default="—"):
    if val is None:
        return default
    return str(val)

def ts_ago(ts_str):
    """Return a human-readable 'X min ago' string from an ISO timestamp."""
    if not ts_str:
        return "—"
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - ts
        secs = int(delta.total_seconds())
        if secs < 0:
            return "in the future?"
        if secs < 60:
            return f"{secs}s ago"
        if secs < 3600:
            return f"{secs // 60}m ago"
        return f"{secs // 3600}h {(secs % 3600) // 60}m ago"
    except Exception:
        return ts_str[:19]

try:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
except Exception as e:
    print(f"ERROR: Cannot open DB at {DB}: {e}")
    sys.exit(1)

print("=" * 70)
print("SHADOW TRADER — HEALTH SNAPSHOT")
print(f"generated : {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
print("=" * 70)

# ── Current run ────────────────────────────────────────────────────────────
run_row = conn.execute(
    "SELECT run_id, version, git_commit, start_ts, signature "
    "FROM run_registry ORDER BY start_ts DESC LIMIT 1"
).fetchone()

if not run_row:
    print("  No runs found in run_registry.")
    conn.close()
    sys.exit(0)

run_id  = run_row["run_id"]
version = run_row["version"] or "?"
commit  = (run_row["git_commit"] or "?")[:8]
sig     = run_row["signature"] or "NULL (pre-v1.15)"
started = (run_row["start_ts"] or "?")[:19]

print(f"\n  CURRENT RUN")
print(f"  run_id    : {run_id[:8]}  ({ts_ago(run_row['start_ts'])})")
print(f"  version   : {version}")
print(f"  commit    : {commit}")
print(f"  signature : {sig}")
print(f"  started   : {started} UTC")

# ── Last tick ──────────────────────────────────────────────────────────────
tick_row = conn.execute(
    "SELECT logged_at, eligible_count, tradeable_count, opened_trade_bool, "
    "       reason_no_trade, best_token, best_score, best_block_reason, "
    "       whatif_no_pf_stability, whatif_no_anti_chase, whatif_no_pf_early, "
    "       whatif_no_lane_liq, whatif_no_lane_vol "
    "FROM selection_tick_log "
    "WHERE run_id = ? "
    "ORDER BY logged_at DESC LIMIT 1",
    (run_id,)
).fetchone()

print(f"\n  LAST TICK")
if tick_row:
    reason_str = tick_row["reason_no_trade"] or "NULL"
    opened_str = "YES" if tick_row["opened_trade_bool"] else "no"
    best_sc_str = f"{tick_row['best_score']:.4f}" if tick_row["best_score"] is not None else "—"
    print(f"  timestamp : {fmt(tick_row['logged_at'])[:19]} UTC  ({ts_ago(tick_row['logged_at'])})")
    print(f"  eligible  : {fmt(tick_row['eligible_count'])}  tradeable: {fmt(tick_row['tradeable_count'])}  opened: {opened_str}")
    print(f"  reason    : {reason_str}")
    print(f"  best_tok  : {fmt(tick_row['best_token'])}  score={best_sc_str}  block={fmt(tick_row['best_block_reason'])}")
    # What-if counters
    wi_pf_stab  = tick_row["whatif_no_pf_stability"]
    wi_anti     = tick_row["whatif_no_anti_chase"]
    wi_pf_early = tick_row["whatif_no_pf_early"]
    wi_liq      = tick_row["whatif_no_lane_liq"]
    wi_vol      = tick_row["whatif_no_lane_vol"]
    def wi_fmt(v):
        return str(v) if v is not None else "NULL(not computed)"
    print(f"  what-if   : no_pf_stab={wi_fmt(wi_pf_stab)}  no_anti_chase={wi_fmt(wi_anti)}  "
          f"no_pf_early={wi_fmt(wi_pf_early)}  no_liq={wi_fmt(wi_liq)}  no_vol={wi_fmt(wi_vol)}")
else:
    print("  No tick rows found for current run yet.")

# ── Last trade entered / exited ────────────────────────────────────────────
last_entered = conn.execute(
    "SELECT entered_at, token_symbol, strategy FROM shadow_trades_v1 "
    "WHERE run_id = ? ORDER BY entered_at DESC LIMIT 1",
    (run_id,)
).fetchone()

last_exited = conn.execute(
    "SELECT exited_at, token_symbol, strategy, gross_pnl_pct FROM shadow_trades_v1 "
    "WHERE run_id = ? AND status='closed' ORDER BY exited_at DESC LIMIT 1",
    (run_id,)
).fetchone()

print(f"\n  LAST TRADE")
if last_entered:
    strat_short = "strategy" if not last_entered["strategy"].startswith("baseline") else "baseline"
    print(f"  entered   : {fmt(last_entered['entered_at'])[:19]} UTC  ({ts_ago(last_entered['entered_at'])})  "
          f"token={fmt(last_entered['token_symbol'])}  leg={strat_short}")
else:
    print("  entered   : — (no trades this run)")

if last_exited:
    gross_pct = (last_exited["gross_pnl_pct"] or 0.0) * 100
    strat_short = "strategy" if not last_exited["strategy"].startswith("baseline") else "baseline"
    print(f"  exited    : {fmt(last_exited['exited_at'])[:19]} UTC  ({ts_ago(last_exited['exited_at'])})  "
          f"token={fmt(last_exited['token_symbol'])}  gross={gross_pct:+.4f}%  leg={strat_short}")
else:
    print("  exited    : — (no closed trades this run)")

# ── n_closed_pairs for current signature ──────────────────────────────────
print(f"\n  CLOSED PAIRS — CURRENT SIGNATURE ({sig[:16]})")
if sig and sig != "NULL (pre-v1.15)":
    sig_pairs = conn.execute("""
        SELECT COUNT(*) / 2 AS n_pairs, MAX(st.exited_at) AS last_exit
        FROM shadow_trades_v1 st
        JOIN run_registry rr ON rr.run_id = st.run_id
        WHERE rr.signature = ?
          AND st.status = 'closed'
          AND st.exit_reason != 'rollover_close'
    """, (sig,)).fetchone()
    n_sig_pairs = sig_pairs["n_pairs"] if sig_pairs else 0
    last_sig_exit = (sig_pairs["last_exit"] or "—")[:19] if sig_pairs else "—"
    print(f"  n_pairs   : {n_sig_pairs}  (last_exit: {last_sig_exit} UTC)")
else:
    # Fallback: count by version
    ver_pairs = conn.execute("""
        SELECT COUNT(*) / 2 AS n_pairs, MAX(exited_at) AS last_exit
        FROM shadow_trades_v1
        WHERE version = ?
          AND status = 'closed'
          AND exit_reason != 'rollover_close'
    """, (version,)).fetchone()
    n_ver_pairs = ver_pairs["n_pairs"] if ver_pairs else 0
    last_ver_exit = (ver_pairs["last_exit"] or "—")[:19] if ver_pairs else "—"
    print(f"  n_pairs   : {n_ver_pairs}  (by version={version}, last_exit: {last_ver_exit} UTC)")
    print(f"  NOTE: signature not available — using version fallback")

# ── Quick diagnosis hint ───────────────────────────────────────────────────
print(f"\n  DIAGNOSIS HINT")
if tick_row:
    mins_since_tick = None
    try:
        ts = datetime.fromisoformat((tick_row["logged_at"] or "").replace("Z", "+00:00"))
        mins_since_tick = (datetime.now(timezone.utc) - ts).total_seconds() / 60
    except Exception:
        pass
    if mins_since_tick is not None and mins_since_tick > 20:
        print(f"  ⚠ Last tick was {mins_since_tick:.0f} min ago — scanner may be stalled.")
    elif tick_row["opened_trade_bool"]:
        print(f"  ✓ Last tick opened a trade — system is healthy.")
    elif tick_row["reason_no_trade"] == "no_tradeable_tokens":
        wi_pf_early = tick_row["whatif_no_pf_early"]
        if wi_pf_early is not None and wi_pf_early > 0:
            print(f"  Market quiet. Binding gate: pf_early (lifting it would give {wi_pf_early} tradeable tokens).")
        else:
            print(f"  Market quiet. No single gate is clearly binding — multiple gates firing.")
    elif tick_row["reason_no_trade"] == "tradeable_lt_2":
        print(f"  Only 1 tradeable token — need 2 for baseline slot. Market is thin.")
    else:
        print(f"  reason={tick_row['reason_no_trade']} — check logs for details.")
else:
    print(f"  No tick data yet for this run.")

print("=" * 70)
conn.close()
