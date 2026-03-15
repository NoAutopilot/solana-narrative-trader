# External Feedback → Recommendation

**Program:** external_feedback_to_tests_map
**Date:** 2026-03-15
**Author:** Manus AI

---

## The Recommendation

**Run T2 (Actuarial / Casino-Math Book Test) now. Archive T1 and T3 until T2 is resolved.**

---

## Which Test Is Next

**T2 — Actuarial / Casino-Math Book Test.**

Run this test first. The question is: does the empirical payoff distribution of mechanical entries and exits across a large, non-selected Solana token universe — using a simple quality filter and fixed asymmetric exit rules — produce positive expected value after realistic transaction costs?

This is the only candidate test that is genuinely orthogonal to every prior closed line. It does not ask whether any token can be predicted to go up. It asks whether the aggregate distribution of outcomes, without prediction, has the right shape to support a mechanical book. This question has never been asked in the prior program history. It cannot fail for the same reasons the prior programs failed, because it does not depend on a predictive signal.

The test requires no new infrastructure. The data is largely already available. The analysis is a distribution study, not a signal search. The self-deception risk is low because there is no prediction to overfit. The time to verdict is 1-3 weeks. If the result is positive, it is directly actionable as a mechanical book. If the result is negative, the line is closed cleanly with a specific, falsifiable reason.

---

## Which Two Are Backups

**Backup 1 — T1 (Shortable Toxic-State Pilot).** Archive until T2 is resolved. If T2 passes, T1 becomes a potential enhancement (the toxic-state signal could be used to size the book asymmetrically). If T2 fails, T1 becomes the next test: it asks a different question (inversion of prior signal work) and requires different data (perps funding rates).

**Backup 2 — T3 (Stablecoin Basis / Delta-Neutral Carry Pilot).** Archive until T1 is resolved. The delta-neutral compression data from the Yield Surface Stage A makes a positive result unlikely, but the test is cheap and fast enough to run if T1 also fails. The specific question — is there a Solana-native basis structure that survives friction? — has not been answered with granular Solana perps data.

---

## What Not to Do

**Do not run T4 (Liquidation Hunting) unless T1 and T2 both fail.** The expected answer is NO. Liquidation events on Solana are resolved in sub-second timeframes by bots with co-location and Jito bundle access. A feasibility test will likely confirm this in 1-2 weeks, but it is not worth running before the higher-probability tests.

**Do not run T5 (MEV / Instruction-Level Extraction) at all.** This requires infrastructure the user has explicitly ruled out. The edge is real but the cost to access it is prohibitive given the stated constraints.

**Do not run any variant of the following:**
- New momentum or reversion signal search
- New feature-family sweep
- LP timing or threshold optimization
- Wallet graph or behavioral prediction
- Generic "try another chain" exploration
- Business-model pivot to consulting or products (this is a different kind of decision, not a test)

These are all variants of the closed question: "Can public-data predictive selection find a directional edge?" The answer is no. Running another variant of this question wastes time and risks the specific failure mode the user identified: research drift.

---

## Why T2 Is the Least Likely to Waste More Time

T2 is the least likely to waste time for three specific reasons.

**First, it cannot fail for the same reasons as prior programs.** Every prior closure was a failure of predictive signal work. T2 has no predictive signal. It cannot fail because the signal decays, because the feature family is not informative, or because the edge is too small after friction. It can only fail if the empirical distribution does not have the right shape — which is a clean, falsifiable result.

**Second, the data is already largely available.** The quality filter logic, the token universe data, and the historical price data are all products of prior work. The new data requirement (broader mid-cap universe) is a data pull, not an infrastructure build. The test can be set up and run in days, not weeks.

**Third, a positive result is directly actionable.** If the distribution supports positive EV under a mechanical book, the next step is a paper trading period to validate the distribution estimate out-of-sample. There is no ambiguity about what to do with a positive result. This is not true of T1 (a positive result requires a shortable universe large enough to size) or T3 (a positive result requires a carry that is large enough to justify the operational complexity).

---

## The Adversarial Check

Before finalizing this recommendation, apply the hard rule from the brief: does T2 change the question materially from "Can public-data predictive selection find a directional edge on Solana?"

**Yes.** T2 asks: "Does the empirical payoff distribution of mechanical exits across a non-selected universe support positive EV?" This is a distributional question, not a predictive question. It does not require selecting tokens that will outperform. It requires only that the aggregate distribution has positive mean under asymmetric exit rules. The mechanism is actuarial, not predictive. The question is materially different.

T1 also passes this check: it asks whether an existing negative signal is usable as a short entry trigger, which is an inversion question, not a new predictive search.

T3 passes this check: it asks whether a specific structural carry trade is viable after frictions, which is a carry question, not a directional prediction.

All three top candidates change the question materially. None of them are variants of the closed question.

---

## Final Summary

| Item | Answer |
|------|--------|
| Next test | T2 — Actuarial / Casino-Math Book Test |
| Backup 1 | T1 — Shortable Toxic-State Pilot |
| Backup 2 | T3 — Stablecoin Basis / Delta-Neutral Carry Pilot |
| Do not do | T4 before T1/T2 resolved; T5 ever; any momentum/feature/LP/wallet variant |
| Why T2 first | Only test orthogonal to all prior failures; no prediction; data largely available; 1-3 week verdict; directly actionable if positive |
| Expected T2 outcome | Unknown — genuinely untested question. If Solana token distribution has fat upside tails under asymmetric exits, positive. If distribution is symmetric or left-skewed, negative. |
| If T2 is positive | Run paper trading period; then size a small mechanical book |
| If T2 is negative | Run T1 immediately; T3 is low-probability backup |
