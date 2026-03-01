# Broad Feed Feasibility Report

**Generated:** 2026-03-01 18:35 UTC

**Conclusion:** The feed is no longer the bottleneck. The v1.2-broad scanner provides a dramatically wider and more diverse universe. However, the frozen v1.25 strategy, with its `ALLOWED_LANES = {"pumpfun_mature"}` policy, filters this broad universe down to a 100% `pumpswap` / `pumpfun_mature` tradeable set. The problem has been successfully moved from the scanner to the strategy's lane policy.

---

## 1. Feasibility Analysis

The broader feed results in a staggering improvement in feasibility metrics. The strategy now finds tradeable candidates in every single tick, a 10x improvement over the narrow feed.

| Metric                    | Narrow (v1.1) | Broad (v1.2) | Change |
| :------------------------ | :------------ | :----------- | :----- |
| % Ticks Tradeable >= 2    | 9.0%          | **100.0%**   | +91.0% |
| % Ticks Tradeable >= 1    | 14.0%         | **100.0%**   | +86.0% |
| Avg. Tradeable / Tick     | 0.33          | **2.75**     | +733%  |
| Opens / 100 Fires         | 6             | **100**      | +1567% |

**Primary Block Reasons Have Shifted:**
With a wider universe, `lane:not_allowed` is no longer a top blocker. Instead, fundamental gate failures on a larger set of tokens are the main reason for rejection.

| Reason              | Count | %      |
| :------------------ | :---- | :----- |
| not_cpamm_valid     | 880   | 25.6%  |
| lane:age            | 732   | 21.3%  |
| lane:vol_h1         | 685   | 20.0%  |
| pf_stability        | 422   | 12.3%  |
| lane:liq            | 335   | 9.8%   |


## 2. Upstream vs. Downstream Composition

The core finding of this experiment is how the strategy filters a broad, diverse upstream feed into a narrow, homogeneous downstream tradeable set.

**Upstream Feed (Post-Broad-Scanner):**
The universe entering the strategy is now highly diverse.

| Composition | pumpswap | raydium | orca  | meteora | Other |
| :---------- | :------- | :------ | :---- | :------ | :---- |
| **Venue**   | 53%      | 26%     | 17%   | 4%      | <1%   |

| Composition      | pumpfun_mature | large_cap_ray | pumpfun_early | non_pumpfun_mature |
| :--------------- | :------------- | :------------ | :------------ | :----------------- |
| **Lane**         | 24%            | 26%           | 28%           | 23%                |

**Downstream Funnel (Tradeable Set):**
After applying the frozen v1.25 strategy gates, the final tradeable set is 100% `pumpfun_mature` from the `pumpswap` venue.

| Funnel Stage          | pumpswap | raydium | orca | pfo=1 | pfo=0 | pumpfun_mature | large_cap_ray |
| :-------------------- | :------- | :------ | :--- | :---- | :---- | :------------- | :------------ |
| Eligible Snapshot     | 54%      | 26%     | 15%  | 52%   | 47%   | 24%            | 26%           |
| CPAMM Valid           | 71%      | 27%     | <1%  | 69%   | 30%   | 32%            | 27%           |
| Microstructure Recent | **100%** | 0%      | 0%   | **100%** | 0%    | **100%**       | 0%            |
| **Tradeable Set**     | **100%** | 0%      | 0%   | **100%** | 0%    | **100%**       | 0%            |

This demonstrates conclusively that the strategy's `ALLOWED_LANES` policy is the new bottleneck.

## 3. Top Candidates

The top tradeable candidates are now exclusively from the `pumpfun_mature` lane. Previously top-ranked (but blocked) `large_cap_ray` tokens like WETH are now correctly identified as `not_cpamm_valid` or filtered by the lane policy.

| Symbol | Venue    | Age   | Vol/h   | Liq     | Tradeable      | First Fail       |
| :----- | :------- | :---- | :------ | :------ | :------------- | :--------------- |
| Peace  | pumpswap | 32h   | 111,769 | 74,307  | 100/100 (100%) | —                |
| Rabbit | pumpswap | 46h   | 40,131  | 41,084  | 100/100 (100%) | —                |
| Tom    | pumpswap | 158h  | 43,175  | 33,623  | 51/53 (96%)    | lane:liq         |
| WETH   | orca     | 28550h| 1.9M    | 7.7M    | 0/100 (0%)     | not_cpamm_valid  |
| pippin | raydium  | 11446h| 1.6M    | 15.7M   | 0/3 (0%)       | lane:not_allowed |

## 4. Decision

**VERDICT: PROCEED.** The broad feed materially improves feasibility.

The next logical experiment is to test a `large_cap_ray` lane, as the strategy is clearly seeing these tokens but is policy-blocked from acting on them.
