# Benchmark Suite v1

**Generated:** 2026-03-12  
**Status:** FINAL — supersedes all prior per-branch reports  
**Purpose:** Permanent baseline that every future experiment must beat before live deployment.

---

## Overview

This document records the final quantitative results for every completed experimental branch and feature sweep in the Solana Narrative Trader research program. It serves as the canonical reference for what has already been tested and what performance bar a new idea must clear.

The net-proxy formula used throughout is:

> **net_proxy = r_forward_Xm − round_trip_pct**
>
> where `round_trip_pct = impact_buy_pct + impact_sell_pct` (CPAMM-based round-trip cost at fire snapshot time). This is an optimistic lower-bound cost estimate; actual net returns will be lower due to fees, gas, and real slippage.

---

## Part 1 — Live Observer Branches

These branches ran as live observers on the VPS and collected real-time signal/control pairs.

| run_id | Family | Lane | Direction | n | Mean Signal Net +5m | Median Signal Net +5m | Mean Delta +5m | Median Delta +5m | CI (95%) | Final Classification |
|--------|--------|------|-----------|---|--------------------|-----------------------|----------------|------------------|----------|----------------------|
| `0c5337dd` | LCR Continuation | large_cap_ray | continuation | 248 | negative | negative | mildly positive | negative | crosses zero | RANKING FEATURE ONLY / NOT PROMOTABLE |
| `1677a7da` | PFM Continuation | pumpfun_mature | continuation | 212 | negative | negative | mildly positive | negative | crosses zero | RANKING FEATURE ONLY / NOT PROMOTABLE |
| `99ed0fd1` | PFM Reversion | pumpfun_mature | reversion | 208 | ~−0.030 | negative | mildly positive | negative | crosses zero | INCONCLUSIVE / ABANDONED |
| `bb7244cd` | LCR Rank-Lift Sidecar | large_cap_ray | rank-lift | 19 | −0.045 | — | — | — | not computed (n too small) | NON-BINDING / LOW INCREMENTAL VALUE |

**Key finding across all live branches:** Absolute mean net markout at +5m is negative in every branch and lane. Relative deltas are mildly positive in some cases but do not produce positive absolute expected value. No branch cleared the promotion bar.

---

## Part 2 — Retrospective Subgroup Analysis

| run_id | Family | Subgroup | n | Mean Net +5m | Median Net +5m | Mean Delta +5m | CI (95%) | Top-1 Share | Final Classification |
|--------|--------|----------|---|-------------|----------------|----------------|----------|-------------|----------------------|
| — | Age-Conditioned Continuation | PFM old-tercile (age > 53.8h) | 71 | +0.003455 | −0.024952 | +0.021214 | [−0.006, +0.052] | 12.1% | NO-GO — OUTLIER-DRIVEN |

**Key finding:** Positive mean is driven by two tokens (Doom +0.627, BioLLM +0.460). Median is negative. Effect is not systematic.

---

## Part 3 — Feature Tape v1 Family Sweep (+5m, Full Sample)

**Dataset:** 3,774 rows (96 fires, disk-gap rows excluded), 100% label coverage  
**Label source:** universe_snapshot.price_usd  
**Net-proxy:** r_forward_5m − round_trip_pct  
**Round-trip cost (median):** ~0.514%

### Track A — Full-Sample Features (100% coverage)

| Feature | Coverage | Best Bucket Gross Mean | Best Bucket Net Mean | Gross Median | Tercile Diff (Gross) | Tercile Diff (Net) | Outlier Top-1 Share | Recommendation |
|---------|----------|----------------------|---------------------|--------------|---------------------|-------------------|---------------------|----------------|
| median_pool_r_m5 | 100% | +0.566% | +0.051% | 0.000% | +0.910% | +0.909% | 2.6% | CANDIDATE (net barely positive, median zero) |
| breadth_positive_pct | 100% | +0.512% | −0.002% | 0.000% | +0.722% | +0.720% | 2.6% | SKIP |
| jup_vs_cpamm_diff_pct | 100% | +0.168% | −0.341% | 0.000% | +0.153% | +0.124% | 2.6% | SKIP |
| round_trip_pct | 100% | +0.336% | −0.197% | 0.000% | +0.341% | +0.308% | 2.6% | SKIP |
| impact_buy_pct | 100% | +0.348% | −0.197% | 0.000% | +0.348% | +0.315% | 2.6% | SKIP |
| impact_sell_pct | 100% | +0.348% | −0.198% | 0.000% | +0.348% | +0.315% | 2.6% | SKIP |
| pool_dispersion_r_m5 | 100% | +0.136% | −0.378% | 0.000% | +0.013% | +0.012% | 2.6% | SKIP |
| age_hours | 100% | +0.215% | −0.298% | 0.000% | −0.121% | −0.094% | 2.6% | SKIP |
| liquidity_usd | 100% | +0.318% | −0.215% | 0.000% | −0.331% | −0.298% | 2.6% | SKIP |
| vol_h1 | 100% | +0.179% | −0.332% | 0.000% | −0.060% | −0.063% | 2.6% | SKIP |

**Track A verdict:** NO NEW LIVE OBSERVER. Every feature fails the net-proxy gate. Round-trip cost (~0.51%) consumes all gross alpha. Medians are uniformly zero.

### Track B — Micro-Derived Features (Subset-Only, ~70–79% coverage)

> **WARNING:** Track B results reflect non-random missingness. Missing rows = Orca/Meteora micro scope gap (~21–29%). Do NOT generalise to full universe.

| Feature | Coverage | Best Bucket Gross Mean | Best Bucket Net Mean | Gross Median | Net Median | Bootstrap CI (mean net) | Bootstrap CI (median net) | Top-1 Share | Recommendation |
|---------|----------|----------------------|---------------------|--------------|------------|------------------------|--------------------------|-------------|----------------|
| r_m5 | 78.5% | +0.824% | +0.304% | 0.000% | −0.514% | [−0.230%, +0.859%] | [−0.515%, −0.513%] | 3.4% | CANDIDATE (mean net positive, median negative — CI crosses zero) |
| vol_accel_m5_vs_h1 | 78.5% | +0.706% | +0.192% | 0.000% | −0.513% | [−0.209%, +0.627%] | [−0.513%, −0.512%] | 4.5% | CANDIDATE (same pattern) |
| txn_accel_m5_vs_h1 | 78.5% | +0.616% | +0.101% | 0.000% | — | not computed | — | 2.7% | CANDIDATE (thin) |
| liq_change_pct | 78.4% | +0.389% | −0.128% | 0.000% | — | — | — | 2.7% | SKIP |
| avg_trade_usd_m5 | 70.9% | +0.469% | −0.039% | 0.000% | — | — | — | 2.7% | SKIP |
| buy_sell_ratio_m5 | 70.9% | +0.433% | −0.086% | 0.000% | — | — | — | 2.7% | SKIP |
| signed_flow_m5 | 70.9% | +0.433% | −0.086% | 0.000% | — | — | — | 2.7% | SKIP |

**Track B verdict:** NO NEW LIVE OBSERVER. Median net-proxy is −0.514% in the best bucket for all candidates. Effect is mean-driven by tail events. CI crosses zero for all candidates.

---

## Part 4 — Feature Tape v1 Family Sweep (+15m, Winsorized)

**Dataset:** 2,350 rows (p1/p99 winsorized — FURY token +34,070% event excluded from means)  
**Net-proxy:** r_forward_15m − round_trip_pct

| Feature | Track | Best Bucket Net Mean (winsorized) | Net Median | Recommendation |
|---------|-------|----------------------------------|------------|----------------|
| breadth_positive_pct | A | +0.091% | −0.514% | SKIP (median negative) |
| median_pool_r_m5 | A | +0.081% | −0.514% | SKIP (median negative) |
| r_m5 | B | +0.048% | −0.514% | SKIP (median negative) |
| All others | A/B | negative | negative | SKIP |

**+15m verdict:** No feature clears the net-proxy gate at +15m. Medians remain negative throughout.

---

## Part 5 — Feature Tape v1 Family Sweep (+30m, Winsorized)

**Dataset:** 2,193 rows (p1/p99 winsorized)  
**Net-proxy:** r_forward_30m − round_trip_pct

| Feature | Track | Best Bucket Net Mean (winsorized) | Net Median | Recommendation |
|---------|-------|----------------------------------|------------|----------------|
| r_m5 | B | +4.83% | +1.96% | CANDIDATE — but subset-only, momentum-adjacent, CI not computed |
| breadth_positive_pct | A | +0.910% | −0.400% | SKIP (median negative) |
| median_pool_r_m5 | A | +0.893% | −0.464% | SKIP (median negative) |
| All others | A/B | negative or thin | negative | SKIP |

**+30m verdict:** r_m5 at +30m (winsorized) is the only combination with positive mean AND median net-proxy. However it is subset-only (Orca/Meteora excluded), momentum-adjacent (same family as abandoned observer), and CI was not computed due to the extreme outlier distortion. Does not meet the promotion bar.

---

## Summary Decision Table

| Branch / Sweep | Horizon | n | Net Mean (best bucket) | Net Median | CI lo > 0 | Verdict |
|----------------|---------|---|----------------------|------------|-----------|---------|
| LCR Continuation | +5m | 248 | negative | negative | No | SKIP |
| PFM Continuation | +5m | 212 | negative | negative | No | SKIP |
| PFM Reversion | +5m | 208 | negative | negative | No | SKIP |
| LCR Rank-Lift | +5m | 19 | −0.045 | — | No | SKIP |
| Age-Conditioned (retro) | +5m | 71 | +0.003 | −0.025 | No | SKIP |
| Feature Sweep Track A | +5m | 3,774 | +0.051% (best) | 0.000% | No | SKIP |
| Feature Sweep Track B | +5m | 2,964 | +0.304% (best) | −0.514% | No | SKIP |
| Feature Sweep Track A | +15m | 2,350 | +0.091% (best) | −0.514% | No | SKIP |
| Feature Sweep Track B | +15m | 1,694 | +0.048% (best) | −0.514% | No | SKIP |
| Feature Sweep Track A | +30m | 2,193 | +0.910% (best) | −0.464% | No | SKIP |
| Feature Sweep Track B | +30m | 1,694 | +4.83% (best, winsorized) | +1.96% | not computed | CONDITIONAL SKIP |

**Overall conclusion:** The current public-data long-only selection line failed across all tested horizons (+5m, +15m, +30m) and all tested feature families. No branch or feature clears all six promotion gates simultaneously.

---

## Promotion Gates (All Six Must Pass)

A new live observer is approved only if all of the following are satisfied:

1. Mean net-proxy > 0 in best bucket
2. Median net-proxy > 0 in best bucket
3. Bootstrap 95% CI lower bound > 0 for mean net-proxy
4. Top-1 contributor share < 25%
5. Conceptually distinct from abandoned momentum/reversion family
6. Coverage is non-random (not subset-only due to scope gap)

No branch in this suite passes all six gates.


---

## Feature Acquisition v2 — Full-Universe Sweep (Added 2026-03-15)

| run_id | Family | Horizon | N | Mean Net | Median Net | Win Rate | CI | Classification |
|--------|--------|---------|---|----------|------------|----------|----|----------------|
| feature_tape_v2 | feature_acquisition_v2 | +5m | 4,065 | negative | negative | 9-13% | crosses zero | CLOSED |
| feature_tape_v2 | feature_acquisition_v2 | +15m | 4,065 | negative | negative | 9-13% | crosses zero | CLOSED |
| feature_tape_v2 | feature_acquisition_v2 | +30m | 4,065 | negative | negative | 9-13% | crosses zero | CLOSED |
| feature_tape_v2 | feature_acquisition_v2 | +1h | 4,065 | negative | negative | 9-13% | crosses zero | CLOSED |
| feature_tape_v2 | feature_acquisition_v2 | +4h | 4,065 | negative | negative | 9-13% | crosses zero | CLOSED |

42 features tested per horizon (210 total combinations). 0 passed discovery gates. See `feature_tape_v2_FINAL_closure.md` for full details.
