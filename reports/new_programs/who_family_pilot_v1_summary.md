# Who Family Pilot v1 — Summary

**Program:** who_family_pilot_v1
**Date:** 2026-03-15

---

## Question

Is there any real evidence that "who launched / who bought early" contains more signal than the price/feature families that already failed?

## Answer

**No.** The pilot found no evidence supporting the wallet-based signal hypothesis, and the strongest statistical test produced evidence **against** it.

## Key Findings

**Deployer recidivism** could not be assessed. All 20 sampled pumpfun tokens have their mint authority revoked, making deployer identification impossible via standard RPC. A custom transaction parser would be required — a non-trivial infrastructure investment with no prior evidence that the signal exists.

**Early-buyer overlap** was tested with a permutation-based null comparison. The stronger-performing tokens showed **zero** overlap among their first 10 buyers, compared to a null expectation of 0.129 (z = -3.12, p = 100%). This means winners' early buyers are **less** connected than random — the opposite of the "smart money clusters in winners" hypothesis. The weaker group actually showed more overlap, consistent with indiscriminate buying across many tokens that mostly fail.

**Concentration metrics** showed no meaningful difference between stronger and weaker groups. Average HHI was 2,123 for stronger tokens and 2,549 for weaker tokens (with only 3–4 tokens per group having sufficient data). There is no basis for claiming that early buyer concentration predicts performance.

**Data feasibility** is poor. Only 11 of 20 tokens yielded any early buyer data, and the extraction was severely asymmetric between groups (4/10 stronger vs 7/10 weaker). The Helius Enhanced API misses many early pumpfun transactions (bonding curve buys, migration swaps). Building a reliable "who" pipeline would require custom indexing infrastructure.

## Comparison to Prior Programs

The hard kill rule requires that this family show a "materially stronger reason to continue" than momentum/reversion, feature acquisition v2, or large-cap swing Stage A. It does not. In fact, this pilot produced the clearest negative result of any program to date: a z-score of -3.12 against the primary hypothesis, combined with a fundamental data blocker on the deployer question.

| Program | Best Signal Found | Verdict |
|---------|------------------|---------|
| Momentum/Reversion | Weak, noisy, cost-dominated | NO-GO |
| Feature Acquisition v2 | 0/210 passed discovery | NO-GO |
| Large-Cap Swing Stage A | Negative EV before costs | NO-GO |
| **Who Family Pilot v1** | **Anti-signal (z = -3.12)** | **NO-GO** |

## Verdict

### NO-GO

The wallet/deployer/early-buyer signal family does not warrant a full research program. The pilot found:

1. Zero deployer data (structural blocker for pumpfun tokens)
2. Anti-signal on early-buyer overlap (z = -3.12 against hypothesis)
3. No concentration difference between winners and losers
4. Poor data feasibility requiring custom infrastructure with no evidence of payoff

This line is closed. No further investigation is recommended.
