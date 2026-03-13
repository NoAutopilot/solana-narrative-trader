#!/usr/bin/env python3
"""
generate_manifest.py — Generate a provenance manifest for any v2 run.
Cold-path infra only. Does NOT modify any live collection or DB.

Usage:
  python3 scripts/generate_manifest.py \
      --run-type holdout_sweep \
      --db-path /root/solana_trader/data/solana_trader.db \
      --script-path scripts/holdout_sweep_v2.py \
      --output-dir reports/sweeps/v2_5m/

  python3 scripts/generate_manifest.py \
      --run-type health_check \
      --db-path /root/solana_trader/data/solana_trader.db \
      --output-dir reports/health/
"""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256_file(path):
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_info(repo_dir=None):
    """Get current git commit and branch."""
    cwd = repo_dir or os.getcwd()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        commit = "UNKNOWN"
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        branch = "UNKNOWN"
    return commit, branch


def vps_git_commit(db_path):
    """Try to get VPS local git commit from the repo containing the DB."""
    repo_dir = Path(db_path).parent.parent
    return git_info(str(repo_dir))


def db_stats(db_path):
    """Get basic stats from the feature_tape_v2 tables."""
    stats = {}
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # Row counts
        cur.execute("SELECT COUNT(*) FROM feature_tape_v2")
        stats["n_rows_total"] = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM feature_tape_v2 WHERE eligible = 1")
        stats["n_rows_eligible"] = cur.fetchone()[0]

        stats["n_rows_ineligible"] = stats["n_rows_total"] - stats["n_rows_eligible"]

        # Fire counts
        cur.execute("SELECT COUNT(DISTINCT fire_id) FROM feature_tape_v2")
        stats["n_fires"] = cur.fetchone()[0]

        # First/last fire
        cur.execute("""
            SELECT fire_id, fire_time_utc FROM feature_tape_v2_fire_log
            ORDER BY fire_time_epoch ASC LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            stats["first_fire_id"] = row[0]
            stats["first_fire_time"] = row[1]

        cur.execute("""
            SELECT fire_id, fire_time_utc FROM feature_tape_v2_fire_log
            ORDER BY fire_time_epoch DESC LIMIT 1
        """)
        row = cur.fetchone()
        if row:
            stats["last_fire_id"] = row[0]
            stats["last_fire_time"] = row[1]

        conn.close()
    except Exception as e:
        stats["error"] = str(e)

    # DB file size
    try:
        stats["db_size_bytes"] = os.path.getsize(db_path)
    except Exception:
        stats["db_size_bytes"] = None

    return stats


def generate_manifest(args):
    """Generate the provenance manifest."""
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat()

    # Git info (local sandbox)
    repo_dir = Path(__file__).parent.parent
    commit, branch = git_info(str(repo_dir))

    # Code section
    code = {
        "github_repo": "NoAutopilot/solana-narrative-trader",
        "github_commit": commit,
        "github_branch": branch,
    }

    if args.script_path:
        script_path = Path(args.script_path)
        if script_path.exists():
            code["script_path"] = str(script_path)
            code["script_sha256"] = sha256_file(script_path)
        else:
            # Try relative to repo
            full_path = repo_dir / script_path
            if full_path.exists():
                code["script_path"] = str(script_path)
                code["script_sha256"] = sha256_file(full_path)

    # Data section
    data = {"db_path": args.db_path, "table_name": "feature_tape_v2", "fire_log_table": "feature_tape_v2_fire_log"}
    if os.path.exists(args.db_path):
        data.update(db_stats(args.db_path))
    else:
        data["note"] = "DB not accessible from this environment (expected if running on sandbox, not VPS)"

    # Collection section
    collection = {
        "service_name": "solana-feature-tape-v2",
        "collection_script": "feature_tape_v2.py",
    }
    collection_script = repo_dir / "feature_tape_v2.py"
    if collection_script.exists():
        collection["collection_script_sha256"] = sha256_file(collection_script)

    # Analysis section (populated from args or left empty)
    analysis = {}
    if args.view:
        analysis["view"] = args.view
    if args.horizon:
        analysis["horizon"] = args.horizon
    if args.features:
        analysis["features_tested"] = args.features.split(",")

    # Sample definition
    sample = {
        "filter": "eligible = 1" if args.view == "primary" else "none (full universe)",
    }
    if data.get("first_fire_time") and data.get("last_fire_time"):
        sample["time_range"] = f"{data['first_fire_time']} to {data['last_fire_time']}"
    sample["exclusions"] = "none"

    # Assemble manifest
    manifest = {
        "manifest_version": "2.0",
        "generated_at": now,
        "run_type": args.run_type,
        "code": code,
        "data": data,
        "collection": collection,
        "analysis": analysis,
        "sample_definition": sample,
    }

    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, default=str)

    print(f"Manifest written to {manifest_path}")
    print(f"  Run type:    {args.run_type}")
    print(f"  Git commit:  {commit[:12]}")
    print(f"  DB path:     {args.db_path}")
    if data.get("n_fires"):
        print(f"  Fires:       {data['n_fires']}")
        print(f"  Rows:        {data['n_rows_total']} total, {data['n_rows_eligible']} eligible")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Provenance Manifest")
    parser.add_argument("--run-type", required=True,
                        choices=["holdout_sweep", "final_sweep", "health_check", "collection_session"],
                        help="Type of run")
    parser.add_argument("--db-path", default="/root/solana_trader/data/solana_trader.db",
                        help="Path to SQLite database")
    parser.add_argument("--script-path", default=None,
                        help="Path to the script being run")
    parser.add_argument("--output-dir", required=True,
                        help="Output directory for manifest")
    parser.add_argument("--view", default="primary", choices=["primary", "secondary"],
                        help="Analysis view")
    parser.add_argument("--horizon", default=None,
                        help="Forward return horizon")
    parser.add_argument("--features", default=None,
                        help="Comma-separated feature list")
    args = parser.parse_args()
    generate_manifest(args)
