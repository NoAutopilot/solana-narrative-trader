# Holdout Sweep Report — 30m

**Date:** 2026-03-15 02:18 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 30m (1800s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 44
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| age_hours | FAIL | 0.163% | -0.655% | -1.866% | 48.2% | 0.008 | 100.0% |
| liquidity_usd | FAIL | 0.328% | -0.816% | -2.006% | 46.8% | 0.013 | 100.0% |
| vol_h1 | FAIL | 0.099% | -0.484% | -0.670% | 27.7% | 0.022 | 100.0% |
| vol_h24 | FAIL | 0.576% | -0.424% | -0.733% | 34.4% | 0.015 | 100.0% |
| price_usd | FAIL | 0.753% | -0.462% | -2.331% | 45.0% | 0.010 | 100.0% |
| r_m5_snap | SKIP | — | — | — | — | — | — |
| r_h1_snap | SKIP | — | — | — | — | — | — |
| buys_m5 | FAIL | 2.597% | 0.411% | -1.729% | 50.1% | 0.013 | 77.3% |
| sells_m5 | FAIL | 2.544% | 0.427% | -1.764% | 51.0% | 0.013 | 77.3% |
| buys_h1 | FAIL | 1.168% | -0.554% | -3.479% | 46.6% | 0.013 | 77.3% |
| sells_h1 | FAIL | 0.941% | -0.534% | -3.747% | 47.3% | 0.012 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 0.291% | -0.798% | -3.244% | 45.3% | 0.019 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 0.855% | -0.409% | -1.716% | 46.2% | 0.013 | 75.0% |
| buy_count_ratio_m5 | FAIL | 0.291% | -0.798% | -3.244% | 45.3% | 0.019 | 68.8% |
| buy_count_ratio_h1 | FAIL | 0.855% | -0.409% | -1.716% | 46.2% | 0.013 | 75.0% |
| avg_trade_usd_m5 | FAIL | 2.316% | -0.554% | -0.667% | 45.3% | 0.016 | 68.8% |
| avg_trade_usd_h1 | FAIL | 0.965% | -0.619% | -2.222% | 46.2% | 0.012 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 3.221% | -0.260% | 0.539% | 45.6% | 0.014 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 2.262% | -0.354% | -0.395% | 43.9% | 0.014 | 75.0% |
| r_m5_micro | FAIL | 5.748% | 2.389% | 2.289% | 57.5% | 0.013 | 77.3% |
| rv_5m | FAIL | 1.028% | -0.565% | -3.709% | 48.4% | 0.011 | 77.1% |
| rv_1m | FAIL | 2.152% | 0.038% | -2.424% | 50.1% | 0.013 | 77.1% |
| range_5m | FAIL | 0.894% | -0.554% | -1.801% | 48.9% | 0.012 | 77.1% |
| buys_m5_snap | FAIL | 0.096% | -0.457% | -0.443% | 23.6% | 0.028 | 100.0% |
| sells_m5_snap | FAIL | 0.124% | -0.515% | -2.135% | 39.9% | 0.011 | 100.0% |
| buy_count_ratio_m5_snap | FAIL | 0.727% | -0.529% | -2.004% | 43.2% | 0.017 | 90.5% |
| avg_trade_usd_m5_snap | FAIL | 0.960% | -0.528% | -1.146% | 42.4% | 0.012 | 90.5% |
| jup_vs_cpamm_diff_pct | FAIL | 0.650% | -0.144% | -1.754% | 48.9% | 0.011 | 77.4% |
| round_trip_pct | FAIL | 0.237% | -0.954% | -2.165% | 46.5% | 0.013 | 100.0% |
| impact_buy_pct | FAIL | 0.237% | -0.954% | -2.165% | 46.5% | 0.013 | 100.0% |
| impact_sell_pct | FAIL | 0.306% | -0.816% | -1.949% | 46.8% | 0.013 | 100.0% |
| impact_asymmetry_pct | FAIL | -0.232% | -0.508% | -0.934% | 34.3% | 0.003 | 100.0% |
| liq_change_pct | FAIL | 0.065% | -0.572% | -4.015% | 46.4% | 0.017 | 77.1% |
| liq_cliff_flag | FAIL | -0.293% | -0.585% | -1.464% | 41.2% | 0.003 | 77.3% |
| breadth_positive_pct | FAIL | 0.022% | -0.380% | -1.672% | 38.4% | 0.009 | 98.6% |
| breadth_negative_pct | FAIL | 0.361% | -0.362% | -1.464% | 39.3% | 0.013 | 98.6% |
| median_pool_r_m5 | FAIL | -0.195% | -0.533% | -1.289% | 35.3% | 0.004 | 98.6% |
| pool_dispersion_r_m5 | FAIL | -0.372% | -0.500% | -2.135% | 33.3% | 0.013 | 98.6% |
| median_pool_rv5m | FAIL | 0.281% | -0.526% | -1.686% | 38.2% | 0.012 | 98.6% |
| pool_liquidity_median | FAIL | 0.335% | -0.383% | -1.664% | 42.4% | 0.011 | 100.0% |
| pool_vol_h1_median | FAIL | 0.964% | -0.408% | -1.138% | 36.9% | 0.017 | 100.0% |
| pool_size_total | FAIL | 0.207% | -0.439% | -1.630% | 38.2% | 0.012 | 100.0% |
| pool_size_with_micro | FAIL | 0.129% | -0.412% | -1.552% | 38.4% | 0.011 | 100.0% |
| coverage_ratio_micro | FAIL | 0.102% | -0.485% | -1.606% | 35.9% | 0.012 | 100.0% |

**No features promoted from discovery. Program should proceed to next option or stop.**
