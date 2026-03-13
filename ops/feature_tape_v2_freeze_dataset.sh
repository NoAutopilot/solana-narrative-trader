#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# feature_tape_v2_freeze_dataset.sh
# Cold-path only. Does NOT mutate the live tape or stop the collector.
#
# Creates:
#   1) reports/synthesis/feature_tape_v2_final_manifest.json
#   2) A frozen SQLite snapshot: artifacts/feature_tape_v2_frozen_YYYYMMDD_HHMMSS.db
#   3) A frozen CSV export:      artifacts/feature_tape_v2_frozen_YYYYMMDD_HHMMSS.csv
#
# Usage:
#   bash ops/feature_tape_v2_freeze_dataset.sh
#   bash ops/feature_tape_v2_freeze_dataset.sh --db /path/to/db
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/root/solana_trader/data/solana_trader.db}"
STATUS_DIR="${STATUS_DIR:-/root/solana_trader/status}"
MATURITY_STATUS="${STATUS_DIR}/feature_tape_v2_labels_mature.json"
MANIFEST_PATH="reports/synthesis/feature_tape_v2_final_manifest.json"
ARTIFACTS_DIR="artifacts"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db)         DB_PATH="$2"; shift 2 ;;
        --status-dir) STATUS_DIR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

# ── Pre-checks ────────────────────────────────────────────────────────────────
if [[ ! -f "$MATURITY_STATUS" ]]; then
    echo "ERROR: Label maturity status not found at ${MATURITY_STATUS}"
    echo "Run ops/feature_tape_v2_wait_for_label_maturity.sh first."
    exit 1
fi

if [[ ! -f "$DB_PATH" ]]; then
    echo "ERROR: Database not found at ${DB_PATH}"
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "  feature_tape_v2 — Dataset Freeze"
echo "  DB path: ${DB_PATH}"
echo "════════════════════════════════════════════════════════════"

NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")
TIMESTAMP=$(date -u +"%Y%m%d_%H%M%S")
SESSION_ID="freeze_${TIMESTAMP}"

mkdir -p "$ARTIFACTS_DIR"
mkdir -p "$(dirname "$MANIFEST_PATH")"

# ── Collect stats ─────────────────────────────────────────────────────────────
echo "  Collecting dataset statistics..."

N_FIRES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2_fire_log;")
N_ROWS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2;")
N_ELIGIBLE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2 WHERE eligible = 1;")
N_INELIGIBLE=$((N_ROWS - N_ELIGIBLE))

FIRST_FIRE_ID=$(sqlite3 "$DB_PATH" "SELECT fire_id FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch ASC LIMIT 1;")
FIRST_FIRE_TIME=$(sqlite3 "$DB_PATH" "SELECT fire_time_utc FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch ASC LIMIT 1;")
LAST_FIRE_ID=$(sqlite3 "$DB_PATH" "SELECT fire_id FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch DESC LIMIT 1;")
LAST_FIRE_TIME=$(sqlite3 "$DB_PATH" "SELECT fire_time_utc FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch DESC LIMIT 1;")

GAP_FIRES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2_fire_log WHERE rows_written = 0;")

# Micro coverage
N_MICRO=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2 WHERE order_flow_source = 'microstructure_log';")
N_MICRO_ELIG=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2 WHERE eligible = 1 AND order_flow_source = 'microstructure_log';")

# Quote coverage (eligible-only)
N_QUOTE_ELIG=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2 WHERE eligible = 1 AND jup_vs_cpamm_diff_pct IS NOT NULL;")

# Label coverage by horizon (check universe_snapshot availability)
echo "  Computing label coverage by horizon..."
LABEL_COV_5M=$(sqlite3 "$DB_PATH" "
    SELECT ROUND(100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM feature_tape_v2 ft
    LEFT JOIN universe_snapshot us ON us.mint = ft.candidate_mint
        AND us.snapshot_at >= datetime(ft.fire_time_epoch + 240, 'unixepoch')
        AND us.snapshot_at <= datetime(ft.fire_time_epoch + 420, 'unixepoch')
    WHERE ft.eligible = 1;
" 2>/dev/null || echo "0.0")

LABEL_COV_15M=$(sqlite3 "$DB_PATH" "
    SELECT ROUND(100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM feature_tape_v2 ft
    LEFT JOIN universe_snapshot us ON us.mint = ft.candidate_mint
        AND us.snapshot_at >= datetime(ft.fire_time_epoch + 840, 'unixepoch')
        AND us.snapshot_at <= datetime(ft.fire_time_epoch + 1020, 'unixepoch')
    WHERE ft.eligible = 1;
" 2>/dev/null || echo "0.0")

LABEL_COV_30M=$(sqlite3 "$DB_PATH" "
    SELECT ROUND(100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM feature_tape_v2 ft
    LEFT JOIN universe_snapshot us ON us.mint = ft.candidate_mint
        AND us.snapshot_at >= datetime(ft.fire_time_epoch + 1740, 'unixepoch')
        AND us.snapshot_at <= datetime(ft.fire_time_epoch + 1920, 'unixepoch')
    WHERE ft.eligible = 1;
" 2>/dev/null || echo "0.0")

LABEL_COV_1H=$(sqlite3 "$DB_PATH" "
    SELECT ROUND(100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM feature_tape_v2 ft
    LEFT JOIN universe_snapshot us ON us.mint = ft.candidate_mint
        AND us.snapshot_at >= datetime(ft.fire_time_epoch + 3540, 'unixepoch')
        AND us.snapshot_at <= datetime(ft.fire_time_epoch + 3720, 'unixepoch')
    WHERE ft.eligible = 1;
" 2>/dev/null || echo "0.0")

LABEL_COV_4H=$(sqlite3 "$DB_PATH" "
    SELECT ROUND(100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 1)
    FROM feature_tape_v2 ft
    LEFT JOIN universe_snapshot us ON us.mint = ft.candidate_mint
        AND us.snapshot_at >= datetime(ft.fire_time_epoch + 14340, 'unixepoch')
        AND us.snapshot_at <= datetime(ft.fire_time_epoch + 14520, 'unixepoch')
    WHERE ft.eligible = 1;
" 2>/dev/null || echo "0.0")

# ── Git info ──────────────────────────────────────────────────────────────────
GITHUB_COMMIT=$(cd "$REPO_DIR" && git rev-parse HEAD 2>/dev/null || echo "UNKNOWN")
GITHUB_BRANCH=$(cd "$REPO_DIR" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "UNKNOWN")

# VPS local commit (same repo on VPS)
VPS_COMMIT=$(cd /root/solana_trader 2>/dev/null && git rev-parse HEAD 2>/dev/null || echo "UNKNOWN_OR_NOT_GIT")

# Script SHA-256
COLLECTOR_SHA=$(sha256sum "$REPO_DIR/feature_tape_v2.py" 2>/dev/null | awk '{print $1}' || echo "UNKNOWN")

# DB file size
DB_SIZE=$(stat -c%s "$DB_PATH" 2>/dev/null || echo "0")

# ── Write manifest ────────────────────────────────────────────────────────────
echo "  Writing manifest..."

cat > "$MANIFEST_PATH" <<EOF
{
  "manifest_version": "2.0",
  "session_id": "${SESSION_ID}",
  "generated_at": "${NOW_UTC}",
  "run_type": "dataset_freeze",

  "code": {
    "github_repo": "NoAutopilot/solana-narrative-trader",
    "github_commit": "${GITHUB_COMMIT}",
    "github_branch": "${GITHUB_BRANCH}",
    "vps_local_commit": "${VPS_COMMIT}",
    "collection_script": "feature_tape_v2.py",
    "collection_script_sha256": "${COLLECTOR_SHA}"
  },

  "data": {
    "db_path": "${DB_PATH}",
    "db_size_bytes": ${DB_SIZE},
    "table_name": "feature_tape_v2",
    "fire_log_table": "feature_tape_v2_fire_log",
    "n_fires": ${N_FIRES},
    "n_rows_total": ${N_ROWS},
    "n_rows_eligible": ${N_ELIGIBLE},
    "n_rows_ineligible": ${N_INELIGIBLE},
    "first_fire_id": "${FIRST_FIRE_ID}",
    "first_fire_time": "${FIRST_FIRE_TIME}",
    "last_fire_id": "${LAST_FIRE_ID}",
    "last_fire_time": "${LAST_FIRE_TIME}",
    "gap_fires": ${GAP_FIRES},
    "micro_coverage_total": ${N_MICRO},
    "micro_coverage_eligible": ${N_MICRO_ELIG},
    "quote_coverage_eligible": ${N_QUOTE_ELIG}
  },

  "label_coverage_pct": {
    "5m": ${LABEL_COV_5M},
    "15m": ${LABEL_COV_15M},
    "30m": ${LABEL_COV_30M},
    "1h": ${LABEL_COV_1H},
    "4h": ${LABEL_COV_4H},
    "1d": "EXCLUDED_FROM_PRIMARY"
  },

  "collection": {
    "service_name": "solana-feature-tape-v2",
    "collector_stopped": false
  },

  "sample_definition": {
    "primary_filter": "eligible = 1",
    "secondary_filter": "none (full universe)",
    "time_range": "${FIRST_FIRE_TIME} to ${LAST_FIRE_TIME}",
    "exclusions": "gap_fires=${GAP_FIRES}"
  },

  "frozen_artifacts": {
    "sqlite_snapshot": "${ARTIFACTS_DIR}/feature_tape_v2_frozen_${TIMESTAMP}.db",
    "csv_export": "${ARTIFACTS_DIR}/feature_tape_v2_frozen_${TIMESTAMP}.csv"
  }
}
EOF

echo "  Manifest written to: ${MANIFEST_PATH}"

# ── Create frozen SQLite snapshot ─────────────────────────────────────────────
echo "  Creating frozen SQLite snapshot..."
FROZEN_DB="${ARTIFACTS_DIR}/feature_tape_v2_frozen_${TIMESTAMP}.db"

sqlite3 "$DB_PATH" ".dump feature_tape_v2" | sqlite3 "$FROZEN_DB"
sqlite3 "$DB_PATH" ".dump feature_tape_v2_fire_log" | sqlite3 "$FROZEN_DB"

FROZEN_DB_SIZE=$(stat -c%s "$FROZEN_DB" 2>/dev/null || echo "0")
echo "  Frozen DB: ${FROZEN_DB} (${FROZEN_DB_SIZE} bytes)"

# ── Create frozen CSV export ─────────────────────────────────────────────────
echo "  Creating frozen CSV export..."
FROZEN_CSV="${ARTIFACTS_DIR}/feature_tape_v2_frozen_${TIMESTAMP}.csv"

sqlite3 -header -csv "$DB_PATH" "SELECT * FROM feature_tape_v2;" > "$FROZEN_CSV"

FROZEN_CSV_SIZE=$(stat -c%s "$FROZEN_CSV" 2>/dev/null || echo "0")
echo "  Frozen CSV: ${FROZEN_CSV} (${FROZEN_CSV_SIZE} bytes)"

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo "  DATASET FROZEN."
echo "  Live tape NOT mutated. Collector NOT stopped."
echo ""
echo "  Artifacts:"
echo "    Manifest:  ${MANIFEST_PATH}"
echo "    SQLite:    ${FROZEN_DB}"
echo "    CSV:       ${FROZEN_CSV}"
echo ""
echo "  Next step: run ops/run_feature_tape_v2_final_sweeps.sh"
