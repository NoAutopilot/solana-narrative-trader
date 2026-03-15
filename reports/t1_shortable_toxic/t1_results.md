# T1 — Shortable Toxic-State Pilot: Results

**Program:** T1 Shortable Toxic-State Pilot  
**Design version:** v1 (pre-registered 2026-03-15)  
**Execution date:** 2026-03-15  
**Data sources:** Yahoo Finance (OHLCV, 2-year history); OKX (funding rate reference)  
**Test period:** 2024-03-15 to 2026-03-15  

---

## OVERALL VERDICT: FAIL

**Structures passing: 1 of 3.** A result requires at least 2 of 3 structures to pass. T1 fails.

The single passing structure (S3: TP=25%, SL=15%, 30-day max hold) has a positive mean and beats the random benchmark by 3.84 percentage points at conservative cost. However, it fails the pre-registered requirement of ≥ 2/3 structures passing. The result is also heavily contaminated by a single-date cluster event (February 2026) that accounts for a disproportionate share of the positive outcomes. This is a concentration artifact, not a robust edge.

---

## 1. Universe

| Item | Value |
|---|---|
| Candidate shortable tokens | 28 |
| Tokens with 2-year history | 23 |
| Tokens failing data filter | 5 (POPCAT, MEW, GIGA, DRIFT, PENGU) |
| Kill criterion (min 15 tokens) | **PASSED** (23 ≥ 15) |
| SOL total return (test period) | **-52.05%** |
| Reconstitution periods | 24 monthly |
| Strict toxic trades | 41 |
| Relaxed toxic trades | 217 |
| Random benchmark trades | 531 |

The shortable universe is dominated by high-beta Solana-native tokens. SOL itself fell 52% over the test period, which means the entire universe was in a sustained bear market for the second half of the test period. This is a critical context: **a short strategy in a bear market is not the same as a short strategy with a genuine edge.** The question is whether the toxic-state filter adds value beyond simply being short in a declining market.

---

## 2. Toxic State Frequency

The strict toxic state definition (all 4 conditions: ≥25% drawdown from 30d high, 7d return ≤ -10%, volume declining, price < 85% of 20d SMA) is rare. Most tokens enter strict toxic state only 3–12% of the time. The relaxed definition (any 2 of 4 conditions) fires 30–60% of the time — too frequently to be a useful filter.

| Token | Strict Toxic % | Relaxed Toxic % |
|---|---|---|
| AI16Z-USD | 18.4% | 60.9% |
| CLOUD-USD | 13.4% | 46.4% |
| ZEREBRO-USD | 12.3% | 49.3% |
| ACT-USD | 10.4% | 42.0% |
| PNUT-USD | 9.7% | 45.1% |
| AIXBT-USD | 9.8% | 44.8% |
| GOAT-USD | 8.3% | 44.2% |
| FARTCOIN-USD | 5.5% | 41.8% |
| BONK-USD | 7.4% | 36.7% |
| JUP-USD | 7.4% | 45.0% |
| WIF-USD | 3.6% | 36.5% |
| JTO-USD | 2.7% | 29.0% |
| KMNO-USD | 0.7% | 29.2% |

The low frequency of strict toxic states (41 total entries over 24 months across 23 tokens) is itself a problem: this is too small a sample to draw reliable conclusions. **41 trades is not enough to distinguish signal from noise in a high-variance asset class.**

---

## 3. Results by Exit Structure

| Structure | Mean (conservative) | Median (conservative) | % Positive | Sharpe | Adv. over Random | SP+ | Verdict |
|---|---|---|---|---|---|---|---|
| S1 (TP=15%, SL=10%) | +1.17% | **-10.62%** | 46.3% | 0.78 | +1.27pp | 3/3 | **FAIL** |
| S2 (TP=20%, SL=12%) | +3.22% | **-0.65%** | 48.8% | 1.42 | +2.78pp | 2/3 | **FAIL** |
| S3 (TP=25%, SL=15%) | +5.13% | **+24.02%** | 51.2% | 1.52 | +3.84pp | 3/3 | **PASS** |

**S1 fails** on advantage over random (1.27pp < 3pp threshold) and on median (-10.62% median means the typical trade loses money even though the mean is positive — a skew artifact).

**S2 fails** on advantage over random (2.78pp < 3pp threshold). The median is marginally negative (-0.65%), which does not meet the requirement that median matters as much as mean.

**S3 passes** on all individual criteria: mean positive, median strongly positive (+24%), beats random by 3.84pp, positive in all 3 subperiods. However, this is the only structure that passes, and the result is contaminated by a cluster event (see Section 5).

---

## 4. Cost and Funding Sensitivity

**Cost sensitivity (S3):**

| Cost Level | Round-trip Cost | Mean Return |
|---|---|---|
| Optimistic | 0.10% | +5.63% |
| Base | 0.30% | +5.43% |
| Conservative | 0.60% | +5.13% |
| Stress | 1.20% | +4.53% |

S3 is robust to cost assumptions. The mean return degrades gracefully across cost levels and remains positive even at 1.20% round-trip (stress scenario).

**Funding sensitivity (S3, base cost):**

| Funding Scenario | Annualized Rate | Mean Return |
|---|---|---|
| Low | 3% | +5.49% |
| Base | 6% | +5.43% |
| High | 10% | +5.36% |
| Extreme | 20% | +5.16% |

S3 is also robust to funding assumptions. The reason is that the average hold period is very short (most trades hit TP or SL within 1–5 days), so annualized funding rates have minimal impact on per-trade returns. A 10% annualized funding rate on a 3-day hold is only ~0.08% drag per trade.

**Interpretation:** The robustness to cost and funding is not a sign of edge quality. It reflects the fact that S3 is a binary TP/SL structure with a large TP target (25%) — when it works, it works quickly and the cost is irrelevant. When it fails, it hits the SL (-15%) quickly. The mean is dominated by the TP/SL ratio and the hit rate, not by any genuine alpha.

---

## 5. Concentration and Cluster Event Analysis

This is the critical finding that invalidates the S3 pass.

**Top 10 positions by return (S3):**

All 6 of the top-returning positions entered on **2025-02-01** and hit their TP target on **2025-02-02** — a single-day 25% decline across multiple tokens simultaneously. This is a single market event (likely the TRUMP/MELANIA token collapse contagion in early February 2025 that dragged all Solana meme tokens down sharply).

| Token | Entry | Exit | Exit Type | Gross Return |
|---|---|---|---|---|
| ZEREBRO-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| BOME-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| CHILLGUY-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| PNUT-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| AI16Z-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| VIRTUAL-USD | 2025-02-01 | 2025-02-02 | TP | +25.0% |
| GOAT-USD | 2025-02-01 | 2025-02-03 | TP | +25.0% |

**7 of the 21 TP hits (33%) occurred on the same reconstitution date, driven by a single macro event.** If this one event is removed, the S3 advantage over random collapses.

**Concentration metrics (S3):**
- Top-3 token share of total PnL: **69%** (FARTCOIN, BOME, PYTH)
- Top-decile position share: **46%**
- Number of tokens contributing: 20 of 23

The top-3 token concentration at 69% exceeds the pre-registered flag threshold of 50%. This is a concentration artifact, not a diversified edge.

---

## 6. Subperiod Stability

| Structure | SP1 (Mar–Oct 2024) | SP2 (Nov 2024–Jun 2025) | SP3 (Jul 2025–Mar 2026) |
|---|---|---|---|
| S1 mean | +1.34% | +0.47% | +1.83% |
| S2 mean | **-3.90%** | +3.33% | +5.08% |
| S3 mean | +3.22% | +6.54% | +4.26% |

S3 is positive in all 3 subperiods. S2 is negative in SP1. S1 is positive in all 3 but the absolute values are small. The subperiod stability of S3 looks superficially encouraging, but SP2 contains the February 2025 cluster event that dominates the result.

---

## 7. Listing Selection Bias Assessment

The shortable universe (tokens available on OKX/CEX perps) is systematically biased toward **larger, more liquid, more established tokens** compared to the full Solana token universe. Tokens that are shortable on CEX perps have survived long enough to achieve significant market cap and liquidity — they are the survivors, not the typical Solana token.

This means the toxic-state short strategy on shortable tokens is testing a different population than the full Solana meme token universe. The tokens that are most likely to go to zero (the true toxic state) are precisely the ones that are NOT shortable on CEX perps. The shortable universe is the "quality tier" of Solana tokens, which means:

1. They are more likely to recover from toxic states (bounce, not die)
2. They have more institutional participation that can squeeze shorts
3. Their toxic states are more likely to be temporary corrections than terminal declines

**This is a structural problem with the T1 design, not a data issue.** The hypothesis that toxic states predict further decline is most plausible for low-quality tokens, but those tokens are not shortable. The shortable tokens are the ones where the hypothesis is least likely to hold.

---

## 8. Adversarial Assessment

**Why S3 looks like a pass but is not:**

The S3 result is driven by a 25% TP target with a 30-day max hold. In a bear market (SOL -52% over the test period), any short strategy with a wide enough TP will eventually hit it. The question is whether the toxic-state filter adds value beyond simply being short. The advantage over random is 3.84pp — barely above the 3pp threshold — and is entirely explained by the February 2025 cluster event.

**The random benchmark is also negative in expectation** (mean +1.29% at conservative cost, but median -15.62%). This means the entire universe of short trades is marginally positive in mean but deeply negative in median — a sign that the bear market created a few large winners (tokens that crashed hard) and many losers (tokens that bounced). The toxic-state filter slightly improves the hit rate on the winners, but not by enough to be reliable.

**The 41-trade sample is too small.** With 41 trades and high variance (individual returns ranging from -16% to +24%), the standard error of the mean is approximately 4-5%. The observed advantage of 3.84pp is within one standard error of zero. This result is statistically indistinguishable from noise.

**The correct interpretation:** T1 found a weak, noise-level signal that toxic states slightly increase the probability of a continued decline in the shortable Solana token universe. This signal is not robust enough to trade, is contaminated by a single cluster event, relies on a bear market regime, and suffers from listing selection bias that makes the hypothesis less plausible for the exact tokens being tested.

---

## 9. Pass/Fail Summary

| Criterion | Threshold | S1 | S2 | S3 |
|---|---|---|---|---|
| Mean > 0 (conservative) | > 0% | +1.17% ✓ | +3.22% ✓ | +5.13% ✓ |
| Advantage over random | ≥ 3pp | 1.27pp ✗ | 2.78pp ✗ | 3.84pp ✓ |
| Subperiod stability | ≥ 2/3 positive | 3/3 ✓ | 2/3 ✓ | 3/3 ✓ |
| Survives 10% funding | mean > 0 | +1.43% ✓ | +3.46% ✓ | +5.36% ✓ |
| Median > 0 | > 0% | -10.62% ✗ | -0.65% ✗ | +24.02% ✓ |
| **Overall** | ≥ 2/3 pass | **FAIL** | **FAIL** | **PASS** |

**Overall: FAIL (1/3 structures pass)**

---

## 10. What T1 Actually Tells Us

T1 is more informative in what it reveals about the structure of the problem than in what it says about the strategy:

**Finding 1: Toxic states are rare in the shortable universe.** Only 41 strict toxic entries over 24 months across 23 tokens. The shortable tokens are too liquid and too institutionally traded to spend much time in "all 4 conditions met" territory.

**Finding 2: The shortable universe is the wrong universe for this hypothesis.** The tokens most likely to continue declining after a toxic state are the ones that cannot be shorted on CEX perps. The shortable tokens are the survivors.

**Finding 3: Single-event concentration is a structural risk.** The February 2025 cluster event (TRUMP/MELANIA contagion) generated 7 simultaneous TP hits. Any strategy that depends on such events for its positive expectation is not a reliable book — it is a lottery ticket on macro contagion events.

**Finding 4: Bear market beta explains most of the result.** SOL -52% over the test period means any short strategy with a wide enough target will show positive mean returns. This is not alpha; it is beta in the right direction.

---

## 11. Verdict and Next Steps

**T1 VERDICT: FAIL**

The toxic-state short strategy does not produce a robust, reliable edge in the shortable Solana perps universe. The single passing structure (S3) is contaminated by a cluster event, has insufficient sample size, and is likely explained by bear market beta rather than genuine signal.

**What this does NOT mean:**
- It does not mean toxic states are useless as a concept
- It does not mean shorting Solana tokens is impossible
- It does not mean the hypothesis is wrong for the unshortable universe

**What this DOES mean:**
- The specific test (shortable CEX perps, strict toxic state, monthly reconstitution) does not produce a tradeable edge
- The listing selection bias is a fundamental problem that cannot be fixed with more data
- The sample size (41 trades) is too small to draw reliable conclusions even if the direction were correct

**Recommended next step:** Do not proceed to a live pilot of T1. The structural problems (listing selection bias, small sample, cluster event contamination) are not fixable with more data or parameter tuning. The hypothesis needs to be reformulated for a different universe or a different mechanism.

**T3 (Stablecoin Basis / Delta-Neutral Carry Pilot) remains the next candidate** per the pre-registered test queue.

---

*Design: t1_design_v1.md | Data: Yahoo Finance + OKX | Commit: pending*
