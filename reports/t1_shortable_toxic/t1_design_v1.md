# T1 — Shortable Toxic-State Pilot: Pre-Registered Design

**Program:** T1 Shortable Toxic-State Pilot  
**Design version:** v1  
**Pre-registration date:** 2026-03-15 (before any data collection or examination)  
**Status:** LOCKED — no changes permitted after this point

---

## 1. Exact Question

Do the previously identified "bad long" / toxic states — the conditions under which prior programs found that long entries performed poorly — produce positive **net** returns as **short** entries inside the actually shortable Solana token universe, after accounting for perpetual futures funding rates and listing-selection bias?

This is a direct inversion test. It does not require discovering a new signal. It requires testing whether an existing negative signal is usable as a positive short signal.

**The question is not:** "Is shorting Solana tokens profitable in general?"  
**The question is:** "Does the toxic-state label add incremental value over random short entries?"

If shorting is generally profitable in the test period (a bear market), the test must show that toxic-state short entries outperform random short entries in the same period. Otherwise the result is just beta to a declining market, not a signal.

---

## 2. Toxic-State Definition (Pre-Registered)

Since prior program artifacts are not available in this execution context, the toxic-state label is defined from first principles using the most common conditions identified in prior Solana token research as bad-long states. These conditions are structural and non-predictive — they describe the state of the token at entry, not a forecast of future price.

**A token is in a TOXIC STATE on date D if it meets ALL of the following:**

| Condition | Threshold | Rationale |
|---|---|---|
| Price drawdown from 30d high | ≥ 25% | Token is already in a significant downtrend |
| 7d return | ≤ -10% | Recent momentum is strongly negative |
| 30d volume trend | Declining (7d avg vol < 30d avg vol × 0.7) | Liquidity is drying up |
| Price vs. 20d SMA | Price < 20d SMA × 0.85 | Token is extended below its moving average |

**Rationale for this definition:** These four conditions together identify tokens that are in active distribution/decline phases. As long entries, these conditions were consistently associated with poor outcomes in prior programs. The question is whether they are also good short entries.

**Alternative toxic-state definition (for sensitivity check):**  
A RELAXED toxic state requires only 2 of the 4 conditions above. Results under the relaxed definition are reported separately but do not affect the primary pass/fail verdict.

---

## 3. Shortable Universe Definition (Pre-Registered)

The shortable universe is defined as: **tokens available as perpetual futures on Drift Protocol** (the primary Solana-native perps venue) with sufficient open interest to be tradable at human scale.

**Minimum criteria for inclusion:**
- Listed as a perpetual futures market on Drift Protocol
- Open interest ≥ $500,000 USD (at the time of the trade, estimated from historical data)
- Not a stablecoin or LST (these are excluded — they are not speculative short targets)
- Not SOL itself (SOL is the benchmark; including it conflates the signal test with market beta)

**Expected universe size:** 15–40 tokens. If fewer than 15 tokens qualify, the test is killed per the pre-registered kill criterion.

---

## 4. Data Requirements (Pre-Registered)

| Data Type | Source | Period Required |
|---|---|---|
| Perpetual futures listing on Drift | Drift Protocol public API / docs | Current snapshot |
| Historical daily price (OHLCV) | Yahoo Finance / CoinGecko | 2024-03-01 to 2026-03-01 (24 months) |
| Perpetual futures funding rates | Drift Protocol historical data / Coinglass | 2024-03-01 to 2026-03-01 |
| Open interest history | Coinglass / Drift | 2024-03-01 to 2026-03-01 |

**Fallback for funding rates:** If Drift-specific funding rate history is unavailable, use Binance perpetual funding rates for the same tokens as a proxy. This is documented as a limitation.

---

## 5. Trade Simulation Rules (Pre-Registered)

### 5.1 Entry Rules

- **Entry signal:** Token is in TOXIC STATE on the reconstitution date (end of each calendar month)
- **Entry timing:** Short entered at the next-day open price
- **Entry sizing:** Equal-weight (1 unit per trade, no dynamic sizing)
- **Re-entry:** Allowed — if a token is in toxic state in consecutive months, a new short is entered each month (treated as independent trades)

### 5.2 Exit Rules

**Three exit structures are tested (all pre-registered, no grid search):**

| Structure | Take-Profit | Stop-Loss | Max Hold |
|---|---|---|---|
| S1 | -15% (price falls 15%) | +10% (price rises 10%) | 30 calendar days |
| S2 | -20% (price falls 20%) | +12% (price rises 12%) | 30 calendar days |
| S3 | -25% (price falls 25%) | +15% (price rises 15%) | 30 calendar days |

**Note:** For shorts, take-profit means the price falls (we profit), stop-loss means the price rises (we lose).

**SL-first rule:** If both TP and SL are hit on the same day (using daily high/low), SL is assumed to have been hit first (conservative assumption).

### 5.3 Cost Assumptions (Pre-Registered)

| Level | Round-Trip Cost | Description |
|---|---|---|
| Optimistic | 0.10% | Tight spread, low fee |
| Base | 0.30% | Typical Drift taker fee + spread |
| Conservative | 0.60% | Realistic for less liquid tokens |
| Stress | 1.20% | Illiquid conditions |

**Funding rate cost:** Applied separately from execution cost. Funding drag is calculated as: (mean annualized funding rate × hold period in days / 365). Applied to each trade individually based on its actual hold period.

### 5.4 Benchmarks (Pre-Registered)

| Benchmark | Description |
|---|---|
| BRandom | Random short entries on the same tokens, same dates, same exit rules — no toxic-state filter |
| BPassive | Simple 30-day short hold on all shortable tokens, equal-weight, no filter |

**The primary pass criterion requires the toxic-state short to outperform BRandom.** Outperforming BPassive alone is not sufficient — it could simply reflect a declining market.

---

## 6. Pass/Fail Gates (Pre-Registered)

### PASS (proceed to Stage B — paper trading of toxic-state short entries)

All of the following must be true at conservative cost (0.60%):

1. Mean net return per short trade > 0% (after execution cost + funding drag)
2. Mean net return of toxic-state shorts is materially better than BRandom (≥ +3pp advantage)
3. Result holds in at least 2 of 3 subperiods (defined below)
4. Funding drag does not eliminate the edge: net return > 0% even at 10% annualized funding
5. Shortable universe contains ≥ 15 tokens

### FAIL (close the line)

Any of the following triggers a FAIL:

- Mean net return ≤ 0% after conservative cost
- Toxic-state shorts perform no better than BRandom (< +3pp advantage)
- Result holds in fewer than 2 of 3 subperiods
- Funding drag eliminates the edge at 10% annualized funding

### AMBIGUOUS (report with caveats, do not proceed to Stage B without further review)

- Mean net return > 0% but advantage over BRandom is 1–3pp (marginal)
- Result holds in exactly 2 of 3 subperiods but the failing subperiod is recent (SP3)

---

## 7. Subperiod Definitions (Pre-Registered)

The 24-month test period is divided into three subperiods before data is examined:

| Subperiod | Date Range | Description |
|---|---|---|
| SP1 | 2024-03-01 to 2024-10-31 | Early period |
| SP2 | 2024-11-01 to 2025-06-30 | Mid period |
| SP3 | 2025-07-01 to 2026-03-01 | Recent period |

---

## 8. Kill Criteria (Pre-Registered)

The test is killed immediately if:

1. Shortable universe contains fewer than 15 tokens at any reconstitution date
2. Mean annualized funding rate for short positions exceeds 20% (carry cost is prohibitive regardless of gross return)
3. Toxic-state signal fires on fewer than 30 total trades across the full test period (too sparse to draw conclusions)
4. Data quality issues affect more than 20% of the universe (e.g., missing price data, gaps > 5 consecutive days)

---

## 9. Concentration and Robustness Reporting (Pre-Registered)

The following must be reported regardless of verdict:

- Top-1 and top-3 token share of total PnL
- Top-decile position share of total PnL
- Maximum single-month share of total PnL
- Number of unique tokens contributing to positive PnL
- Listing-selection bias assessment: compare mean market cap and volatility of shortable universe vs. full token universe

---

## 10. What This Test Cannot Prove

Even if T1 passes, it does not prove:

- That the toxic-state signal will continue to work in the future
- That the signal is not a regime artifact (bear market 2025 makes all shorts look good)
- That execution at the simulated prices is achievable in practice on Drift
- That funding rates will remain at historical levels

A PASS verdict means: "The data is consistent with the toxic-state label adding incremental value over random shorting." It does not mean "this is a profitable business."

---

## 11. Execution Checklist (Must Be Confirmed Before Data Collection)

- [x] Toxic-state definition locked (Section 2)
- [x] Shortable universe criteria locked (Section 3)
- [x] Exit structures locked (Section 5.2) — 3 structures, no grid search
- [x] Cost assumption levels locked (Section 5.3)
- [x] Benchmark definitions locked (Section 5.4)
- [x] Pass/fail thresholds locked (Section 6)
- [x] Subperiod boundaries locked (Section 7)
- [x] Kill criteria locked (Section 8)
- [x] Concentration reporting requirements locked (Section 9)

**No changes to any of the above are permitted after data collection begins.**  
Any deviation must be documented with explicit justification.  
Undocumented deviations invalidate the result.
