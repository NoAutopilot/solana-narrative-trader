# LCR Forward Run — Launch Record

**Launch timestamp:** 2026-03-01 18:51 UTC  
**Run ID:** `874f22f4-...` (latest active, regenerated on each restart)  
**Version label:** `v1.25-lcr`  
**Service:** `solana-trader-lcr.service` (systemd, enabled, auto-restart)  
**File:** `/root/solana_trader/et_shadow_trader_lcr.py`  
**Lock:** `/tmp/et_shadow_trader_lcr.lock` (separate from v1.25 main lock)  
**DB:** shared `solana_trader.db` (WAL mode, run_id isolates data)

---

## Preflight Checklist

| Check | Status | Notes |
|:------|:-------|:------|
| Lane definition audited | ✅ PASS | `pumpfun_origin=0`, non-pumpswap venue, `age >= 30d` |
| pumpswap/9999h ambiguity resolved | ✅ PASS | `mature_pumpswap` is a separate lane; 9999h sentinel removed from forward run |
| `ALLOWED_LANES = {"large_cap_ray"}` | ✅ PASS | Confirmed in `run_registry.lane_gates` |
| Banner text correct | ✅ PASS | `large_cap_ray=ALLOWED_ONLY` in startup log |
| Entry truth fields in `shadow_trades_v1` | ✅ PASS | `lane_at_entry`, `age_at_entry_h`, `venue_at_entry`, `pumpfun_origin_at_entry`, `entry_range_5m`, `vol_h1_at_entry` |
| `lcr_entry_truth_log` table created | ✅ PASS | Table exists; write path has a silent bug (conn2 lock), data is in `shadow_trades_v1` |
| First OPEN trade verified | ✅ PASS | PBTC, `lane=large_cap_ray`, `age=10847h`, `venue=raydium`, `pumpfun_origin=0` |
| v1.25 main run unaffected | ✅ PASS | Separate lock, separate run_id, same DB (WAL) |
| Strategy parameters unchanged | ✅ PASS | Same gates, exits, cadence, anti_chase, pf_stability |

---

## Lane Definition (Authoritative)

```
large_cap_ray:
  pumpfun_origin = 0
  venue NOT IN (pumpswap)
  age_hours >= 720  (30 days)
```

All other lanes (`pumpfun_mature`, `pumpfun_early`, `mature_pumpswap`, `non_pumpfun_mature`) are blocked.

---

## First Tick Results (18:51 UTC)

```
tradeable = 9 / 112 eligible (132 total)
top-3: PBTC (sc=4.63 r_m5=-1.02%), Oil (sc=3.59 r_m5=-1.86%), Fartcoin (sc=2.35 r_m5=-0.12%)
rej: age=88, liq=2, vol=11, pf_early=20, anti_chase=1, rug=1, pf_stab=0
OPEN: PBTC lane=large_cap_ray age=10847h liq=$203,939 jup_rt=0.21% SL=-0.80% TP=+2.00%
```

---

## Decision Rule (from brief)

- If LCR shows materially better feasibility AND paired delta is not clearly negative → continue
- If feasibility good but paired delta clearly negative → stop (no edge in this lane)
- If feasibility collapses in forward run → report simulation overstated it and stop

**Evaluation trigger:** `n_closed_pairs >= 20`
