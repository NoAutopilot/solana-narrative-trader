#!/usr/bin/env bash
# pre_upgrade_checkpoint.sh — Run before any VPS resize/upgrade
# 1. Runs one final hot backup
# 2. Runs restore_test.sh on that backup
# 3. Writes checkpoint report
# 4. Exits non-zero if restore fails
# RULE: No VPS resize/upgrade is allowed unless this script passes.
set -euo pipefail

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
REPORT_DIR="/root/solana_trader/reports/ops"
REPORT_FILE="$REPORT_DIR/pre_upgrade_checkpoint_${TIMESTAMP}.md"
LOG_FILE="/var/log/solana_trader/pre_upgrade_checkpoint.log"
SCRIPT_DIR="$(dirname "$0")"

mkdir -p "$REPORT_DIR" "$(dirname "$LOG_FILE")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

log "=== PRE-UPGRADE CHECKPOINT START ts=$TIMESTAMP ==="
log "RULE: Do not proceed with VPS resize/upgrade unless this script exits 0."

# Step 1: Final hot backup
log "Step 1: Running final hot backup..."
"$SCRIPT_DIR/backup_sqlite.sh" "pre_upgrade" 2>&1 | tee -a "$LOG_FILE"
BACKUP_EXIT=${PIPESTATUS[0]}
if [[ $BACKUP_EXIT -ne 0 ]]; then
    log "FAIL: Backup failed (exit $BACKUP_EXIT). DO NOT PROCEED WITH UPGRADE."
    echo "# Pre-Upgrade Checkpoint: FAIL" > "$REPORT_FILE"
    echo "_Timestamp: $TIMESTAMP_" >> "$REPORT_FILE"
    echo "" >> "$REPORT_FILE"
    echo "**BACKUP FAILED — DO NOT PROCEED WITH UPGRADE**" >> "$REPORT_FILE"
    exit 1
fi
log "Step 1: Backup OK."

# Step 2: Restore test
log "Step 2: Running restore test..."
"$SCRIPT_DIR/restore_test.sh" 2>&1 | tee -a "$LOG_FILE"
RESTORE_EXIT=${PIPESTATUS[0]}

# Step 3: Write checkpoint report
RESTORE_REPORT="/root/solana_trader/reports/ops/restore_test_latest.md"
{
    echo "# Pre-Upgrade Checkpoint Report"
    echo "_Timestamp: $TIMESTAMP_"
    echo ""
    if [[ $RESTORE_EXIT -eq 0 ]]; then
        echo "**OVERALL: PASS — Safe to proceed with upgrade.**"
    else
        echo "**OVERALL: FAIL — DO NOT PROCEED WITH UPGRADE.**"
    fi
    echo ""
    echo "## Backup Step"
    echo "- Status: PASS"
    echo ""
    echo "## Restore Test"
    if [[ $RESTORE_EXIT -eq 0 ]]; then
        echo "- Status: PASS"
    else
        echo "- Status: FAIL"
    fi
    echo ""
    if [[ -f "$RESTORE_REPORT" ]]; then
        echo "## Restore Test Detail"
        cat "$RESTORE_REPORT"
    fi
} > "$REPORT_FILE"

log "Checkpoint report written: $REPORT_FILE"

if [[ $RESTORE_EXIT -ne 0 ]]; then
    log "FAIL: Restore test failed. DO NOT PROCEED WITH UPGRADE."
    exit 1
fi

log "=== PRE-UPGRADE CHECKPOINT PASSED — Safe to proceed. ==="
exit 0
