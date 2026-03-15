# Holdout Sweep Report — 15m

**Date:** 2026-03-15 02:17 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 15m (900s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 44
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| age_hours | FAIL | -0.223% | -0.509% | -1.221% | 24.0% | 0.012 | 100.0% |
| liquidity_usd | FAIL | -0.395% | -0.516% | -1.834% | 24.1% | 0.014 | 100.0% |
| vol_h1 | FAIL | -0.148% | -0.514% | -1.298% | 21.6% | 0.013 | 100.0% |
| vol_h24 | FAIL | -0.101% | -0.518% | -0.930% | 17.0% | 0.023 | 100.0% |
| price_usd | FAIL | -0.171% | -0.510% | -1.447% | 23.2% | 0.012 | 100.0% |
| r_m5_snap | SKIP | — | — | — | — | — | — |
| r_h1_snap | SKIP | — | — | — | — | — | — |
| buys_m5 | FAIL | 1.263% | -0.514% | -1.501% | 26.8% | 0.014 | 77.3% |
| sells_m5 | FAIL | 1.600% | -0.513% | -0.993% | 26.3% | 0.015 | 77.3% |
| buys_h1 | FAIL | 0.364% | -0.516% | -2.248% | 23.4% | 0.015 | 77.3% |
| sells_h1 | FAIL | 0.170% | -0.516% | -2.755% | 23.6% | 0.015 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 0.217% | -0.517% | -1.930% | 25.6% | 0.020 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 0.022% | -0.518% | -1.579% | 21.1% | 0.027 | 75.0% |
| buy_count_ratio_m5 | FAIL | 0.217% | -0.517% | -1.930% | 25.6% | 0.020 | 68.8% |
| buy_count_ratio_h1 | FAIL | 0.022% | -0.518% | -1.579% | 21.1% | 0.027 | 75.0% |
| avg_trade_usd_m5 | FAIL | 1.233% | -0.514% | -0.921% | 23.0% | 0.022 | 68.8% |
| avg_trade_usd_h1 | FAIL | 0.228% | -0.519% | -1.878% | 22.3% | 0.019 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 2.097% | -0.511% | 0.145% | 26.9% | 0.022 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 0.798% | -0.514% | -1.131% | 25.7% | 0.019 | 75.0% |
| r_m5_micro | FAIL | 2.787% | -0.517% | 0.529% | 28.5% | 0.017 | 77.3% |
| rv_5m | FAIL | 0.378% | -0.515% | -1.501% | 26.4% | 0.014 | 77.1% |
| rv_1m | FAIL | 0.902% | -0.518% | -1.954% | 24.8% | 0.017 | 77.1% |
| range_5m | FAIL | 0.558% | -0.516% | -1.241% | 25.9% | 0.014 | 77.1% |
| buys_m5_snap | FAIL | -0.331% | -0.506% | -0.575% | 13.5% | 0.021 | 100.0% |
| sells_m5_snap | FAIL | -0.467% | -0.515% | -0.677% | 13.4% | 0.017 | 100.0% |
| buy_count_ratio_m5_snap | FAIL | -0.406% | -0.516% | -1.900% | 22.3% | 0.014 | 90.5% |
| avg_trade_usd_m5_snap | FAIL | 0.346% | -0.513% | -1.031% | 22.4% | 0.018 | 90.5% |
| jup_vs_cpamm_diff_pct | FAIL | 0.098% | -0.504% | -0.505% | 13.7% | 0.042 | 77.4% |
| round_trip_pct | FAIL | -0.405% | -0.517% | -1.813% | 23.9% | 0.014 | 100.0% |
| impact_buy_pct | FAIL | -0.316% | -0.517% | -1.785% | 24.4% | 0.014 | 100.0% |
| impact_sell_pct | FAIL | -0.307% | -0.517% | -1.736% | 24.6% | 0.014 | 100.0% |
| impact_asymmetry_pct | FAIL | -0.411% | -0.514% | -0.883% | 19.1% | 0.004 | 100.0% |
| liq_change_pct | FAIL | -0.039% | -0.516% | -2.616% | 21.2% | 0.030 | 77.1% |
| liq_cliff_flag | FAIL | -0.492% | -0.517% | -1.205% | 21.4% | 0.004 | 77.3% |
| breadth_positive_pct | FAIL | -0.249% | -0.515% | -1.501% | 19.0% | 0.020 | 98.6% |
| breadth_negative_pct | FAIL | -0.359% | -0.515% | -1.723% | 23.8% | 0.016 | 98.6% |
| median_pool_r_m5 | FAIL | -0.227% | -0.513% | -1.393% | 21.1% | 0.016 | 98.6% |
| pool_dispersion_r_m5 | FAIL | -0.124% | -0.514% | -1.375% | 21.2% | 0.018 | 98.6% |
| median_pool_rv5m | FAIL | -0.257% | -0.514% | -1.532% | 19.2% | 0.019 | 98.6% |
| pool_liquidity_median | FAIL | -0.093% | -0.516% | -1.065% | 15.0% | 0.023 | 100.0% |
| pool_vol_h1_median | FAIL | 0.136% | -0.512% | -1.198% | 22.6% | 0.019 | 100.0% |
| pool_size_total | FAIL | -0.078% | -0.515% | -1.311% | 19.0% | 0.018 | 100.0% |
| pool_size_with_micro | FAIL | -0.378% | -0.513% | -1.288% | 17.3% | 0.022 | 100.0% |
| coverage_ratio_micro | FAIL | -0.006% | -0.519% | -2.200% | 25.5% | 0.021 | 100.0% |

**No features promoted from discovery. Program should proceed to next option or stop.**
