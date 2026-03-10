#!/usr/bin/env bash
# restore_test.sh — Restore drill for all critical DBs
# Takes the latest backup of each critical DB, restores to temp dir,
# runs integrity_check, prints table counts, confirms latest run_id/timestamp.
# Writes: reports/ops/restore_test_latest.md
set -euo pipefail

BACKUP_ROOT="/root/solana_trader/backups/sqlite"
RESTORE_DIR="/tmp/solana_restore_test_$$"
REPORT_DIR="/root/solana_trader/reports/ops"
REPORT_FILE="$REPORT_DIR/restore_test_latest.md"
LOG_FILE="/var/log/solana_trader/restore_test.log"
TIMESTAMP="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

mkdir -p "$RESTORE_DIR" "$REPORT_DIR" "$(dirname "$LOG_FILE")"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }

log "=== restore_test.sh START ==="

python3 - <<PYEOF
import sqlite3, os, glob, json
from datetime import datetime, timezone

BACKUP_ROOT = "$BACKUP_ROOT"
RESTORE_DIR = "$RESTORE_DIR"
REPORT_FILE = "$REPORT_FILE"
TIMESTAMP   = "$TIMESTAMP"

CRITICAL_DBS = [
    "solana_trader",
    "observer_lcr_cont_v1",
    "observer_pfm_cont_v1",
    "observer_pfm_rev_v1",
    "post_bonding",
]

results = []
overall_pass = True

for db_name in CRITICAL_DBS:
    db_dir = os.path.join(BACKUP_ROOT, db_name)
    backups = sorted(glob.glob(f"{db_dir}/*.db"))
    if not backups:
        results.append({
            "db": db_name,
            "status": "FAIL",
            "reason": "No backup found",
            "backup_file": None,
            "integrity": None,
            "row_counts": {},
            "latest_ts": None,
        })
        overall_pass = False
        continue

    latest = backups[-1]
    restore_path = os.path.join(RESTORE_DIR, f"{db_name}_restored.db")

    # Copy backup to restore dir
    import shutil
    shutil.copy2(latest, restore_path)

    # Verify SHA256 if .sha256 exists
    sha256_file = latest + ".sha256"
    sha256_ok = None
    if os.path.exists(sha256_file):
        import hashlib
        h = hashlib.sha256()
        with open(latest, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        computed = h.hexdigest()
        with open(sha256_file) as f:
            expected = f.read().split()[0]
        sha256_ok = (computed == expected)

    # Integrity check
    try:
        con = sqlite3.connect(f"file:{restore_path}?mode=ro", uri=True, timeout=30)
        integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        row_counts = {}
        for t in tables:
            try: row_counts[t] = con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            except: row_counts[t] = -1

        # Get latest timestamp
        latest_ts = None
        for t in tables:
            cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
            for col in ["updated_at_iso","created_at_iso","fire_time_iso","snapshot_at","logged_at"]:
                if col in cols:
                    val = con.execute(f'SELECT MAX("{col}") FROM "{t}"').fetchone()[0]
                    if val and (latest_ts is None or str(val) > str(latest_ts)):
                        latest_ts = str(val)
                    break

        # Get latest run_id for observer tables
        run_ids = {}
        for t in tables:
            cols = [r[1] for r in con.execute(f'PRAGMA table_info("{t}")').fetchall()]
            if "run_id" in cols:
                runs = con.execute(f'SELECT run_id, COUNT(*) as n FROM "{t}" GROUP BY run_id ORDER BY n DESC LIMIT 3').fetchall()
                run_ids[t] = [(r[0], r[1]) for r in runs]
        con.close()

        status = "PASS" if integrity == "ok" else "FAIL"
        if integrity != "ok":
            overall_pass = False

    except Exception as e:
        integrity = f"ERROR: {e}"
        tables = []
        row_counts = {}
        latest_ts = None
        run_ids = {}
        status = "FAIL"
        overall_pass = False

    results.append({
        "db": db_name,
        "status": status,
        "backup_file": os.path.basename(latest),
        "sha256_ok": sha256_ok,
        "integrity": integrity,
        "row_counts": row_counts,
        "latest_ts": latest_ts,
        "run_ids": run_ids,
    })

# Write report
lines = [
    f"# Restore Test Report",
    f"_Run: {TIMESTAMP}_",
    f"_Overall: {'PASS' if overall_pass else 'FAIL'}_",
    "",
    "---",
    "",
]
for r in results:
    lines.append(f"## {r['db']}")
    lines.append(f"- **Status:** {r['status']}")
    lines.append(f"- **Backup file:** {r.get('backup_file', 'N/A')}")
    if r.get('sha256_ok') is not None:
        lines.append(f"- **SHA256 verified:** {'YES' if r['sha256_ok'] else 'NO — MISMATCH'}")
    lines.append(f"- **Integrity check:** {r.get('integrity', 'N/A')}")
    lines.append(f"- **Latest timestamp:** {r.get('latest_ts', 'N/A')}")
    if r.get('row_counts'):
        lines.append("- **Row counts:**")
        for t, n in r['row_counts'].items():
            lines.append(f"  - {t}: {n}")
    if r.get('run_ids'):
        lines.append("- **Run IDs (top 3 by row count):**")
        for t, runs in r['run_ids'].items():
            for run_id, n in runs:
                lines.append(f"  - {t}: {run_id} ({n} rows)")
    lines.append("")

lines.append("---")
lines.append(f"_Restore test {'PASSED' if overall_pass else 'FAILED'} at {TIMESTAMP}_")

os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
with open(REPORT_FILE, "w") as f:
    f.write("\n".join(lines))

print(f"OVERALL: {'PASS' if overall_pass else 'FAIL'}")
print(f"Report: {REPORT_FILE}")
for r in results:
    sha = f" sha256={'OK' if r.get('sha256_ok') else 'NO'}" if r.get('sha256_ok') is not None else ""
    print(f"  {r['db']}: {r['status']}{sha} integrity={r.get('integrity','?')} latest={r.get('latest_ts','?')}")

import sys
sys.exit(0 if overall_pass else 1)
PYEOF

EXIT_CODE=$?
log "=== restore_test.sh DONE exit=$EXIT_CODE ==="
rm -rf "$RESTORE_DIR"
exit $EXIT_CODE
