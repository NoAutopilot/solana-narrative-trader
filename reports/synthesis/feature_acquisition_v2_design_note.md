# Feature Acquisition v2 — Design Note

**Date:** 2026-03-12  
**Status:** DESIGN ONLY — no implementation until Path B is selected  
**Author:** Manus AI

---

## Purpose

This document defines the candidate feature families, source tables and APIs, no-lookahead capture rules, coverage risks, storage implications, and promotion bar for a potential Feature Acquisition v2 effort. Nothing in this document is implemented until Path B is explicitly selected.

---

## Why a New Family Is Required

The `feature_tape_v1` sweep tested 17 features across three horizons and found no deployable edge. The binding constraints were: (1) round-trip transaction costs (~0.51%) consuming all gross alpha at short horizons; (2) right-skewed return distributions where means are outlier-driven and medians are zero or negative; and (3) non-random missingness in the micro-derived subset. A new family must address at least one of these constraints structurally — not by tuning thresholds on the same features.

---

## Candidate Family 1 — Trade-by-Trade Order Flow / Urgency

### Hypothesis

Individual trade urgency (measured by trade size relative to pool depth, inter-trade arrival time, and buy/sell sequencing at the sub-minute level) predicts short-horizon price direction better than aggregated 5-minute flow metrics.

### Distinction from Tested Features

`buy_sell_ratio_m5`, `signed_flow_m5`, and `txn_accel_m5_vs_h1` in `feature_tape_v1` are all 5-minute aggregates. This family operates at the individual trade level and captures sequencing effects (e.g., accelerating buy sequences, large-trade clustering) that are lost in aggregation.

### Candidate Features

| Feature | Definition | No-Lookahead Rule |
|---------|-----------|-------------------|
| `urgency_score` | Trade size / pool depth at trade time, averaged over last N trades | Computed from trades with `block_time <= fire_epoch` only |
| `inter_trade_accel` | Change in inter-trade arrival time over last 30 trades vs prior 30 | Same — strictly pre-fire |
| `buy_sequence_len` | Length of current unbroken buy sequence at fire time | Strictly pre-fire |
| `large_trade_share_5m` | Fraction of 5m volume from trades > $500 | Strictly pre-fire |
| `vwap_deviation` | Last trade price vs 5m VWAP | Strictly pre-fire |

### Source Tables / APIs

- **Primary:** Solana RPC `getSignaturesForAddress` + `getTransaction` for each pool address at fire time
- **Alternative:** Helius enhanced transactions API (structured DEX trade events)
- **Fallback:** `microstructure_log` if trade-level data is unavailable for a pool

### Coverage Risks

- Solana RPC rate limits may restrict per-fire trade history depth
- Helius API requires a paid plan for high-throughput access
- Pool type coverage gap (Orca/Meteora) persists unless Helius covers those pools
- Expected coverage: ~60–75% of candidate universe (similar to current micro gap)

### Storage Implications

- ~50 rows per fire × 96 fires = ~4,800 rows per collection run
- Each row: ~20 columns × 8 bytes = ~160 bytes → ~768 KB per run (negligible)
- Trade-level raw data (if stored): ~500 trades/fire × 200 bytes = ~10 MB/fire → ~960 MB for 96 fires (store compressed or discard after feature extraction)

---

## Candidate Family 2 — Route / Quote Quality

### Hypothesis

The quality of the best available execution route at fire time (multi-hop depth, quote freshness, cross-venue spread) predicts whether a candidate token can be entered and exited at a cost that makes the trade viable.

### Distinction from Tested Features

`jup_vs_cpamm_diff_pct`, `round_trip_pct`, `impact_buy_pct`, and `impact_sell_pct` were tested in `feature_tape_v1` and failed. The new family extends this by capturing route *depth* (how much size can be traded before slippage exceeds threshold), quote *freshness* (staleness of the best available quote), and *cross-venue spread* (difference between Jupiter best route and direct pool price across multiple size tiers).

### Candidate Features

| Feature | Definition | No-Lookahead Rule |
|---------|-----------|-------------------|
| `route_depth_100` | Max USDC size tradeable with < 1% slippage | Computed at fire time via Jupiter quote API |
| `route_depth_500` | Max USDC size tradeable with < 5% slippage | Same |
| `quote_freshness_s` | Age of best quote at fire time (seconds) | Strictly pre-fire |
| `cross_venue_spread_pct` | Jupiter best route vs direct pool price | Computed at fire time |
| `multi_hop_flag` | Whether best route requires > 1 hop | Computed at fire time |

### Source Tables / APIs

- **Primary:** Jupiter Quote API v6 (`/quote` endpoint, multiple size tiers)
- **Fallback:** CPAMM price formula from `universe_snapshot`

### Coverage Risks

- Jupiter API covers most Solana DEX pools but may miss very new or low-liquidity pools
- Quote freshness depends on Jupiter cache TTL (typically 1–3 seconds)
- Expected coverage: ~85–90% of candidate universe (better than micro)

### Storage Implications

- ~5 API calls per candidate per fire (5 size tiers) × 40 candidates × 96 fires = ~19,200 API calls per run
- Storage: ~40 rows × 10 columns × 8 bytes × 96 fires = ~307 KB (negligible)

---

## Candidate Family 3 — Market-State Gating

### Hypothesis

A market-state gate (overall Solana DEX volume trend, SOL price trend, network congestion) determines whether any selection signal is valid. In low-volume or high-congestion regimes, no selection signal is deployable regardless of feature values.

### Distinction from Tested Features

This is not a selection feature — it is a validity gate applied on top of any selection signal. It was not tested in `feature_tape_v1` because no selection signal survived to the gating stage.

### Candidate Gate Variables

| Variable | Definition | Source |
|---------|-----------|--------|
| `sol_price_trend_1h` | SOL/USDC 1h return at fire time | `universe_snapshot` (SOL mint) |
| `dex_vol_trend_1h` | Total Solana DEX volume 1h change | Birdeye or Helius aggregate API |
| `network_tps` | Solana network TPS at fire time | Solana RPC `getRecentPerformanceSamples` |
| `mempool_congestion` | Estimated priority fee at fire time | Solana RPC `getRecentPrioritizationFees` |

### Coverage Risks

- SOL price is already in `universe_snapshot` (zero additional cost)
- DEX volume aggregate requires a third-party API (Birdeye, DeFiLlama)
- Network TPS and priority fees are available via public RPC (no additional cost)
- Expected coverage: 100% (market-state variables are global, not per-mint)

### Storage Implications

- ~4 variables per fire × 96 fires = ~384 rows (negligible)

---

## Promotion Bar for Any New Family

A new live observer is approved only if the retrospective sweep on the new feature family shows **all** of the following:

1. Positive net-proxy mean (winsorized at p1/p99)
2. Non-negative net-proxy median (winsorized at p1/p99)
3. Bootstrap 95% CI lower bound > 0 (10,000 resamples)
4. Top-1 contributor share < 0.30
5. Coverage ≥ 70% of candidate universe, or explicitly bounded subset with documented non-random missingness and a coverage-expansion plan
6. Conceptually distinct from the momentum/direction family (r_m5, buy_sell_ratio, signed_flow, txn_accel, vol_accel, age_hours, continuation, reversion)

If no feature in the new family passes all six gates, the program moves to Path A (stop).

---

## What Is Not In Scope for v2

- No continuation, reversion, age-conditioned, or rank-lift variant of `feature_tape_v1` features
- No live observer launch before all six gates pass
- No dashboard redesign
- No strategy changes to existing live observers
- No new observer from the momentum/direction family under any framing
