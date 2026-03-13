#!/usr/bin/env python3
"""
build_status_packet.py — Generate a compact read-only status packet.

Reads the live DB and repo state to produce a single Markdown summary
of current phase, active services, fire count, and next milestone.

Usage:
  python3 scripts/build_status_packet.py \
      --db-path /root/solana_trader/data/solana_trader.db

  python3 scripts/build_status_packet.py --dry-run
"""

import argparse
import json
import logging
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
log = logging.getLogger(__name__)

TARGET_FIRES = 96
LABEL_MATURITY_HOURS = 4.0
LABEL_MATURITY_BUFFER_MINUTES = 2


def _find_project_root() -> str:
    d = Path(__file__).resolve().parent.parent
    if (d / ".git").exists():
        return str(d)
    return str(Path.cwd())


def _git_commit(root: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", root, "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _service_status(service_name: str) -> str:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", service_name],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def _db_stats(db_path: str) -> dict:
    """Read fire count and row stats from the live DB."""
    if not Path(db_path).exists():
        return {"error": f"DB not found: {db_path}"}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

        # Fire count
        cur = conn.execute("""
            SELECT COUNT(DISTINCT fire_id) as fires,
                   COUNT(*) as total_rows,
                   SUM(CASE WHEN eligible=1 THEN 1 ELSE 0 END) as eligible_rows,
                   SUM(CASE WHEN lane IS NULL THEN 1 ELSE 0 END) as null_lanes,
                   SUM(CASE WHEN buys_m5 IS NOT NULL THEN 1 ELSE 0 END) as micro_rows
            FROM feature_tape_v2
        """)
        row = cur.fetchone()
        stats = dict(row) if row else {}

        # Last fire time
        cur = conn.execute("""
            SELECT fire_utc, rows_written
            FROM feature_tape_v2_fire_log
            ORDER BY fire_utc DESC LIMIT 1
        """)
        last_fire = cur.fetchone()
        if last_fire:
            stats["last_fire_utc"] = last_fire["fire_utc"]
            stats["last_fire_rows"] = last_fire["rows_written"]

        # Last fire epoch for label maturity
        cur = conn.execute("""
            SELECT MAX(fire_epoch) as last_epoch
            FROM feature_tape_v2_fire_log
        """)
        epoch_row = cur.fetchone()
        stats["last_fire_epoch"] = epoch_row["last_epoch"] if epoch_row else None

        conn.close()
        return stats
    except sqlite3.OperationalError as e:
        return {"error": str(e)}


def _compute_next_milestone(stats: dict) -> dict:
    """Compute the next automatic milestone."""
    fires = stats.get("fires", 0)
    last_epoch = stats.get("last_fire_epoch")
    now = datetime.now(timezone.utc)
    now_epoch = now.timestamp()

    if fires < TARGET_FIRES:
        fires_remaining = TARGET_FIRES - fires
        # Each fire is 15 minutes
        eta_minutes = fires_remaining * 15
        eta_hours = eta_minutes / 60
        return {
            "milestone": f"96-fire completion ({fires}/{TARGET_FIRES} fires)",
            "eta": f"~{eta_hours:.1f}h ({fires_remaining} fires remaining)",
        }

    if last_epoch:
        maturity_epoch = last_epoch + (LABEL_MATURITY_HOURS * 3600) + (LABEL_MATURITY_BUFFER_MINUTES * 60)
        if now_epoch < maturity_epoch:
            seconds_remaining = maturity_epoch - now_epoch
            eta_minutes = seconds_remaining / 60
            maturity_utc = datetime.fromtimestamp(maturity_epoch, tz=timezone.utc).isoformat()
            return {
                "milestone": "Label maturity (+4h horizon)",
                "eta": f"~{eta_minutes:.0f}m (at {maturity_utc})",
            }
        else:
            return {
                "milestone": "Label maturity REACHED — sweep should be running",
                "eta": "now",
            }

    return {"milestone": "Unknown", "eta": "Unknown"}


def build_packet(db_path: str, dry_run: bool) -> str:
    """Build the status packet as a Markdown string."""
    root = _find_project_root()
    now = datetime.now(timezone.utc).isoformat()
    commit = _git_commit(root)

    lines = [
        "# Status Packet — Solana Narrative Trader",
        f"**Generated:** {now}",
        f"**GitHub commit:** `{commit}`",
        "",
        "---",
        "",
        "## Current Phase",
        "",
        "**Feature Acquisition v2 — Data Collection**",
        "",
        "The system is in passive collection mode. No live observer is running.",
        "No human action is required until the final recommendation is produced.",
        "",
        "---",
        "",
        "## Active Services",
        "",
    ]

    if dry_run:
        lines += [
            "| Service | Status |",
            "|---------|--------|",
            "| `solana-feature-tape-v2.service` | (dry-run — not checked) |",
            "| `feature_tape_v2_autopilot.sh` | (dry-run — not checked) |",
            "",
        ]
    else:
        collector_status = _service_status("solana-feature-tape-v2.service")
        lines += [
            "| Service | Status |",
            "|---------|--------|",
            f"| `solana-feature-tape-v2.service` | `{collector_status}` |",
            "| No live observer | — |",
            "",
        ]

    lines += [
        "---",
        "",
        "## Collection Stats",
        "",
    ]

    if dry_run:
        lines += [
            "| Metric | Value |",
            "|--------|-------|",
            "| fires | (dry-run) |",
            "| total_rows | (dry-run) |",
            "| eligible_rows | (dry-run) |",
            "| null_lanes | (dry-run) |",
            "| micro_rows | (dry-run) |",
            "| last_fire_utc | (dry-run) |",
            "",
        ]
    else:
        stats = _db_stats(db_path)
        if "error" in stats:
            lines += [f"**Error reading DB:** {stats['error']}", ""]
        else:
            fires = stats.get("fires", 0)
            total = stats.get("total_rows", 0)
            eligible = stats.get("eligible_rows", 0)
            null_lanes = stats.get("null_lanes", 0)
            micro = stats.get("micro_rows", 0)
            last_fire = stats.get("last_fire_utc", "—")
            last_rows = stats.get("last_fire_rows", "—")

            pct_eligible = f"{100*eligible/total:.0f}%" if total > 0 else "—"
            pct_micro = f"{100*micro/eligible:.0f}%" if eligible > 0 else "—"

            lines += [
                "| Metric | Value |",
                "|--------|-------|",
                f"| fires | {fires} / {TARGET_FIRES} |",
                f"| total_rows | {total:,} |",
                f"| eligible_rows | {eligible:,} ({pct_eligible}) |",
                f"| null_lanes | {null_lanes} {'✓' if null_lanes == 0 else '✗ FAIL'} |",
                f"| micro_rows | {micro:,} ({pct_micro} of eligible) |",
                f"| last_fire_utc | {last_fire} |",
                f"| last_fire_rows | {last_rows} |",
                "",
            ]

            milestone = _compute_next_milestone(stats)
            lines += [
                "---",
                "",
                "## Next Milestone",
                "",
                f"**{milestone['milestone']}**",
                f"ETA: {milestone['eta']}",
                "",
            ]

    lines += [
        "---",
        "",
        "## Key File Paths",
        "",
        "| File | Purpose |",
        "|------|---------|",
        "| `reports/research/CURRENT_STATE.md` | Authoritative current state |",
        "| `reports/research/OPERATOR_RUNBOOK_v1.md` | Step-by-step procedures |",
        "| `reports/research/DECISION_TREE_v1.md` | All outcomes and allowed moves |",
        "| `reports/research/ARTIFACT_MAP_v1.md` | Every file mapped to purpose |",
        "| `reports/research/COMMAND_INDEX_v1.md` | Exact one-liner commands |",
        "| `reports/synthesis/feature_family_sweep_v2_final_recommendation.md` | **Final recommendation** (generated by autopilot) |",
        "",
        "---",
        "",
        "## What NOT to Touch",
        "",
        "- `feature_tape_v2.py` — frozen",
        "- `feature_tape_v2` table schema — frozen",
        "- Label derivation semantics — frozen",
        "- No live observer — none approved",
        "",
    ]

    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description="Build Status Packet")
    parser.add_argument("--db-path", default="/root/solana_trader/data/solana_trader.db",
                        help="Path to SQLite DB")
    parser.add_argument("--output", default=None,
                        help="Output file path (default: print to stdout)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Skip DB and service checks")
    args = parser.parse_args()

    packet = build_packet(args.db_path, args.dry_run)

    if args.output:
        Path(args.output).write_text(packet)
        log.info("Status packet written to: %s", args.output)
    else:
        print(packet)


if __name__ == "__main__":
    main()
