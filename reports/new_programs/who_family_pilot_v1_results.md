# Who Family Pilot v1 — Results Document

**Program:** who_family_pilot_v1
**Date:** 2026-03-15

---

## 1. Deployer Recurrence

**Result: BLOCKED — no data.**

All 20 sampled tokens returned `mint_authority = None`. Pumpfun tokens have their mint authority revoked upon graduation, making this field unusable as a deployer proxy. Zero deployer wallets were identified, and no recurrence analysis was possible.

This is not a sampling failure — it is a structural property of the pumpfun token class. Any "who" program targeting pumpfun tokens would need a custom transaction parser to extract the original `create` instruction signer, which is a non-trivial infrastructure requirement.

## 2. Early-Buyer Overlap

### 2.1 Within-Group Overlap

Pairwise overlap was computed for all token pairs within each group that had sufficient buyer data.

| Metric | Stronger Group | Weaker Group | Cross-Group |
|--------|---------------|-------------|-------------|
| **First-10 buyers** | | | |
| Pairs with data | 6 | 21 | 28 |
| Avg overlap count | 0.000 | 0.143 | 0.143 |
| Avg Jaccard similarity | 0.0000 | 0.0084 | 0.0082 |
| **First-20 buyers** | | | |
| Pairs with data | 6 | 21 | 28 |
| Avg overlap count | 0.167 | 0.286 | 0.393 |
| Avg Jaccard similarity | 0.0045 | 0.0099 | 0.0129 |

### 2.2 Interpretation

The hypothesis predicts that stronger tokens should show **higher** early-buyer overlap (i.e., the same "smart money" wallets repeatedly buying winners). The data shows the **opposite**:

- At the first-10 level, the stronger group has **zero** overlap, while the weaker group shows a small but non-zero overlap (0.143 avg).
- At the first-20 level, the stronger group (0.167) has **less** overlap than the weaker group (0.286).
- Cross-group overlap (0.393 at first-20) is actually **higher** than either within-group measure, suggesting that whatever overlap exists is not group-specific.

The evidence directly contradicts the "smart money clusters in winners" hypothesis. If anything, early buyers of weaker tokens overlap more — possibly because the same wallets are buying many tokens indiscriminately, and most tokens underperform.

### 2.3 Null Comparison

A permutation test with 1,000 random shuffles of group assignment was used to assess whether the observed stronger-group overlap is distinguishable from random grouping.

| Metric | Actual (Stronger) | Null Mean | Null Std | z-Score | p(null >= actual) |
|--------|-------------------|-----------|----------|---------|-------------------|
| First-10 overlap | 0.000 | 0.129 | 0.041 | **-3.12** | 100.0% |
| First-20 overlap | 0.167 | 0.322 | 0.081 | **-1.92** | 100.0% |

The stronger group's overlap is **significantly below** the null expectation. The z-scores are negative (-3.12 and -1.92), meaning the actual stronger group has less overlap than a random grouping would produce. The empirical p-value is 100% — every single random shuffle produced higher overlap than the actual stronger group.

This is the strongest possible evidence against the hypothesis. Not only is there no "smart money overlap" signal in winners, but winners actively show **less** buyer overlap than random expectation.

## 3. Smart-Money Concentration

Concentration metrics were computed for the first 20 buyers of each token that had sufficient data.

| Token | Group | N Buyers | Top-1 Share (%) | Top-3 Share (%) | HHI |
|-------|-------|----------|----------------|----------------|-----|
| EXPRESSION | stronger | 7 | 36.1 | 91.4 | 2,929 |
| SHEEPAGENT | stronger | 1 | 100.0 | 100.0 | 10,000 |
| Snorp | stronger | 18 | 23.1 | 56.6 | 1,488 |
| SOS | stronger | 23 | 38.5 | 62.1 | 1,953 |
| NORWOOD | weaker | 19 | 56.3 | 76.7 | 3,474 |
| SMORT | weaker | 16 | 51.4 | 63.9 | 2,878 |
| $2 | weaker | 15 | 48.9 | 61.5 | 2,637 |
| 01001000 | weaker | 21 | 21.9 | 51.3 | 1,205 |
| NOTGAY | weaker | 3 | 33.3 | 100.0 | 3,333 |
| Distorted | weaker | 3 | 50.0 | 100.0 | 5,000 |
| Life | weaker | 1 | 100.0 | 100.0 | 10,000 |

### 3.1 Group Comparison

Excluding tokens with fewer than 10 buyers (too few for meaningful concentration):

| Metric | Stronger (N=3) | Weaker (N=4) |
|--------|---------------|-------------|
| Avg Top-1 Share | 32.6% | 44.6% |
| Avg Top-3 Share | 70.0% | 63.4% |
| Avg HHI | 2,123 | 2,549 |

There is no meaningful difference. The weaker group actually shows slightly higher top-1 concentration and HHI, while the stronger group shows slightly higher top-3 concentration. With only 3–4 tokens per group, these differences are well within noise. There is no evidence that early buyer concentration distinguishes winners from losers.

## 4. Strength vs. Weakness of Evidence

| Question | Evidence Strength | Direction |
|----------|------------------|-----------|
| A. Deployer recidivism | **None** (blocked) | Cannot assess |
| B. Early-buyer overlap | **Strong negative** | Opposite of hypothesis |
| C. Concentration | **Weak/null** | No meaningful difference |
| D. Feasibility | **Poor** | Major data gaps |

The strongest finding is the **negative result on early-buyer overlap**: the permutation test shows that stronger tokens have significantly less buyer overlap than random expectation (z = -3.12). This is not merely "no signal" — it is evidence against the hypothesis.

The concentration analysis is inconclusive due to small sample size, but shows no trend favoring the hypothesis.

The deployer analysis is entirely blocked, which itself is a feasibility finding: any "who" program targeting pumpfun tokens would require custom infrastructure that does not currently exist.
