# Holdout Sweep Report — 4h

**Date:** 2026-03-15 02:19 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 4h (14400s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 44
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| age_hours | FAIL | 5.729% | -3.462% | -1.806% | 46.6% | 0.031 | 100.0% |
| liquidity_usd | FAIL | 13.595% | 0.134% | 3.961% | 50.5% | 0.029 | 100.0% |
| vol_h1 | FAIL | 2.263% | -0.840% | -0.093% | 37.0% | 0.055 | 100.0% |
| vol_h24 | FAIL | -3.783% | -1.131% | -6.648% | 28.6% | 0.015 | 100.0% |
| price_usd | FAIL | 14.255% | -0.197% | 4.418% | 48.9% | 0.031 | 100.0% |
| r_m5_snap | SKIP | — | — | — | — | — | — |
| r_h1_snap | SKIP | — | — | — | — | — | — |
| buys_m5 | FAIL | 1.947% | -0.805% | -2.472% | 42.4% | 0.034 | 77.3% |
| sells_m5 | FAIL | 2.126% | -1.318% | -4.349% | 43.2% | 0.050 | 77.3% |
| buys_h1 | FAIL | 1.588% | -1.235% | -4.909% | 45.4% | 0.049 | 77.3% |
| sells_h1 | FAIL | 1.399% | -0.648% | -2.782% | 44.5% | 0.038 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 3.894% | -1.553% | -5.555% | 46.5% | 0.042 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 4.251% | -0.199% | -3.269% | 48.2% | 0.047 | 75.0% |
| buy_count_ratio_m5 | FAIL | 3.894% | -1.553% | -5.555% | 46.5% | 0.042 | 68.8% |
| buy_count_ratio_h1 | FAIL | 4.251% | -0.199% | -3.269% | 48.2% | 0.047 | 75.0% |
| avg_trade_usd_m5 | FAIL | 7.345% | -1.448% | -3.269% | 36.7% | 0.063 | 68.8% |
| avg_trade_usd_h1 | FAIL | 7.245% | -1.478% | -3.167% | 39.1% | 0.051 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 1.900% | -0.865% | -4.654% | 44.2% | 0.032 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 1.201% | -1.087% | -4.874% | 45.7% | 0.021 | 75.0% |
| r_m5_micro | FAIL | -2.974% | -6.800% | -10.711% | 38.7% | 0.023 | 77.3% |
| rv_5m | FAIL | -0.389% | -0.967% | -2.819% | 37.1% | 0.038 | 77.1% |
| rv_1m | FAIL | 4.771% | -2.843% | -4.793% | 48.9% | 0.031 | 77.1% |
| range_5m | FAIL | 1.536% | -3.540% | -5.000% | 40.1% | 0.052 | 77.1% |
| buys_m5_snap | FAIL | -2.432% | -1.152% | -6.058% | 39.1% | 0.017 | 100.0% |
| sells_m5_snap | FAIL | 2.187% | -0.551% | -2.008% | 45.8% | 0.026 | 100.0% |
| buy_count_ratio_m5_snap | FAIL | 0.283% | -0.397% | -3.981% | 47.1% | 0.019 | 90.5% |
| avg_trade_usd_m5_snap | FAIL | 2.815% | -1.144% | -4.489% | 44.4% | 0.037 | 90.5% |
| jup_vs_cpamm_diff_pct | FAIL | -1.105% | -4.015% | -6.866% | 40.4% | 0.026 | 77.4% |
| round_trip_pct | FAIL | 14.238% | 0.265% | 3.639% | 51.5% | 0.029 | 100.0% |
| impact_buy_pct | FAIL | 14.238% | 0.265% | 3.639% | 51.5% | 0.029 | 100.0% |
| impact_sell_pct | FAIL | 14.238% | 0.265% | 3.639% | 51.5% | 0.029 | 100.0% |
| impact_asymmetry_pct | FAIL | -2.681% | -0.852% | -4.634% | 36.9% | 0.009 | 100.0% |
| liq_change_pct | FAIL | 0.479% | -1.088% | -2.198% | 41.0% | 0.007 | 77.1% |
| liq_cliff_flag | FAIL | -0.344% | -1.109% | -2.751% | 40.9% | 0.005 | 77.3% |
| breadth_positive_pct | FAIL | -0.952% | -0.966% | -4.598% | 38.2% | 0.026 | 98.6% |
| breadth_negative_pct | FAIL | 0.208% | -1.169% | -4.305% | 34.6% | 0.023 | 98.6% |
| median_pool_r_m5 | FAIL | -1.102% | -0.842% | -4.712% | 40.6% | 0.024 | 98.6% |
| pool_dispersion_r_m5 | FAIL | -0.746% | -0.723% | -4.313% | 42.1% | 0.023 | 98.6% |
| median_pool_rv5m | FAIL | 0.521% | -0.965% | -4.269% | 37.6% | 0.025 | 98.6% |
| pool_liquidity_median | FAIL | 0.111% | -0.948% | -4.432% | 42.6% | 0.024 | 100.0% |
| pool_vol_h1_median | FAIL | 6.879% | -0.454% | 0.105% | 41.2% | 0.046 | 100.0% |
| pool_size_total | FAIL | 4.688% | -0.386% | -1.503% | 43.2% | 0.045 | 100.0% |
| pool_size_with_micro | FAIL | 3.681% | -0.311% | -1.042% | 45.1% | 0.032 | 100.0% |
| coverage_ratio_micro | FAIL | 3.972% | -0.141% | -1.188% | 47.7% | 0.041 | 100.0% |

**No features promoted from discovery. Program should proceed to next option or stop.**
