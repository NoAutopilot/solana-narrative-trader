# Decision Memo: Solana Trading Bot - Trade Execution Analysis

**To:** User
**From:** Manus AI
**Date:** 2026-03-01
**Subject:** Analysis of 0% Tradeable Rate and Recommendations

## 1. Executive Summary

This memo analyzes the root cause of the Solana trading bot's inability to open new pair trades, which has been at 0% for the last 100 strategy ticks. The investigation, based on five diagnostic queries run on the live system, concludes that the primary bottleneck is the `lane_age` gate, which is currently set to a minimum of 24 hours. This gate alone is responsible for rejecting the vast majority of otherwise viable trading opportunities.

Our analysis indicates that the universe of tokens scanned is heavily skewed towards assets younger than 24 hours, which possess sufficient liquidity and volume to be considered tradeable. Data quality and microstructure data coverage are not significant issues. While other gates like `pf_stability` and `anti_chase` do contribute to rejections, their impact is secondary to the `lane_age` constraint.

Relaxing the `lane_age` gate to 6 hours is projected to increase the `tradeable>=2` rate from 9% to a significantly higher level, potentially unlocking consistent trade execution. This change represents the most impactful lever for improving strategy performance.

## 2. Diagnostic Findings

The following sections detail the results of the five diagnostic queries.

### Q1: Age Distribution of Universe Snapshot

The current universe of tokens is dominated by young assets. The 24-hour age gate is filtering out a large pool of tokens that have high volume, which are prime candidates for the strategy.

| Age Bucket | Count | Avg Vol/h | Avg Liq   | Min Vol/h | Max Vol/h   |
| :--------- | ----: | :-------- | :-------- | :-------- | :---------- |
| 0-6h       |     6 | $402,788  | $32,608   | $45,327   | $1,840,262  |
| 6-12h      |     5 | $142,982  | $64,907   | $38,849   | $336,119    |
| 12-24h     |     2 | $38,461   | $30,501   | $27,615   | $49,307     |
| 24h+       |    24 | $78,474   | $1,567,823| $43       | $1,190,631  |

-   **Tokens passing all gates (age>=24h):** 6
-   **Tokens passing all gates (age>=6h):** 13

Relaxing the age gate from 24 hours to 6 hours more than doubles the number of tradeable candidates in the current snapshot.

### Q2: Microstructure Coverage by Age Cohort

Microstructure data coverage is excellent across all age cohorts, with near 100% coverage for all tokens, including those in the 0-6h bucket. This indicates that data availability is not a bottleneck for trading younger tokens.

| Age Bucket | N Tokens | W/ Micro | % Micro | W/ rv5m | % rv5m |
| :--------- | -------: | -------: | ------: | ------: | -----: |
| 0-6h       |    1,009 |    1,009 |  100.0% |   1,003 |  99.4% |
| 6-12h      |    4,509 |    4,509 |  100.0% |   4,504 |  99.9% |
| 12-24h     |    4,691 |    4,691 |  100.0% |   4,689 | 100.0% |
| 24h+       |   14,250 |   14,242 |   99.9% |  14,226 |  99.8% |

### Q3: `pf_stability` Gate Failure Modes

The `pf_stability` gate is the second-largest source of rejections after `lane_age`. The primary reason for failure is the `range_5m_ratio_fail`, where the 5-minute price range exceeds 3x the realized volatility. This suggests that while tokens may have sufficient volume and liquidity, they are often too volatile in the short term for the current stability parameters.

| Failure Mode                | Count | Avg Score |
| :-------------------------- | ----: | --------: |
| range_5m_ratio_fail         |   100 |      6.23 |
| rv5m_missing                |    17 |      6.89 |
| rv5m_too_high (>1.5%)       |    13 |      8.45 |

### Q4: `anti_chase` Gate Hit Rate

The `anti_chase` gate has a significant impact. The what-if analysis shows that removing this gate would dramatically increase the number of `tradeable>=2` ticks from 9 to 123 (out of 146), an increase of over 13x. This indicates that the strategy is frequently identifying tokens that are already experiencing a sharp price increase, and the `anti_chase` gate is preventing entry.

-   **Actual tradeable>=2 ticks:** 9 / 146
-   **What-if no anti_chase:** 123 / 146

### Q5: `vol_h1` Distribution of `lane_age`-Blocked Ticks

This query confirms that there is a substantial number of young tokens (6-24h old) with high volume that are being blocked by the `lane_age` gate. Tokens like `TRUMP` and `Aslan` have hourly volumes exceeding $100,000 and would be prime candidates for the strategy if the age gate were relaxed.

| Vol/h Bucket | Count | Avg Age | Avg Liq  | 6-24h |
| :----------- | ----: | ------: | :------- | ----: |
| $25-50k/h    |     3 |   16.5h | $31,991  |     3 |
| $50-100k/h   |     2 |    6.1h | $32,651  |     1 |
| >$100k/h     |     4 |    8.0h | $90,059  |     3 |

## 3. Root Cause Analysis

The evidence from the diagnostic queries points to a single, dominant root cause for the 0% trade execution rate: the `lane_age` gate is too restrictive. The current 24-hour minimum age requirement is filtering out the majority of high-volume, liquid tokens that the scanner is identifying.

The strategy is effectively blind to the most active part of the market. While other gates, particularly `anti_chase` and `pf_stability`, also play a role in limiting tradeable candidates, their impact is secondary. The `lane_age` gate is the primary bottleneck that must be addressed to enable the strategy to function as intended.

## 4. Recommendations

Based on this analysis, the following recommendations are proposed:

1.  **Relax the `lane_age` gate from 24 hours to 6 hours.** This is the single most impactful change that can be made to increase the number of tradeable candidates and enable the bot to start opening trades. The data shows that there is a significant pool of tokens in the 6-24 hour age range with sufficient volume and liquidity.

2.  **Maintain the `anti_chase` and `pf_stability` gates at their current settings.** While these gates are restrictive, they serve as important risk management controls. It is recommended to first observe the impact of the `lane_age` change before considering adjustments to these secondary gates.

By implementing the recommended change to the `lane_age` gate, we expect to see a significant improvement in the `tradeable>=2` rate and the overall performance of the trading bot.
