# ADVERSARIAL REVIEW — Full Reasoning Chain (Sessions 1-8)

Applied: OPERATING_PRINCIPLES.md checklist
Date: 2026-02-23
Method: Every claim extracted from the reasoning chain, tested against the adversarial checklist

---

## SECTION 1: CLAIM-BY-CLAIM SCORECARD

| Claim | Verdict | Confidence |
|---|---|---|
| Paper trading is profitable (+73 SOL) | TRUE for n=4 moonshots, unproven generally | LOW |
| 91% of profit is 1 trade (Trump Mobile) | TRUE — verified in cycling model | HIGH |
| Remove top 5 → still positive (+0.46 SOL) | TRUE — but razor-thin, within noise | MEDIUM |
| Remove top 10 → negative | TRUE — system loses money | HIGH |
| All 4 moonshots closed within 5 min | TRUE for n=4, unproven as universal law | LOW |
| Big winners (50-180%, n=38) median 2.6 min | TRUE — broader sample supports pattern | MEDIUM |
| 99% of profit from trades closing <5 min | TRUE — verified against raw data | HIGH |
| 5-min timeout costs nothing (+0.0006 SOL lost) | TRUE — verified | HIGH |
| 5-min timeout reduces capital ~2 SOL → ~0.92 SOL | TRUE — P95 concurrent positions verified | HIGH |
| Throttling at 80+ concurrent (49% of runtime) | TRUE — entry gap 15s → 398s verified | HIGH |
| 5-min timeout eliminates throttling → +45% trades | PROJECTED — not yet observed post-change | MEDIUM |
| +7.8 SOL projection at 0.10 SOL/trade | OVERSTATED — slippage nonlinear, acknowledged | LOW |
| Realistic projection is 40-60% of +7.8 SOL | SPECULATIVE — no live data at 0.10 size | LOW |
| Break-even at 3.24x (224% gain) | TRUE — arithmetic verified | HIGH |
| 4.0% of trades exceed 3.24x threshold | TRUE for current dataset (17h) | MEDIUM |
| Base trades (no moonshots) are -1.54 SOL net | TRUE — verified | HIGH |
| Capturing 10% post-migration gains → +32.22 SOL | PROJECTED — holding through migration unproven | LOW |
| TP at 30% doesn't cap moonshots | CONTRADICTED ITSELF — see Section 2 | LOW |
| Moonshots exited at +1,915% not 30% | UNCLEAR — reasoning chain contradicts itself | LOW |
| No strong differentiating signal for moonshots | TRUE — uniform across modes/categories | HIGH |
| Moonshots look like every other trade at entry | TRUE — 4.7% rate uniform across all signals | HIGH |
| Conviction filter misses 60% of moonshots | TRUE — 56 of 92 moonshots filtered out | HIGH |
| Conviction filter is "actively counterproductive" | TRUE — control captures 40% of moonshots | HIGH |
| Narrative matching adds edge (p=0.09) | NOT PROVEN — fails significance threshold | HIGH |
| Win rate is 15% regardless of filter | TRUE — consistent across all modes | HIGH |
| Live PnL% matches paper PnL% (131/131) | TRUE — verified on-chain | HIGH |
| Post-migration sells work (5/5) | TRUE — verified on-chain | MEDIUM (n=5) |
| On-chain sell recovery 96.8% of buy cost | TRUE — 187 sells verified | HIGH |
| TX fees negligible (0.13% of avg buy) | TRUE — verified | HIGH |
| System runs 114 trades/hour | TRUE — mechanically verified | HIGH |
| 4.6% moonshot rate persists across days | UNTESTED — only 17h of data | NONE |
| Market regime independence | UNTESTED — single day | NONE |
| Can hold through migration and sell at peak | UNTESTED — production flow unproven | NONE |

---

## SECTION 2: INTERNAL CONTRADICTIONS FOUND

**Contradiction 1: TP cap and moonshot exit price**

The reasoning chain says three different things:

> "The moonshots actually DID exit at +1,915% and +1,788%, not at 30%"

Then:

> "The moonshots hit the 30% TP and closed. They didn't ride to 1,900%"

Then:

> "Wait, that contradicts the data… let me re-check"

This was never resolved in the text. The TP fires at 30% but the *recorded PnL* reflects the price at the 10-second check interval, which may be far above 30%. The system exits at whatever price exists when the check fires, not at exactly 30%. This matters because it means the TP is not a precision tool — it's a "somewhere above 30%" exit, and the actual capture depends on price velocity and check frequency.

**Verdict:** The claim "TP doesn't cap moonshots" is PARTIALLY TRUE — it doesn't cap them at 30%, but it does exit them at whatever the 10-second check sees. If the price peaks at 1,900% and the check fires at 1,200%, you captured 1,200%, not 1,900%. The system is check-frequency-dependent, not TP-dependent.

**Contradiction 2: "Strategy B is the right approach" vs. North Star Metric**

The reasoning chain concludes:

> "The system's edge is in taking every trade, losing small on the 85% that fail"

But the North Star Metric says:

> "Consistent profitability WITHOUT relying on outlier moonshots. The base case must at least break even."

Strategy B (take every trade, let outliers carry) is the *opposite* of the North Star Metric. The base case is -1.54 SOL. The strategy explicitly relies on outliers. Either the strategy or the North Star Metric is wrong — they can't both be right.

**Verdict:** The reasoning chain abandoned its own success criteria without acknowledging it. If Strategy B is correct, the North Star Metric needs to be rewritten to: "Positive expected value per trade including moonshot probability." If the North Star Metric is correct, Strategy B fails.

---

## SECTION 3: ADVERSARIAL CHECKLIST RESULTS

| Checklist Item | Result | Detail |
|---|---|---|
| Outlier test: remove top 1, 3, 5 | FAIL | Top 1 = 91% of PnL. Top 5 removed → barely positive. Top 10 → negative. |
| Time-window test: holds across 4h blocks? | UNTESTED | Only 17h of data, single market session. Cannot test. |
| Selectivity test: what % filtered? | FAIL | System trades everything. No meaningful filter. "A coin flip is not a strategy." |
| Coverage test: metric covers >90% of trades? | PASS | PnL data covers all 280 trades. |
| Fee test: positive after realistic fees? | MARGINAL | Adjusted PnL +73.11 SOL (but 91% is one trade). Without top 5: ~breakeven. |
| Sample size: n>100 per group? | PARTIAL | Total trades >100. Moonshots n=4. Political n=28. Key subgroups too small. |
| Multi-test agreement? | FAIL | Chi-squared p=0.09, Welch's p=0.52, Mann-Whitney p=0.79. Tests disagree. Most conservative says no signal. |
| Simulation-reality gap <2x? | FAIL | Paper: +73 SOL. Live on-chain: -0.29 SOL. Gap is 250x. |
| On-chain verification? | PARTIAL | 187 sells verified. But paper moonshot profits not replicated on-chain. |
| Falsification condition stated? | PARTIAL | Some claims have conditions. "Strategy is profitable" does not. |
| Base rate comparison? | FAIL | Control group moonshot rate (4.5%) ≈ Narrative rate (3.9%). No better than random. |

**Checklist score: 2 PASS, 3 PARTIAL, 6 FAIL out of 11 items.**

Per OPERATING_PRINCIPLES: *"No claim survives without it."*

---

## SECTION 4: THE REASONING FLAW

The chain made one critical logical error that cascaded through everything:

**Infrastructure improvement ≠ Strategy validation**

The 5-minute timeout is genuinely better infrastructure. It reduces capital, eliminates throttling, costs nothing. All verified.

But "the machine runs more efficiently" does not mean "the machine makes money." A more efficient lottery ticket machine still runs a lottery.

The chain moved from:
1. "Timeout optimization is valid" (TRUE)
2. "More trades = more moonshot chances" (TRUE in theory)
3. "Therefore deploy 0.5-1 SOL" (DOES NOT FOLLOW)

Step 3 requires proving that the moonshot rate (4.6%) persists, that moonshots can be captured on-chain at paper prices, and that the base case at least breaks even. None of these are proven.

---

## SECTION 5: WHAT'S ACTUALLY REAL

These survive the full adversarial checklist:

1. **Infrastructure works** — paper trader detects, enters, exits, logs. Mechanically sound. (HIGH)
2. **On-chain sells return SOL** — 96.8% recovery across 187 sells. Not 0%. (HIGH)
3. **Post-migration selling works** — 5/5 PumpSwap sells. (MEDIUM, n=5)
4. **5-min timeout is strictly better** — same PnL, less capital, no throttling. (HIGH)
5. **Power-law distribution is real** — tiny fraction of trades generate all profit. (HIGH)
6. **No entry signal predicts moonshots** — uniform across all modes. (HIGH)
7. **TX fees are negligible** — 0.13% of avg buy. (HIGH)

---

## SECTION 6: WHAT'S NOT REAL

These fail the adversarial checklist:

1. **"We have a profitable strategy"** — Lottery ticket. Fails outlier test.
2. **"Narrative matching adds value"** — p=0.09 at best. Control performs equally.
3. **"+7.8 SOL projection"** — Overstated. Nonlinear slippage. Paper-only.
4. **"0.5 SOL cycling would be profitable"** — 91% one trade. Fails outlier test.
5. **"Moonshot rate will persist"** — 17h of data. Untested across days.
6. **"We can capture moonshots on-chain at paper prices"** — 250x gap between paper and live.

---

## SECTION 7: RECOMMENDED PATH

| Action | Risk | Rationale |
|---|---|---|
| Let VPS run 7+ days, collect data | ZERO | Need multi-day moonshot rate before any conclusion |
| Re-run full adversarial checklist on 7-day data | ZERO | Time-window test becomes possible |
| If base case (ex-top-5) positive over 7 days → micro-live 0.01 SOL | LOW | Tests execution, not profitability |
| If micro-live matches paper within 2x → consider 0.04 SOL | LOW | Closes the simulation-reality gap |
| Rewrite North Star Metric if Strategy B is the path | ZERO | Current metric contradicts chosen strategy |
| Do NOT deploy 0.5-1 SOL based on current data | — | Fails 6 of 11 adversarial checklist items |
