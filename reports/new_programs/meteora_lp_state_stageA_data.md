# Meteora LP State Study — Stage A Data Document

**Program:** meteora_lp_state_stageA  
**Date:** 2026-03-15  
**Status:** Stage A Complete  
**Author:** Manus AI  

---

## 1. Data Sources

This study uses two public, unauthenticated APIs.

| Source | Endpoint | Data Type | Availability |
|--------|----------|-----------|-------------|
| Meteora DLMM API | `dlmm-api.meteora.ag/pair/all` | Current pool state: fees, volume, TVL, fee/TVL ratio by window, base/max fee percentage | Free, no auth, returns 137,899 pools |
| GeckoTerminal API | `api.geckoterminal.com/api/v2/networks/solana/pools/{address}/ohlcv/hour` | Historical hourly OHLCV (up to 500 bars, ~20 days) per pool | Free, no auth, rate-limited |

**Blocked / Unavailable:** Historical fee time series (fee earned per hour per pool) is not available from any public source. Exact LP PnL requires position-level on-chain data (Helius/Bitquery paid API). This study uses clearly-labeled proxies throughout.

---

## 2. Universe Construction

The Meteora DLMM API returned 137,899 pools as of 2026-03-15. After applying universe filters:

| Filter | Criterion | Pools Remaining |
|--------|-----------|----------------|
| Raw pool list | All DLMM pools | 137,899 |
| Not blacklisted / not hidden | `is_blacklisted = false`, `hide = false` | ~130,000 |
| SOL as quote token | `mint_x` or `mint_y` = SOL mint | ~45,000 |
| Active (fees_24h > $50) | `fees_24h > 50` | ~2,800 |
| Non-trivial TVL | `liquidity > $5,000` | ~1,200 |

The top 60 pools by `fees_24h` were selected for OHLCV fetching. Of these, 15 had GeckoTerminal OHLCV data available; 45 returned 404 (pool address not indexed by GeckoTerminal, typically very new or low-activity pools).

---

## 3. Pool Coverage

| Pool Name | Type | Bars | Days | Base Fee | fee_tvl_h1 |
|-----------|------|------|------|----------|------------|
| SOL-USDC (pool 1) | standard | 500 | 20.8 | 0.01% | 0.83% |
| PUMP-SOL | standard | 500 | 20.8 | 0.04% | 0.00% |
| SOL-USDC (pool 2) | standard | 500 | 20.8 | 0.01% | 0.45% |
| BP-SOL | standard | 500 | 20.9 | 0.04% | 1.60% |
| PENGUIN-SOL | elevated | 500 | 26.1 | 1.00% | 2.33% |
| JUP-SOL | standard | 500 | 22.0 | 0.04% | 0.24% |
| Jellybean-SOL | elevated | 386 | 16.0 | 1.00% | 15.03% |
| 我的刀盾-SOL | launch | 295 | 12.2 | 2.00% | 1.82% |
| SOS-SOL | launch | 133 | 5.5 | 2.00% | 52.52% |
| Life-SOL | elevated | 105 | 4.6 | 1.00% | 14.19% |
| SMITH-SOL | elevated | 37 | 1.5 | 1.00% | 66.97% |
| Memehouse-SOL (pool 1) | elevated | 24 | 1.0 | 1.00% | 96.92% |
| Memehouse-SOL (pool 2) | elevated | 24 | 1.0 | 1.00% | 80.12% |
| Rosie-SOL (pool 1) | elevated | 12 | 0.5 | 1.00% | 53.95% |
| Rosie-SOL (pool 2) | standard | 12 | 0.5 | 0.04% | 88.18% |

**Pool type classification:**
- **Standard:** `base_fee < 1%`
- **Elevated:** `1% ≤ base_fee < 2%`
- **Launch:** `base_fee ≥ 2%` AND `max_fee ≥ 5%`

---

## 4. Event Counts

| Hypothesis | Condition | Events |
|------------|-----------|--------|
| H1 elevated | fee_tvl_h1 ≥ 0.01 | 1,984 |
| H1 null | All events | 3,968 |
| H2 toxic | \|ret_1h\| > 5% | 844 |
| H2 non-toxic | \|ret_1h\| ≤ 5% | 3,124 |
| H3 launch | base_fee ≥ 2%, max_fee ≥ 5% | 420 |
| H3 standard | All non-launch | 3,548 |

Total unique hourly bar events: **3,968** across 15 pools.

---

## 5. LP Proxy Construction

The LP proxy is a simulation under simplifying assumptions. It is **not** exact LP PnL.

**Fee proxy (per deployment):**
```
fee_proxy = (base_fee_pct / 100) × vol_usd_per_bar / tvl_usd × n_bars
```

**Impermanent loss proxy:**
```
il_proxy = 0.5 × (price_return_over_horizon)²
```
Capped at 50% for extreme moves. This is the standard second-order approximation for IL in a constant-product AMM, applied as a conservative proxy for DLMM concentrated liquidity positions.

**Operational friction:** 0.06% per deployment (entry + exit slippage, gas).

**Net LP proxy:**
```
net_lp_proxy = fee_proxy - il_proxy - 0.0006
```

**+15m horizon:** Approximated as 25% of the +1h price move (linear interpolation), since only hourly bars are available.

**Known limitations:**
1. Fee proxy uses base fee only, not dynamic fee (conservative lower bound).
2. IL proxy uses constant-product AMM formula, not DLMM concentrated liquidity IL (which can be higher or lower depending on bin range).
3. +15m is an interpolation, not a direct observation.
4. TVL is current-state, not historical (TVL at event time is unknown).
5. Only 15 of 60 candidate pools had GeckoTerminal OHLCV data.

---

## 6. Data Quality Notes

The 45 pools without OHLCV data are predominantly very new or low-liquidity pools that GeckoTerminal has not indexed. The 15 pools with data skew toward more established, higher-volume pools. This creates a mild survivorship bias: the working sample is more liquid and longer-lived than the full universe. Results should be interpreted in the context of this bias.

---

*End of Data Document*
