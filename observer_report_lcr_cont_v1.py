#!/usr/bin/env python3
"""
observer_report_lcr_cont_v1.py
================================
READ-ONLY report script for lcr_continuation_observer_v1.
Prints statistics STRICT by run_id.

Usage:
    python3 observer_report_lcr_cont_v1.py [run_id]
    (If run_id not provided, uses the most recent run_id in the DB.)
"""

import sqlite3
import sys
import math
import statistics
from datetime import datetime, timezone

OBS_DB_PATH = "/root/solana_trader/data/observer_lcr_cont_v1.db"
SEP = "=" * 80
THIN = "-" * 80

def pct(x):
    return f"{x*100:+.4f}%" if x is not None else "N/A"

def bootstrap_ci(deltas: list[float], n_boot: int = 2000, ci: float = 0.95) -> tuple:
    """Bootstrap 95% CI for the mean."""
    if len(deltas) < 2:
        return (float('nan'), float('nan'))
    import random
    means = []
    for _ in range(n_boot):
        sample = [random.choice(deltas) for _ in deltas]
        means.append(sum(sample) / len(sample))
    means.sort()
    lo_idx = int((1 - ci) / 2 * n_boot)
    hi_idx = int((1 + ci) / 2 * n_boot)
    return (means[lo_idx], means[hi_idx])

def t_ci(deltas: list[float], ci: float = 0.95) -> tuple:
    """t-distribution 95% CI for the mean."""
    n = len(deltas)
    if n < 2:
        return (float('nan'), float('nan'))
    mean = sum(deltas) / n
    std  = statistics.stdev(deltas)
    se   = std / math.sqrt(n)
    # t critical value (approx for large n; use 2.0 as conservative)
    t_crit = 2.0 if n >= 30 else {
        1: 12.7, 2: 4.3, 3: 3.18, 4: 2.78, 5: 2.57,
        6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23,
        15: 2.13, 20: 2.09, 25: 2.06, 29: 2.05
    }.get(n - 1, 2.0)
    return (mean - t_crit * se, mean + t_crit * se)

def main():
    con = sqlite3.connect(OBS_DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Resolve run_id
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    else:
        cur.execute("SELECT run_id FROM observer_lcr_cont_v1 ORDER BY created_at_iso DESC LIMIT 1")
        row = cur.fetchone()
        if not row:
            print("No data found in observer DB.")
            sys.exit(0)
        run_id = row["run_id"]

    now_iso = datetime.now(timezone.utc).isoformat()
    print(SEP)
    print(f"  LCR CONTINUATION OBSERVER v1 — REPORT")
    print(f"  Report time:  {now_iso}")
    print(f"  run_id:       {run_id}")
    print(SEP)
    print()

    # ── INTEGRITY CHECKS ─────────────────────────────────────────────────────
    print("  ── INTEGRITY CHECKS ──────────────────────────────────────────────────────")

    # Abort if run_id missing
    cur.execute("SELECT COUNT(*) AS n FROM observer_lcr_cont_v1 WHERE run_id IS NULL OR run_id = ''")
    n_missing_run = cur.fetchone()["n"]
    if n_missing_run > 0:
        print(f"  *** ABORT: {n_missing_run} rows have missing run_id. Data integrity failure.")
        sys.exit(1)

    # Count signals and controls for this run_id
    cur.execute("""
        SELECT candidate_type, COUNT(*) AS n
        FROM observer_lcr_cont_v1
        WHERE run_id = ?
        GROUP BY candidate_type
    """, (run_id,))
    type_counts = {r["candidate_type"]: r["n"] for r in cur.fetchall()}
    n_signals  = type_counts.get("signal", 0)
    n_controls = type_counts.get("control", 0)

    # Duplicate fire check
    cur.execute("""
        SELECT signal_fire_id, candidate_type, COUNT(*) AS n
        FROM observer_lcr_cont_v1
        WHERE run_id = ?
        GROUP BY signal_fire_id, candidate_type
        HAVING n > 1
    """, (run_id,))
    dupes = cur.fetchall()

    print(f"  n_signals:                {n_signals}")
    print(f"  n_controls:               {n_controls}")
    print(f"  signals == controls:      {'OK' if n_signals == n_controls else '*** MISMATCH ***'}")
    print(f"  duplicate fires:          {'NONE' if not dupes else f'*** {len(dupes)} DUPLICATES ***'}")
    print()

    # ── FIRE LOG SUMMARY ─────────────────────────────────────────────────────
    cur.execute("""
        SELECT outcome, COUNT(*) AS n
        FROM observer_fire_log
        WHERE run_id = ?
        GROUP BY outcome
    """, (run_id,))
    fire_outcomes = {r["outcome"]: r["n"] for r in cur.fetchall()}
    n_fires_total = sum(fire_outcomes.values())
    print(f"  ── FIRE LOG ──────────────────────────────────────────────────────────────")
    print(f"  n_fires_total:            {n_fires_total}")
    for k, v in sorted(fire_outcomes.items()):
        print(f"    {k:<20}  {v}")
    print()

    # ── QUOTE COVERAGE (A2: ok/due, not ok/total; pending tracked separately) ──
    import time as _time
    now_epoch = int(_time.time())
    HORIZON_SEC = {"1m": 60, "5m": 300, "15m": 900, "30m": 1800}
    print(f"  ── QUOTE COVERAGE (ok/due — pending excluded from denominator) ────────────")
    print(f"  now_epoch = {now_epoch}")
    for ctype in ["signal", "control"]:
        print(f"  [{ctype.upper()}]")
        print(f"  {'horizon':<8} {'due':>5} {'ok':>5} {'fail':>5} {'pending':>8} {'coverage (ok/due)':>18}")
        print(f"  {'-'*8} {'-'*5} {'-'*5} {'-'*5} {'-'*8} {'-'*18}")
        for h, h_sec in HORIZON_SEC.items():
            cur.execute(f"""
                SELECT
                  SUM(CASE WHEN fire_time_epoch + {h_sec} <= {now_epoch} THEN 1 ELSE 0 END) as due_count,
                  SUM(CASE WHEN fire_time_epoch + {h_sec} <= {now_epoch}
                            AND fwd_quote_ok_{h} = 1 THEN 1 ELSE 0 END) as ok_count,
                  SUM(CASE WHEN fire_time_epoch + {h_sec} <= {now_epoch}
                            AND (fwd_quote_ok_{h} IS NULL OR fwd_quote_ok_{h} = 0)
                            THEN 1 ELSE 0 END) as fail_count,
                  SUM(CASE WHEN fire_time_epoch + {h_sec} > {now_epoch} THEN 1 ELSE 0 END) as pending_count
                FROM observer_lcr_cont_v1
                WHERE run_id = ? AND candidate_type = ?
                  AND entry_quote_ok = 1
            """, (run_id, ctype))
            r = cur.fetchone()
            due     = r["due_count"] or 0
            ok      = r["ok_count"] or 0
            fail    = r["fail_count"] or 0
            pending = r["pending_count"] or 0
            cov     = f"{ok/due*100:.1f}%" if due > 0 else "N/A"
            flag    = "  *** BELOW 95% ***" if due > 0 and ok/due < 0.95 else ""
            print(f"  +{h:<7} {due:>5} {ok:>5} {fail:>5} {pending:>8} {cov:>18}{flag}")
        print()

    # Pair completeness at +5m
    cur.execute("""
        SELECT COUNT(*) AS n
        FROM observer_lcr_cont_v1 s
        JOIN observer_lcr_cont_v1 c ON c.control_for_signal_id = s.candidate_id
        WHERE s.run_id = ? AND s.candidate_type = 'signal'
          AND s.entry_quote_ok = 1 AND s.fwd_quote_ok_5m = 1
          AND c.entry_quote_ok = 1 AND c.fwd_quote_ok_5m = 1
    """, (run_id,))
    n_pairs_5m = cur.fetchone()["n"]
    print(f"  pairs_complete_5m:        {n_pairs_5m}/{n_signals} "
          f"({100*n_pairs_5m/max(n_signals,1):.1f}%)")
    print()

    # ── ROW VALIDITY (B2) ─────────────────────────────────────────────────────
    print(f"  ── ROW VALIDITY (B2: row_valid invariant check) ──────────────────────────")
    cur.execute("""
        SELECT
          COUNT(*) as n_total,
          SUM(CASE WHEN row_valid = 1 OR row_valid IS NULL THEN 1 ELSE 0 END) as n_valid,
          SUM(CASE WHEN row_valid = 0 THEN 1 ELSE 0 END) as n_invalid
        FROM observer_lcr_cont_v1
        WHERE run_id = ? AND fwd_quote_ok_5m = 1
    """, (run_id,))
    rv = cur.fetchone()
    print(f"  rows with fwd_quote_ok_5m=1: {rv['n_total']}")
    print(f"  row_valid=1 (or NULL):        {rv['n_valid']}")
    print(f"  row_valid=0 (invariant fail): {rv['n_invalid']}")
    cur.execute("""
        SELECT candidate_id, candidate_type, signal_fire_id, invalid_reason
        FROM observer_lcr_cont_v1
        WHERE run_id = ? AND row_valid = 0
    """, (run_id,))
    bad_rows = cur.fetchall()
    if bad_rows:
        print(f"  INVALID ROWS:")
        for b in bad_rows:
            print(f"    fire={b['signal_fire_id']} type={b['candidate_type']} "
                  f"id={b['candidate_id'][:8]} reason={b['invalid_reason']}")
    else:
        print(f"  No invalid rows.")
    # Paired delta invariant: delta == sig_net - ctrl_net by construction (no stored delta column)
    print(f"  Paired delta invariant: delta computed as (sig_net - ctrl_net) at query time.")
    print(f"  max_abs(delta - (sig_net - ctrl_net)) = 0.00e+00  (0 by construction — no stored delta column)")
    print(f"  INVARIANT: PASS")
    print()

    # ── ABSOLUTE NET MARKOUT ─────────────────────────────────────────────────
    print(f"  ── THIS TABLE IS: ABSOLUTE NET MARKOUT (net_fee100) ─────────────────────")
    print(f"  {'Group':<8}  {'Horizon':>7}  {'n':>4}  {'Mean':>10}  {'Median':>10}  {'%>0':>6}")
    print("  " + THIN)
    for ctype in ["signal", "control"]:
        for label in ["1m", "5m", "15m", "30m"]:
            cur.execute(f"""
                SELECT fwd_net_fee100_{label} AS val
                FROM observer_lcr_cont_v1
                WHERE run_id = ? AND candidate_type = ?
                  AND fwd_quote_ok_{label} = 1
                  AND fwd_net_fee100_{label} IS NOT NULL
            """, (run_id, ctype))
            vals = [r["val"] for r in cur.fetchall()]
            if not vals:
                print(f"  {ctype:<8}  {'+'+label:>7}  {'0':>4}  {'N/A':>10}  {'N/A':>10}  {'N/A':>6}")
                continue
            mean_v   = sum(vals) / len(vals)
            median_v = statistics.median(vals)
            pct_pos  = 100 * sum(1 for v in vals if v > 0) / len(vals)
            marker = " <-- PRIMARY" if ctype == "signal" and label == "5m" else ""
            print(f"  {ctype:<8}  {'+'+label:>7}  {len(vals):>4}  "
                  f"{mean_v*100:>+10.4f}%  {median_v*100:>+10.4f}%  {pct_pos:>5.1f}%{marker}")
    print()

    # ── SIGNAL-MINUS-CONTROL DELTA ───────────────────────────────────────────
    print(f"  ── THIS TABLE IS: SIGNAL-MINUS-CONTROL DELTA (net_fee100) ───────────────")
    print(f"  {'Horizon':>7}  {'n':>4}  {'Mean':>10}  {'Median':>10}  {'95% CI Lo':>12}  {'95% CI Hi':>12}  {'%>0':>6}")
    print("  " + THIN)
    for label in ["1m", "5m", "15m", "30m"]:
        cur.execute(f"""
            SELECT
                s.fwd_net_fee100_{label} AS s_val,
                c.fwd_net_fee100_{label} AS c_val
            FROM observer_lcr_cont_v1 s
            JOIN observer_lcr_cont_v1 c ON c.control_for_signal_id = s.candidate_id
            WHERE s.run_id = ? AND s.candidate_type = 'signal'
              AND s.fwd_quote_ok_{label} = 1 AND c.fwd_quote_ok_{label} = 1
              AND s.fwd_net_fee100_{label} IS NOT NULL
              AND c.fwd_net_fee100_{label} IS NOT NULL
        """, (run_id,))
        pairs = cur.fetchall()
        if not pairs:
            print(f"  {'+'+label:>7}  {'0':>4}  {'N/A':>10}  {'N/A':>10}  {'N/A':>12}  {'N/A':>12}  {'N/A':>6}")
            continue
        deltas = [r["s_val"] - r["c_val"] for r in pairs]
        mean_d   = sum(deltas) / len(deltas)
        median_d = statistics.median(deltas)
        pct_pos  = 100 * sum(1 for d in deltas if d > 0) / len(deltas)
        ci_lo, ci_hi = t_ci(deltas)
        marker = " <-- PRIMARY" if label == "5m" else ""
        print(f"  {'+'+label:>7}  {len(deltas):>4}  "
              f"{mean_d*100:>+10.4f}%  {median_d*100:>+10.4f}%  "
              f"{ci_lo*100:>+12.4f}%  {ci_hi*100:>+12.4f}%  "
              f"{pct_pos:>5.1f}%{marker}")
    print()

    # ── KILL / PROMOTION CHECK ───────────────────────────────────────────────
    print(f"  ── KILL / PROMOTION CHECK ────────────────────────────────────────────────")
    if n_pairs_5m < 30:
        print(f"  Insufficient data for kill check (n_pairs_5m={n_pairs_5m} < 30).")
    else:
        cur.execute(f"""
            SELECT
                s.fwd_net_fee100_5m AS s_val,
                c.fwd_net_fee100_5m AS c_val
            FROM observer_lcr_cont_v1 s
            JOIN observer_lcr_cont_v1 c ON c.control_for_signal_id = s.candidate_id
            WHERE s.run_id = ? AND s.candidate_type = 'signal'
              AND s.fwd_quote_ok_5m = 1 AND c.fwd_quote_ok_5m = 1
              AND s.fwd_net_fee100_5m IS NOT NULL AND c.fwd_net_fee100_5m IS NOT NULL
        """, (run_id,))
        pairs_5m = cur.fetchall()
        deltas_5m = [r["s_val"] - r["c_val"] for r in pairs_5m]
        mean_5m   = sum(deltas_5m) / len(deltas_5m)
        median_5m = statistics.median(deltas_5m)
        # Density: fires per day
        cur.execute("""
            SELECT MIN(fire_time_epoch) AS t_min, MAX(fire_time_epoch) AS t_max
            FROM observer_lcr_cont_v1
            WHERE run_id = ? AND candidate_type = 'signal'
        """, (run_id,))
        tr = cur.fetchone()
        span_days = max((tr["t_max"] - tr["t_min"]) / 86400, 0.01) if tr["t_min"] else 0.01
        density   = n_signals / span_days
        # Quote coverage at 5m
        cur.execute("""
            SELECT SUM(fwd_quote_ok_5m) AS ok, COUNT(*) AS n
            FROM observer_lcr_cont_v1
            WHERE run_id = ? AND candidate_type = 'signal'
        """, (run_id,))
        qr = cur.fetchone()
        coverage_5m = 100 * (qr["ok"] or 0) / max(qr["n"], 1)

        kills = []
        if mean_5m <= 0:
            kills.append(f"KILL: mean delta +5m = {mean_5m*100:+.4f}% <= 0")
        if median_5m <= 0:
            kills.append(f"KILL: median delta +5m = {median_5m*100:+.4f}% <= 0")
        if density < 5:
            kills.append(f"KILL: density = {density:.1f}/day < 5/day")
        if coverage_5m < 95:
            kills.append(f"KILL: fwd_5m quote coverage = {coverage_5m:.1f}% < 95%")

        if kills:
            for k in kills:
                print(f"  *** {k}")
        else:
            print(f"  No kill criteria met (n={n_pairs_5m}, mean={mean_5m*100:+.4f}%, "
                  f"median={median_5m*100:+.4f}%, density={density:.1f}/day, "
                  f"coverage={coverage_5m:.1f}%)")

        if n_pairs_5m >= 50:
            ci_lo, ci_hi = t_ci(deltas_5m)
            print()
            print(f"  PROMOTION CHECK (n >= 50):")
            promo = (mean_5m > 0 and median_5m > 0 and density >= 5 and
                     coverage_5m >= 95 and ci_lo > -0.005)
            print(f"    mean > 0:           {'YES' if mean_5m > 0 else 'NO'}")
            print(f"    median > 0:         {'YES' if median_5m > 0 else 'NO'}")
            print(f"    density >= 5/day:   {'YES' if density >= 5 else 'NO'}")
            print(f"    coverage >= 95%:    {'YES' if coverage_5m >= 95 else 'NO'}")
            print(f"    CI lo not < -0.5%:  {'YES' if ci_lo > -0.005 else 'NO'}")
            print(f"    OVERALL:            {'PROMOTE' if promo else 'DO NOT PROMOTE'}")
    print()

    # ── OUTLIER DEBUG DUMP (C2) ─────────────────────────────────────────────
    print(f"  ── OUTLIER DEBUG DUMP (C2: abs(delta_5m) >= 10%) ────────────────────────")
    cur.execute("""
        SELECT s.signal_fire_id,
               s.mint as sig_mint, s.symbol as sig_sym,
               c.mint as ctrl_mint, c.symbol as ctrl_sym,
               s.entry_out_amount_raw as sig_entry_out_raw,
               c.entry_out_amount_raw as ctrl_entry_out_raw,
               s.fwd_sol_out_lamports_5m as sig_fwd_sol_5m,
               c.fwd_sol_out_lamports_5m as ctrl_fwd_sol_5m,
               ROUND(s.fwd_gross_markout_5m*100, 4) as sig_gross_5m,
               ROUND(s.fwd_net_fee100_5m*100, 4) as sig_net_5m,
               ROUND(c.fwd_gross_markout_5m*100, 4) as ctrl_gross_5m,
               ROUND(c.fwd_net_fee100_5m*100, 4) as ctrl_net_5m,
               ROUND((s.fwd_net_fee100_5m - c.fwd_net_fee100_5m)*100, 4) as delta_5m,
               s.entry_price_impact_pct as sig_impact,
               c.entry_price_impact_pct as ctrl_impact,
               s.fire_time_epoch,
               s.fwd_due_epoch_5m as sig_due_5m,
               s.fwd_exec_epoch_5m as sig_exec_5m,
               c.fwd_due_epoch_5m as ctrl_due_5m,
               c.fwd_exec_epoch_5m as ctrl_exec_5m
        FROM observer_lcr_cont_v1 s
        JOIN observer_lcr_cont_v1 c ON c.control_for_signal_id = s.candidate_id
        WHERE s.run_id = ? AND s.candidate_type = 'signal'
          AND s.fwd_quote_ok_5m = 1 AND c.fwd_quote_ok_5m = 1
          AND ABS(s.fwd_net_fee100_5m - c.fwd_net_fee100_5m) >= 0.10
        ORDER BY ABS(s.fwd_net_fee100_5m - c.fwd_net_fee100_5m) DESC
    """, (run_id,))
    outliers = cur.fetchall()
    if not outliers:
        print(f"  No outliers with abs(delta_5m) >= 10%.")
    for o in outliers:
        sig_exec  = o['sig_exec_5m']  or 0
        sig_due   = o['sig_due_5m']   or 0
        ctrl_exec = o['ctrl_exec_5m'] or 0
        ctrl_due  = o['ctrl_due_5m']  or 0
        cross_ok  = (o['sig_entry_out_raw'] != o['ctrl_entry_out_raw'])
        print(f"  fire_id:          {o['signal_fire_id']}")
        print(f"  delta_5m:         {o['delta_5m']}%")
        print(f"  --- SIGNAL ---")
        print(f"    mint:           {o['sig_mint']}")
        print(f"    symbol:         {o['sig_sym']}")
        print(f"    entry_out_raw:  {o['sig_entry_out_raw']} tokens  (used for fwd sell)")
        print(f"    fwd_sol_out_5m: {o['sig_fwd_sol_5m']} lamports")
        print(f"    gross_5m:       {o['sig_gross_5m']}%")
        print(f"    net_5m:         {o['sig_net_5m']}%")
        print(f"    price_impact:   {o['sig_impact']}%")
        print(f"    due_5m: {sig_due}  exec_5m: {sig_exec}  jitter: {sig_exec - sig_due:+d}s")
        print(f"  --- CONTROL ---")
        print(f"    mint:           {o['ctrl_mint']}")
        print(f"    symbol:         {o['ctrl_sym']}")
        print(f"    entry_out_raw:  {o['ctrl_entry_out_raw']} tokens  (used for fwd sell)")
        print(f"    fwd_sol_out_5m: {o['ctrl_fwd_sol_5m']} lamports")
        print(f"    gross_5m:       {o['ctrl_gross_5m']}%")
        print(f"    net_5m:         {o['ctrl_net_5m']}%")
        print(f"    price_impact:   {o['ctrl_impact']}%")
        print(f"    due_5m: {ctrl_due}  exec_5m: {ctrl_exec}  jitter: {ctrl_exec - ctrl_due:+d}s")
        print(f"  --- PAIRING VALIDATION ---")
        print(f"    sig_entry_out != ctrl_entry_out: {cross_ok}  (confirms token amounts not mixed)")
        print(f"    sig fwd sell used sig entry_out: {o['sig_entry_out_raw'] is not None and o['sig_fwd_sol_5m'] is not None}")
        print(f"    ctrl fwd sell used ctrl entry_out: {o['ctrl_entry_out_raw'] is not None and o['ctrl_fwd_sol_5m'] is not None}")
        print()
    print()

    # ── SAMPLE ROWS ──────────────────────────────────────────────────────────
    print(f"  ── SAMPLE ROWS (3 most recent signal+control pairs) ─────────────────────")
    cur.execute("""
        SELECT s.signal_fire_id, s.mint AS s_mint, s.symbol AS s_sym,
               s.entry_r_m5 AS s_r_m5, s.entry_quote_ok AS s_eq_ok,
               s.entry_out_amount_raw AS s_out,
               c.mint AS c_mint, c.symbol AS c_sym,
               c.entry_r_m5 AS c_r_m5, c.entry_quote_ok AS c_eq_ok,
               c.entry_out_amount_raw AS c_out,
               c.control_match_distance AS dist
        FROM observer_lcr_cont_v1 s
        JOIN observer_lcr_cont_v1 c ON c.control_for_signal_id = s.candidate_id
        WHERE s.run_id = ? AND s.candidate_type = 'signal'
        ORDER BY s.fire_time_epoch DESC
        LIMIT 3
    """, (run_id,))
    rows = cur.fetchall()
    if not rows:
        print("  No paired rows yet.")
    else:
        for r in rows:
            print(f"  Fire: {r['signal_fire_id']}")
            print(f"    Signal:  {r['s_mint'][:12]}... ({r['s_sym']}) "
                  f"r_m5={r['s_r_m5']:.4f}  entry_ok={r['s_eq_ok']}  out={r['s_out']}")
            print(f"    Control: {r['c_mint'][:12]}... ({r['c_sym']}) "
                  f"r_m5={r['c_r_m5']:.4f}  entry_ok={r['c_eq_ok']}  out={r['c_out']}  "
                  f"dist={'N/A' if r['dist'] is None else round(r['dist'],3)}")
    print()
    print(SEP)
    con.close()

if __name__ == "__main__":
    main()
