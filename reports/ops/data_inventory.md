# Data Inventory Report
_Generated: 2026-03-10T15:40Z_

---

## Critical DBs (Protected by Backup System)

| DB Name | Path | Size | Latest Timestamp | Critical | Notes |
|---|---|---|---|---|---|
| solana_trader.db | `/root/solana_trader/data/solana_trader.db` | 127 MB | 2026-03-10T15:34Z | YES | Main trading DB — microstructure_log, universe_snapshot, discovery_log, narratives |
| observer_lcr_cont_v1.db | `/root/solana_trader/data/observer_lcr_cont_v1.db` | 0.68 MB | 2026-03-06T21:15Z | YES | LCR continuation observer — 702 rows, ARCHIVED |
| observer_pfm_cont_v1.db | `/root/solana_trader/data/observer_pfm_cont_v1.db` | 0.39 MB | 2026-03-09T06:20Z | YES | PFM continuation observer — 484 rows, ARCHIVED |
| observer_pfm_rev_v1.db | `/root/solana_trader/data/observer_pfm_rev_v1.db` | 0.19 MB | 2026-03-10T14:16Z | YES | PFM reversion observer — 208 rows, ARCHIVED |
| post_bonding.db | `/root/solana_trader/data/post_bonding.db` | 28 MB | 2026-03-02T23:27Z | YES | Post-bonding price snapshots — 123,247 rows |

---

## Non-Critical / Empty DBs (Not Backed Up)

| DB Name | Path | Size | Notes |
|---|---|---|---|
| microstructure_log.db | `/root/solana_trader/data/microstructure_log.db` | 0 B | Empty stub — not used |
| observer_pfm_continuation_v1.db | `/root/solana_trader/data/observer_pfm_continuation_v1.db` | 0 B | Empty stub |
| trades.db | `/root/solana_trader/data/trades.db` | 0 B | Empty stub |
| et_data.db | `/root/solana_trader/et_data.db` | 0 B | Empty stub |
| et_shadow_v1.db | `/root/solana_trader/et_shadow_v1.db` | 0 B | Empty stub |
| observer_lcr_cont.db | `/root/solana_trader/observer_lcr_cont.db` | 0 B | Empty stub |
| observer_lcr_cont_v1.db (root) | `/root/solana_trader/observer_lcr_cont_v1.db` | 0.01 MB | Preflight pings only (19 rows) — not critical |
| observer_pfm_cont_v1.db (root) | `/root/solana_trader/observer_pfm_cont_v1.db` | 0 B | Empty stub |
| post_bonding.db (root) | `/root/solana_trader/post_bonding/post_bonding.db` | 0 B | Empty stub |
| shadow_trades.db | `/root/solana_trader/shadow_trades.db` | 0 B | Empty stub |
| shadow_trades_v1.db | `/root/solana_trader/shadow_trades_v1.db` | 0 B | Empty stub |
| solana_trader.db (root) | `/root/solana_trader/solana_trader.db` | 0 B | Empty stub |
| trades.db (root) | `/root/solana_trader/trades.db` | 0 B | Empty stub |

---

## Existing Backup (Pre-Existing, Partial)

| DB Name | Path | Size | Latest Timestamp | Notes |
|---|---|---|---|---|
| solana_trader_backup.db | `/root/solana_trader/backups/solana_trader_backup.db` | 123 MB | 2026-03-10T15:00Z | Existing manual backup of solana_trader.db — not structured, no SHA256, no meta |

---

## Canonical Data Root

All critical DBs are under `/root/solana_trader/data/`. No critical DBs found outside this root.
The existing backup at `/root/solana_trader/backups/` is not structured — will be superseded by the new backup system.

---

## Key Row Counts (Critical DBs)

| DB | Table | Rows |
|---|---|---|
| solana_trader.db | microstructure_log | 160,741 |
| solana_trader.db | universe_snapshot | 53,441 |
| solana_trader.db | discovery_log | 1,354 |
| solana_trader.db | narratives | 727 |
| observer_lcr_cont_v1.db | observer_lcr_cont_v1 | 702 |
| observer_lcr_cont_v1.db | observer_fire_log | 418 |
| observer_pfm_cont_v1.db | observer_pfm_cont_v1 | 484 |
| observer_pfm_cont_v1.db | observer_fire_log | 243 |
| observer_pfm_rev_v1.db | observer_pfm_rev_v1 | 208 |
| observer_pfm_rev_v1.db | observer_fire_log | 118 |
| post_bonding.db | price_snapshots | 123,247 |
| post_bonding.db | graduated_tokens | 2,498 |

---

## Disk Usage Summary

| Location | Used | Available |
|---|---|---|
| /root/solana_trader/data/ | ~157 MB (critical DBs) | ~15 GB free on VPS |
| /root/solana_trader/backups/ | ~124 MB (unstructured) | — |
