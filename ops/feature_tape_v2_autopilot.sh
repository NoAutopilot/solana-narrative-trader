#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# feature_tape_v2_autopilot.sh
# MATURITY-AWARE END-OF-RUN AUTOPILOT
#
# Cold-path only. Does NOT modify the collector, scanner, or live DB schema.
# Does NOT stop the collector. Does NOT start any live observer.
#
# Chains:
#   1) Wait for collection completion (>= 96 fires)
#   2) Wait for label maturity (all primary horizons)
#   3) Freeze dataset (manifest + artifacts)
#   4) Run final sweeps (full-sample, subset-micro, holdout, benchmark)
#   5) Generate final recommendation memo
#
# Usage:
#   nohup bash ops/feature_tape_v2_autopilot.sh > /var/log/ft_v2_autopilot.log 2>&1 &
#   bash ops/feature_tape_v2_autopilot.sh --dry-run
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

OPS_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$OPS_DIR/.." && pwd)"
cd "$REPO_DIR"

DB_PATH="${DB_PATH:-/root/solana_trader/data/solana_trader.db}"
DRY_RUN=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --db)      DB_PATH="$2"; shift 2 ;;
        --dry-run) DRY_RUN="--dry-run"; shift ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

export DB_PATH

echo "════════════════════════════════════════════════════════════"
echo "  feature_tape_v2 — MATURITY-AWARE END-OF-RUN AUTOPILOT"
echo "  Started: $(date -u +"%Y-%m-%dT%H:%M:%S+00:00")"
echo "  DB path: ${DB_PATH}"
echo "  Dry run: ${DRY_RUN:-no}"
echo "════════════════════════════════════════════════════════════"
echo ""

# ── Step 1: Wait for collection completion ────────────────────────────────────
echo "═══ STEP 1/5: Collection Completion Watcher ═══"
bash "$OPS_DIR/feature_tape_v2_wait_for_completion.sh" --db "$DB_PATH"
echo ""

# ── Step 2: Wait for label maturity ───────────────────────────────────────────
echo "═══ STEP 2/5: Label Maturity Gate ═══"
bash "$OPS_DIR/feature_tape_v2_wait_for_label_maturity.sh" --db "$DB_PATH"
echo ""

# ── Step 3: Freeze dataset ───────────────────────────────────────────────────
echo "═══ STEP 3/5: Dataset Freeze ═══"
bash "$OPS_DIR/feature_tape_v2_freeze_dataset.sh" --db "$DB_PATH"
echo ""

# ── Step 4: Run final sweeps ──────────────────────────────────────────────────
echo "═══ STEP 4/5: Final Sweeps ═══"
bash "$OPS_DIR/run_feature_tape_v2_final_sweeps.sh" --db "$DB_PATH" $DRY_RUN
echo ""

# ── Step 5: Done ──────────────────────────────────────────────────────────────
echo "═══ STEP 5/5: Complete ═══"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  AUTOPILOT COMPLETE"
echo "  Finished: $(date -u +"%Y-%m-%dT%H:%M:%S+00:00")"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Final outputs:"
echo "    reports/synthesis/feature_tape_v2_final_manifest.json"
echo "    reports/synthesis/feature_tape_v2_label_maturity.md"
echo "    reports/synthesis/feature_family_sweep_v2_full_sample.md"
echo "    reports/synthesis/feature_family_sweep_v2_subset_micro.md"
echo "    reports/synthesis/feature_family_sweep_v2_holdout.md"
echo "    reports/synthesis/feature_family_sweep_v2_ranked_summary.csv"
echo "    reports/synthesis/feature_family_sweep_v2_final_recommendation.md"
echo ""
echo "  Safety:"
echo "    - Collector NOT stopped"
echo "    - Live tape NOT mutated"
echo "    - No live observer started"
echo "    - No scanner/strategy changes made"
