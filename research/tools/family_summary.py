#!/usr/bin/env python3
"""
family_summary.py — Pooled comparable-runs summary generator.

Usage:
  python3 family_summary.py --family <family_name> --config <family_config.json> \
      [--out-dir <dir>]

Family config JSON format:
{
  "family_name": "pfm_reversion_observer_v1",
  "observer_name": "pfm_reversion_observer_v1",
  "lane": "pumpfun_mature",
  "direction": "reversion",
  "notional": 0.01,
  "horizons": ["1m","5m","15m","30m"],
  "quote_model": "Jupiter Ultra",
  "runs": [
    {"run_id": "99ed0fd1", "db": "/path/to/db", "table": "observer_pfm_rev_v1"}
  ]
}

Outputs:
  <out_dir>/<family_name>/pooled_summary.md
  <out_dir>/<family_name>/pooled_summary.json
"""
import argparse
import json
import math
import os
import random
import sqlite3
import statistics
from datetime import datetime, timezone

OUTLIER_THRESHOLD = 0.10
JITTER_GATE_SEC   = 20
BOOTSTRAP_N       = 2000


def jitter_sec(row, hz):
    e = row.get(f"fwd_exec_epoch_{hz}")
    d = row.get(f"fwd_due_epoch_{hz}")
    if e is None or d is None:
        return None
    return e - d


def net(row, hz):
    return row.get(f"fwd_net_fee100_{hz}")


def get_pairs(db, table, run_id):
    conn = sqlite3.connect(db, timeout=5)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        f"SELECT * FROM {table} WHERE run_id=? ORDER BY fire_time_epoch, candidate_type",
        (run_id,)
    ).fetchall()]
    conn.close()

    signals  = {r["signal_fire_id"]: r for r in rows if r["candidate_type"] == "signal"}
    ctrl_raw = [r for r in rows if r["candidate_type"] == "control"]
    ctrl_map = {}
    for c in ctrl_raw:
        # Join on signal_fire_id (shared between signal and its matched control)
        ctrl_map[c["signal_fire_id"]] = c

    pairs = []
    for sig_id, s in signals.items():
        c = ctrl_map.get(sig_id)
        if c and s.get("fwd_quote_ok_5m") == 1 and c.get("fwd_quote_ok_5m") == 1:
            pairs.append((s, c))
    pairs.sort(key=lambda x: x[0]["fire_time_epoch"])
    return pairs


def health_status(pairs):
    """Returns 'VALID' or 'INVALID: <reason>'."""
    if not pairs:
        return "INVALID: no_completed_pairs"
    n = len(pairs)
    entry_ok = sum(1 for s, c in pairs
                   if s.get("entry_quote_ok") == 1 and c.get("entry_quote_ok") == 1)
    invalid_rows = sum(1 for s, c in pairs
                       if s.get("row_valid") != 1 or c.get("row_valid") != 1)
    if n > 0 and entry_ok / n < 0.95:
        return f"INVALID: entry_coverage={100*entry_ok/n:.1f}%"
    if invalid_rows > 0:
        return f"INVALID: {invalid_rows}_invalid_rows"
    return "VALID"


def run_metrics(pairs, run_id, classification=""):
    deltas   = [net(s, "5m") - net(c, "5m") for s, c in pairs
                if net(s, "5m") is not None and net(c, "5m") is not None]
    sig_nets = [net(s, "5m") for s, c in pairs if net(s, "5m") is not None]
    ctl_nets = [net(c, "5m") for s, c in pairs if net(c, "5m") is not None]

    if not deltas:
        return {"run_id": run_id, "n": 0, "classification": classification}

    n        = len(deltas)
    mean_d   = statistics.mean(deltas)
    median_d = statistics.median(deltas)
    pct_pos  = sum(1 for d in deltas if d > 0) / n * 100
    sig_net  = statistics.mean(sig_nets) if sig_nets else None
    hs       = health_status(pairs)

    return {
        "run_id":            run_id,
        "n":                 n,
        "mean_delta_5m":     round(mean_d, 6),
        "median_delta_5m":   round(median_d, 6),
        "pct_delta_positive": round(pct_pos, 2),
        "mean_signal_net_5m": round(sig_net, 6) if sig_net else None,
        "health_status":     hs,
        "classification":    classification,
    }


def bootstrap_ci(lst, stat_fn, n=BOOTSTRAP_N, alpha=0.05):
    if len(lst) < 2:
        return (None, None)
    random.seed(42)
    samples = [stat_fn(random.choices(lst, k=len(lst))) for _ in range(n)]
    samples.sort()
    lo = samples[int(n * alpha / 2)]
    hi = samples[int(n * (1 - alpha / 2))]
    return (lo, hi)


def t_ci(lst, alpha=0.05):
    if len(lst) < 2:
        return (None, None)
    m  = statistics.mean(lst)
    sd = statistics.stdev(lst)
    se = sd / math.sqrt(len(lst))
    return (m - 2.0 * se, m + 2.0 * se)


def fmt(v, d=6):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:+.{d}f}"
    return str(v)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--family",  required=True, help="Family name (used as output dir name)")
    p.add_argument("--config",  required=True, help="Path to family config JSON")
    p.add_argument("--out-dir", default="reports/experiment_families")
    p.add_argument("--scorecard-dir", default="reports/experiments",
                   help="Dir where per-run scorecard.json files live")
    args = p.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    family_name   = cfg["family_name"]
    observer_name = cfg.get("observer_name", "")
    runs_cfg      = cfg["runs"]

    # Load per-run classification from scorecard.json if available
    cls_map = {}
    for r in runs_cfg:
        sc_path = os.path.join(args.scorecard_dir, r["run_id"], "scorecard.json")
        if os.path.exists(sc_path):
            with open(sc_path) as f2:
                sc = json.load(f2)
            cls_map[r["run_id"]] = sc.get("all_completed_view", {}).get("classification", "")

    # Build per-run pair sets, exclude INVALID
    valid_runs = []
    all_deltas = []
    all_sig_nets = []
    all_ctl_nets = []
    per_run_rows = []
    sample_defs_used = set()

    for r in runs_cfg:
        pairs = get_pairs(r["db"], r["table"], r["run_id"])
        hs    = health_status(pairs)
        cls   = cls_map.get(r["run_id"], "")
        m     = run_metrics(pairs, r["run_id"], cls)
        per_run_rows.append(m)

        if hs == "VALID":
            valid_runs.append(r["run_id"])
            sample_defs_used.add("ALL_COMPLETED_VIEW")
            for s, c in pairs:
                sn = net(s, "5m")
                cn = net(c, "5m")
                if sn is not None and cn is not None:
                    all_deltas.append(sn - cn)
                    all_sig_nets.append(sn)
                    all_ctl_nets.append(cn)

    # Pooled metrics
    pooled = {}
    if all_deltas:
        n = len(all_deltas)
        mean_d   = statistics.mean(all_deltas)
        median_d = statistics.median(all_deltas)
        pct_pos  = sum(1 for d in all_deltas if d > 0) / n * 100
        ci_t     = t_ci(all_deltas)
        ci_bs    = bootstrap_ci(all_deltas, statistics.mean)
        outliers = sum(1 for d in all_deltas if abs(d) >= OUTLIER_THRESHOLD)
        top_contrib = max(abs(d) for d in all_deltas) / sum(abs(d) for d in all_deltas)

        pooled = {
            "n_valid_runs":          len(valid_runs),
            "n_pairs_complete_5m":   n,
            "mean_delta_5m":         round(mean_d, 6),
            "median_delta_5m":       round(median_d, 6),
            "pct_delta_positive":    round(pct_pos, 2),
            "ci_95_t":               [round(ci_t[0], 6), round(ci_t[1], 6)],
            "ci_95_bootstrap_mean":  [round(ci_bs[0], 6) if ci_bs[0] else None,
                                      round(ci_bs[1], 6) if ci_bs[1] else None],
            "mean_signal_net_5m":    round(statistics.mean(all_sig_nets), 6),
            "mean_control_net_5m":   round(statistics.mean(all_ctl_nets), 6),
            "outlier_count":         outliers,
            "outlier_rate_pct":      round(outliers / n * 100, 2),
            "top_contributor_share": round(top_contrib, 4),
        }

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Write markdown
    out_base = os.path.join(args.out_dir, family_name)
    os.makedirs(out_base, exist_ok=True)
    md_path   = os.path.join(out_base, "pooled_summary.md")
    json_path = os.path.join(out_base, "pooled_summary.json")

    warn_banner = ""
    if len(sample_defs_used) > 1:
        warn_banner = f"\n> **WARNING**: Multiple sample definitions used: {sample_defs_used}\n"

    lines = [
        f"# Pooled Family Summary",
        f"",
        f"**family**: `{family_name}`  ",
        f"**observer**: `{observer_name}`  ",
        f"**lane**: `{cfg.get('lane', '—')}`  ",
        f"**direction**: `{cfg.get('direction', '—')}`  ",
        f"**notional**: `{cfg.get('notional', '—')} SOL`  ",
        f"**quote_model**: `{cfg.get('quote_model', '—')}`  ",
        f"**sample_definition**: `ALL_COMPLETED_VIEW` (INVALID runs excluded)  ",
        f"**generated_at**: `{generated_at}`  ",
    ]
    if warn_banner:
        lines.append(warn_banner)

    lines += [
        f"",
        f"---",
        f"",
        f"## Pooled Metrics (valid runs only: {len(valid_runs)})",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    for k, v in pooled.items():
        lines.append(f"| {k} | {fmt(v) if isinstance(v, float) else v} |")

    lines += [
        f"",
        f"---",
        f"",
        f"## Per-Run Comparison",
        f"",
        f"| run_id | n | mean_delta | median_delta | %>0 | mean_signal_net | health_status | classification |",
        f"|--------|---|-----------|-------------|-----|----------------|---------------|----------------|",
    ]
    for m in per_run_rows:
        lines.append(
            f"| `{m['run_id']}` | {m.get('n', 0)} "
            f"| {fmt(m.get('mean_delta_5m'))} "
            f"| {fmt(m.get('median_delta_5m'))} "
            f"| {m.get('pct_delta_positive', '—')}% "
            f"| {fmt(m.get('mean_signal_net_5m'))} "
            f"| {m.get('health_status', '—')} "
            f"| {m.get('classification', '—')} |"
        )

    with open(md_path, "w") as f:
        f.write("\n".join(lines) + "\n")

    payload = {
        "family_name":    family_name,
        "observer_name":  observer_name,
        "generated_at":   generated_at,
        "valid_run_ids":  valid_runs,
        "all_run_ids":    [r["run_id"] for r in runs_cfg],
        "pooled_metrics": pooled,
        "per_run":        per_run_rows,
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"DONE  family={family_name}  valid_runs={len(valid_runs)}  "
          f"pooled_n={pooled.get('n_pairs_complete_5m', 0)}  "
          f"md={md_path}  json={json_path}")


if __name__ == "__main__":
    main()
