# Adversarial Review: "Did We Have a Profitable Strategy to Test?"

> Applying OPERATING_PRINCIPLES.md to the full reasoning chain from Sessions 1-8.
> Date: 2026-02-23

---

## THE CLAIM CHAIN (reconstructed from context)

The reasoning that led us to believe we had a profitable strategy went roughly:

1. **Paper trading shows +73 SOL profit** over ~280 trades
2. **Winners exit fast** — all 4 moonshots closed within 5 minutes
3. **Timeout optimization** — cutting from 15→5 min reduces capital needed from ~2 SOL to ~1 SOL
4. **Throttling elimination** — 5-min timeout prevents the 80+ concurrent position bottleneck, enabling ~45% more trades
5. **Force-closing at 5 min costs nothing** — trades between 5-15 min total +0.0006 SOL
6. **On-chain sells work** — 97% of sells return SOL, avg recovery 96.8%
7. **Post-migration selling proven** — 5/5 PumpSwap sells successful
8. **Therefore:** deploy 0.5-1 SOL, cycle through trades with 5-min timeout, let moonshots carry the portfolio

---

## PRINCIPLE-BY-PRINCIPLE AUDIT

### PRINCIPLE 1: TRUST NOTHING, PROVE EVERYTHING

**Outlier removal test (MANDATORY per principles):**

| Scenario | PnL | Verdict |
|---|---|---|
| All 280 trades | +73.89 SOL | Looks amazing |
| Remove top 1 trade | +6.49 SOL | 91% of profit was ONE trade |
| Remove top 3 trades | +1.82 SOL | Barely positive |
| Remove top 5 trades | +0.46 SOL | Razor-thin, within noise |
| Remove top 10 trades | Negative | System loses money |

**VERDICT: FAIL.** The system does not survive the outlier test. Per Principle 1: *"If the result flips sign, you don't have an edge — you have a lottery ticket."* This is a lottery ticket.

**Statistical significance:**
- Narrative vs. Control: p=0.09 (NOT significant)
- Bootstrap: P(narrative PnL > control PnL) = 83.2% (NOT conclusive)
- Win rate: 17-18% across all modes — no meaningful differentiation

**VERDICT: FAIL.** Per Principle 1: *"Never label a finding as HIGH confidence unless it survives outlier removal, passes p<0.05, AND holds across multiple time windows."* Zero findings meet this bar.

---

### PRINCIPLE 2: SCIENTIFIC DATA COLLECTION

**Sample size:**
- Moonshots: n=4. Per Principle 2: *"Don't celebrate <50 samples."*
- Political category edge: n=28. Need 75+.
- Total runtime: ~24 hours across multiple DB resets. Per Principle 2: *"Don't draw conclusions from <100 trades per group."*

**Control group comparison:**
- The screenshots show: Control 4.5% moonshot rate, Proactive 5.8%, Narrative 3.9%
- **Narrative has the LOWEST moonshot rate.** The thing we built the system around performs worst.

**VERDICT: FAIL.** Insufficient sample sizes, and the control group outperforms narrative on the metric that matters most (moonshot capture).

---

### PRINCIPLE 3: ADVERSARIAL SELF-EVALUATION

The Session 7 adversarial audit was good — it correctly identified:
- Capital needed was understated (0.33 → 0.92 SOL)
- +7.8 SOL projection was overstated (slippage nonlinear)
- n=4 moonshots is not statistically significant

But it then proceeded to recommend deployment anyway, framing it as "low risk." This violates the spirit of Principle 3: *"When presenting results, lead with what CONTRADICTS the thesis."*

**What contradicts the thesis (from the screenshots):**
- "No strong differentiating signal exists" for moonshot prediction
- Moonshots look like every other trade at entry
- 4.7% moonshot rate is uniform across modes, categories, signal types
- The conviction filter is "actively counterproductive"
- "+7.8 SOL projection — OVERSTATED"
- "Profitability depends on rare events — 4 moonshots are 47% of total PnL"

**VERDICT: MIXED.** The adversarial audit was honest about the weaknesses but the conclusion ("deploy anyway") doesn't follow from the evidence.

---

### PRINCIPLE 7: FEES ARE THE ENEMY

**From Session 8 validation:**
- Per-trade friction: 0.00262 SOL (6.6% of a 0.04 SOL trade)
- Total friction across 268 trades: -0.70 SOL
- On-chain avg sell recovery: 96.8% (better than feared)

**But the critical number from the screenshots:**
- Break-even requires 3.24x (224% gain)
- Only 4.0% of trades exceed this threshold
- Below 3.24x, the system loses money

**VERDICT: PARTIALLY PASSES.** Fees are lower than initially feared (96.8% recovery, not 100% loss). But the break-even threshold (3.24x) means the system is profitable ONLY if moonshots occur at >4% rate AND are captured. This is unproven over multiple days.

---

### PRINCIPLE 8: NO THEATRE

**The simulation-reality gap:**
- Paper PnL: +73.89 SOL
- Live PnL (on-chain): -0.291 SOL (Session 7 corrected)
- Gap: paper says +73, reality says -0.29

Per Principle 8: *"If paper says +336 SOL and live says -0.10 SOL, the system is not 'almost profitable' — it's broken."*

**Why the gap exists:**
- Paper trades at 0.04 SOL each, live trades at variable sizes
- Paper captures moonshots at peak price, live may not hold through migration
- Paper has no failed TXs, live has some

**VERDICT: FAIL.** The gap between paper and live is enormous. Paper profitability is not evidence of real profitability.

---

### NORTH STAR METRIC CHECK

From RESEARCH_TRACKER.md:
> **NORTH STAR METRIC: Consistent profitability WITHOUT relying on outlier moonshots. The base case (non-moonshot trades) must at least break even.**

**Does the base case break even?**
- Remove moonshots: system is net negative
- Remove top 5: +0.46 SOL (barely positive, within noise)
- Remove top 10: negative

**VERDICT: FAIL.** The north star metric is explicitly NOT met. The base case does not break even.

---

## THE HONEST SCORECARD

| Claim | Status | Confidence |
|---|---|---|
| Paper trading is profitable | TRUE — but 91% from 1 trade | LOW |
| Winners exit fast (<5 min) | TRUE for n=4 moonshots | LOW (n=4) |
| 5-min timeout reduces capital needed | TRUE | HIGH |
| 5-min timeout eliminates throttling | TRUE | HIGH |
| Narrative matching adds edge | NOT PROVEN (p=0.09) | LOW |
| Moonshots can be predicted at entry | DISPROVEN — "look like every other trade" | HIGH |
| Post-migration selling works | PROVEN on-chain (5/5) | MEDIUM (n=5) |
| On-chain sells recover ~97% of cost | PROVEN (n=187) | HIGH |
| System is profitable net of fees | NOT PROVEN — depends on moonshot rate | LOW |
| Base case breaks even | DISPROVEN — net negative without outliers | HIGH |
| Strategy works across multiple days | UNTESTED — only ~24h of data | NONE |

---

## WHAT WAS ACTUALLY PROVEN (things we can trust)

1. **The infrastructure works.** Paper trader runs, detects tokens, enters/exits trades, logs everything. Mechanically sound.
2. **On-chain execution works.** Sells return SOL. Post-migration sells work. TX fees are negligible.
3. **The timeout optimization is valid.** 5-min timeout is strictly better than 15-min: same PnL, less capital, no throttling.
4. **Power-law distribution is real.** A tiny fraction of trades generate all the profit. This is consistent with pump.fun research.
5. **The bonding curve is not a wall.** Post-migration selling proven.

## WHAT WAS NOT PROVEN (things we believed but shouldn't have)

1. **"We have a profitable strategy."** We have a lottery ticket machine. The expected value depends entirely on moonshot frequency, which we have ~24 hours of data on.
2. **"Narrative matching adds value."** p=0.09 is not significant. Control group has similar or better moonshot rates.
3. **"0.5 SOL cycling would be profitable."** The cycling model shows +73 SOL but that's 91% one trade. Remove it and you're near zero or negative.
4. **"We can predict which tokens will moon."** The screenshots explicitly say "no strong differentiating signal exists" and "moonshots look like every other trade at entry."
5. **"+7.8 SOL projection."** Acknowledged as overstated in the adversarial audit but still used as motivation.

---

## THE UNCOMFORTABLE TRUTH

The reasoning chain had a subtle but critical flaw: **it conflated infrastructure improvements with strategy validation.**

- "5-min timeout is better" → TRUE (infrastructure improvement)
- "Therefore the strategy is profitable" → DOES NOT FOLLOW

The timeout change makes the system more *efficient* at running a lottery. It doesn't make the lottery profitable. The profitability question was never answered — it was assumed based on paper PnL that is 91% one trade.

**The question we should have been asking:**
> "If we run this system for 30 days, will it make money NET of everything?"

**The honest answer:** We don't know. We have 24 hours of data, 4 moonshots, and a north star metric that is explicitly not met.

---

## WHAT SHOULD WE DO NOW?

**Option A: Keep collecting data (RECOMMENDED)**
- The VPS is running. Let it accumulate 7+ days of data.
- After 7 days, re-run the outlier test, time-window test, and fee test.
- If the base case (excluding top 5 trades) is positive over 7 days, THEN consider live deployment.

**Option B: Micro-test with 0.01 SOL/trade**
- If you want to test live execution, use the absolute minimum: 0.01 SOL/trade.
- This tests the execution pipeline without meaningful capital risk.
- But don't confuse "testing execution" with "testing profitability."

**Option C: Pivot the hypothesis**
- The data says narrative matching doesn't add edge. The moonshot rate is uniform.
- Maybe the edge isn't in *selection* but in *execution speed* — being first to buy a token that's about to moon.
- Or maybe there's no edge at all, and pump.fun is a negative-sum game for automated traders.

**What NOT to do:**
- Deploy 0.5-1 SOL based on 24 hours of data and 4 moonshots
- Assume paper PnL translates to live PnL (the gap is 250x)
- Treat infrastructure improvements as strategy validation
