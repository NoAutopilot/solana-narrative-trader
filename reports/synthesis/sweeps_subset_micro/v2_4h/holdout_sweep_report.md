# Holdout Sweep Report — 4h

**Date:** 2026-03-15 02:21 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 4h (14400s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 18
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| buys_m5 | FAIL | 1.947% | -0.805% | -2.213% | 42.4% | 0.034 | 77.3% |
| sells_m5 | FAIL | 2.126% | -1.318% | -3.922% | 43.2% | 0.050 | 77.3% |
| buys_h1 | FAIL | 1.588% | -1.235% | -4.519% | 45.4% | 0.049 | 77.3% |
| sells_h1 | FAIL | 1.399% | -0.648% | -2.487% | 44.5% | 0.038 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 3.894% | -1.553% | -5.048% | 46.5% | 0.042 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 4.251% | -0.199% | -2.861% | 48.2% | 0.047 | 75.0% |
| buy_count_ratio_m5 | FAIL | 3.894% | -1.553% | -5.048% | 46.5% | 0.042 | 68.8% |
| buy_count_ratio_h1 | FAIL | 4.251% | -0.199% | -2.861% | 48.2% | 0.047 | 75.0% |
| avg_trade_usd_m5 | FAIL | 7.345% | -1.448% | -2.420% | 36.7% | 0.063 | 68.8% |
| avg_trade_usd_h1 | FAIL | 7.245% | -1.478% | -2.089% | 39.1% | 0.051 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 1.900% | -0.865% | -3.967% | 44.2% | 0.032 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 1.201% | -1.087% | -4.340% | 45.7% | 0.021 | 75.0% |
| r_m5_micro | FAIL | -2.974% | -6.800% | -10.108% | 38.7% | 0.023 | 77.3% |
| rv_5m | FAIL | -0.389% | -0.967% | -2.633% | 37.1% | 0.038 | 77.1% |
| rv_1m | FAIL | 4.771% | -2.843% | -4.175% | 48.9% | 0.031 | 77.1% |
| range_5m | FAIL | 1.536% | -3.540% | -4.728% | 40.1% | 0.052 | 77.1% |
| liq_change_pct | FAIL | 0.479% | -1.088% | -1.977% | 41.0% | 0.007 | 77.1% |
| liq_cliff_flag | FAIL | -0.344% | -1.109% | -2.651% | 40.9% | 0.005 | 77.3% |

**No features promoted from discovery. Program should proceed to next option or stop.**
