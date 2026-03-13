#!/usr/bin/env bash
# backup_sqlite.sh — Hot SQLite backup with SHA256, meta.json, and tiered retention
# Safe for live DBs: uses SQLite online backup API via Python
# Usage: ./backup_sqlite.sh [15min|hourly|daily]
# Called by systemd timer; tier argument used for retention labelling only.
#
# RETENTION POLICY (v3 — 2026-03-11, sustainable for 24GB VPS):
#
#   ACTIVE DBs (solana_trader — live, growing):
#     15-min backups : keep 6h   (24 copies × ~185MB = ~4.4GB)
#     hourly backups : keep 48h  (48 copies × ~185MB = ~8.9GB — but only :00 files)
#     daily backups  : keep 7d   (7 copies  × ~185MB = ~1.3GB — but only 00:00 files)
#     Steady state   : ~14.6GB max (well within 24GB disk)
#
#   ARCHIVED / STATIC DBs (observer_*, post_bonding — no active writes):
#     Keep ONE immutable local snapshot only
#     No 15-min backups, no hourly backups
#     Optional daily backup for 7d max (skipped here — snapshot is sufficient)
#
# COMPRESSION: none (SQLite backup API produces valid .db files)
# OUTPUT: <timestamp>.db + <timestamp>.db.sha256 + <timestamp>.db.meta.json
#
# Local durability only — off-box backup not configured.
set -euo pipefail

TIER="${1:-15min}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_ROOT="/root/solana_trader/backups/sqlite"
LOG_FILE="/var/log/solana_trader/backup_sqlite.log"
mkdir -p "$(dirname "$LOG_FILE")"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }
log "=== backup_sqlite.sh START tier=$TIER ts=$TIMESTAMP ==="

# ── ACTIVE DBs — backed up every 15 min ───────────────────────────────────
declare -A ACTIVE_DBS=(
    ["solana_trader"]="/root/solana_trader/data/solana_trader.db"
)

# ── ARCHIVED / STATIC DBs — one immutable snapshot only ───────────────────
declare -A ARCHIVED_DBS=(
    ["observer_lcr_cont_v1"]="/root/solana_trader/data/observer_lcr_cont_v1.db"
    ["observer_pfm_cont_v1"]="/root/solana_trader/data/observer_pfm_cont_v1.db"
    ["observer_pfm_rev_v1"]="/root/solana_trader/data/observer_pfm_rev_v1.db"
    ["post_bonding"]="/root/solana_trader/data/post_bonding.db"
)

BACKUP_OK=0
BACKUP_FAIL=0

# ── Helper: backup one DB ──────────────────────────────────────────────────
backup_db() {
    local DB_NAME="$1"
    local SRC="$2"
    local DEST_DIR="$BACKUP_ROOT/$DB_NAME"
    mkdir -p "$DEST_DIR"

    if [[ ! -f "$SRC" ]]; then
        log "SKIP $DB_NAME — not found at $SRC"
        return 0
    fi

    local DEST_FILE="$DEST_DIR/${TIMESTAMP}.db"
    log "Backing up $DB_NAME ($SRC) -> $DEST_FILE"

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
        rm -f "$DEST_FILE"
        BACKUP_FAIL=$((BACKUP_FAIL + 1))
        return 1
    fi

    # Row counts
    local ROW_COUNTS
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

    local FILE_SIZE
    FILE_SIZE="$(stat -c%s "$DEST_FILE")"

    # SHA256
    local SHA256
    SHA256="$(sha256sum "$DEST_FILE" | awk '{print $1}')"
    echo "$SHA256  ${TIMESTAMP}.db" > "${DEST_FILE}.sha256"

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
    "row_counts": $ROW_COUNTS,
    "retention_policy": "active: 6h/15min 48h/hourly 7d/daily",
    "durability_note": "Local durability only — off-box backup not configured."
}
with open("${DEST_FILE}.meta.json", "w") as f:
    json.dump(meta, f, indent=2)
print("meta written")
PYEOF

    log "OK $DB_NAME size=${FILE_SIZE}B sha256=${SHA256:0:16}..."
    BACKUP_OK=$((BACKUP_OK + 1))
}

# ── Back up active DBs ─────────────────────────────────────────────────────
for DB_NAME in "${!ACTIVE_DBS[@]}"; do
    backup_db "$DB_NAME" "${ACTIVE_DBS[$DB_NAME]}"
done

# ── Back up archived DBs (one immutable snapshot only) ────────────────────
for DB_NAME in "${!ARCHIVED_DBS[@]}"; do
    DEST_DIR="$BACKUP_ROOT/$DB_NAME"
    # Check if any snapshot already exists
    EXISTING=$(find "$DEST_DIR" -name "*.db" ! -name "*.sha256" ! -name "*.meta.json" 2>/dev/null | wc -l)
    if [[ "$EXISTING" -gt 0 ]]; then
        log "SKIP archived $DB_NAME — immutable snapshot already exists ($EXISTING files)"
        continue
    fi
    log "Creating one-time immutable snapshot for archived DB: $DB_NAME"
    backup_db "$DB_NAME" "${ARCHIVED_DBS[$DB_NAME]}"
done

# ── Retention cleanup ──────────────────────────────────────────────────────
log "Running retention cleanup..."
python3 - <<PYEOF
import os, glob, re
from datetime import datetime, timezone

BACKUP_ROOT = "$BACKUP_ROOT"
NOW = datetime.now(timezone.utc)

# Active DB retention windows
KEEP_15MIN_HOURS = 6        # 15-min backups: keep 6h   (~24 copies)
KEEP_HOURLY_HOURS = 48      # hourly backups: keep 48h  (~48 copies at :00)
KEEP_DAILY_HOURS  = 24 * 7  # daily backups:  keep 7d   (~7 copies at 00:00)

# Archived/static DBs — never delete any snapshot
ARCHIVED_DBS = {
    "observer_lcr_cont_v1", "observer_pfm_cont_v1",
    "observer_pfm_rev_v1", "post_bonding"
}
ACTIVE_DBS = {"solana_trader"}

deleted = 0
kept = 0

for db_dir in glob.glob(f"{BACKUP_ROOT}/*/"):
    db_name = os.path.basename(db_dir.rstrip("/"))

    if db_name in ARCHIVED_DBS:
        # Keep all existing snapshots for archived DBs — never delete
        files = [f for f in glob.glob(f"{db_dir}*.db")
                 if not f.endswith('.sha256') and not f.endswith('.meta.json')]
        kept += len(files)
        continue

    # Active DBs: tiered retention
    files = sorted([f for f in glob.glob(f"{db_dir}*.db")
                    if not f.endswith('.sha256') and not f.endswith('.meta.json')])

    for f in files:
        fname = os.path.basename(f)
        m = re.match(r'^(\d{8}T\d{6}Z)\.db$', fname)
        if not m:
            continue
        try:
            ts = datetime.strptime(m.group(1), '%Y%m%dT%H%M%SZ').replace(tzinfo=timezone.utc)
        except:
            continue
        age_h = (NOW - ts).total_seconds() / 3600

        # Keep all within 6h (covers 15-min tier)
        if age_h <= KEEP_15MIN_HOURS:
            kept += 1
            continue
        # Keep hourly within 48h (files at :00 minutes)
        if age_h <= KEEP_HOURLY_HOURS and ts.minute == 0:
            kept += 1
            continue
        # Keep daily within 7d (files at 00:00 UTC)
        if age_h <= KEEP_DAILY_HOURS and ts.hour == 0 and ts.minute == 0:
            kept += 1
            continue

        # Delete this backup and its sidecars
        for ext in ['', '.sha256', '.meta.json']:
            fp = f + ext
            if os.path.exists(fp):
                os.remove(fp)
        deleted += 1

print(f"Retention cleanup: kept={kept} deleted={deleted}")
PYEOF

log "=== backup_sqlite.sh DONE ok=$BACKUP_OK fail=$BACKUP_FAIL ==="
if [[ $BACKUP_FAIL -gt 0 ]]; then
    exit 1
fi
exit 0
