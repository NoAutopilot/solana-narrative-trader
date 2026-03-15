# Meteora LP State Study — Stage A Design Document

**Program:** meteora_lp_state_stageA  
**Date:** 2026-03-15  
**Status:** Stage A — Feasibility and Event Study  
**Author:** Manus AI  

---

## 1. Program Scope

This is a clean, adversarial event-study on Meteora DLMM pool LP economics. It is structurally distinct from all prior closed programs (momentum/reversion, feature acquisition v2, large-cap swing, who-family pilot, Drift perps state), which were all directional token-selection programs. This program asks whether **fee capture can exceed adverse selection** in identifiable pool states — a different business model with different data, different mechanics, and different failure modes.

No live LP deployment. No live trading. No directional price prediction.

---

## 2. Hypotheses

### H1 — Volatility-Fee State
When a pool's dynamic fee state is elevated (high fee/TVL ratio, high recent volume relative to TVL), do hypothetical LP deployments plausibly earn more in fees than they lose to adverse selection over short holding windows?

**State variable:** `fee_tvl_ratio_h1` (fee earned in last 1h / current TVL) from Meteora API.  
**Elevated threshold:** `fee_tvl_ratio_h1 > 0.01` (1% fee yield per hour).  
**Proxy:** fee proxy minus adverse selection proxy over +15m, +1h, +4h.

### H2 — Toxic Flow Filter
Are there identifiable pool states where adverse selection is so strong that LP deployment should be systematically vetoed?

**State variable:** Price move magnitude in the hour following hypothetical LP entry.  
**Toxic threshold:** |price_move_h1| > 5% (large directional move indicating informed order flow).  
**Proxy:** Net LP proxy is negative when adverse selection dominates fee income.

### H3 — Launch / Bootstrap Toxicity
For launch-style pools (high base fee ≥ 2%, high max fee ≥ 5%, newly created), do fee conditions ever offset the toxicity of early trading, or are these systematically bad LP states?

**State variable:** `base_fee_percentage ≥ 2%` AND `max_fee_percentage ≥ 5%` (launch/anti-sniper configuration).  
**Proxy:** Same LP proxy construction as H1/H2, but restricted to launch-type pools.

---

## 3. Universe Construction

### Pool Selection
- Source: Meteora DLMM API `pair/all` endpoint (137,899 pools as of 2026-03-15)
- Filter to pools with SOL as quote token (most liquid, comparable)
- Filter to pools with `fees_24h > $50` (active pools only)
- Filter to pools with `liquidity > $5,000` (non-trivial TVL)
- Filter to pools not blacklisted (`is_blacklisted = false`)
- Exclude pools with `hide = true`

This produces a **working universe** of active, non-trivial Meteora DLMM pools.

### Pool Type Classification
| Type | Criteria |
|------|----------|
| Standard | `base_fee_percentage < 1%` |
| Elevated-fee | `1% ≤ base_fee_percentage < 2%` |
| Launch/Anti-sniper | `base_fee_percentage ≥ 2%` AND `max_fee_percentage ≥ 5%` |

---

## 4. Data Sources

| Source | Data | Availability |
|--------|------|-------------|
| Meteora DLMM API (`dlmm-api.meteora.ag/pair/all`) | Current pool state: fees, volume, TVL, fee/TVL ratio by window, base/max fee | Available, free, no auth |
| GeckoTerminal API (`api.geckoterminal.com/api/v2`) | Historical OHLCV hourly, up to 1000 bars (~42 days) per pool | Available, free, no auth |
| Meteora DLMM API (`pair/{address}`) | Per-pool current state including fee windows | Available |

**Blocked / Not Available:**
- Historical fee time series (fee earned per hour per pool): **NOT available** from any public source
- Historical bin activity / liquidity distribution changes: **NOT available**
- Exact LP PnL (requires position-level on-chain data): **NOT available** without Helius/Bitquery paid API

---

## 5. LP PnL Proxy Construction

Because exact LP PnL is not computable from available data, this study uses a clearly-labeled proxy.

### Fee Proxy (per bar)
```
fee_proxy_per_bar = base_fee_percentage × volume_per_bar_usd / tvl_usd
```
Where `volume_per_bar_usd` is estimated from GeckoTerminal OHLCV volume column (USD volume per hourly bar).

**Limitation:** This uses base fee only, not dynamic fee. Dynamic fee can be higher during volatility, so this is a **conservative lower bound** on fee income.

### Adverse Selection Proxy
```
adverse_selection_proxy = |price_return_over_horizon|
```
The absolute price move over the holding window. If price moves significantly in one direction, the LP suffers impermanent loss (IL) proportional to the move. For small moves, IL ≈ 0.5 × (price_return)².

**IL approximation:**
```
il_proxy = 0.5 × price_return² (for |return| < 20%)
```

### Net LP Proxy
```
net_lp_proxy = fee_proxy_accumulated - il_proxy - operational_friction
```

**Operational friction assumptions (conservative):**
- Gas/transaction cost: 0.01% of position (fixed)
- Rebalancing cost: not modeled in Stage A (no rebalancing assumed)
- Slippage on entry/exit: 0.05% (conservative for liquid pools)
- Total friction: **0.06%** per deployment

### Proxy Label
All results are labeled **"LP proxy"** throughout. This is not exact LP PnL. It is a simulation under simplifying assumptions. Stage B would require exact position-level data.

---

## 6. Event Definition

An **LP deployment event** is defined as:
- A pool in the working universe at a given hourly bar
- The pool meets the state condition for the hypothesis (e.g., elevated fee/TVL for H1)
- The event timestamp is the bar open time
- Forward returns are measured at +15m, +1h, +4h from the bar open

Events are constructed from the historical OHLCV data for each pool in the working universe.

---

## 7. Horizons

Primary: **+15m, +1h, +4h**  
Appendix only (if data permits): +1d

---

## 8. Output Metrics

For each hypothesis × horizon combination:
- N (sample size)
- Mean LP proxy
- Median LP proxy
- Winsorized mean LP proxy (5th–95th percentile)
- % positive LP proxy
- Bootstrap 95% CI for mean (1,000 resamples)
- Bootstrap 95% CI for median (1,000 resamples)
- Top-1 contributor share (largest single event / total)
- Top-3 contributor share

---

## 9. Pass/Fail Gates

A hypothesis/horizon combination **passes** only if ALL of the following hold:

| Gate | Criterion |
|------|-----------|
| G1 | N ≥ 30 independent events |
| G2 | Winsorized mean LP proxy > 0 |
| G3 | Median LP proxy > 0 |
| G4 | Bootstrap CI lower bound > 0 |
| G5 | Top-1 contributor share < 25% |
| G6 | Top-3 contributor share < 50% |
| G7 | Result is structurally distinct from directional price prediction |

---

## 10. Kill Criteria

The program is immediately marked **NO-GO** if:
- 0 hypothesis/horizon combinations pass all gates
- The only passing combinations have N < 30
- All positive results are driven by a single pool or single time period

The program is marked **BLOCKED** if:
- The fee proxy cannot be constructed from available data
- The OHLCV data covers fewer than 14 days for the majority of pools in the working universe

---

## 11. Stage B Criteria

Stage B (live LP state monitoring) is only justified if:
- At least one H1 or H3 combination passes all gates
- The passing combination has N ≥ 50 and CI lower > 0.1%
- The result is not explained by a single pool or single market event

---

*End of Design Document*
