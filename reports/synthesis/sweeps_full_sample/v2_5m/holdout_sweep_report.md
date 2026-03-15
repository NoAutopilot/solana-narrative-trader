# Holdout Sweep Report — 5m

**Date:** 2026-03-15 02:16 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 5m (300s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 44
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| age_hours | FAIL | -0.249% | -0.517% | -1.244% | 12.5% | 0.022 | 100.0% |
| liquidity_usd | FAIL | -0.389% | -0.517% | -1.252% | 11.2% | 0.021 | 100.0% |
| vol_h1 | FAIL | -0.321% | -0.503% | -0.562% | 9.2% | 0.023 | 100.0% |
| vol_h24 | FAIL | -0.474% | -0.516% | -1.181% | 10.8% | 0.019 | 100.0% |
| price_usd | FAIL | -0.135% | -0.509% | -0.819% | 12.9% | 0.017 | 100.0% |
| r_m5_snap | SKIP | — | — | — | — | — | — |
| r_h1_snap | SKIP | — | — | — | — | — | — |
| buys_m5 | FAIL | 0.209% | -0.514% | -1.509% | 12.3% | 0.023 | 77.3% |
| sells_m5 | FAIL | 0.611% | -0.514% | -1.090% | 13.2% | 0.024 | 77.3% |
| buys_h1 | FAIL | -0.515% | -0.516% | -2.256% | 11.0% | 0.022 | 77.3% |
| sells_h1 | FAIL | -0.513% | -0.515% | -1.907% | 12.0% | 0.022 | 77.3% |
| buy_sell_ratio_m5 | FAIL | -0.350% | -0.516% | -1.247% | 10.4% | 0.038 | 68.8% |
| buy_sell_ratio_h1 | FAIL | -0.078% | -0.517% | -1.345% | 9.9% | 0.038 | 75.0% |
| buy_count_ratio_m5 | FAIL | -0.350% | -0.516% | -1.247% | 10.4% | 0.038 | 68.8% |
| buy_count_ratio_h1 | FAIL | -0.078% | -0.517% | -1.345% | 9.9% | 0.038 | 75.0% |
| avg_trade_usd_m5 | FAIL | 0.827% | -0.513% | -0.574% | 11.8% | 0.038 | 68.8% |
| avg_trade_usd_h1 | FAIL | -0.088% | -0.512% | -0.992% | 11.1% | 0.029 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 1.154% | -0.512% | -0.243% | 15.3% | 0.031 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 0.576% | -0.513% | -0.792% | 14.2% | 0.029 | 75.0% |
| r_m5_micro | FAIL | 0.982% | -0.517% | -0.711% | 13.6% | 0.027 | 77.3% |
| rv_5m | FAIL | -0.297% | -0.516% | -1.515% | 13.0% | 0.024 | 77.1% |
| rv_1m | FAIL | -0.141% | -0.518% | -1.948% | 11.4% | 0.026 | 77.1% |
| range_5m | FAIL | 0.235% | -0.516% | -1.123% | 13.6% | 0.023 | 77.1% |
| buys_m5_snap | FAIL | -0.486% | -0.501% | -0.604% | 7.7% | 0.012 | 100.0% |
| sells_m5_snap | FAIL | -0.522% | -0.501% | -0.633% | 6.7% | 0.014 | 100.0% |
| buy_count_ratio_m5_snap | FAIL | -0.388% | -0.515% | -1.502% | 12.5% | 0.019 | 90.5% |
| avg_trade_usd_m5_snap | FAIL | -0.119% | -0.512% | -1.060% | 10.2% | 0.031 | 90.5% |
| jup_vs_cpamm_diff_pct | FAIL | -0.180% | -0.502% | -0.696% | 10.9% | 0.050 | 77.4% |
| round_trip_pct | FAIL | -0.370% | -0.517% | -1.199% | 11.2% | 0.021 | 100.0% |
| impact_buy_pct | FAIL | -0.389% | -0.517% | -1.249% | 11.2% | 0.022 | 100.0% |
| impact_sell_pct | FAIL | -0.398% | -0.517% | -1.240% | 11.1% | 0.021 | 100.0% |
| impact_asymmetry_pct | FAIL | -0.456% | -0.512% | -0.745% | 10.2% | 0.005 | 100.0% |
| liq_change_pct | FAIL | -0.645% | -0.516% | -2.179% | 11.2% | 0.035 | 77.1% |
| liq_cliff_flag | FAIL | -0.591% | -0.515% | -1.054% | 11.3% | 0.006 | 77.3% |
| breadth_positive_pct | FAIL | -0.192% | -0.514% | -1.046% | 12.9% | 0.025 | 98.6% |
| breadth_negative_pct | FAIL | -0.307% | -0.513% | -1.121% | 9.8% | 0.035 | 98.6% |
| median_pool_r_m5 | FAIL | -0.407% | -0.511% | -1.250% | 15.4% | 0.017 | 98.6% |
| pool_dispersion_r_m5 | FAIL | -0.251% | -0.513% | -1.105% | 13.8% | 0.021 | 98.6% |
| median_pool_rv5m | FAIL | -0.139% | -0.513% | -0.781% | 8.9% | 0.034 | 98.6% |
| pool_liquidity_median | FAIL | 0.126% | -0.512% | -0.684% | 11.2% | 0.025 | 100.0% |
| pool_vol_h1_median | FAIL | -0.014% | -0.513% | -1.180% | 16.6% | 0.020 | 100.0% |
| pool_size_total | FAIL | -0.156% | -0.513% | -1.224% | 14.9% | 0.020 | 100.0% |
| pool_size_with_micro | FAIL | -0.436% | -0.514% | -1.082% | 13.1% | 0.022 | 100.0% |
| coverage_ratio_micro | FAIL | -0.119% | -0.514% | -0.558% | 9.3% | 0.032 | 100.0% |

**No features promoted from discovery. Program should proceed to next option or stop.**
