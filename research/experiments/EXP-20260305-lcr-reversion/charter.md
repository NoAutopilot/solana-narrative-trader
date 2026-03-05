# EXP-20260305-lcr-reversion — Preregistered Charter

**Status:** DESIGNED / NOT STARTED
**Date preregistered:** 2026-03-05
**Preceded by:** EXP-20260303-lcr-continuation (PROMOTE — see decision.md when written)

---

## 1. Decision This Experiment Will Inform

Does large-cap-ray (LCR) exhibit a **mean-reversion** effect at the +5m horizon?
Specifically: do tokens with recent negative momentum (r_m5 < 0) recover relative to tokens with recent positive momentum (r_m5 >= 0)?

This experiment is the direct complement to the LCR continuation experiment. If continuation is supported and reversion is also supported, the two effects must be reconciled. If reversion is falsified, continuation is the dominant regime.

---

## 2. Exact Signal / Control Rules

**Signal:**
- `lane = 'large_cap_ray'`
- `r_m5 < 0` (negative 5-minute momentum at fire time)

**Control:**
- Matched from the **same fire** (same `signal_fire_id` / fire window)
- `r_m5 >= 0` (non-negative 5-minute momentum at same fire time)
- All other matching criteria identical to `lcr_continuation_observer_v1` (age bucket, liquidity bucket, vol bucket — closest available match)

**Everything else is unchanged from lcr_continuation_observer_v1:**
- Mode: READ-ONLY observer (no live trades)
- Quote model: same executable quote (Jupiter API, same notional, same slippage_bps)
- Fixed notional: same SOL notional as continuation observer
- Horizons: +1m, +5m, +15m, +30m (primary metric = +5m)
- Matching machinery: same control-matching logic, same dedup rules
- Reports / validity checks: same schema, same row_valid logic, same jitter rules

---

## 3. Primary Metric

**Mean signal-minus-control net markout at +5m**

`delta_5m = signal.fwd_net_fee100_5m - control.fwd_net_fee100_5m`

A positive delta means the negative-momentum token outperformed the positive-momentum token at +5m — i.e., mean reversion is present.

---

## 4. Secondary Metric

**Median delta at +5m**

`median(delta_5m)` across all complete pairs.

Both mean and median must be positive for PROMOTE. If mean is positive but median is negative (or vice versa), result is INCONCLUSIVE pending n >= 50.

---

## 5. Minimum Sample Size

`n_min = 30` complete pairs (both signal and control have `fwd_quote_ok_5m = 1`).

No decision is made before n = 30.

---

## 6. Promotion Threshold

`n_promote = 50` complete pairs.

Promotion requires:
- `n_pairs_complete_5m >= 50`
- `mean_delta_5m > 0`
- `median_delta_5m > 0`
- `CI_95_lower` is not meaningfully negative (> -0.001 as a practical threshold)

---

## 7. Kill Criteria

Kill immediately if **any** of the following:

| Criterion | Threshold |
|---|---|
| n >= 30 AND mean delta <= 0 AND median delta <= 0 | Hard kill |
| +5m quote coverage < 95% | Data quality kill |
| +5m timing validity (jitter ±30s) < 95% | Data quality kill |
| Density < 5 signals/day after 24h of running | Density kill |
| `row_valid = 0` count > 5% of rows | Data integrity kill |

---

## 8. Invariants / Data-Quality Gates

All invariants from `lcr_continuation_observer_v1` apply unchanged:

- `entry_quote_ok = 1` required for both signal and control before a pair is recorded
- `row_valid = 1` required for a pair to count toward n
- `fwd_quote_ts_epoch_5m - fwd_due_epoch_5m` must be within ±30s (jitter gate)
- No synthetic or imputed features in any reported metric
- No mixing of run_ids in any aggregate
- Read-only guard: no `tx_*` fields may be populated

---

## 9. Scope-Lock Placeholders

The following are locked at experiment start and must not change mid-run:

| Parameter | Value (to be filled at start) |
|---|---|
| `run_id` | `[ASSIGNED AT START]` |
| `git_commit` | `[DEPLOYED SHA AT START]` |
| `start_time_utc` | `[TIMESTAMP AT START]` |
| `lane` | `large_cap_ray` |
| `signal_condition` | `r_m5 < 0` |
| `control_condition` | `r_m5 >= 0` |
| `fixed_notional_sol` | `[SAME AS CONTINUATION OBSERVER]` |
| `slippage_bps` | `[SAME AS CONTINUATION OBSERVER]` |
| `horizons` | `+1m, +5m, +15m, +30m` |

**Do NOT start this experiment until:**
- LCR continuation is killed, OR
- Explicit approval from user

---

## 10. Next Steps (when approved to start)

1. Implement `lcr_reversion_observer_v1.py` (copy of v1 with signal/control conditions swapped)
2. Register as `solana-lcr-rev-observer.service`
3. Run canary (2 fires) before declaring live
4. Write `canary_proof.md` to research/experiments/EXP-20260305-lcr-reversion/
5. Update EXPERIMENT_INDEX.md status to RUNNING
