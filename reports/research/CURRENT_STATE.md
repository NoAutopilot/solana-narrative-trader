# Current State — Solana Narrative Trader

**Last updated:** 2026-03-15
**Phase:** Program Closed — Awaiting Decision

---

## What Is Running

Nothing. All services related to Feature Acquisition v2 have been stopped.

| Service | Status | Since |
|---------|--------|-------|
| `solana-feature-tape-v2.service` | STOPPED | 2026-03-14T15:00Z |
| `solana-trader.service` (supervisor) | RUNNING | 2026-03-13T18:43Z |
| `solana-backup-sqlite.timer` | ACTIVE | continuous |
| `solana-restore-test.timer` | ACTIVE | continuous |

The upstream scanner (`et_universe_scanner.py`) and supervisor continue running because they serve other purposes. The feature tape collector is the only component that was stopped.

---

## What Is Archived

| Item | Location | Status |
|------|----------|--------|
| `feature_tape_v1.py` | repo root | **ARCHIVED** — superseded by v2 |
| Observer `pfm_1677a7da` | VPS (stopped) | **ARCHIVED** — failed, reconciled |
| Momentum sweep v1 (11 features) | `reports/synthesis/` | **CLOSED** — all 11 entered no-go registry |
| Feature tape v1 closure memo | `reports/synthesis/feature_tape_v1_closure_memo.md` | **FINAL** |
| Feature tape v2 closure memo | `reports/synthesis/feature_tape_v2_FINAL_closure.md` | **FINAL** |
| Feature tape v2 final recommendation | `reports/synthesis/feature_family_sweep_v2_final_recommendation.md` | **FINAL** |

---

## What Is Frozen

| Artifact | Path |
|----------|------|
| Frozen 96-fire DB | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.db` |
| Frozen 96-fire CSV | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.csv` |
| Manifest | `reports/synthesis/feature_tape_v2_final_manifest.json` |

---

## Current Phase

**Program Closed — Awaiting Decision**

All three research lines have been exhausted:

| Line | Experiments | Verdict |
|------|------------|---------|
| Momentum / Direction | 001-007 | No viable signal |
| Public-Data Long-Only (v1) | 008 | No viable signal |
| Feature Acquisition v2 | 009 | No viable signal |

The public on-chain feature space (universe_snapshot + microstructure_log) does not contain a signal strong enough to overcome round-trip costs in a long-only token selection framework on Solana memecoins.

---

## Allowed Next Moves

See `reports/synthesis/post_v2_options.md` for the three allowed options:

| Option | Description |
|--------|-------------|
| A | Stop the program entirely |
| B | Start a new program around wallet/deployer/"who" data |
| C | Start a new program around large-cap swing / different market |

No re-runs of existing features are permitted. No live observer may be launched from the current feature space. The no-go registry (NG-001 through NG-006) is authoritative.

---

## What Must NOT Change

The no-go registry is append-only. No entries may be removed. No feature from the current public on-chain feature space may be re-tested without a fundamentally new data source or market structure.
