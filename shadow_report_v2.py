#!/usr/bin/env python3
"""
shadow_report_v2.py — Run-scoped paired delta report for shadow trader.

REQUIREMENTS:
  --run_id is MANDATORY. No default. Hard error if missing.

USAGE:
  python3 shadow_report_v2.py --run_id 9a74d448
  python3 shadow_report_v2.py --run_id 9a74d448 --mode mini    # n>=3 pair health
  python3 shadow_report_v2.py --run_id 9a74d448 --mode decision # n>=20 full report

P0: mandatory run_id, correct pnl scaling (stored decimal * 100), join-based pairs
P1: integrity checks (missing_baseline, invalid_pair, rollover exclusion)
P2: mini-report at n>=3, decision report at n>=20
P3: position cap cross-run label (in harness; report shows rollover exclusion count)
"""

import sys
import sqlite3
import argparse
import random
from datetime import datetime, timezone

DB = "/root/solana_trader/data/solana_trader.db"

# ── CLI ────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--run_id", required=True,
                    help="MANDATORY: full or prefix of run_id to report on")
parser.add_argument("--mode", choices=["mini", "decision", "auto"], default="auto",
                    help="mini=pair health (n>=3), decision=full (n>=20), auto=pick by n")
args = parser.parse_args()

# ── DB ─────────────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# Resolve run_id (allow prefix)
rid_rows = conn.execute(
    "SELECT run_id, version, start_ts FROM run_registry WHERE run_id LIKE ? ORDER BY start_ts DESC LIMIT 1",
    (args.run_id + "%",)
).fetchall()
if not rid_rows:
    print(f"ERROR: run_id '{args.run_id}' not found in run_registry. Aborting.")
    sys.exit(1)

RID = rid_rows[0]["run_id"]
VERSION = rid_rows[0]["version"] or "?"
START_TS = rid_rows[0]["start_ts"]

# Time window
last_row = conn.execute(
    "SELECT MAX(COALESCE(exited_at, entered_at)) as last_ts FROM shadow_trades_v1 WHERE run_id=?",
    (RID,)
).fetchone()
END_TS = last_row["last_ts"] if last_row else "?"

now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

print("=" * 70)
print("SHADOW TRADER RUN-SCOPED REPORT")
print("=" * 70)
print(f"  run_id    : {RID}")
print(f"  version   : {VERSION}")
print(f"  window    : {START_TS} → {END_TS}")
print(f"  generated : {now_utc}")
print(f"  dataset   : run_id={RID} ONLY (no cross-run data)")
print("=" * 70)

# ── P0.2: PnL scaling proof — 5 sample rows ────────────────────────────────
print("\nP0.2 — PnL SCALING PROOF (stored decimal → displayed %)")
print("-" * 70)
samples = conn.execute("""
    SELECT trade_id, token_symbol, strategy, gross_pnl_pct, shadow_pnl_pct_fee100
    FROM shadow_trades_v1
    WHERE run_id=? AND status='closed' AND exit_reason != 'rollover_close'
    LIMIT 5
""", (RID,)).fetchall()
if samples:
    print(f"  {'trade_id':<10} {'token':<10} {'gross_decimal':>14} {'gross_pct%':>12} {'fee100_decimal':>15} {'fee100_pct%':>12}")
    for s in samples:
        gd = s["gross_pnl_pct"] or 0.0
        fd = s["shadow_pnl_pct_fee100"] or 0.0
        print(f"  {s['trade_id'][:8]:<10} {s['token_symbol']:<10} {gd:>14.6f} {gd*100:>11.4f}% {fd:>15.6f} {fd*100:>11.4f}%")
else:
    print("  No closed non-rollover trades yet for this run_id.")

# ── P1: INTEGRITY CHECKS ───────────────────────────────────────────────────
print("\nP1 — INTEGRITY CHECKS")
print("-" * 70)

# Total strategy trades (not baseline)
n_strat = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND strategy NOT LIKE 'baseline%'
""", (RID,)).fetchone()[0]

# Total baseline trades
n_base = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND strategy LIKE 'baseline%'
""", (RID,)).fetchone()[0]

# Missing baseline (strategy trade with no matching baseline)
n_missing_baseline = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1 s
    WHERE s.run_id=?
      AND s.strategy NOT LIKE 'baseline%'
      AND NOT EXISTS (
          SELECT 1 FROM shadow_trades_v1 b
          WHERE b.baseline_trigger_id = s.trade_id
            AND b.run_id = s.run_id
      )
""", (RID,)).fetchone()[0]

# invalid_pair count (flag only — no reason column in schema)
n_invalid = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND invalid_pair=1
""", (RID,)).fetchone()[0]
inv_rows = []  # no reason column available

# Rollover exclusions
n_rollover = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND exit_reason='rollover_close'
""", (RID,)).fetchone()[0]

print(f"  strategy trades (non-baseline) : {n_strat}")
print(f"  baseline trades                : {n_base}")
print(f"  missing_baseline               : {n_missing_baseline}  {'✓ OK' if n_missing_baseline == 0 else '⚠ ALERT — atomic pairing may have failed'}")
print(f"  invalid_pair total             : {n_invalid}  {'✓ OK' if n_invalid == 0 else '⚠ ALERT — check harness logs for cause'}")
print(f"  rollover_close excluded        : {n_rollover}  (not counted in any PnL summary)")

# ── P0.3 + P0.4: JOIN-BASED CLOSED PAIRS ──────────────────────────────────
print("\nP0.3 — JOIN-BASED CLOSED PAIR COUNTING")
print("-" * 70)

pairs = conn.execute("""
    SELECT
        s.trade_id        AS s_id,
        s.token_symbol    AS s_token,
        s.strategy        AS s_strat,
        s.entered_at      AS s_entered,
        s.exited_at       AS s_exited,
        s.exit_reason     AS s_exit,
        s.gross_pnl_pct   AS s_gross,
        s.shadow_pnl_pct_fee100 AS s_fee100,
        b.trade_id        AS b_id,
        b.token_symbol    AS b_token,
        b.strategy        AS b_strat,
        b.exited_at       AS b_exited,
        b.exit_reason     AS b_exit,
        b.gross_pnl_pct   AS b_gross,
        b.shadow_pnl_pct_fee100 AS b_fee100
    FROM shadow_trades_v1 s
    JOIN shadow_trades_v1 b
        ON b.baseline_trigger_id = s.trade_id
       AND b.run_id = s.run_id
    WHERE s.run_id = ?
      AND s.status = 'closed'
      AND b.status = 'closed'
      AND s.strategy NOT LIKE 'baseline%'
      AND s.exit_reason != 'rollover_close'
      AND b.exit_reason != 'rollover_close'
    ORDER BY s.exited_at ASC
""", (RID,)).fetchall()

n_pairs = len(pairs)
print(f"  n_closed_pairs (join-based) : {n_pairs}")

# Also count strategy still open, baseline still open
n_strat_open = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND status='open' AND strategy NOT LIKE 'baseline%'
""", (RID,)).fetchone()[0]
n_base_open = conn.execute("""
    SELECT COUNT(*) FROM shadow_trades_v1
    WHERE run_id=? AND status='open' AND strategy LIKE 'baseline%'
""", (RID,)).fetchone()[0]
print(f"  strategy still open         : {n_strat_open}")
print(f"  baseline still open         : {n_base_open}")

# ── Decide mode ────────────────────────────────────────────────────────────
mode = args.mode
if mode == "auto":
    if n_pairs >= 20:
        mode = "decision"
    elif n_pairs >= 3:
        mode = "mini"
    else:
        mode = "none"

print(f"\n  Mode selected: {mode.upper()} (n_pairs={n_pairs})")

if n_pairs == 0:
    print("\n  No closed pairs yet. Re-run when n_closed_pairs >= 3.")
    sys.exit(0)

# ── MINI-REPORT (n>=3) ─────────────────────────────────────────────────────
if mode in ("mini", "decision"):
    print("\n" + "=" * 70)
    print("PAIR HEALTH MINI-REPORT (run-scoped, join-based)")
    print("=" * 70)
    print(f"{'#':<3} {'s_token':<10} {'b_token':<10} {'entry':<20} {'s_exit':<9} {'b_exit':<9} "
          f"{'s_gross%':>9} {'b_gross%':>9} {'s_f100%':>8} {'b_f100%':>8} {'delta%':>8}")
    print("-" * 110)

    deltas = []
    for i, p in enumerate(pairs, 1):
        sg = (p["s_gross"] or 0.0) * 100
        bg = (p["b_gross"] or 0.0) * 100
        sf = (p["s_fee100"] or 0.0) * 100
        bf = (p["b_fee100"] or 0.0) * 100
        delta = sf - bf
        deltas.append(delta)
        print(f"{i:<3} {p['s_token']:<10} {p['b_token']:<10} "
              f"{(p['s_entered'] or '')[:19]:<20} "
              f"{p['s_exit']:<9} {p['b_exit']:<9} "
              f"{sg:>9.3f} {bg:>9.3f} {sf:>8.3f} {bf:>8.3f} {delta:>8.3f}")

    print("-" * 110)
    print(f"\n  INTEGRITY: missing_baseline={n_missing_baseline} invalid_pair={n_invalid} rollover_excluded={n_rollover}")
    print(f"  PnL SCALE: stored as decimal, displayed as % (×100). Verified above in P0.2.")

    # Summary stats
    n = len(deltas)
    mean_d = sum(deltas) / n
    sorted_d = sorted(deltas)
    median_d = sorted_d[n // 2] if n % 2 == 1 else (sorted_d[n//2-1] + sorted_d[n//2]) / 2
    pct_pos = 100.0 * sum(1 for d in deltas if d > 0) / n

    print(f"\n  DELTA SUMMARY (fee100, strategy − baseline, in %):")
    print(f"    n_pairs    : {n}")
    print(f"    mean delta : {mean_d:+.4f}%")
    print(f"    median     : {median_d:+.4f}%")
    print(f"    %delta>0   : {pct_pos:.1f}%")

    # Bootstrap 95% CI
    if n >= 3:
        random.seed(42)
        boot_means = []
        for _ in range(5000):
            sample = [random.choice(deltas) for _ in range(n)]
            boot_means.append(sum(sample) / n)
        boot_means.sort()
        ci_lo = boot_means[int(0.025 * 5000)]
        ci_hi = boot_means[int(0.975 * 5000)]
        print(f"    95% CI     : [{ci_lo:+.4f}%, {ci_hi:+.4f}%]")
        print(f"    CI note    : {'CI crosses zero — insufficient evidence of edge' if ci_lo < 0 < ci_hi else ('CI entirely positive — strategy outperforming' if ci_lo > 0 else 'CI entirely negative — strategy underperforming')}")

# ── DECISION REPORT (n>=20) ────────────────────────────────────────────────
if mode == "decision":
    print("\n" + "=" * 70)
    print("DECISION REPORT (n>=20, run-scoped)")
    print("=" * 70)

    # Lane breakdown
    print("\n2) LANE BREAKDOWN")
    print("-" * 70)
    lane_map = {}
    for p in pairs:
        # Lane is embedded in the OPEN log but not in the trade table directly.
        # Use strategy name as proxy; actual lane stored in token metadata.
        # Best we can do from DB: group by token prefix heuristic.
        # If lane column exists in shadow_trades_v1, use it.
        pass

    # Try to get lane from the trade table if column exists
    cols = [r[1] for r in conn.execute("PRAGMA table_info(shadow_trades_v1)").fetchall()]
    has_lane = "lane" in cols

    if has_lane:
        lane_rows = conn.execute("""
            SELECT s.lane AS lane, COUNT(*) as n,
                   AVG(s.shadow_pnl_pct_fee100 - b.shadow_pnl_pct_fee100) as avg_delta
            FROM shadow_trades_v1 s
            JOIN shadow_trades_v1 b ON b.baseline_trigger_id = s.trade_id AND b.run_id = s.run_id
            WHERE s.run_id=? AND s.status='closed' AND b.status='closed'
              AND s.strategy NOT LIKE 'baseline%'
              AND s.exit_reason != 'rollover_close' AND b.exit_reason != 'rollover_close'
            GROUP BY s.lane
        """, (RID,)).fetchall()
        for lr in lane_rows:
            print(f"  lane={lr['lane'] or 'unknown':<25} n={lr['n']}  avg_delta_fee100={lr['avg_delta']*100:+.4f}%")
    else:
        print("  (lane column not in shadow_trades_v1 — log-level only)")

    # Exit reason breakdown
    print("\n3) EXIT REASON BREAKDOWN")
    print("-" * 70)
    exit_rows = conn.execute("""
        SELECT s.exit_reason, COUNT(*) as n,
               AVG(s.gross_pnl_pct)*100 as avg_gross_pct,
               AVG(s.shadow_pnl_pct_fee100)*100 as avg_fee100_pct,
               'strategy' as leg
        FROM shadow_trades_v1 s
        JOIN shadow_trades_v1 b ON b.baseline_trigger_id = s.trade_id AND b.run_id = s.run_id
        WHERE s.run_id=? AND s.status='closed' AND b.status='closed'
          AND s.strategy NOT LIKE 'baseline%'
          AND s.exit_reason != 'rollover_close' AND b.exit_reason != 'rollover_close'
        GROUP BY s.exit_reason
        UNION ALL
        SELECT b.exit_reason, COUNT(*) as n,
               AVG(b.gross_pnl_pct)*100 as avg_gross_pct,
               AVG(b.shadow_pnl_pct_fee100)*100 as avg_fee100_pct,
               'baseline' as leg
        FROM shadow_trades_v1 s
        JOIN shadow_trades_v1 b ON b.baseline_trigger_id = s.trade_id AND b.run_id = s.run_id
        WHERE s.run_id=? AND s.status='closed' AND b.status='closed'
          AND s.strategy NOT LIKE 'baseline%'
          AND s.exit_reason != 'rollover_close' AND b.exit_reason != 'rollover_close'
        GROUP BY b.exit_reason
        ORDER BY leg, n DESC
    """, (RID, RID)).fetchall()

    print(f"  {'leg':<10} {'exit_reason':<15} {'n':>4} {'avg_gross%':>11} {'avg_fee100%':>12}")
    for er in exit_rows:
        print(f"  {er['leg']:<10} {er['exit_reason'] or 'NULL':<15} {er['n']:>4} "
              f"{er['avg_gross_pct']:>11.4f} {er['avg_fee100_pct']:>12.4f}")

    # Concentration check
    print("\n4) CONCENTRATION CHECK (top-3 token contribution)")
    print("-" * 70)
    total_abs_delta = sum(abs(d) for d in deltas)
    token_deltas = {}
    for p in pairs:
        tok = p["s_token"]
        sf = (p["s_fee100"] or 0.0) * 100
        bf = (p["b_fee100"] or 0.0) * 100
        token_deltas[tok] = token_deltas.get(tok, 0) + (sf - bf)

    sorted_tokens = sorted(token_deltas.items(), key=lambda x: abs(x[1]), reverse=True)
    top3_abs = sum(abs(v) for _, v in sorted_tokens[:3])
    conc_pct = min(100.0, (top3_abs / total_abs_delta * 100) if total_abs_delta > 0 else 0.0)
    print(f"  top-3 token concentration: {conc_pct:.1f}% of total |delta|")
    for tok, dv in sorted_tokens[:5]:
        print(f"    {tok:<15} cumulative_delta={dv:+.4f}%")

    # Final verdict
    n = len(deltas)
    mean_d = sum(deltas) / n
    sorted_d = sorted(deltas)
    median_d = sorted_d[n // 2] if n % 2 == 1 else (sorted_d[n//2-1] + sorted_d[n//2]) / 2
    pct_pos = 100.0 * sum(1 for d in deltas if d > 0) / n
    random.seed(42)
    boot_means = [sum(random.choice(deltas) for _ in range(n)) / n for _ in range(5000)]
    boot_means.sort()
    ci_lo = boot_means[int(0.025 * 5000)]
    ci_hi = boot_means[int(0.975 * 5000)]

    print("\n" + "=" * 70)
    print("DECISION SUMMARY")
    print("=" * 70)
    print(f"  n_pairs       : {n}")
    print(f"  mean delta    : {mean_d:+.4f}%  (fee100, strategy − baseline)")
    print(f"  median delta  : {median_d:+.4f}%")
    print(f"  %delta > 0    : {pct_pos:.1f}%")
    print(f"  95% CI        : [{ci_lo:+.4f}%, {ci_hi:+.4f}%]")
    if ci_lo > 0:
        verdict = "POSITIVE EDGE — CI entirely above zero. Consider extending run."
    elif ci_hi < 0:
        verdict = "NEGATIVE EDGE — CI entirely below zero. Strategy underperforming."
    else:
        verdict = "INCONCLUSIVE — CI crosses zero. Need more pairs."
    print(f"  VERDICT       : {verdict}")

print("\n" + "=" * 70)
conn.close()
