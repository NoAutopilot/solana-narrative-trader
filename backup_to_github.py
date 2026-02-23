#!/usr/bin/env python3
"""
backup_to_github.py — Back up SQLite database to GitHub
========================================================
Copies the live DB to a tracked backup directory (not in .gitignore),
commits, and pushes. Designed to run:
  1. Manually: python3 backup_to_github.py
  2. Automatically: called before every git push
  3. On a cron: */30 * * * * cd /path/to/repo && python3 backup_to_github.py

The backup is stored as: backups/solana_trader_backup.db
This directory is NOT in .gitignore, so it gets pushed to GitHub.
"""

import os
import sys
import shutil
import sqlite3
import subprocess
import datetime

# Paths
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
DB_SOURCE = os.path.join(REPO_DIR, "data", "solana_trader.db")
BACKUP_DIR = os.path.join(REPO_DIR, "backups")
BACKUP_FILE = os.path.join(BACKUP_DIR, "solana_trader_backup.db")
BACKUP_META = os.path.join(BACKUP_DIR, "backup_info.txt")


def run_cmd(cmd, cwd=None):
    """Run a shell command and return (success, output)."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=cwd or REPO_DIR, timeout=60
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception as e:
        return False, str(e)


def get_db_stats(db_path):
    """Get basic stats from the database."""
    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        stats = {}
        
        c.execute("SELECT COUNT(*) FROM trades WHERE status='open'")
        stats['open_trades'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM trades WHERE status='closed'")
        stats['closed_trades'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM trades")
        stats['total_trades'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM live_trades")
        stats['live_trades'] = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM narratives")
        stats['narratives'] = c.fetchone()[0]
        
        # Get total PnL
        c.execute("SELECT COALESCE(SUM(pnl_sol), 0) FROM trades WHERE status='closed'")
        stats['total_pnl'] = round(c.fetchone()[0], 4)
        
        conn.close()
        return stats
    except Exception as e:
        return {'error': str(e)}


def backup_database():
    """Safely copy the database using SQLite's backup API."""
    if not os.path.exists(DB_SOURCE):
        print(f"ERROR: Source database not found: {DB_SOURCE}")
        return False
    
    # Create backup directory
    os.makedirs(BACKUP_DIR, exist_ok=True)
    
    # Use SQLite's online backup API (safe even if DB is being written to)
    try:
        source = sqlite3.connect(DB_SOURCE)
        dest = sqlite3.connect(BACKUP_FILE)
        source.backup(dest)
        dest.close()
        source.close()
        print(f"Database backed up: {DB_SOURCE} -> {BACKUP_FILE}")
    except Exception as e:
        print(f"SQLite backup failed, falling back to file copy: {e}")
        try:
            shutil.copy2(DB_SOURCE, BACKUP_FILE)
            print(f"File copy backup: {DB_SOURCE} -> {BACKUP_FILE}")
        except Exception as e2:
            print(f"ERROR: Both backup methods failed: {e2}")
            return False
    
    # Write metadata
    stats = get_db_stats(BACKUP_FILE)
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    meta = f"""Backup Timestamp: {now}
Source: {DB_SOURCE}
File Size: {os.path.getsize(BACKUP_FILE)} bytes

Database Stats:
  Total Trades: {stats.get('total_trades', '?')}
  Open Trades: {stats.get('open_trades', '?')}
  Closed Trades: {stats.get('closed_trades', '?')}
  Live Trades: {stats.get('live_trades', '?')}
  Narratives: {stats.get('narratives', '?')}
  Total Paper PnL: {stats.get('total_pnl', '?')} SOL
"""
    with open(BACKUP_META, 'w') as f:
        f.write(meta)
    
    print(f"Backup metadata written to {BACKUP_META}")
    print(meta)
    return True


def push_to_github():
    """Commit and push the backup to GitHub."""
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    
    # Stage backup files
    ok, out = run_cmd("git add backups/")
    if not ok:
        print(f"ERROR: git add failed: {out}")
        return False
    
    # Check if there are changes to commit
    ok, out = run_cmd("git diff --cached --quiet")
    if ok:
        print("No changes to commit — backup is identical to last push.")
        return True
    
    # Commit
    stats = get_db_stats(BACKUP_FILE)
    msg = f"DB backup {now} | {stats.get('total_trades', '?')} trades | PnL: {stats.get('total_pnl', '?')} SOL"
    ok, out = run_cmd(f'git commit -m "{msg}"')
    if not ok:
        print(f"ERROR: git commit failed: {out}")
        return False
    print(f"Committed: {msg}")
    
    # Push
    ok, out = run_cmd("git push origin master")
    if not ok:
        # Try main branch
        ok, out = run_cmd("git push origin main")
        if not ok:
            print(f"ERROR: git push failed: {out}")
            return False
    
    print("Pushed to GitHub successfully.")
    return True


def restore_from_github():
    """Restore the database from the GitHub backup."""
    if not os.path.exists(BACKUP_FILE):
        print("ERROR: No backup file found. Pull from GitHub first:")
        print("  git pull origin master")
        return False
    
    # Create data directory
    os.makedirs(os.path.dirname(DB_SOURCE), exist_ok=True)
    
    # Copy backup to live location
    try:
        shutil.copy2(BACKUP_FILE, DB_SOURCE)
        print(f"Database restored: {BACKUP_FILE} -> {DB_SOURCE}")
        stats = get_db_stats(DB_SOURCE)
        print(f"Restored stats: {stats}")
        return True
    except Exception as e:
        print(f"ERROR: Restore failed: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--restore":
        print("=== Restoring database from GitHub backup ===")
        restore_from_github()
    elif len(sys.argv) > 1 and sys.argv[1] == "--backup-only":
        print("=== Backing up database (no push) ===")
        backup_database()
    else:
        print("=== Backing up database and pushing to GitHub ===")
        if backup_database():
            push_to_github()
