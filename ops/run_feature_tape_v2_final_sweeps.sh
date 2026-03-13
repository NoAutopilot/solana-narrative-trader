#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# run_feature_tape_v2_final_sweeps.sh
# Cold-path only. Does NOT modify the collector, scanner, or live DB.
#
# Orchestrates the complete end-of-run evaluation:
#   A) Full-sample sweep (all eligible rows, all horizons)
#   B) Subset-micro sweep (eligible rows with micro coverage only)
#   C) Holdout evaluation (75/25 temporal split, 8 promotion gates)
#   D) Benchmark comparison (vs benchmark_suite_v1 / no_go_registry_v1)
#   E) Final recommendation memo
#
# Prerequisites:
#   1) Collection complete (>= 96 fires)
#   2) Labels mature (all primary horizons)
#   3) Dataset frozen (manifest + artifacts)
#
# Usage:
#   bash ops/run_feature_tape_v2_final_sweeps.sh
#   bash ops/run_feature_tape_v2_final_sweeps.sh --db /path/to/db
#   bash ops/run_feature_tape_v2_final_sweeps.sh --dry-run
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/root/solana_trader/data/solana_trader.db}"
STATUS_DIR="${STATUS_DIR:-/root/solana_trader/status}"
MATURITY_STATUS="${STATUS_DIR}/feature_tape_v2_labels_mature.json"
MANIFEST_PATH="reports/synthesis/feature_tape_v2_final_manifest.json"
OUTPUT_BASE="reports/synthesis"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)/scripts"
DRY_RUN=false

HORIZONS="5m,15m,30m,1h,4h"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db)         DB_PATH="$2"; shift 2 ;;
        --status-dir) STATUS_DIR="$2"; shift 2 ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --horizons)   HORIZONS="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Pre-checks ────────────────────────────────────────────────────────────────
echo "════════════════════════════════════════════════════════════"
echo "  feature_tape_v2 — Final Sweep Autorun"
echo "  DB path:  ${DB_PATH}"
echo "  Horizons: ${HORIZONS}"
echo "  Dry run:  ${DRY_RUN}"
echo "════════════════════════════════════════════════════════════"

if [[ ! -f "$MATURITY_STATUS" ]]; then
    echo "WARNING: Label maturity status not found at ${MATURITY_STATUS}"
    echo "Labels may not be fully mature. Proceeding anyway..."
fi

if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "WARNING: Final manifest not found at ${MANIFEST_PATH}"
    echo "Dataset may not be frozen. Proceeding anyway..."
fi

if [[ ! -f "$DB_PATH" ]]; then
    echo "ERROR: Database not found at ${DB_PATH}"
    exit 1
fi

NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")

mkdir -p "$OUTPUT_BASE"

# ══════════════════════════════════════════════════════════════════════════════
# STEP A: Full-sample sweep (all eligible rows, all horizons)
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP A: Full-sample sweep (eligible-only)"
echo "══════════════════════════════════════════════════════════"

FULL_SAMPLE_DIR="${OUTPUT_BASE}/sweeps_full_sample"
mkdir -p "$FULL_SAMPLE_DIR"

if $DRY_RUN; then
    echo "  [DRY RUN] Would run full-sample sweep for horizons: ${HORIZONS}"
else
    python3 "${SCRIPT_DIR}/final_sweep_v2.py" \
        --db-path "$DB_PATH" \
        --horizons "$HORIZONS" \
        --output-base "$FULL_SAMPLE_DIR" \
        2>&1 | tee "${FULL_SAMPLE_DIR}/sweep_log.txt"

    # Copy unified report to expected path
    if [[ -f "${FULL_SAMPLE_DIR}/unified_sweep_report.md" ]]; then
        cp "${FULL_SAMPLE_DIR}/unified_sweep_report.md" \
           "${OUTPUT_BASE}/feature_family_sweep_v2_full_sample.md"
        echo "  Full-sample report: ${OUTPUT_BASE}/feature_family_sweep_v2_full_sample.md"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP B: Subset-micro sweep (eligible + micro coverage only)
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP B: Subset-micro sweep (eligible + micro only)"
echo "══════════════════════════════════════════════════════════"

MICRO_DIR="${OUTPUT_BASE}/sweeps_subset_micro"
mkdir -p "$MICRO_DIR"

# Micro-native features only
MICRO_FEATURES="buys_m5,sells_m5,buys_h1,sells_h1,buy_sell_ratio_m5,buy_sell_ratio_h1"
MICRO_FEATURES="${MICRO_FEATURES},buy_count_ratio_m5,buy_count_ratio_h1"
MICRO_FEATURES="${MICRO_FEATURES},avg_trade_usd_m5,avg_trade_usd_h1"
MICRO_FEATURES="${MICRO_FEATURES},vol_accel_m5_vs_h1,txn_accel_m5_vs_h1"
MICRO_FEATURES="${MICRO_FEATURES},r_m5_micro,rv_5m,rv_1m,range_5m"
MICRO_FEATURES="${MICRO_FEATURES},liq_change_pct,liq_cliff_flag"

if $DRY_RUN; then
    echo "  [DRY RUN] Would run subset-micro sweep for horizons: ${HORIZONS}"
else
    # Create a temporary view for micro-only eligible rows
    # The holdout_sweep_v2.py uses eligible=1 filter; we need to further filter
    # to rows with micro coverage. We'll pass features that are micro-native
    # and the script will naturally skip rows where these are NULL.
    python3 "${SCRIPT_DIR}/final_sweep_v2.py" \
        --db-path "$DB_PATH" \
        --horizons "$HORIZONS" \
        --features "$MICRO_FEATURES" \
        --output-base "$MICRO_DIR" \
        2>&1 | tee "${MICRO_DIR}/sweep_log.txt"

    if [[ -f "${MICRO_DIR}/unified_sweep_report.md" ]]; then
        cp "${MICRO_DIR}/unified_sweep_report.md" \
           "${OUTPUT_BASE}/feature_family_sweep_v2_subset_micro.md"
        echo "  Subset-micro report: ${OUTPUT_BASE}/feature_family_sweep_v2_subset_micro.md"
    fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP C: Holdout evaluation (already included in sweep, but extract summary)
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP C: Holdout evaluation summary"
echo "══════════════════════════════════════════════════════════"

if $DRY_RUN; then
    echo "  [DRY RUN] Would extract holdout summary"
else
    # The holdout results are already in the sweep outputs.
    # Generate a consolidated holdout report.
    python3 -c "
import json, os, sys
from pathlib import Path

output_base = '${FULL_SAMPLE_DIR}'
horizons = '${HORIZONS}'.split(',')
report_lines = ['# Feature Tape v2 — Holdout Evaluation Summary\n']
report_lines.append('**Date:** ${NOW_UTC}\n')
report_lines.append('**View:** PRIMARY (eligible-only)\n\n---\n')

all_promoted = {}
for h in horizons:
    rpath = Path(output_base) / f'v2_{h}' / 'holdout_sweep_results.json'
    if not rpath.exists():
        report_lines.append(f'\n## +{h} — NO RESULTS\n')
        continue
    with open(rpath) as f:
        r = json.load(f)
    promoted = r.get('promoted_features', [])
    report_lines.append(f'\n## +{h}\n')
    report_lines.append(f'Discovery: {r[\"n_rows_discovery\"]} rows | Holdout: {r[\"n_rows_holdout\"]} rows\n')
    if promoted:
        report_lines.append(f'Promoted: {\", \".join(promoted)}\n')
        all_promoted[h] = promoted
        # Holdout details
        for feat in promoted:
            hr = r.get('holdout_results', {}).get(feat, {})
            if 'metrics' in hr:
                m = hr['metrics']
                report_lines.append(f'  {feat}: mean={m[\"G1_mean_net_proxy\"]*100:.3f}% median={m[\"G2_median_net_proxy\"]*100:.3f}% wr={m[\"G5_win_rate\"]*100:.1f}% → {hr[\"status\"]}\n')
    else:
        report_lines.append('No features promoted from discovery.\n')

report_lines.append('\n---\n\n## Verdict\n\n')
if all_promoted:
    report_lines.append('Features promoted to holdout at one or more horizons.\n')
    report_lines.append('See individual horizon reports for gate details.\n')
else:
    report_lines.append('**No features promoted at any horizon.**\n')
    report_lines.append('Signal is fundamentally weak across all tested features and horizons.\n')

with open('${OUTPUT_BASE}/feature_family_sweep_v2_holdout.md', 'w') as f:
    f.writelines(report_lines)
print('  Holdout report: ${OUTPUT_BASE}/feature_family_sweep_v2_holdout.md')
" 2>&1
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP D: Benchmark comparison (already run per-horizon, consolidate)
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP D: Benchmark comparison"
echo "══════════════════════════════════════════════════════════"

if $DRY_RUN; then
    echo "  [DRY RUN] Would consolidate benchmark comparisons"
else
    echo "  Benchmark comparisons already generated per-horizon in sweep outputs."
    echo "  See ${FULL_SAMPLE_DIR}/v2_*/benchmark_comparison.md"
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP E: Ranked summary CSV
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP E: Ranked summary CSV"
echo "══════════════════════════════════════════════════════════"

if $DRY_RUN; then
    echo "  [DRY RUN] Would generate ranked summary CSV"
else
    python3 -c "
import json, csv, os
from pathlib import Path

output_base = '${FULL_SAMPLE_DIR}'
horizons = '${HORIZONS}'.split(',')
rows = []

for h in horizons:
    rpath = Path(output_base) / f'v2_{h}' / 'holdout_sweep_results.json'
    if not rpath.exists():
        continue
    with open(rpath) as f:
        r = json.load(f)
    for feat, data in r.get('discovery_results', {}).items():
        if 'metrics' not in data:
            continue
        m = data['metrics']
        rows.append({
            'horizon': h,
            'feature': feat,
            'discovery_status': data['status'],
            'mean_net_proxy': round(m['G1_mean_net_proxy'], 6),
            'median_net_proxy': round(m['G2_median_net_proxy'], 6),
            'ci_lower_mean': round(m['G3_ci_lower_mean'], 6),
            'win_rate': round(m['G5_win_rate'], 4),
            'top1_share': round(m['G6_top1_share'], 4),
            'top3_share': round(m['G7_top3_share'], 4),
            'coverage': round(m['G8_coverage'], 4),
            'all_gates_pass': m['all_gates_pass'],
        })

# Sort by mean_net_proxy descending
rows.sort(key=lambda x: x['mean_net_proxy'], reverse=True)

csv_path = '${OUTPUT_BASE}/feature_family_sweep_v2_ranked_summary.csv'
if rows:
    with open(csv_path, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    print(f'  Ranked summary: {csv_path} ({len(rows)} rows)')
else:
    print('  No results to rank.')
" 2>&1
fi

# ══════════════════════════════════════════════════════════════════════════════
# STEP F: Final recommendation memo
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  STEP F: Final recommendation memo"
echo "══════════════════════════════════════════════════════════"

if $DRY_RUN; then
    echo "  [DRY RUN] Would generate final recommendation memo"
else
    python3 "${SCRIPT_DIR}/generate_final_recommendation.py" \
        --sweep-base "$FULL_SAMPLE_DIR" \
        --horizons "$HORIZONS" \
        --output "${OUTPUT_BASE}/feature_family_sweep_v2_final_recommendation.md" \
        2>&1
fi

# ── Generate provenance manifest ──────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  Generating provenance manifest"
echo "══════════════════════════════════════════════════════════"

if $DRY_RUN; then
    echo "  [DRY RUN] Would generate manifest"
else
    python3 "${SCRIPT_DIR}/generate_manifest.py" \
        --run-type final_sweep \
        --db-path "$DB_PATH" \
        --script-path "scripts/final_sweep_v2.py" \
        --output-dir "$FULL_SAMPLE_DIR" \
        --horizon "all" \
        2>&1 || echo "  Manifest generation failed (non-critical)"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  FINAL SWEEP COMPLETE"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Expected outputs:"
echo "    ${OUTPUT_BASE}/feature_family_sweep_v2_full_sample.md"
echo "    ${OUTPUT_BASE}/feature_family_sweep_v2_subset_micro.md"
echo "    ${OUTPUT_BASE}/feature_family_sweep_v2_holdout.md"
echo "    ${OUTPUT_BASE}/feature_family_sweep_v2_ranked_summary.csv"
echo "    ${OUTPUT_BASE}/feature_family_sweep_v2_final_recommendation.md"
echo ""
echo "  Collector NOT stopped. Live tape NOT mutated."
