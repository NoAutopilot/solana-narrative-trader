#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# feature_tape_v2_wait_for_completion.sh
# Cold-path only. Does NOT stop, restart, or modify the collector.
#
# Monitors feature_tape_v2_fire_log until n_fires >= TARGET_FIRES.
# When reached, writes a status file and exits 0.
#
# Usage:
#   bash ops/feature_tape_v2_wait_for_completion.sh
#   bash ops/feature_tape_v2_wait_for_completion.sh --target 96 --db /path/to/db
#   nohup bash ops/feature_tape_v2_wait_for_completion.sh &
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/root/solana_trader/data/solana_trader.db}"
TARGET_FIRES="${TARGET_FIRES:-96}"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-300}"  # 5 minutes
STATUS_DIR="${STATUS_DIR:-/root/solana_trader/status}"
STATUS_FILE="${STATUS_DIR}/feature_tape_v2_collection_complete.json"

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --target)   TARGET_FIRES="$2"; shift 2 ;;
        --db)       DB_PATH="$2"; shift 2 ;;
        --interval) POLL_INTERVAL_S="$2"; shift 2 ;;
        --status-dir) STATUS_DIR="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$STATUS_DIR"

echo "════════════════════════════════════════════════════════════"
echo "  feature_tape_v2 — Collection Completion Watcher"
echo "  Target fires:  ${TARGET_FIRES}"
echo "  DB path:       ${DB_PATH}"
echo "  Poll interval: ${POLL_INTERVAL_S}s"
echo "  Status file:   ${STATUS_FILE}"
echo "════════════════════════════════════════════════════════════"

# ── Poll loop ─────────────────────────────────────────────────────────────────
while true; do
    NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")

    # Query fire count
    N_FIRES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2_fire_log;" 2>/dev/null || echo "0")
    N_ROWS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2;" 2>/dev/null || echo "0")
    N_ELIGIBLE=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM feature_tape_v2 WHERE eligible = 1;" 2>/dev/null || echo "0")

    echo "[${NOW_UTC}] fires=${N_FIRES}/${TARGET_FIRES}  rows=${N_ROWS}  eligible=${N_ELIGIBLE}"

    if [[ "$N_FIRES" -ge "$TARGET_FIRES" ]]; then
        echo ""
        echo "  COLLECTION COMPLETE — ${N_FIRES} fires reached."
        echo ""

        # Get first/last fire info
        FIRST_FIRE=$(sqlite3 "$DB_PATH" \
            "SELECT fire_id || '|' || fire_time_utc FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch ASC LIMIT 1;" \
            2>/dev/null || echo "unknown|unknown")
        LAST_FIRE=$(sqlite3 "$DB_PATH" \
            "SELECT fire_id || '|' || fire_time_utc FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch DESC LIMIT 1;" \
            2>/dev/null || echo "unknown|unknown")

        FIRST_FIRE_ID=$(echo "$FIRST_FIRE" | cut -d'|' -f1)
        FIRST_FIRE_TIME=$(echo "$FIRST_FIRE" | cut -d'|' -f2)
        LAST_FIRE_ID=$(echo "$LAST_FIRE" | cut -d'|' -f1)
        LAST_FIRE_TIME=$(echo "$LAST_FIRE" | cut -d'|' -f2)

        # Check for gaps (fires with 0 rows written)
        GAPS=$(sqlite3 "$DB_PATH" \
            "SELECT COUNT(*) FROM feature_tape_v2_fire_log WHERE rows_written = 0;" \
            2>/dev/null || echo "0")

        # Write status file
        cat > "$STATUS_FILE" <<EOF
{
  "status": "COLLECTION_COMPLETE",
  "detected_at": "${NOW_UTC}",
  "n_fires": ${N_FIRES},
  "target_fires": ${TARGET_FIRES},
  "n_rows_total": ${N_ROWS},
  "n_rows_eligible": ${N_ELIGIBLE},
  "first_fire_id": "${FIRST_FIRE_ID}",
  "first_fire_time": "${FIRST_FIRE_TIME}",
  "last_fire_id": "${LAST_FIRE_ID}",
  "last_fire_time": "${LAST_FIRE_TIME}",
  "gap_fires": ${GAPS},
  "db_path": "${DB_PATH}",
  "collector_stopped": false,
  "notes": "Collector NOT stopped. Watcher exited cleanly."
}
EOF

        echo "  Status written to: ${STATUS_FILE}"
        echo "  Collector NOT stopped (cold-path only)."
        echo ""
        echo "  Next step: run ops/feature_tape_v2_wait_for_label_maturity.sh"
        exit 0
    fi

    sleep "$POLL_INTERVAL_S"
done
