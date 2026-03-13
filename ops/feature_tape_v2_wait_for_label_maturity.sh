#!/usr/bin/env bash
# ══════════════════════════════════════════════════════════════════════════════
# feature_tape_v2_wait_for_label_maturity.sh
# Cold-path only. Does NOT modify the collector, scanner, or live DB schema.
#
# After collection completes (>= 96 fires), this script waits until forward
# return labels for all primary decision horizons are mature.
#
# Maturity rule:
#   A label for horizon H is mature for fire F when:
#     now_utc >= fire_time(F) + H + JITTER_BUFFER
#
#   All labels for horizon H are mature when the LAST fire's label is mature.
#
# Primary decision horizons: +5m, +15m, +30m, +1h, +4h
# Excluded from primary decision: +1d (deferred)
#
# Usage:
#   bash ops/feature_tape_v2_wait_for_label_maturity.sh
#   bash ops/feature_tape_v2_wait_for_label_maturity.sh --db /path/to/db
# ══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
DB_PATH="${DB_PATH:-/root/solana_trader/data/solana_trader.db}"
STATUS_DIR="${STATUS_DIR:-/root/solana_trader/status}"
COMPLETION_STATUS="${STATUS_DIR}/feature_tape_v2_collection_complete.json"
MATURITY_STATUS="${STATUS_DIR}/feature_tape_v2_labels_mature.json"
MATURITY_REPORT="reports/synthesis/feature_tape_v2_label_maturity.md"
POLL_INTERVAL_S="${POLL_INTERVAL_S:-120}"  # 2 minutes
JITTER_BUFFER_S=120  # 2 minutes extra buffer for snapshot timing jitter

# Horizon definitions (seconds)
declare -A HORIZONS
HORIZONS[5m]=300
HORIZONS[15m]=900
HORIZONS[30m]=1800
HORIZONS[1h]=3600
HORIZONS[4h]=14400

# ── Parse args ────────────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --db)         DB_PATH="$2"; shift 2 ;;
        --status-dir) STATUS_DIR="$2"; shift 2 ;;
        --interval)   POLL_INTERVAL_S="$2"; shift 2 ;;
        *) echo "Unknown arg: $1"; exit 1 ;;
    esac
done

mkdir -p "$STATUS_DIR"

# ── Pre-check: collection must be complete ────────────────────────────────────
if [[ ! -f "$COMPLETION_STATUS" ]]; then
    echo "ERROR: Collection completion status not found at ${COMPLETION_STATUS}"
    echo "Run ops/feature_tape_v2_wait_for_completion.sh first."
    exit 1
fi

echo "════════════════════════════════════════════════════════════"
echo "  feature_tape_v2 — Label Maturity Gate"
echo "  DB path:       ${DB_PATH}"
echo "  Jitter buffer: ${JITTER_BUFFER_S}s"
echo "  Poll interval: ${POLL_INTERVAL_S}s"
echo "  Horizons:      5m, 15m, 30m, 1h, 4h (primary)"
echo "  Excluded:      1d (deferred)"
echo "════════════════════════════════════════════════════════════"

# ── Get last fire epoch ───────────────────────────────────────────────────────
LAST_FIRE_EPOCH=$(sqlite3 "$DB_PATH" \
    "SELECT fire_time_epoch FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch DESC LIMIT 1;" \
    2>/dev/null)

if [[ -z "$LAST_FIRE_EPOCH" ]]; then
    echo "ERROR: Could not read last fire epoch from DB."
    exit 1
fi

LAST_FIRE_TIME=$(sqlite3 "$DB_PATH" \
    "SELECT fire_time_utc FROM feature_tape_v2_fire_log ORDER BY fire_time_epoch DESC LIMIT 1;" \
    2>/dev/null)

echo "  Last fire: ${LAST_FIRE_TIME} (epoch: ${LAST_FIRE_EPOCH})"
echo ""

# Compute maturity deadlines for each horizon
declare -A DEADLINES
for H in 5m 15m 30m 1h 4h; do
    HS=${HORIZONS[$H]}
    # Deadline = last_fire_epoch + horizon_seconds + jitter_buffer
    DEADLINE=$(echo "${LAST_FIRE_EPOCH} + ${HS} + ${JITTER_BUFFER_S}" | bc)
    DEADLINES[$H]=$DEADLINE
    DEADLINE_UTC=$(date -u -d "@${DEADLINE}" +"%Y-%m-%dT%H:%M:%S+00:00" 2>/dev/null || \
                   python3 -c "from datetime import datetime,timezone; print(datetime.fromtimestamp(${DEADLINE},timezone.utc).isoformat())")
    echo "  +${H} matures at: ${DEADLINE_UTC}"
done

echo ""

# ── Poll loop ─────────────────────────────────────────────────────────────────
while true; do
    NOW_EPOCH=$(date +%s)
    NOW_UTC=$(date -u +"%Y-%m-%dT%H:%M:%S+00:00")

    ALL_MATURE=true
    MATURE_LIST=""
    PENDING_LIST=""

    for H in 5m 15m 30m 1h 4h; do
        DL=${DEADLINES[$H]}
        if [[ "$NOW_EPOCH" -ge "$DL" ]]; then
            MATURE_LIST="${MATURE_LIST} +${H}"
        else
            ALL_MATURE=false
            REMAINING=$((DL - NOW_EPOCH))
            REMAINING_MIN=$((REMAINING / 60))
            PENDING_LIST="${PENDING_LIST} +${H}(${REMAINING_MIN}m)"
        fi
    done

    echo "[${NOW_UTC}] mature:${MATURE_LIST:-none}  pending:${PENDING_LIST:-none}"

    if $ALL_MATURE; then
        echo ""
        echo "  ALL PRIMARY LABELS MATURE."
        echo ""

        # ── Verify actual label availability in DB ────────────────────────
        # Check universe_snapshot coverage for each horizon
        echo "  Verifying label availability in universe_snapshot..."

        LABEL_COVERAGE=""
        for H in 5m 15m 30m 1h 4h; do
            HS=${HORIZONS[$H]}
            # Count how many fire+mint pairs have a matching snapshot at fire_time + horizon
            COVERAGE=$(sqlite3 "$DB_PATH" "
                SELECT ROUND(
                    100.0 * SUM(CASE WHEN us.price_usd IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*),
                    1
                )
                FROM feature_tape_v2 ft
                LEFT JOIN universe_snapshot us
                    ON us.mint = ft.candidate_mint
                    AND us.snapshot_at >= datetime(ft.fire_time_epoch + ${HS} - 60, 'unixepoch')
                    AND us.snapshot_at <= datetime(ft.fire_time_epoch + ${HS} + 120, 'unixepoch')
                WHERE ft.eligible = 1;
            " 2>/dev/null || echo "0.0")
            echo "    +${H}: ${COVERAGE}% label coverage (eligible-only)"
            LABEL_COVERAGE="${LABEL_COVERAGE}\"${H}\": ${COVERAGE}, "
        done

        # ── Write maturity status ─────────────────────────────────────────
        cat > "$MATURITY_STATUS" <<EOF
{
  "status": "ALL_PRIMARY_LABELS_MATURE",
  "detected_at": "${NOW_UTC}",
  "last_fire_time": "${LAST_FIRE_TIME}",
  "last_fire_epoch": ${LAST_FIRE_EPOCH},
  "jitter_buffer_s": ${JITTER_BUFFER_S},
  "horizons_mature": ["5m", "15m", "30m", "1h", "4h"],
  "horizons_excluded": ["1d"],
  "label_coverage_pct": {${LABEL_COVERAGE%%, }},
  "db_path": "${DB_PATH}"
}
EOF

        # ── Write maturity report ─────────────────────────────────────────
        REPORT_DIR=$(dirname "$MATURITY_REPORT")
        mkdir -p "$REPORT_DIR"
        cat > "$MATURITY_REPORT" <<EOF
# Feature Tape v2 — Label Maturity Report

**Date:** ${NOW_UTC}
**Status:** ALL PRIMARY LABELS MATURE

---

## Maturity Summary

| Horizon | Mature? | Coverage (eligible-only) |
|---------|---------|------------------------:|
| +5m     | YES     | see status JSON          |
| +15m    | YES     | see status JSON          |
| +30m    | YES     | see status JSON          |
| +1h     | YES     | see status JSON          |
| +4h     | YES     | see status JSON          |
| +1d     | EXCLUDED (deferred) | N/A          |

## Timing

- Last fire: ${LAST_FIRE_TIME}
- Jitter buffer: ${JITTER_BUFFER_S}s
- All primary labels matured at: ${NOW_UTC}

## Next Step

Run: \`bash ops/run_feature_tape_v2_final_sweeps.sh\`
EOF

        echo ""
        echo "  Status written to: ${MATURITY_STATUS}"
        echo "  Report written to: ${MATURITY_REPORT}"
        echo ""
        echo "  Next step: run ops/run_feature_tape_v2_final_sweeps.sh"
        exit 0
    fi

    sleep "$POLL_INTERVAL_S"
done
