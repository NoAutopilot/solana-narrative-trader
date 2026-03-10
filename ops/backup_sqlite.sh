#!/usr/bin/env bash
# backup_sqlite.sh — Hot SQLite backup with SHA256, meta.json, and retention
# Safe for live DBs: uses SQLite online backup API via Python
# Usage: ./backup_sqlite.sh [15min|hourly|daily]
# Called by systemd timer; tier argument used for retention labelling only.
set -euo pipefail

TIER="${1:-15min}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="/root/solana_trader/backups/sqlite"
LOG_FILE="/var/log/solana_trader/backup_sqlite.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

log "=== backup_sqlite.sh START tier=$TIER ts=$TIMESTAMP ==="

# ── Critical DBs to back up ────────────────────────────────────────────────
declare -A CRITICAL_DBS=(
    ["solana_trader"]="/root/solana_trader/data/solana_trader.db"
    ["observer_lcr_cont_v1"]="/root/solana_trader/data/observer_lcr_cont_v1.db"
    ["observer_pfm_cont_v1"]="/root/solana_trader/data/observer_pfm_cont_v1.db"
    ["observer_pfm_rev_v1"]="/root/solana_trader/data/observer_pfm_rev_v1.db"
    ["post_bonding"]="/root/solana_trader/data/post_bonding.db"
)

BACKUP_OK=0
BACKUP_FAIL=0

for DB_NAME in "${!CRITICAL_DBS[@]}"; do
    SRC="${CRITICAL_DBS[$DB_NAME]}"
    if [[ ! -f "$SRC" ]]; then
        log "SKIP $DB_NAME — not found at $SRC"
        continue
    fi

    DEST_DIR="$BACKUP_ROOT/$DB_NAME"
    mkdir -p "$DEST_DIR"
    DEST_FILE="$DEST_DIR/${TIMESTAMP}.db"

    log "Backing up $DB_NAME ($SRC) -> $DEST_FILE"

    # Hot backup via Python sqlite3 online backup API (safe for live DBs)
    python3 - <<PYEOF
import sqlite3, sys
src = "$SRC"
dst = "$DEST_FILE"
try:
    src_con = sqlite3.connect(f"file:{src}?mode=ro", uri=True, timeout=30)
    dst_con = sqlite3.connect(dst, timeout=30)
    src_con.backup(dst_con, pages=100)
    dst_con.close()
    src_con.close()
    print(f"OK: {dst}")
except Exception as e:
    print(f"FAIL: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

    if [[ $? -ne 0 ]]; then
        log "FAIL backup $DB_NAME"
        BACKUP_FAIL=$((BACKUP_FAIL + 1))
        continue
    fi

    # SHA256
    SHA256="$(sha256sum "$DEST_FILE" | awk '{print $1}')"
    echo "$SHA256  ${TIMESTAMP}.db" > "${DEST_FILE}.sha256"

    # Row counts for key tables
    ROW_COUNTS="$(python3 - <<PYEOF
import sqlite3, json
con = sqlite3.connect(f"file:$DEST_FILE?mode=ro", uri=True, timeout=10)
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
counts = {}
for t in tables:
    try: counts[t] = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    except: counts[t] = -1
con.close()
print(json.dumps(counts))
PYEOF
)"

    FILE_SIZE="$(stat -c%s "$DEST_FILE")"

    # meta.json
    python3 - <<PYEOF
import json
meta = {
    "db_name": "$DB_NAME",
    "db_path": "$SRC",
    "backup_path": "$DEST_FILE",
    "timestamp_utc": "$TIMESTAMP",
    "tier": "$TIER",
    "file_size_bytes": $FILE_SIZE,
    "sha256": "$SHA256",
    "row_counts": $ROW_COUNTS
}
with open("${DEST_FILE}.meta.json", "w") as f:
    json.dump(meta, f, indent=2)
print("meta written")
PYEOF

    log "OK $DB_NAME size=${FILE_SIZE}B sha256=${SHA256:0:16}..."
    BACKUP_OK=$((BACKUP_OK + 1))
done

# ── Retention cleanup ──────────────────────────────────────────────────────
log "Running retention cleanup..."
python3 - <<PYEOF
import os, glob, time
from datetime import datetime, timezone, timedelta

BACKUP_ROOT = "$BACKUP_ROOT"
NOW = datetime.now(timezone.utc)

# Retention windows (in hours)
KEEP_15MIN_HOURS = 72       # 15-min backups: keep 72h
KEEP_HOURLY_HOURS = 24 * 14 # hourly: keep 14 days
KEEP_DAILY_HOURS  = 24 * 30 # daily: keep 30 days

deleted = 0
kept = 0

for db_dir in glob.glob(f"{BACKUP_ROOT}/*/"):
    files = sorted(glob.glob(f"{db_dir}/*.db"))
    for f in files:
        fname = os.path.basename(f)
        try:
            ts = datetime.strptime(fname.replace('.db',''), '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        except:
            continue
        age_h = (NOW - ts).total_seconds() / 3600

        # Determine if this file should be kept
        # Keep all within 72h (covers 15-min tier)
        if age_h <= KEEP_15MIN_HOURS:
            kept += 1
            continue
        # Keep hourly within 14 days (files at :00 minutes)
        if age_h <= KEEP_HOURLY_HOURS and ts.minute == 0:
            kept += 1
            continue
        # Keep daily within 30 days (files at 00:00 UTC)
        if age_h <= KEEP_DAILY_HOURS and ts.hour == 0 and ts.minute == 0:
            kept += 1
            continue
        # Delete
        for ext in ['', '.sha256', '.meta.json']:
            fp = f + ext
            if os.path.exists(fp):
                os.remove(fp)
        deleted += 1

print(f"Retention: kept={kept} deleted={deleted}")
PYEOF

log "=== backup_sqlite.sh DONE ok=$BACKUP_OK fail=$BACKUP_FAIL ==="
if [[ $BACKUP_FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
