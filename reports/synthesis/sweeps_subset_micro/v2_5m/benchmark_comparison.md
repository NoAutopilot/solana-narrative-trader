# Benchmark Comparison — 5m

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
| buys_m5 | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| sells_m5 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| buys_h1 | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| sells_h1 | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| buy_sell_ratio_m5 | NO (aggregated_order_flow) | NO | NONE | NOT_NOVEL |
| buy_sell_ratio_h1 | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| buy_count_ratio_m5 | NO (aggregated_order_flow) | NO | NONE | NOT_NOVEL |
| buy_count_ratio_h1 | NO (aggregated_order_flow) | NO | C3 | NOT_NOVEL |
| avg_trade_usd_m5 | YES | NO | C1 | NOVEL_BUT_NOT_IMPROVED |
| avg_trade_usd_h1 | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| vol_accel_m5_vs_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| txn_accel_m5_vs_h1 | NO (aggregated_order_flow) | NO | C1, C3 | NOT_NOVEL |
| r_m5_micro | NO (momentum_direction) | NO | C1, C3 | NOT_NOVEL |
| rv_5m | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| rv_1m | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| range_5m | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| liq_change_pct | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |
| liq_cliff_flag | YES | NO | C3 | NOVEL_BUT_NOT_IMPROVED |

### No-Go Registry Flags

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

