# Current State — Solana Narrative Trader

**Last updated:** 2026-03-13
**Phase:** Feature Acquisition v2 — Data Collection

---

## What Is Active Right Now

| Service | Location | Status | Purpose |
|---------|----------|--------|---------|
| `feature_tape_v2.py` | VPS `/root/solana_trader/` | **RUNNING** | Collects 15-min fire snapshots (full-universe) |
| `solana-feature-tape-v2.service` | VPS systemd | **ENABLED** | Keeps collector alive across reboots |
| `feature_tape_v2_autopilot.sh` | VPS (pending pull) | **NOT YET LAUNCHED** | Waits for 96 fires + label maturity, then runs final sweep |

The collector fires every 15 minutes at :00, :15, :30, :45 UTC. It writes to `/root/solana_trader/data/solana_trader.db`, tables `feature_tape_v2` and `feature_tape_v2_fire_log`. No live observer is running. No live trading is active.

---

## What Is Archived

| Item | Location | Status |
|------|----------|--------|
| `feature_tape_v1.py` | repo root | **ARCHIVED** — superseded by v2 |
| Observer `pfm_1677a7da` | VPS (stopped) | **ARCHIVED** — failed, reconciled |
| Momentum sweep v1 (11 features) | `reports/synthesis/` | **CLOSED** — all 11 entered no-go registry |
| Feature tape v1 closure memo | `reports/synthesis/feature_tape_v1_closure_memo.md` | **FINAL** |

---

## What Is Frozen

Nothing is frozen yet. The dataset freeze happens automatically when the autopilot detects 96+ fires and label maturity. The freeze creates:

- `artifacts/feature_tape_v2_frozen_YYYYMMDD_HHMMSS.db`
- `artifacts/feature_tape_v2_frozen_YYYYMMDD_HHMMSS.csv`
- `reports/synthesis/feature_tape_v2_final_manifest.json`

---

## Current Phase

**Phase:** Feature Acquisition v2 — Data Collection

The system is in a passive collection phase. The only active process is the collector. All analysis, sweeps, and decisions are deferred until the autopilot completes. No human action is required during this phase.

**Collection scope:** Full universe (all scanned tokens, eligible and ineligible).
**Analysis scope:** Eligible-only (primary), full-universe (audit only).

---

## Next Automatic Milestone

| Milestone | Trigger | ETA |
|-----------|---------|-----|
| **10-fire health checkpoint** | 10 fires in `feature_tape_v2_fire_log` | ~2h after service start |
| **96-fire completion** | 96 fires collected | ~24h after service start |
| **Label maturity** | Last fire epoch + 4h + 2m buffer | ~28h after service start |
| **Dataset freeze** | Autopilot detects maturity | ~28h after service start |
| **Final sweep** | Immediately after freeze | ~28-30h after service start |
| **Final recommendation** | Sweep completes | `reports/synthesis/feature_family_sweep_v2_final_recommendation.md` |

---

## Next Possible Decisions

The final recommendation will contain exactly one of three verdicts:

| Verdict | Meaning | Next Action |
|---------|---------|-------------|
| **PROCEED** | A candidate family passed all 8 promotion gates and the red-team battery | Launch live observer for that family |
| **PIVOT** | No family passed; large-cap swing study is viable | Execute Stage B of large-cap swing study |
| **STOP** | No viable edge found; program is not viable at current scale | Pause program; design Feature Acquisition v3 or product pivot |

No other decisions are permitted. No observer may be launched before the final recommendation is produced and reviewed.

---

## What Must NOT Change During Collection

- `feature_tape_v2.py` — frozen
- `feature_tape_v2` table schema — frozen
- Label derivation semantics — frozen
- Source table schemas (`universe_snapshot`, `microstructure_log`) — frozen
- No-go registry — frozen (additions only, no removals)
- Benchmark suite v1 — frozen
