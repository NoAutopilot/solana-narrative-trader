# External Feedback → Top 3 Tests

**Program:** external_feedback_to_tests_map
**Date:** 2026-03-15
**Author:** Manus AI

---

## Scoring Summary

Six candidate tests were evaluated. Two were disqualified before ranking: T5 (MEV / Instruction-Level Extraction) violates the user's explicit constraint against large infrastructure projects, and T6 (Negative Quality Screen) is partially subsumed by T2 and does not stand alone as a distinct test. The four remaining candidates were scored across seven dimensions.

| Test | Type | Novelty | Constraint Fit | Data Available | New Infra | Time to Verdict | Self-Deception Risk | Actionable If Positive | Overall |
|------|------|---------|---------------|----------------|-----------|-----------------|--------------------|-----------------------|---------|
| T1: Shortable Toxic-State Pilot | Negative-screen | HIGH | MEDIUM | MEDIUM | LOW | MEDIUM | MEDIUM | MEDIUM | HIGH |
| T2: Actuarial / Casino-Math Book | Actuarial | HIGH | HIGH | HIGH | LOW | LOW | LOW | HIGH | VERY HIGH |
| T3: Stablecoin Basis / Carry | Structural carry | HIGH | MEDIUM | MEDIUM | LOW | MEDIUM | LOW | MEDIUM | MEDIUM |
| T4: Liquidation Hunting Feasibility | Structural extraction | HIGH | LOW | MEDIUM | LOW | LOW | LOW | LOW | LOW |

**Ranking: T2 > T1 > T3 > T4**

T4 is retained as a conditional backup (only if T1 and T2 both fail or block) because it can be resolved quickly and cheaply, even though the expected answer is NO.

---

## Rank 1 — Actuarial / Casino-Math Book Test (T2)

### 1. Exact Question

For tokens passing a simple, non-predictive minimum quality filter (liquidity, age, market cap floor), does the empirical payoff distribution of mechanical entries and exits — using fixed sizing and fixed asymmetric exit rules — produce a positive expected value across the historical universe? Specifically: does the distribution have positive mean, acceptable skew, and a Sharpe-equivalent that survives realistic transaction cost assumptions?

This question does **not** ask whether any token can be predicted to go up. It asks whether the aggregate distribution of outcomes, across a large universe of tokens with no selection beyond the quality filter, supports a mechanical book with positive EV. This is the casino-math framing: the house does not predict individual hands; it knows the distribution.

### 2. Exact Dataset Needed

The test requires historical OHLCV data for a large universe of Solana tokens (minimum 200 tokens, ideally 500+) with at least 90 days of trading history each. The dataset must include: daily open, high, low, close, and volume; approximate market cap at each date; and an approximate liquidity proxy (e.g., average daily volume or bid-ask spread estimate). Transaction cost assumptions must be documented and applied consistently.

### 3. What Existing Data Can Be Reused

Prior work on Solana token data collection (from the Who Family, Feature Acquisition, and Large-Cap Swing programs) has already established data pipelines for on-chain token data. The quality filter logic developed in prior programs (liquidity thresholds, age filters, market cap floors) can be reused directly as the non-predictive pre-filter for this test. No signal work from prior programs is reused — only the data infrastructure and filter logic.

### 4. What New Data Is Required

The test requires extending the token universe beyond the large-cap focus of prior programs. Prior work focused on the top 20-50 tokens by market cap. This test requires the broader mid-cap and small-cap universe (tokens with $5M-$500M market cap, 90+ days of history). This data is available from public sources (DeFiLlama, Birdeye, CoinGecko) but requires a new data pull covering a wider universe.

### 5. Exact Output Metrics

The test produces the following metrics for each candidate exit structure (e.g., fixed 15% take-profit / 8% stop-loss, fixed 20% take-profit / 10% stop-loss, etc.):

- **Mean return per trade** (after transaction costs)
- **Median return per trade** (after transaction costs)
- **Win rate** (fraction of trades hitting take-profit before stop-loss)
- **Payoff ratio** (mean win / mean loss)
- **Expected value per trade** = (win rate × mean win) + ((1 - win rate) × mean loss)
- **Distribution skew and kurtosis** (to detect fat tails)
- **Sharpe-equivalent** (annualized mean / annualized std dev of trade returns)
- **Maximum drawdown** of the mechanical book over the test period
- **Sensitivity to transaction cost assumption** (test at 0.1%, 0.3%, 0.5%, 1.0% round-trip)

### 6. Exact Pass/Fail Gates

**PASS** (proceed to Stage B — live or paper trading of the mechanical book):
- Mean return per trade > 0% after 0.5% round-trip transaction cost
- Expected value per trade > 0% at the median transaction cost assumption
- Sharpe-equivalent > 0.5 across at least 3 of 4 exit structure variants tested
- Result is stable across at least two sub-periods of the historical data (not a single-period artifact)
- The quality filter retains at least 100 tokens (book is not too thin to size)

**FAIL** (close the line):
- Mean return per trade ≤ 0% after 0.3% round-trip transaction cost
- Expected value per trade ≤ 0% at any reasonable transaction cost assumption
- Result is unstable across sub-periods
- Quality filter retains fewer than 50 tokens (universe too thin)

### 7. Exact Kill Criteria

The test is killed immediately if any of the following are observed during analysis:

- The positive EV result depends on a single exit structure that was clearly optimized to fit the data (overfitting signal)
- The positive EV result disappears entirely when transaction costs exceed 0.3% round-trip (not robust to realistic costs)
- The positive EV result is driven by fewer than 20 tokens (too concentrated; not a distributional result)
- The quality filter cannot be defined without reference to future outcomes (look-ahead bias)

### 8. Why This Is Genuinely Different from Prior Failures

Every prior closed line asked: "Can I predict which tokens will go up?" This test asks: "Does the aggregate distribution of token outcomes, without prediction, support a positive-EV mechanical book?" These are fundamentally different questions. The prior question requires a predictive signal that is durable and non-obvious. This question requires only that the empirical distribution has the right shape — which is a property of the market structure, not of any signal's predictive power.

The casino-math framing is the key difference. A casino does not predict which player will win; it designs games where the aggregate distribution produces positive EV for the house. If the Solana token universe has a distribution that supports this — e.g., because the upside tails are fat enough relative to the downside tails under asymmetric exit rules — then a mechanical book is viable without any prediction. This has never been tested in the prior program history.

---

## Rank 2 — Shortable Toxic-State Pilot (T1)

### 1. Exact Question

Do the previously identified "bad long" / toxic states — the conditions under which prior programs found that long entries performed poorly — produce positive net returns as short entries inside the actually shortable universe, after accounting for perpetual futures funding rates, borrow costs, and listing-selection bias?

This question is a direct inversion of prior signal work. It does not require discovering a new signal; it requires testing whether an existing negative signal is usable as a positive short signal.

### 2. Exact Dataset Needed

The test requires: (a) the toxic-state labels from prior programs (the conditions identified as bad-long states); (b) historical perpetual futures funding rate data for the shortable Solana token universe on Drift, Mango, and/or Backpack; (c) historical price data for the same tokens; and (d) an estimate of listing-selection bias (tokens that are shortable via perps tend to be larger and more liquid than the full token universe).

### 3. What Existing Data Can Be Reused

The toxic-state labels from prior programs are directly reused. The historical price data from prior programs covers the large-cap universe, which overlaps substantially with the shortable universe. No new signal work is required.

### 4. What New Data Is Required

Perpetual futures funding rate history for Solana tokens on Drift and other Solana perps venues. This data is publicly available but has not been collected in prior programs. Borrow cost data for spot shorting (if applicable) is also needed, though the test is primarily focused on perps shorting.

### 5. Exact Output Metrics

- **Mean return per short trade** (after funding costs) in toxic states
- **Mean return per long trade** (after costs) in toxic states (for comparison — should be negative)
- **Funding rate drag** (average annualized funding cost for short positions in the test period)
- **Net return = gross short return minus funding drag**
- **Win rate of short entries in toxic states**
- **Comparison to random short entries** (is the toxic-state signal adding value, or is shorting always profitable in the test period?)
- **Listing-selection bias assessment** (how different is the shortable universe from the full universe?)

### 6. Exact Pass/Fail Gates

**PASS:**
- Mean net return of short entries in toxic states > 0% after funding costs
- Mean net return is materially better than random short entries in the same period
- Result holds in at least two sub-periods
- Funding drag does not eliminate the edge (net return > 0% even at 10% annualized funding)

**FAIL:**
- Mean net return ≤ 0% after funding costs
- Short entries in toxic states perform no better than random short entries
- Listing-selection bias explains the entire result (shortable tokens are just larger and more stable)

### 7. Exact Kill Criteria

- If the shortable universe contains fewer than 15 tokens, the test is too thin to be actionable
- If the mean funding rate exceeds 15% annualized, the carry cost is prohibitive regardless of gross return
- If the toxic-state signal adds no incremental value over random shorting, the inversion hypothesis is rejected

### 8. Why This Is Genuinely Different from Prior Failures

Prior programs used the toxic-state signal as a long filter (avoid entering longs in toxic states). This test asks whether the same signal is actionable as a short entry trigger. The mechanism is different: instead of predicting which tokens will go up, the test asks whether a known bad-long state is also a good-short state. The answer is not obvious — a bad-long state may simply be a high-volatility state where neither direction is predictable — but the question is testable and the data is largely already available.

---

## Rank 3 — Stablecoin Basis / Delta-Neutral Carry Pilot (T3)

### 1. Exact Question

Can a human-scale operator capture positive median carry after real funding rates, borrow costs, and execution frictions using a market-neutral or near-neutral basis structure on Solana? Specifically: is there a basis trade (e.g., long spot SOL / short SOL perps, or long JitoSOL / short SOL perps) where the carry after all frictions is positive, consistent, and large enough to be worth the operational complexity?

This is a narrower and more honest version of the delta-neutral question than what Grok proposed. The Solana Yield Surface Stage A already showed that delta-neutral yields have compressed to approximately 1-3% net. This test asks whether there is a specific basis structure that survives this compression.

### 2. Exact Dataset Needed

Historical perpetual futures funding rate data for SOL on Drift, Mango, and Backpack (at minimum 6 months). Historical JitoSOL/SOL price ratio data. Estimated execution costs for entering and exiting the basis position. Borrow cost data for any spot short component.

### 3. What Existing Data Can Be Reused

The Solana Yield Surface Stage A data collection includes LST yield data and some funding rate context. The delta-neutral yield compression data (Q4 2024: 6.2%, Q4 2025: 1.1%) provides a baseline for what the test is likely to find.

### 4. What New Data Is Required

Granular historical funding rate data for SOL perps on Solana venues (not just Binance/CME). This is the key data gap. If Solana-native perps funding rates are systematically different from CEX rates, there may be a basis that is not visible in aggregate delta-neutral yield statistics.

### 5. Exact Output Metrics

- **Median annualized carry** after funding costs and execution friction
- **Consistency of carry** (fraction of weeks with positive carry)
- **Maximum carry drawdown** (longest period of negative carry)
- **Break-even funding rate** (the funding rate at which carry becomes zero)
- **Sensitivity to execution cost assumption**

### 6. Exact Pass/Fail Gates

**PASS:**
- Median annualized carry > 3% after all frictions (must exceed T-bill rate meaningfully to justify complexity)
- Carry is positive in at least 60% of weeks in the test period
- Break-even funding rate is below the historical 25th percentile of observed funding rates

**FAIL:**
- Median annualized carry ≤ 1% after frictions (not worth the complexity)
- Carry is negative in more than 40% of weeks
- The result depends on a single high-funding-rate period that is unlikely to recur

### 7. Exact Kill Criteria

- If Solana-native perps funding rates are consistently below 5% annualized, the carry is insufficient regardless of other factors
- If the basis trade requires more than $50K in capital to execute efficiently (due to minimum position sizes), it exceeds the human-scale constraint
- If the carry is positive but the maximum drawdown period exceeds 3 months, the strategy is not operationally viable

### 8. Why This Is Genuinely Different from Prior Failures

The Solana Yield Surface Stage A evaluated yield optimization broadly and found it uncompelling. This test asks a narrower structural question: is there a specific basis structure on Solana-native venues where the carry is positive after frictions? The prior test was about the yield surface as a whole; this test is about a specific structural trade. The answer may still be NO — the delta-neutral compression data suggests it probably is — but the question is different enough to warrant a fast, cheap test before closing the line entirely.

---

## Conditional Backup — Liquidation Hunting Feasibility Test (T4)

T4 is retained as a conditional backup only if T1 and T2 both fail or block. It can be resolved in 1-2 weeks from public data alone. The expected answer is NO (bots dominate at the speed required), but a fast NO is still valuable information.

**Kill criteria for T4:** If on-chain data shows that liquidation events are resolved within 1-3 blocks (approximately 400-1200ms on Solana), the test is immediately closed as a bot-only game. If the median time from liquidation trigger to execution exceeds 10 seconds, human-scale capture may be feasible and warrants further investigation.
