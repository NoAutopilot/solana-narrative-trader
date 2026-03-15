# T3 — Stablecoin Basis / Delta-Neutral Carry Pilot: Pre-Registered Design

**Program:** T3 Stablecoin Basis / Delta-Neutral Carry Pilot  
**Design version:** v1  
**Pre-registration date:** 2026-03-15  
**Status:** LOCKED — no parameter changes permitted after this date  

---

## 0. Purpose and Context

This design is pre-registered before any data is examined. All pass/fail thresholds, basis structure definitions, cost assumptions, and kill criteria are recorded here. No changes are permitted after data collection begins. Any deviation must be documented with explicit justification and treated as a protocol note that weakens the result.

**Context:** The Solana Yield Surface Stage A (2026-03-15) found that delta-neutral yields have compressed from approximately 6.2% annualized (Q4 2024) to approximately 1.1% annualized (Q4 2025). T3 asks a narrower question: is there a specific basis structure on Solana-native venues where the carry is positive after all frictions and large enough to justify the operational complexity? The prior test evaluated the yield surface broadly; this test evaluates a specific structural trade.

**Prior context from T1:** OKX funding rate data is available for approximately 3 months of history. For longer periods, a fixed-rate assumption must be used with explicit sensitivity testing. This limitation is acknowledged and incorporated into the design.

---

## 1. Exact Question

Can a human-scale operator capture **positive median carry** after real funding rates, borrow costs, and execution frictions using a market-neutral or near-neutral basis structure on Solana?

Specifically, for each of three basis structures:

- **B1:** Long spot SOL / Short SOL-PERP on Solana-native venue (Drift)
- **B2:** Long JitoSOL (LST) / Short SOL-PERP on Solana-native venue (Drift)
- **B3:** Long JitoSOL (LST) / Short SOL-PERP on CEX (OKX) — cross-venue basis

The test asks: does the historical carry for each structure, after all frictions, meet the minimum threshold to justify operational complexity?

The question is **not** whether the carry is the highest available yield. It is whether the carry is:
1. Positive in median (not just mean)
2. Consistent (positive in ≥ 60% of weeks)
3. Large enough to beat T-bills meaningfully (> 3% annualized after frictions)
4. Not dependent on a single high-funding-rate period

---

## 2. Basis Structure Definitions

### B1: Long Spot SOL / Short SOL-PERP (Drift)

- **Long leg:** Spot SOL held in wallet or on Drift spot
- **Short leg:** SOL-PERP perpetual futures short on Drift Protocol
- **Carry source:** Funding rate received on short position (when funding is positive, i.e., longs pay shorts)
- **LST enhancement:** None — pure spot/perp basis
- **Delta:** Near-zero (long spot SOL, short equivalent notional in perps)
- **Residual risk:** Basis risk (perp price diverges from spot), funding rate sign flip (shorts pay longs when funding goes negative)

### B2: Long JitoSOL / Short SOL-PERP (Drift)

- **Long leg:** JitoSOL (Jito liquid staking token) — earns staking yield (~6% annualized) plus MEV rewards
- **Short leg:** SOL-PERP perpetual futures short on Drift Protocol
- **Carry source:** JitoSOL staking yield + MEV rewards + funding rate received on short
- **Delta:** Near-zero (JitoSOL tracks SOL price closely; short SOL-PERP hedges the SOL price exposure)
- **Residual risk:** JitoSOL/SOL depeg risk, funding rate sign flip, Drift protocol risk

### B3: Long JitoSOL / Short SOL-PERP (OKX)

- **Long leg:** JitoSOL held on-chain
- **Short leg:** SOL-PERP perpetual futures short on OKX (CEX)
- **Carry source:** JitoSOL staking yield + MEV rewards + OKX funding rate received on short
- **Delta:** Near-zero
- **Residual risk:** Cross-venue basis risk, OKX funding rate vs Drift funding rate divergence, withdrawal/deposit latency, CEX counterparty risk

---

## 3. Data Requirements

### 3.1 Funding Rate Data

**Primary source:** OKX public API — SOL-USDT-SWAP funding rate history  
**Coverage:** ~3 months of 8-hourly funding rates (confirmed available from T1 data collection)  
**Proxy for longer history:** Fixed funding rate assumptions with sensitivity testing (see Section 6)  
**Drift funding rate:** Drift does not have a public historical API; will use OKX as proxy with documented assumption that Drift rates are correlated but may differ systematically

**Funding rate collection parameters:**
- Symbol: SOL-USDT-SWAP (OKX)
- Frequency: 8-hourly (3 payments per day)
- Period: Maximum available from OKX API (approximately 90 days back from 2026-03-15)
- Annualization: Multiply 8-hourly rate by 3 × 365

### 3.2 JitoSOL/SOL Price Ratio

**Source:** Yahoo Finance (JITOSOL-USD / SOL-USD ratio) or CoinGecko  
**Period:** Maximum available (target 2 years)  
**Purpose:** Compute JitoSOL staking yield as the rate of appreciation of JitoSOL relative to SOL

### 3.3 SOL Price History

**Source:** Yahoo Finance (SOL-USD)  
**Period:** 2024-03-15 to 2026-03-15 (2 years)  
**Purpose:** Compute notional position sizes and mark-to-market P&L

### 3.4 Execution Cost Estimates

All execution cost assumptions are pre-registered and cannot be changed after data collection:

| Cost Component | Optimistic | Base | Conservative | Stress |
|---|---|---|---|---|
| Entry round-trip (spot + perp) | 0.05% | 0.10% | 0.20% | 0.40% |
| Exit round-trip (spot + perp) | 0.05% | 0.10% | 0.20% | 0.40% |
| Total round-trip | 0.10% | 0.20% | 0.40% | 0.80% |
| Annualized (monthly rebalance) | 1.20% | 2.40% | 4.80% | 9.60% |
| Annualized (quarterly rebalance) | 0.40% | 0.80% | 1.60% | 3.20% |

**Rebalancing frequency assumption:** Monthly (12 rebalances per year). This is the base case. Quarterly is tested as a sensitivity.

---

## 4. Simulation Methodology

### 4.1 Weekly Carry Computation

For each week in the test period, compute:

```
weekly_carry_B1 = (funding_rate_received_per_week) - (execution_cost_amortized_per_week)
weekly_carry_B2 = (jitosol_staking_yield_per_week) + (funding_rate_received_per_week) - (execution_cost_amortized_per_week)
weekly_carry_B3 = (jitosol_staking_yield_per_week) + (okx_funding_rate_received_per_week) - (execution_cost_amortized_per_week) - (cross_venue_friction_per_week)
```

Where:
- `funding_rate_received_per_week` = sum of 8-hourly funding rates over the week × notional (positive = shorts receive, negative = shorts pay)
- `jitosol_staking_yield_per_week` = (JitoSOL/SOL ratio at week end / JitoSOL/SOL ratio at week start) - 1
- `execution_cost_amortized_per_week` = total_round_trip_cost / weeks_in_rebalance_period
- `cross_venue_friction_per_week` = 0.05% per week (additional friction for cross-venue basis, pre-registered)

### 4.2 Funding Rate Periods

The OKX API provides approximately 90 days of 8-hourly funding rate data. For the remaining ~21 months of the 2-year test period, the following fixed-rate scenarios are used:

| Scenario | Annualized Rate | 8-hourly Rate | Justification |
|---|---|---|---|
| Bearish (2025 bear market) | 3% | 0.00822% | Low demand for longs in bear market |
| Neutral | 6% | 0.01644% | Historical average for SOL perps |
| Bullish (2024 bull market) | 15% | 0.04110% | High demand for longs in bull market |
| Extreme bull | 30% | 0.08219% | Peak bull market funding (TRUMP launch period) |

The simulation is run under all four scenarios for the historical period not covered by actual OKX data. The actual OKX data is used as-is for the 90-day period where it is available.

### 4.3 JitoSOL Staking Yield

If JitoSOL/SOL ratio data is unavailable for the full 2-year period, the following fixed-rate assumptions are used:

| Scenario | Annual JitoSOL Yield | Justification |
|---|---|---|
| Low | 5.0% | Below-average MEV rewards |
| Base | 6.5% | Current observed rate (from Stage A) |
| High | 8.0% | Above-average MEV rewards |

### 4.4 Capital Concurrency and Scale

The test assumes a **$10,000 notional position** (human-scale). This is the minimum size at which Drift Protocol execution is practical. Carry is reported in both percentage terms and absolute dollar terms to assess whether the strategy is worth the operational complexity at this scale.

---

## 5. Pass/Fail Gates (Pre-Registered)

All thresholds are locked. No changes permitted after data collection begins.

### PASS (proceed to Stage B — live or paper trading of the basis):

All three of the following must be true for at least one basis structure (B1, B2, or B3):

1. **Median annualized carry > 3%** after conservative execution costs (0.40% round-trip) and base funding rate assumption
2. **Carry positive in ≥ 60% of weeks** in the test period (consistency requirement)
3. **Break-even funding rate < 25th percentile** of observed OKX funding rates (the carry does not depend on unusually high funding)

### FAIL (close the line):

Any of the following is sufficient to fail:

1. **Median annualized carry ≤ 1%** after conservative costs for all three structures (not worth the complexity)
2. **Carry negative in > 40% of weeks** for all three structures
3. **Result depends on a single high-funding-rate period** (e.g., the TRUMP launch in January 2025) — defined as: removing the top-decile funding rate weeks causes median carry to fall below 1%
4. **Break-even funding rate > 75th percentile** of observed rates for all structures (carry only works in exceptional conditions)

### AMBIGUOUS (flag for manual review):

- Median carry between 1% and 3% for the best structure
- Carry positive in 50–60% of weeks
- Result is sensitive to funding rate assumption

---

## 6. Sensitivity Analysis (Pre-Registered)

The following sensitivities are computed for all three basis structures:

| Sensitivity | Range |
|---|---|
| Execution cost | Optimistic / Base / Conservative / Stress |
| Funding rate (historical period) | Bearish / Neutral / Bullish / Extreme bull |
| JitoSOL yield | Low (5%) / Base (6.5%) / High (8%) |
| Rebalance frequency | Monthly / Quarterly |
| Capital scale | $10K / $50K / $100K |

---

## 7. Kill Criteria (Pre-Registered)

The test is killed immediately if any of the following are observed:

1. **OKX funding rate data shows median 8-hourly rate < 0.00411%** (< 1.5% annualized) — carry is insufficient regardless of other factors
2. **JitoSOL/SOL ratio data is unavailable** for any period and the fixed-rate assumption produces carry < 1% even at the high scenario — the LST enhancement is not material
3. **Drift Protocol is not operational** or has no SOL-PERP market — B1 and B2 cannot be executed
4. **Maximum carry drawdown period > 3 months** for all structures — not operationally viable

---

## 8. Concentration and Regime Analysis

Unlike T1 and T2, T3 is a single-position strategy (not a multi-token book). Concentration analysis is replaced by:

- **Regime analysis:** Carry broken down by market regime (bull / bear / sideways, defined by SOL 30-day return)
- **Funding rate regime:** Carry broken down by funding rate quartile
- **Subperiod stability:** 3 subperiods (each ~8 months) — carry must be positive in ≥ 2 of 3

---

## 9. What This Test Cannot Tell Us

This test uses OKX as a proxy for Drift funding rates. If Drift rates are systematically lower than OKX rates (which is plausible — Drift is a smaller venue with less retail long demand), the actual carry on Drift may be materially lower than what this test shows. This is a known limitation and must be stated explicitly in the results.

Additionally, the test does not account for:
- Smart contract risk on Drift or JitoSOL
- Liquidation risk if the SOL price moves sharply and the hedge ratio drifts
- Operational complexity of maintaining the hedge (monitoring, rebalancing, gas costs)
- Tax treatment of funding payments vs. staking rewards

These factors are qualitative and are addressed in the results document but not quantified in the simulation.

---

## 10. Execution Checklist (Must Be Confirmed Before Data Is Examined)

- [x] Basis structure definitions locked (B1, B2, B3 as above)
- [x] Pass/fail thresholds locked (Section 5)
- [x] Kill criteria locked (Section 7)
- [x] Cost assumption levels locked (Section 3.4)
- [x] Funding rate scenario levels locked (Section 4.2)
- [x] JitoSOL yield scenario levels locked (Section 4.3)
- [x] Subperiod boundaries defined: SP1 = 2024-03-15 to 2024-11-15, SP2 = 2024-11-15 to 2025-07-15, SP3 = 2025-07-15 to 2026-03-15
- [x] Capital scale assumption locked: $10,000 base case
- [x] Data sources locked: OKX API (funding), Yahoo Finance (prices), fixed-rate assumptions (historical gap)

Any deviation = protocol note with explicit justification required.  
Undocumented deviations invalidate the result.

---

*Pre-registration complete. Data collection may now begin.*
