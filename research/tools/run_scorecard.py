#!/usr/bin/env python3
"""
run_scorecard.py — Per-run scorecard generator.

Usage:
  python3 run_scorecard.py --run-id <run_id> --db <path_to_db> --table <table_name> \
      [--observer-name <name>] [--decision-threshold <n>] [--out-dir <dir>]

Outputs:
  <out_dir>/<run_id>/scorecard.md
  <out_dir>/<run_id>/scorecard.json

Computes metrics for both ALL_COMPLETED_VIEW and TIMING_VALID_VIEW.
Classification is based on ALL_COMPLETED_VIEW (primary),
with TIMING_VALID_VIEW as robustness check.
"""
import argparse
import json
import math
import os
import random
import sqlite3
import statistics
from datetime import datetime, timezone

OUTLIER_THRESHOLD  = 0.10
JITTER_GATE_SEC    = 20
BOOTSTRAP_N        = 2000
TRIM_PCT           = 0.10
DECISION_THRESHOLD = 50   # default n for classification


def jitter_sec(row, hz):
    e = row.get(f"fwd_exec_epoch_{hz}")
    d = row.get(f"fwd_due_epoch_{hz}")
    if e is None or d is None:
        return None
    return e - d


def net(row, hz):
    return row.get(f"fwd_net_fee100_{hz}")


def get_all_rows(conn, table, run_id):
    return [dict(r) for r in conn.execute(
        f"SELECT * FROM {table} WHERE run_id=? ORDER BY fire_time_epoch, candidate_type",
        (run_id,)
    ).fetchall()]


def build_pairs(rows):
    signals  = {r["signal_fire_id"]: r for r in rows if r["candidate_type"] == "signal"}
    ctrl_raw = [r for r in rows if r["candidate_type"] == "control"]
    ctrl_map = {}
    for c in ctrl_raw:
        # Join on signal_fire_id (shared between signal and its matched control)
        ctrl_map[c["signal_fire_id"]] = c
    pairs = []
    for sig_id, s in signals.items():
        c = ctrl_map.get(sig_id)
        if c:
            pairs.append((s, c))
    pairs.sort(key=lambda x: x[0]["fire_time_epoch"])
    return pairs


def filter_complete_5m(pairs):
    return [(s, c) for s, c in pairs
            if s.get("fwd_quote_ok_5m") == 1 and c.get("fwd_quote_ok_5m") == 1]


def filter_timing_valid(pairs):
    out = []
    for s, c in pairs:
        sj = jitter_sec(s, "5m")
        cj = jitter_sec(c, "5m")
        if (s.get("row_valid") == 1 and c.get("row_valid") == 1
                and s.get("entry_quote_ok") == 1 and c.get("entry_quote_ok") == 1
                and sj is not None and cj is not None
                and abs(sj) <= JITTER_GATE_SEC and abs(cj) <= JITTER_GATE_SEC):
            out.append((s, c))
    return out


def ptile(lst, p):
    if not lst:
        return None
    s = sorted(lst)
    idx = max(0, min(int(len(s) * p / 100), len(s) - 1))
    return round(s[idx], 3)


def trimmed_mean(lst, pct=TRIM_PCT):
    if not lst:
        return None
    s = sorted(lst)
    k = int(len(s) * pct)
    trimmed = s[k: len(s) - k] if k > 0 else s
    return statistics.mean(trimmed) if trimmed else None


def winsorized_mean(lst, pct=TRIM_PCT):
    if not lst:
        return None
    s = sorted(lst)
    k = int(len(s) * pct)
    lo = s[k] if k < len(s) else s[0]
    hi = s[-(k+1)] if k < len(s) else s[-1]
    wins = [max(lo, min(hi, v)) for v in s]
    return statistics.mean(wins)


def bootstrap_ci(lst, stat_fn, n=BOOTSTRAP_N, alpha=0.05):
    if len(lst) < 2:
        return (None, None)
    random.seed(42)
    samples = [stat_fn(random.choices(lst, k=len(lst))) for _ in range(n)]
    samples.sort()
    lo = samples[int(n * alpha / 2)]
    hi = samples[int(n * (1 - alpha / 2))]
    return (lo, hi)


def sign_test_p(lst):
    """Two-sided sign test p-value vs H0: median=0."""
    if not lst:
        return None
    pos = sum(1 for x in lst if x > 0)
    neg = sum(1 for x in lst if x < 0)
    n   = pos + neg
    if n == 0:
        return None
    # Binomial exact two-sided
    from math import comb
    p_one = sum(comb(n, k) * 0.5**n for k in range(pos + 1))
    return min(1.0, 2 * min(p_one, 1 - p_one + comb(n, pos) * 0.5**n))


def t_ci(lst, alpha=0.05):
    """Simple t-based 95% CI for mean."""
    if len(lst) < 2:
        return (None, None)
    m  = statistics.mean(lst)
    sd = statistics.stdev(lst)
    se = sd / math.sqrt(len(lst))
    # t critical ~1.96 for large n, use 2.0 as conservative approx
    t  = 2.0
    return (m - t * se, m + t * se)


def compute_health(all_rows, all_pairs, complete_pairs, table):
    signals_all  = [s for s, c in all_pairs]
    controls_all = [c for s, c in all_pairs]

    n_fires       = len(signals_all)
    entry_ok      = sum(1 for s, c in all_pairs
                        if s.get("entry_quote_ok") == 1 and c.get("entry_quote_ok") == 1)
    n_due_5m      = sum(1 for s, c in all_pairs
                        if s.get("fwd_due_epoch_5m") is not None)
    n_complete    = len(complete_pairs)
    n_fail        = n_due_5m - n_complete

    sig_valid   = sum(1 for s, c in complete_pairs if s.get("row_valid") == 1)
    sig_invalid = sum(1 for s, c in complete_pairs if s.get("row_valid") != 1)
    ctl_valid   = sum(1 for s, c in complete_pairs if c.get("row_valid") == 1)
    ctl_invalid = sum(1 for s, c in complete_pairs if c.get("row_valid") != 1)

    invalid_reasons = {}
    for s, c in complete_pairs:
        for r in [s, c]:
            reason = r.get("invalid_reason")
            if reason:
                invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

    # 429 and other failures
    r429_sig   = sum(1 for s, c in all_pairs
                     if s.get("fwd_quote_err_5m") and "429" in str(s.get("fwd_quote_err_5m", "")))
    r429_ctl   = sum(1 for s, c in all_pairs
                     if c.get("fwd_quote_err_5m") and "429" in str(c.get("fwd_quote_err_5m", "")))
    other_sig  = sum(1 for s, c in all_pairs
                     if s.get("fwd_quote_ok_5m") != 1
                     and not (s.get("fwd_quote_err_5m") and "429" in str(s.get("fwd_quote_err_5m", ""))))
    other_ctl  = sum(1 for s, c in all_pairs
                     if c.get("fwd_quote_ok_5m") != 1
                     and not (c.get("fwd_quote_err_5m") and "429" in str(c.get("fwd_quote_err_5m", ""))))

    # Jitter stats
    def jit_stats(pairs, hz):
        vals = [j for s, c in pairs
                for j in [jitter_sec(s, hz), jitter_sec(c, hz)] if j is not None]
        return {"p50": ptile(vals, 50), "p95": ptile(vals, 95), "max": max(vals) if vals else None}

    def dt_stats(pairs, hz):
        vals = []
        for s, c in pairs:
            for row in [s, c]:
                entry_ts = row.get("entry_quote_ts_epoch")
                fwd_ts   = row.get(f"fwd_quote_ts_epoch_{hz}")
                if entry_ts and fwd_ts:
                    vals.append(fwd_ts - entry_ts)
        return {"p50": ptile(vals, 50), "p95": ptile(vals, 95), "max": max(vals) if vals else None}

    entry_cov = (entry_ok / n_fires * 100) if n_fires else None
    cond_cov  = (n_complete / n_due_5m * 100) if n_due_5m else None
    uncond    = (n_complete / n_fires * 100) if n_fires else None

    return {
        "n_fires_total":               n_fires,
        "n_entry_ok_pairs":            entry_ok,
        "n_due_5m":                    n_due_5m,
        "n_pairs_complete_5m":         n_complete,
        "n_fail_5m":                   n_fail,
        "entry_quote_coverage_pct":    round(entry_cov, 2) if entry_cov else None,
        "conditional_5m_coverage_pct": round(cond_cov, 2) if cond_cov else None,
        "unconditional_5m_completion_pct": round(uncond, 2) if uncond else None,
        "row_valid_signal":            sig_valid,
        "row_invalid_signal":          sig_invalid,
        "row_valid_control":           ctl_valid,
        "row_invalid_control":         ctl_invalid,
        "invalid_reason_summary":      invalid_reasons,
        "http_429_signal":             r429_sig,
        "http_429_control":            r429_ctl,
        "other_fail_signal":           other_sig,
        "other_fail_control":          other_ctl,
        "jitter_1m":                   jit_stats(complete_pairs, "1m"),
        "jitter_5m":                   jit_stats(complete_pairs, "5m"),
        "dt_from_entry_1m":            dt_stats(complete_pairs, "1m"),
        "dt_from_entry_5m":            dt_stats(complete_pairs, "5m"),
    }


def compute_perf(complete_pairs):
    deltas = []
    sig_nets = []
    ctl_nets = []
    for s, c in complete_pairs:
        sn = net(s, "5m")
        cn = net(c, "5m")
        if sn is not None and cn is not None:
            deltas.append(sn - cn)
            sig_nets.append(sn)
            ctl_nets.append(cn)

    if not deltas:
        return {"n": 0}

    n = len(deltas)
    mean_d   = statistics.mean(deltas)
    median_d = statistics.median(deltas)
    std_d    = statistics.stdev(deltas) if n > 1 else None
    pct_pos  = sum(1 for d in deltas if d > 0) / n * 100
    ci_t     = t_ci(deltas)
    ci_bs_mean   = bootstrap_ci(deltas, statistics.mean)
    ci_bs_median = bootstrap_ci(deltas, statistics.median)
    sign_p   = sign_test_p(deltas)
    trim_m   = trimmed_mean(deltas)
    wins_m   = winsorized_mean(deltas)
    outliers = [d for d in deltas if abs(d) >= OUTLIER_THRESHOLD]
    top_contrib = max(abs(d) for d in deltas) / sum(abs(d) for d in deltas) if deltas else None

    return {
        "n":                      n,
        "mean_delta_5m":          round(mean_d, 6),
        "median_delta_5m":        round(median_d, 6),
        "pct_delta_positive":     round(pct_pos, 2),
        "std_delta_5m":           round(std_d, 6) if std_d else None,
        "ci_95_t":                [round(ci_t[0], 6) if ci_t[0] else None,
                                   round(ci_t[1], 6) if ci_t[1] else None],
        "ci_95_bootstrap_mean":   [round(ci_bs_mean[0], 6) if ci_bs_mean[0] else None,
                                   round(ci_bs_mean[1], 6) if ci_bs_mean[1] else None],
        "ci_95_bootstrap_median": [round(ci_bs_median[0], 6) if ci_bs_median[0] else None,
                                   round(ci_bs_median[1], 6) if ci_bs_median[1] else None],
        "sign_test_p_value":      round(sign_p, 4) if sign_p else None,
        "mean_signal_net_5m":     round(statistics.mean(sig_nets), 6),
        "mean_control_net_5m":    round(statistics.mean(ctl_nets), 6),
        "outlier_count":          len(outliers),
        "top_contributor_share":  round(top_contrib, 4) if top_contrib else None,
        "trimmed_mean_delta_5m":  round(trim_m, 6) if trim_m else None,
        "winsorized_mean_delta_5m": round(wins_m, 6) if wins_m else None,
    }


def classify(health, perf, decision_threshold):
    n = perf.get("n", 0)

    # Health gates
    if (health["entry_quote_coverage_pct"] is not None and health["entry_quote_coverage_pct"] < 95):
        return "INVALID / INFRA FAILURE", "entry_quote_coverage < 95%"
    if (health["conditional_5m_coverage_pct"] is not None and health["conditional_5m_coverage_pct"] < 95):
        return "INVALID / INFRA FAILURE", "conditional_5m_coverage < 95%"
    if health["row_invalid_signal"] > 0 or health["row_invalid_control"] > 0:
        return "INVALID / INFRA FAILURE", "row_valid < 100%"

    if n < decision_threshold:
        return "ACCUMULATING", f"n={n} < decision_threshold={decision_threshold}"

    mean_d   = perf["mean_delta_5m"]
    median_d = perf["median_delta_5m"]
    ci_lo    = perf["ci_95_t"][0]
    sig_net  = perf["mean_signal_net_5m"]

    if mean_d <= 0 and median_d <= 0:
        return "FALSIFIED", "mean<=0 and median<=0"
    if mean_d > 0 and median_d > 0 and ci_lo is not None and ci_lo > 0:
        if sig_net <= 0:
            return "SUPPORTED AS RANKING FEATURE / NOT PROMOTABLE", \
                   "mean>0, median>0, CI_lo>0, but signal net <=0"
        return "SUPPORTED", "mean>0, median>0, CI_lo>0, signal net >0"
    return "FRAGILE / INCONCLUSIVE", "mean>0 but median<=0 or CI_lo<=0"


def fmt_val(v, d=6):
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:+.{d}f}"
    return str(v)


def write_md(path, run_id, observer_name, health_all, perf_all, cls_all, cls_reason_all,
             health_tv, perf_tv, cls_tv, cls_reason_tv, decision_threshold, generated_at):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    lines = [
        f"# Run Scorecard",
        f"",
        f"**run_id**: `{run_id}`  ",
        f"**observer**: `{observer_name}`  ",
        f"**decision_threshold**: n={decision_threshold}  ",
        f"**generated_at**: `{generated_at}`  ",
        f"",
        f"---",
        f"",
        f"## PRIMARY VIEW: ALL_COMPLETED_VIEW",
        f"",
        f"### Health",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    for k, v in health_all.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                lines.append(f"| {k}.{sk} | {sv} |")
        else:
            lines.append(f"| {k} | {v} |")

    lines += [
        f"",
        f"### Performance",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    for k, v in perf_all.items():
        lines.append(f"| {k} | {fmt_val(v) if isinstance(v, float) else v} |")

    lines += [
        f"",
        f"### Classification (Primary)",
        f"",
        f"**`{cls_all}`**  ",
        f"Reason: {cls_reason_all}  ",
        f"",
        f"---",
        f"",
        f"## ROBUSTNESS VIEW: TIMING_VALID_VIEW",
        f"(gate: row_valid=1, entry_ok=1, fwd_ok=1, abs(jitter_5m)<=20s)",
        f"",
        f"### Health",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    for k, v in health_tv.items():
        if isinstance(v, dict):
            for sk, sv in v.items():
                lines.append(f"| {k}.{sk} | {sv} |")
        else:
            lines.append(f"| {k} | {v} |")

    lines += [
        f"",
        f"### Performance",
        f"",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    for k, v in perf_tv.items():
        lines.append(f"| {k} | {fmt_val(v) if isinstance(v, float) else v} |")

    lines += [
        f"",
        f"### Classification (Robustness)",
        f"",
        f"**`{cls_tv}`**  ",
        f"Reason: {cls_reason_tv}  ",
    ]

    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--run-id",           required=True)
    p.add_argument("--db",               required=True)
    p.add_argument("--table",            required=True)
    p.add_argument("--observer-name",    default="")
    p.add_argument("--decision-threshold", type=int, default=DECISION_THRESHOLD)
    p.add_argument("--out-dir",          default="reports/experiments")
    args = p.parse_args()

    conn = sqlite3.connect(args.db, timeout=5)
    conn.row_factory = sqlite3.Row
    all_rows = get_all_rows(conn, args.table, args.run_id)
    conn.close()

    all_pairs      = build_pairs(all_rows)
    complete_all   = filter_complete_5m(all_pairs)
    complete_tv    = filter_timing_valid(complete_all)

    health_all = compute_health(all_rows, all_pairs, complete_all, args.table)
    perf_all   = compute_perf(complete_all)
    cls_all, cls_reason_all = classify(health_all, perf_all, args.decision_threshold)

    health_tv  = compute_health(all_rows, all_pairs, complete_tv, args.table)
    perf_tv    = compute_perf(complete_tv)
    cls_tv, cls_reason_tv = classify(health_tv, perf_tv, args.decision_threshold)

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_base = os.path.join(args.out_dir, args.run_id)
    md_path  = os.path.join(out_base, "scorecard.md")
    json_path = os.path.join(out_base, "scorecard.json")
    os.makedirs(out_base, exist_ok=True)

    write_md(md_path, args.run_id, args.observer_name,
             health_all, perf_all, cls_all, cls_reason_all,
             health_tv, perf_tv, cls_tv, cls_reason_tv,
             args.decision_threshold, generated_at)

    payload = {
        "run_id": args.run_id,
        "observer_name": args.observer_name,
        "decision_threshold": args.decision_threshold,
        "generated_at": generated_at,
        "all_completed_view": {
            "health": health_all, "performance": perf_all,
            "classification": cls_all, "classification_reason": cls_reason_all
        },
        "timing_valid_view": {
            "health": health_tv, "performance": perf_tv,
            "classification": cls_tv, "classification_reason": cls_reason_tv
        }
    }
    with open(json_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"DONE  run_id={args.run_id}  cls={cls_all}  md={md_path}  json={json_path}")


if __name__ == "__main__":
    main()
