#!/usr/bin/env python3
"""
export_per_fire.py — Per-fire audit table generator.

Usage:
  python3 export_per_fire.py --run-id <run_id> --db <path_to_db> --table <table_name> \
      [--observer-name <name>] [--lane <lane>] [--out-dir <dir>]

Outputs:
  <out_dir>/<run_id>/per_fire.csv
  <out_dir>/<run_id>/per_fire.md

Sample definitions supported (printed at top of every report):
  ALL_COMPLETED_VIEW  : all completed +5m pairs for the run_id  [DEFAULT]
  TIMING_VALID_VIEW   : ALL_COMPLETED + row_valid=1 + jitter<=20s gates
  SNAPSHOT_VIEW       : first N completed +5m pairs (use --snapshot-n)
"""
import argparse
import csv
import json
import math
import os
import sqlite3
import sys
from datetime import datetime, timezone

OUTLIER_THRESHOLD = 0.10
JITTER_GATE_SEC   = 20


def get_pairs(conn, table, run_id, view, snapshot_n=None):
    """Return list of pair dicts for the given view."""
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE run_id=? ORDER BY fire_time_epoch, candidate_type",
        (run_id,)
    ).fetchall()

    signals  = {r["signal_fire_id"]: dict(r) for r in rows if r["candidate_type"] == "signal"}
    controls_raw = [dict(r) for r in rows if r["candidate_type"] == "control"]
    ctrl_map = {}
    for c in controls_raw:
        # Join on signal_fire_id (shared between signal and its matched control)
        ctrl_map[c["signal_fire_id"]] = c

    pairs = []
    for sig_id, s in signals.items():
        c = ctrl_map.get(sig_id)
        if c is None:
            continue
        # Must have +5m forward quote for both
        if not (s.get("fwd_quote_ok_5m") == 1 and c.get("fwd_quote_ok_5m") == 1):
            continue
        pairs.append((s, c))

    # Sort by fire time ascending
    pairs.sort(key=lambda x: x[0]["fire_time_epoch"])

    if view == "SNAPSHOT_VIEW":
        pairs = pairs[:snapshot_n] if snapshot_n else pairs

    if view == "TIMING_VALID_VIEW":
        filtered = []
        for s, c in pairs:
            sj = jitter_sec(s, "5m")
            cj = jitter_sec(c, "5m")
            if (s.get("row_valid") == 1 and c.get("row_valid") == 1
                    and s.get("entry_quote_ok") == 1 and c.get("entry_quote_ok") == 1
                    and sj is not None and cj is not None
                    and abs(sj) <= JITTER_GATE_SEC and abs(cj) <= JITTER_GATE_SEC):
                filtered.append((s, c))
        pairs = filtered

    return pairs


def jitter_sec(row, hz):
    exec_col = f"fwd_exec_epoch_{hz}"
    due_col  = f"fwd_due_epoch_{hz}"
    e = row.get(exec_col)
    d = row.get(due_col)
    if e is None or d is None:
        return None
    return e - d


def net(row, hz):
    return row.get(f"fwd_net_fee100_{hz}")


def build_fire_row(s, c, observer_name, lane):
    delta = {}
    for hz in ["1m", "5m", "15m", "30m"]:
        sn = net(s, hz)
        cn = net(c, hz)
        delta[hz] = (sn - cn) if (sn is not None and cn is not None) else None

    d5 = delta["5m"]
    outlier = 1 if (d5 is not None and abs(d5) >= OUTLIER_THRESHOLD) else 0

    return {
        "run_id":                  s["run_id"],
        "observer_name":           observer_name,
        "lane":                    lane or s.get("lane", ""),
        "fire_id":                 s["signal_fire_id"],
        "fire_time_utc":           s["fire_time_iso"],
        "signal_symbol":           s.get("symbol", ""),
        "signal_mint":             s.get("mint", ""),
        "control_symbol":          c.get("symbol", ""),
        "control_mint":            c.get("mint", ""),
        "signal_net_1m":           net(s, "1m"),
        "control_net_1m":          net(c, "1m"),
        "delta_1m":                delta["1m"],
        "signal_net_5m":           net(s, "5m"),
        "control_net_5m":          net(c, "5m"),
        "delta_5m":                delta["5m"],
        "signal_net_15m":          net(s, "15m"),
        "control_net_15m":         net(c, "15m"),
        "delta_15m":               delta["15m"],
        "signal_net_30m":          net(s, "30m"),
        "control_net_30m":         net(c, "30m"),
        "delta_30m":               delta["30m"],
        "signal_entry_r_m5":       s.get("entry_r_m5"),
        "control_entry_r_m5":      c.get("entry_r_m5"),
        "signal_entry_rv5m":       s.get("entry_rv5m"),
        "control_entry_rv5m":      c.get("entry_rv5m"),
        "signal_entry_vol_h1":     s.get("entry_vol_h1"),
        "control_entry_vol_h1":    c.get("entry_vol_h1"),
        "signal_entry_liquidity":  s.get("liquidity_usd"),
        "control_entry_liquidity": c.get("liquidity_usd"),
        "row_valid_signal":        s.get("row_valid"),
        "row_valid_control":       c.get("row_valid"),
        "signal_fwd_jitter_5m_sec":  jitter_sec(s, "5m"),
        "control_fwd_jitter_5m_sec": jitter_sec(c, "5m"),
        "outlier_flag":            outlier,
    }


def fmt(v, d=6):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:+.{d}f}"
    return str(v)


def write_csv(rows, path):
    if not rows:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_md(rows, path, run_id, observer_name, view, snapshot_n=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(rows)
    deltas = [r["delta_5m"] for r in rows if r["delta_5m"] is not None]
    outliers = [r for r in rows if r["outlier_flag"] == 1]
    top_contrib = max(abs(d) for d in deltas) / sum(abs(d) for d in deltas) if deltas else None

    sig_counts = {}
    for r in rows:
        sig_counts[r["signal_symbol"]] = sig_counts.get(r["signal_symbol"], 0) + 1
    repeated = {k: v for k, v in sig_counts.items() if v > 1}

    sorted_pos = sorted([r for r in rows if (r["delta_5m"] or 0) > 0],
                        key=lambda x: -(x["delta_5m"] or 0))[:10]
    sorted_neg = sorted([r for r in rows if (r["delta_5m"] or 0) < 0],
                        key=lambda x: (x["delta_5m"] or 0))[:10]

    view_label = view
    if view == "SNAPSHOT_VIEW":
        view_label = f"SNAPSHOT_VIEW (first {snapshot_n} pairs)"

    lines = [
        f"# Per-Fire Audit Table",
        f"",
        f"**run_id**: `{run_id}`  ",
        f"**observer**: `{observer_name}`  ",
        f"**sample_definition**: `{view_label}`  ",
        f"**generated_at**: `{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}`  ",
        f"**n_pairs**: {n}  ",
        f"**outlier_count** (|delta_5m|>=0.10): {len(outliers)}  ",
        f"**top_contributor_share**: {fmt(top_contrib, 4) if top_contrib else '—'}  ",
        f"",
    ]

    if repeated:
        lines.append("**Repeated signal tokens:**")
        for sym, cnt in sorted(repeated.items(), key=lambda x: -x[1]):
            lines.append(f"  - {sym}: {cnt} fires")
        lines.append("")

    lines += [
        "## Top 10 Positive Deltas (+5m)",
        "",
        "| fire_id | time | signal | sig_net5m | control | ctl_net5m | delta_5m |",
        "|---------|------|--------|-----------|---------|-----------|----------|",
    ]
    for r in sorted_pos:
        lines.append(
            f"| `{r['fire_id']}` | {r['fire_time_utc'][:16]} | {r['signal_symbol']} "
            f"| {fmt(r['signal_net_5m'])} | {r['control_symbol']} "
            f"| {fmt(r['control_net_5m'])} | **{fmt(r['delta_5m'])}** |"
        )

    lines += [
        "",
        "## Top 10 Negative Deltas (+5m)",
        "",
        "| fire_id | time | signal | sig_net5m | control | ctl_net5m | delta_5m |",
        "|---------|------|--------|-----------|---------|-----------|----------|",
    ]
    for r in sorted_neg:
        lines.append(
            f"| `{r['fire_id']}` | {r['fire_time_utc'][:16]} | {r['signal_symbol']} "
            f"| {fmt(r['signal_net_5m'])} | {r['control_symbol']} "
            f"| {fmt(r['control_net_5m'])} | **{fmt(r['delta_5m'])}** |"
        )

    lines += [
        "",
        "## All Fires",
        "",
        "| fire_id | time | signal | sig_rm5 | sig_net5m | control | ctl_rm5 | ctl_net5m | delta_5m | valid | outlier |",
        "|---------|------|--------|---------|-----------|---------|---------|-----------|----------|-------|---------|",
    ]
    for r in rows:
        lines.append(
            f"| `{r['fire_id']}` | {r['fire_time_utc'][:16]} "
            f"| {r['signal_symbol']} | {fmt(r['signal_entry_r_m5'], 2)} | {fmt(r['signal_net_5m'])} "
            f"| {r['control_symbol']} | {fmt(r['control_entry_r_m5'], 2)} | {fmt(r['control_net_5m'])} "
            f"| {fmt(r['delta_5m'])} | {'✓' if r['row_valid_signal']==1 and r['row_valid_control']==1 else '✗'} "
            f"| {'⚠' if r['outlier_flag'] else ''} |"
        )

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id",       required=True)
    p.add_argument("--db",           required=True)
    p.add_argument("--table",        required=True)
    p.add_argument("--observer-name", default="")
    p.add_argument("--lane",         default="")
    p.add_argument("--view",         default="ALL_COMPLETED_VIEW",
                   choices=["ALL_COMPLETED_VIEW", "TIMING_VALID_VIEW", "SNAPSHOT_VIEW"])
    p.add_argument("--snapshot-n",   type=int, default=None)
    p.add_argument("--out-dir",      default="reports/experiments")
    args = p.parse_args()

    conn = sqlite3.connect(args.db, timeout=5)
    conn.row_factory = sqlite3.Row

    pairs = get_pairs(conn, args.table, args.run_id, args.view, args.snapshot_n)
    conn.close()

    fire_rows = [build_fire_row(s, c, args.observer_name, args.lane) for s, c in pairs]

    out_base = os.path.join(args.out_dir, args.run_id)
    csv_path = os.path.join(out_base, "per_fire.csv")
    md_path  = os.path.join(out_base, "per_fire.md")

    write_csv(fire_rows, csv_path)
    write_md(fire_rows, md_path, args.run_id, args.observer_name, args.view, args.snapshot_n)

    print(f"DONE  n={len(fire_rows)}  csv={csv_path}  md={md_path}")


if __name__ == "__main__":
    main()
