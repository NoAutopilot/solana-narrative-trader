# Benchmark Comparison — 4h

**Date:** 2026-03-15 02:19 UTC

---

## V1 Benchmark Ceiling

| Metric | V1 Best | Feature | Horizon |
|--------|--------:|---------|--------:|
| Best net mean | 0.051% | median_pool_r_m5 | +5m |
| Best net median | 0.000% | all | +5m |
| Best win rate | 50.0% | all | +5m |
| Round-trip cost | 0.51% | median | — |

## Feature-Level Comparison

| Feature | Novel? | Exceeds V1? | Addresses Constraint? | Verdict |
|---------|--------|-------------|----------------------|--------|
| age_hours | NO (static_fundamentals) | NO | C1, C3 | NOT_NOVEL |
| liquidity_usd | NO (static_fundamentals) | YES | C1, C2, C3 | NOT_NOVEL |
| vol_h1 | NO (static_fundamentals) | NO | C1, C3 | NOT_NOVEL |
| vol_h24 | NO (static_fundamentals) | NO | C3 | NOT_NOVEL |
| price_usd | NO (static_fundamentals) | NO | C1, C3 | NOT_NOVEL |
| buys_m5 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| sells_m5 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| buys_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| sells_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| buy_sell_ratio_m5 | NO (aggregated_order_flow) | NO | C1 | NOT_NOVEL |
| buy_sell_ratio_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| buy_count_ratio_m5 | NO (aggregated_order_flow) | NO | C1 | NOT_NOVEL |
| buy_count_ratio_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| avg_trade_usd_m5 | YES | NO | C1 | NOVEL_BUT_NOT_IMPROVED |
| avg_trade_usd_h1 | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| vol_accel_m5_vs_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| txn_accel_m5_vs_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| r_m5_micro | NO (momentum_direction) | NO | C3 | NOT_NOVEL |
| rv_5m | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| rv_1m | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| range_5m | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| buys_m5_snap | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| sells_m5_snap | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| buy_count_ratio_m5_snap | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| avg_trade_usd_m5_snap | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| jup_vs_cpamm_diff_pct | NO (execution_quality) | NO | C3 | NOT_NOVEL |
| round_trip_pct | NO (execution_quality) | YES | C1, C2, C3 | NOT_NOVEL |
| impact_buy_pct | NO (execution_quality) | YES | C1, C2, C3 | NOT_NOVEL |
| impact_sell_pct | NO (execution_quality) | YES | C1, C2, C3 | NOT_NOVEL |
| impact_asymmetry_pct | NO (execution_quality) | NO | C3 | NOT_NOVEL |
| liq_change_pct | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| liq_cliff_flag | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| breadth_positive_pct | NO (momentum_direction) | NO | C3 | NOT_NOVEL |
| breadth_negative_pct | NO (momentum_direction) | NO | C3 | NOT_NOVEL |
| median_pool_r_m5 | NO (momentum_direction) | NO | C3 | NOT_NOVEL |
| pool_dispersion_r_m5 | NO (momentum_direction) | NO | C3 | NOT_NOVEL |
| median_pool_rv5m | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| pool_liquidity_median | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| pool_vol_h1_median | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| pool_size_total | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| pool_size_with_micro | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |
| coverage_ratio_micro | YES | NO | C1, C3 | NOVEL_BUT_NOT_IMPROVED |

### No-Go Registry Flags

**age_hours:** Static fundamentals family exhausted. Median = 0 at all horizons.

**liquidity_usd:** Static fundamentals family exhausted. Median = 0 at all horizons.

**vol_h1:** Static fundamentals family exhausted. Median = 0 at all horizons.

**vol_h24:** Static fundamentals family exhausted. Median = 0 at all horizons.

**price_usd:** Static fundamentals family exhausted. Median = 0 at all horizons.

**buys_m5:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**sells_m5:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buys_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**sells_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buy_sell_ratio_m5:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buy_sell_ratio_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buy_count_ratio_m5:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buy_count_ratio_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**vol_accel_m5_vs_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**txn_accel_m5_vs_h1:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**r_m5_micro:** Momentum/direction family exhausted. Median = 0 at all horizons.

**buys_m5_snap:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**sells_m5_snap:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**buy_count_ratio_m5_snap:** Aggregated order-flow family exhausted. Mean is outlier-driven, median = 0.

**jup_vs_cpamm_diff_pct:** Execution quality family exhausted. Near-zero tercile differentiation.

**round_trip_pct:** Execution quality family exhausted. Near-zero tercile differentiation.

**impact_buy_pct:** Execution quality family exhausted. Near-zero tercile differentiation.

**impact_sell_pct:** Execution quality family exhausted. Near-zero tercile differentiation.

**impact_asymmetry_pct:** Execution quality family exhausted. Near-zero tercile differentiation.

**breadth_positive_pct:** Momentum/direction family exhausted. Median = 0 at all horizons.

**breadth_negative_pct:** Momentum/direction family exhausted. Median = 0 at all horizons.

**median_pool_r_m5:** Momentum/direction family exhausted. Median = 0 at all horizons.

**pool_dispersion_r_m5:** Momentum/direction family exhausted. Median = 0 at all horizons.

