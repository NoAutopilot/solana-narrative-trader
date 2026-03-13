# Provenance Manifest Specification

**Date:** 2026-03-12
**Author:** Manus AI
**Status:** RATIFIED — cold-path documentation

---

## Purpose

Every v2 run, sweep, or report must produce a provenance manifest that records the exact environment, data, and code state at execution time. This ensures full reproducibility and auditability.

---

## Manifest Schema

The manifest is a JSON file named `manifest.json` placed in the output directory of each run.

```json
{
  "manifest_version": "2.0",
  "generated_at": "2026-03-13T21:45:00+00:00",
  "run_type": "holdout_sweep | final_sweep | health_check | collection_session",

  "code": {
    "github_repo": "NoAutopilot/solana-narrative-trader",
    "github_commit": "16014b7...",
    "github_branch": "master",
    "vps_local_commit": "16014b7...",
    "script_path": "scripts/holdout_sweep_v2.py",
    "script_sha256": "abc123..."
  },

  "data": {
    "db_path": "/root/solana_trader/data/solana_trader.db",
    "db_size_bytes": 12345678,
    "table_name": "feature_tape_v2",
    "fire_log_table": "feature_tape_v2_fire_log",
    "n_fires": 96,
    "first_fire_id": "4578ac6b",
    "last_fire_id": "...",
    "first_fire_time": "2026-03-12T21:45:00+00:00",
    "last_fire_time": "2026-03-13T21:30:00+00:00",
    "n_rows_total": 3648,
    "n_rows_eligible": 2736,
    "n_rows_ineligible": 912
  },

  "collection": {
    "service_name": "solana-feature-tape-v2",
    "service_start_time": "2026-03-12T21:34:41+00:00",
    "collection_script": "feature_tape_v2.py",
    "collection_script_sha256": "def456..."
  },

  "analysis": {
    "view": "primary | secondary",
    "horizon": "5m | 15m | 30m | 1h | 4h",
    "features_tested": ["r_m5_micro", "buy_sell_ratio_m5"],
    "discovery_fires": 72,
    "holdout_fires": 24,
    "bonferroni_applied": true,
    "alpha_used": 0.01
  },

  "sample_definition": {
    "filter": "eligible = 1",
    "time_range": "2026-03-12T21:45:00 to 2026-03-13T21:30:00",
    "exclusions": "none",
    "notes": "Full 96-fire collection, no gaps"
  }
}
```

---

## Required Fields by Run Type

| Field | holdout_sweep | final_sweep | health_check | collection_session |
|-------|:---:|:---:|:---:|:---:|
| manifest_version | Y | Y | Y | Y |
| generated_at | Y | Y | Y | Y |
| run_type | Y | Y | Y | Y |
| code.github_commit | Y | Y | Y | Y |
| code.script_sha256 | Y | Y | N | Y |
| data.db_path | Y | Y | Y | Y |
| data.n_fires | Y | Y | Y | N |
| data.n_rows_total | Y | Y | Y | N |
| collection.service_name | N | N | Y | Y |
| analysis.view | Y | Y | N | N |
| analysis.horizon | Y | Y | N | N |
| sample_definition | Y | Y | Y | N |

---

## Script Location

```
scripts/generate_manifest.py
```

The script generates a manifest by inspecting the current environment:

```
python3 scripts/generate_manifest.py \
    --run-type holdout_sweep \
    --db-path /root/solana_trader/data/solana_trader.db \
    --script-path scripts/holdout_sweep_v2.py \
    --output-dir reports/sweeps/v2_5m/
```
