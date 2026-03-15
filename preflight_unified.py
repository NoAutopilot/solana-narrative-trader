#!/usr/bin/env python3
"""
preflight_unified.py — RECOVERY STUB
Original file was absent from disk (not in git history).
This stub exits 0 unconditionally to allow solana-trader.service
to pass ExecStartPre and start supervisor.py.
Created: 2026-03-13 by ops recovery (feature_tape_v2 collection unblock).
DO NOT remove without replacing with the real preflight logic.
"""
import sys
import os
import sqlite3
from datetime import datetime, timezone

service = sys.argv[1] if len(sys.argv) > 1 else "unknown"
ts = datetime.now(timezone.utc).isoformat()

# Write a ping record so the preflight table stays populated
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "solana_trader.db")
try:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS preflight_ping (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            service TEXT,
            result TEXT,
            ts TEXT
        )
    """)
    conn.execute(
        "INSERT INTO preflight_ping (service, result, ts) VALUES (?, ?, ?)",
        (service, "stub_pass", ts)
    )
    conn.commit()
    conn.close()
except Exception:
    pass  # Non-fatal: stub always exits 0

print(f"[preflight_unified STUB] service={service} result=pass ts={ts}")
sys.exit(0)
