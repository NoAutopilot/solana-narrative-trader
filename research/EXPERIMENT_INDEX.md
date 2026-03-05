# EXPERIMENT INDEX

Hypothesis matrix order: LCR continuation → LCR reversion → PFM continuation → PFM reversion

| # | ID | Name | Status | run_id | Started | Decided | Result |
|---|---|---|---|---|---|---|---|
| 1 | EXP-20260303-lcr-continuation | LCR Continuation Observer v1 | **PROMOTE** | `70adb2c2` | 2026-03-03 | 2026-03-05 | SUPPORT |
| 2 | EXP-20260305-lcr-reversion | LCR Reversion Observer v1 | **DESIGNED / NOT STARTED** | — | — | — | — |
| 3 | EXP-TBD-pfm-continuation | PFM Continuation Observer v1 | NOT DESIGNED | — | — | — | — |
| 4 | EXP-TBD-pfm-reversion | PFM Reversion Observer v1 | NOT DESIGNED | — | — | — | — |

---

## Rules

- One live/read-only observer at a time unless explicitly approved otherwise.
- No strategy/scanner/gate/dashboard changes unless the task explicitly says so.
- Every result ends in: SUPPORT / FALSIFY / INCONCLUSIVE.
- Every experiment updates this index and the Learnings Ledger.

---

## Active Observers

| Observer | Service | Status |
|---|---|---|
| `lcr_continuation_observer_v1` | `solana-lcr-cont-observer.service` | **RUNNING** (PROMOTE pending next step) |
