# EXPERIMENT INDEX

Hypothesis matrix order: LCR continuation → LCR reversion → PFM continuation → PFM reversion

| # | ID | Name | Status | run_id | Started | Decided | Result |
|---|---|---|---|---|---|---|---|
| 1 | EXP-20260303-lcr-continuation | LCR Continuation Observer v1 (initial) | **SUPPORTIVE / REPLICATION REQUIRED** | `70adb2c2` | 2026-03-03 | 2026-03-05 | SUPPORTIVE |
| 2 | EXP-20260305-lcr-continuation-conf | LCR Continuation Observer v1 (confirmatory) | **RUNNING** | `3d83189b` | 2026-03-05 | — | — |
| 3 | EXP-20260305-lcr-reversion | LCR Reversion Observer v1 | **DESIGNED / NOT STARTED** | — | — | — | — |
| 4 | EXP-TBD-pfm-continuation | PFM Continuation Observer v1 | NOT DESIGNED | — | — | — | — |
| 5 | EXP-TBD-pfm-reversion | PFM Reversion Observer v1 | NOT DESIGNED | — | — | — | — |

---

## Rules

- One live/read-only observer at a time unless explicitly approved otherwise.
- No strategy/scanner/gate/dashboard changes unless the task explicitly says so.
- Every result ends in: SUPPORT / FALSIFY / INCONCLUSIVE.
- Every experiment updates this index and the Learnings Ledger.

---

## Active Observers

| Observer | Service | Status | run_id |
|---|---|---|---|
| `lcr_continuation_observer_v1` (confirmatory) | `solana-lcr-cont-observer.service` | **RUNNING** | `3d83189b-68b1-429f-bbd9-2be4a36e71c3` |
