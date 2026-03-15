# T3 — Stablecoin Basis / Delta-Neutral Carry Pilot: Results

**Program:** T3 Stablecoin Basis / Delta-Neutral Carry Pilot  
**Design version:** v1 (pre-registered 2026-03-15)  
**Execution date:** 2026-03-15  
**Data sources:** OKX API (SOL-USDT-SWAP funding rates, Dec 2025–Mar 2026); Yahoo Finance (SOL-USD, JITOSOL-USD, 2-year OHLCV); Bybit/Binance (corroborating funding rate data)  
**Test period:** 2024-03-15 to 2026-03-15  

---

## OVERALL VERDICT: FAIL (KILL CRITERION TRIGGERED)

**Kill Criterion 1 triggered.** The OKX actual median 8-hourly funding rate for SOL-USDT-SWAP over the available data period (December 2025 – March 2026) is **-0.00098%** per 8-hour period, equivalent to **-1.07% annualized**. This is below the pre-registered kill threshold of 1.5% annualized. Shorts are currently paying longs, not receiving carry. The basis trade is losing money in the current regime.

This result is corroborated by Bybit (-2.55% annualized median) and Binance (-4.34% annualized median) over the same period. All three venues show the same direction: negative funding, meaning the market is in a regime where short sellers are in excess and must pay a premium to maintain their positions.

---

## 1. Data Availability

| Source | Coverage | Records | Median Ann. Funding |
|---|---|---|---|
| OKX SOL-USDT-SWAP | 2025-12-10 to 2026-03-15 | 287 (8-hourly) | **-1.07%** |
| Bybit SOLUSDT | 2026-01-08 to 2026-03-15 | 200 (8-hourly) | **-2.55%** |
| Binance SOLUSDT | 2026-01-08 to 2026-03-15 | 200 (8-hourly) | **-4.34%** |
| Yahoo Finance SOL-USD | 2024-03-15 to 2026-03-15 | 732 daily | N/A |
| Yahoo Finance JITOSOL-USD | 2024-03-15 to 2026-03-15 | 732 daily | N/A |

**Data gap:** All three CEX venues provide only approximately 90 days of funding rate history via their public APIs. The period 2024-03-15 to 2025-12-09 (approximately 21 months) has no actual funding rate data available from any public source. Per the pre-registered design, the simulation uses fixed-rate scenarios for this gap period.

**JitoSOL staking yield (from actual data):** The Yahoo Finance JITOSOL-USD / SOL-USD ratio appreciation over the 2-year period implies an annualized JitoSOL staking yield of **7.53%** — above the pre-registered base assumption of 6.5% and within the high scenario of 8.0%.

---

## 2. Current Regime: Negative Funding

The most important finding is not about the simulation — it is about the current state of the market.

**SOL fell approximately 52% over the 2-year test period** (from ~$183 to ~$88). In a sustained bear market, the demand for leveraged long positions collapses. When longs are scarce and shorts are abundant, the perpetual futures funding mechanism inverts: shorts must pay longs to maintain their positions. This is the regime that has prevailed since approximately December 2025.

The three venues show consistent negative funding:

| Venue | Period | Median Ann. | Negative Funding % |
|---|---|---|---|
| OKX | Dec 2025 – Mar 2026 | -1.07% | 55% of periods |
| Bybit | Jan 2026 – Mar 2026 | -2.55% | 58% of periods |
| Binance | Jan 2026 – Mar 2026 | -4.34% | 64% of periods |

In this regime, the basis trade (long spot SOL / short SOL-PERP) is not earning carry — it is paying carry. The JitoSOL enhancement (B2) partially offsets this with staking yield, but the net result is marginal or negative.

**Actual period results (Dec 2025 – Mar 2026, conservative cost):**

| Basis | Median Ann. Carry | Mean Ann. Carry | % Positive Weeks |
|---|---|---|---|
| B1 (Long SOL / Short SOL-PERP) | **-5.72%** | -7.15% | 8% |
| B2 (Long JitoSOL / Short SOL-PERP, Drift) | **+1.57%** | -0.93% | 54% |
| B3 (Long JitoSOL / Short SOL-PERP, OKX) | **-1.03%** | -3.53% | 38% |

B2 shows a barely positive median (+1.57%) in the actual data period, but this is below the pre-registered pass threshold of 3% and is not consistent (only 54% of weeks positive). B1 and B3 are clearly negative.

---

## 3. Simulation Results (Full 2-Year Period)

Because actual funding rate data covers only ~90 days, the simulation runs four pre-registered funding rate scenarios for the historical gap period. The results below show what the carry would have been under each scenario.

### Key Scenario Results (Conservative Cost = 0.40% round-trip)

| Basis | Funding Scenario | Median Ann. Carry | % Positive Weeks | Max Neg. Streak | SP+ | Verdict |
|---|---|---|---|---|---|---|
| B1 | Bearish (3%) | -1.81% | 1% | 93 weeks | 0/3 | **FAIL** |
| B1 | Neutral (6%) | +1.18% | 89% | 10 weeks | 3/3 | **AMBIGUOUS** |
| B1 | Bullish (15%) | +10.16% | 89% | 10 weeks | 3/3 | **AMBIGUOUS** |
| B2 | Bearish (3%) | +5.17% | 87% | 4 weeks | 3/3 | **PASS** |
| B2 | Neutral (6%) | +8.12% | 89% | 4 weeks | 3/3 | **PASS** |
| B2 | Bullish (15%) | +17.09% | 90% | 4 weeks | 3/3 | **PASS** |
| B3 | Bearish (3%) | +2.57% | 75% | 4 weeks | 3/3 | **AMBIGUOUS** |
| B3 | Neutral (6%) | +5.52% | 85% | 4 weeks | 3/3 | **PASS** |
| B3 | Bullish (15%) | +14.49% | 89% | 4 weeks | 3/3 | **PASS** |

### Pass Count Summary (across all 20 scenario combinations per basis)

| Basis | PASS | AMBIGUOUS | FAIL |
|---|---|---|---|
| B1 (Long SOL / Short SOL-PERP) | 6/20 | 7/20 | 7/20 |
| B2 (Long JitoSOL / Short SOL-PERP, Drift) | **17/20** | 2/20 | 1/20 |
| B3 (Long JitoSOL / Short SOL-PERP, OKX) | 11/20 | 5/20 | 4/20 |

---

## 4. The Structural Problem: Regime Dependency

The simulation results reveal a fundamental structural problem with the basis trade: **the carry is entirely regime-dependent**.

**When funding is positive (bull market):** The basis trade works well. B2 earns 8–17% annualized under neutral-to-bullish funding. This is the regime that prevailed during the 2024 bull market (SOL rose from ~$100 to ~$260 in late 2024).

**When funding is negative (bear market):** The basis trade loses money. B1 earns -1.81% annualized under the bearish scenario (3% funding). The JitoSOL enhancement (B2) partially offsets this — B2 earns +5.17% even under bearish funding because the 7.53% staking yield more than covers the negative funding and costs. But this is the best case.

**The current regime is worse than "bearish."** The actual OKX data shows -1.07% annualized median funding — negative, not just low. Under actual current conditions, B2's carry is approximately:

```
B2 carry = JitoSOL yield + funding received - execution cost
         = 7.53% - 1.07% - 4.80%  (annualized, conservative cost)
         = +1.66% annualized
```

This is below the 3% pass threshold. And the mean is negative (-0.93%) because the funding rate is volatile and frequently deeply negative.

**The key insight:** The basis trade is not a stable carry strategy. It is a bet on the funding rate regime. In a bull market, it earns well. In a bear market, it earns little or nothing. Since you cannot predict regime changes, the strategy has no reliable expected value — it has conditional expected value that depends on market direction, which is exactly what the test was designed to avoid.

---

## 5. Break-Even Analysis

The break-even funding rate is the annualized funding rate at which carry equals zero.

| Basis | Break-Even Ann. Funding | Current Regime | Gap |
|---|---|---|---|
| B1 (conservative cost) | +4.80% | -1.07% | -5.87pp |
| B2 (conservative cost) | -2.73% | -1.07% | +1.66pp |
| B3 (conservative cost) | -0.13% | -1.07% | -0.94pp |

B2 has a break-even funding rate of -2.73% annualized — meaning it earns positive carry even when funding is moderately negative, because the JitoSOL staking yield covers the gap. The current regime (-1.07%) is above this break-even, which is why B2 shows a barely positive median in the actual data period.

However, the margin is thin: only 1.66 percentage points of buffer between the current funding rate and the B2 break-even. If funding deteriorates further (which is plausible in a continued bear market), B2 also goes negative.

---

## 6. Capital Scale and Operational Complexity

At the pre-registered $10,000 notional scale:

| Basis | Ann. Carry (neutral, conservative) | Annual $ Carry | Monthly $ Carry |
|---|---|---|---|
| B1 | +1.18% | $118 | $9.83 |
| B2 | +8.12% | $812 | $67.67 |
| B3 | +5.52% | $552 | $46.00 |

Even under the most favorable scenario (B2, neutral funding, conservative cost), the annual dollar carry at $10K notional is $812. This requires:
- Maintaining a Drift Protocol account with active SOL-PERP short
- Holding JitoSOL on-chain
- Monthly rebalancing to maintain delta neutrality
- Monitoring for funding rate sign flips
- Managing liquidation risk if SOL price moves sharply

**The operational complexity is not justified at $10K scale.** At $100K notional, the annual carry under neutral funding would be ~$8,120 — more meaningful, but still requires significant operational overhead and exposes $100K to Drift Protocol smart contract risk and JitoSOL depeg risk.

---

## 7. Adversarial Assessment

**Why the simulation looks better than reality:**

The simulation uses fixed-rate scenarios for 21 of the 24 months in the test period. The "neutral" scenario (6% annualized) produces attractive results for B2. But this is a hypothetical. The only actual data we have — the most recent 3 months — shows deeply negative funding. The simulation's favorable scenarios are assumptions, not observations.

**The regime-dependency problem is not solvable.** The basis trade earns carry when the market is bullish (longs pay shorts) and loses carry when the market is bearish (shorts pay longs). This means the strategy has the same directional exposure as a long position — it earns when SOL goes up and loses when SOL goes down — but with lower magnitude and higher operational complexity. A simple long SOL position is strictly better on risk-adjusted terms if you believe SOL will recover.

**The JitoSOL enhancement (B2) is the only viable structure,** but only marginally. Under the current regime, B2 earns approximately +1.57% annualized median carry — not enough to justify the complexity. Under a neutral funding regime, B2 earns ~8% — attractive, but that requires a bull market, which means you would earn more simply by holding SOL.

**The strategy is a worse version of holding SOL.** In a bull market, you earn carry but miss most of the upside (you're short the perp). In a bear market, you lose carry and also lose on the spot leg. The only scenario where the basis trade strictly dominates is a flat market with positive funding — a narrow and unpredictable condition.

---

## 8. Pass/Fail Summary

| Criterion | Threshold | B1 | B2 | B3 |
|---|---|---|---|---|
| Kill 1: Actual median funding > 1.5% ann | > 1.5% | -1.07% ✗ | -1.07% ✗ | -1.07% ✗ |
| Median carry > 3% (neutral, conservative) | > 3% | 1.18% ✗ | 8.12% ✓ | 5.52% ✓ |
| Positive in ≥ 60% of weeks | ≥ 60% | 89% ✓ | 89% ✓ | 85% ✓ |
| Break-even < 25th pct of observed rates | < 3.62% | 4.80% ✗ | -2.73% ✓ | -0.13% ✓ |
| Actual period median > 3% | > 3% | -5.72% ✗ | 1.57% ✗ | -1.03% ✗ |

**Kill Criterion 1 is triggered for all three structures.** The test closes.

---

## 9. What T3 Actually Tells Us

**Finding 1: The basis trade is regime-dependent, not structurally positive.** The carry is positive in bull markets and negative in bear markets. This is not a stable carry strategy — it is a directional bet dressed up as carry.

**Finding 2: JitoSOL (B2) is the only structure with a meaningful buffer.** The 7.53% staking yield provides a cushion that allows B2 to earn positive carry even in mildly negative funding environments. But the current regime (-1.07% funding) is close to the break-even, and the margin is thin.

**Finding 3: The current regime is the worst possible for this strategy.** SOL -52%, negative funding, shorts dominating — this is the exact environment where the basis trade fails. The strategy would have worked well in Q4 2024 (SOL bull run, high positive funding), but that regime is gone.

**Finding 4: At human scale ($10K–$100K), the dollar carry is not worth the operational complexity.** Even under the most favorable assumptions, the annual dollar carry at $10K is under $1,000. The operational overhead (Drift account, JitoSOL custody, rebalancing, monitoring) is not justified at this scale.

**Finding 5: The strategy has no edge over simply holding JitoSOL.** If you believe SOL will recover, holding JitoSOL earns 7.53% staking yield with no operational complexity and no short leg to manage. The basis trade adds complexity and risk without adding proportional return.

---

## 10. Verdict and Next Steps

**T3 VERDICT: FAIL (KILL CRITERION)**

Kill Criterion 1 is triggered. The actual funding rate data shows negative funding (-1.07% annualized median on OKX), which is below the pre-registered 1.5% threshold. The basis trade is not viable in the current regime.

**What this does NOT mean:**
- It does not mean the basis trade never works — it worked well in 2024
- It does not mean JitoSOL is a bad asset — the staking yield is real and attractive
- It does not mean delta-neutral strategies are permanently dead

**What this DOES mean:**
- The basis trade is not a reliable, regime-independent carry strategy
- At current funding rates, the strategy loses money or earns marginally positive returns insufficient to justify complexity
- The strategy requires a bull market to work — which means it is not a hedge, it is a leveraged bet on market direction

**No Stage B recommended.** The test closes.

**Program status:** T1 FAIL, T2 FAIL, T3 FAIL. All three candidate tests from the external feedback conversion have been executed and failed. The conditional backup (T4 — Liquidation Hunting Feasibility) may be run as a fast kill/no-kill check, but the expected answer is NO.

---

*Design: t3_design_v1.md | Data: OKX API + Yahoo Finance | Commit: pending*
