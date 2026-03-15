# Holdout Sweep Report — 1h

**Date:** 2026-03-15 02:18 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 1h (3600s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 44
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| age_hours | FAIL | 2.627% | -4.653% | -3.188% | 42.2% | 0.012 | 100.0% |
| liquidity_usd | FAIL | 5.037% | 1.398% | 0.538% | 53.8% | 0.015 | 100.0% |
| vol_h1 | FAIL | 0.399% | -0.600% | -2.029% | 36.7% | 0.018 | 100.0% |
| vol_h24 | FAIL | 2.497% | -0.406% | -0.536% | 45.6% | 0.021 | 100.0% |
| price_usd | FAIL | 4.644% | -0.080% | 0.456% | 49.2% | 0.017 | 100.0% |
| r_m5_snap | SKIP | — | — | — | — | — | — |
| r_h1_snap | SKIP | — | — | — | — | — | — |
| buys_m5 | FAIL | 5.960% | -2.856% | -1.657% | 45.2% | 0.015 | 77.3% |
| sells_m5 | FAIL | 5.681% | -1.849% | -0.993% | 46.2% | 0.015 | 77.3% |
| buys_h1 | FAIL | 3.738% | -3.901% | -2.737% | 44.0% | 0.015 | 77.3% |
| sells_h1 | FAIL | 3.194% | -5.464% | -3.774% | 42.5% | 0.015 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 3.145% | -0.719% | -2.173% | 47.0% | 0.023 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 2.555% | -0.507% | -1.516% | 47.2% | 0.017 | 75.0% |
| buy_count_ratio_m5 | FAIL | 3.145% | -0.719% | -2.173% | 47.0% | 0.023 | 68.8% |
| buy_count_ratio_h1 | FAIL | 2.555% | -0.507% | -1.516% | 47.2% | 0.017 | 75.0% |
| avg_trade_usd_m5 | FAIL | 3.420% | -0.600% | -0.799% | 46.3% | 0.021 | 68.8% |
| avg_trade_usd_h1 | FAIL | 5.011% | -0.689% | -0.372% | 46.1% | 0.019 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 4.447% | -0.208% | 0.770% | 47.8% | 0.023 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 3.482% | -0.435% | -0.345% | 44.6% | 0.023 | 75.0% |
| r_m5_micro | FAIL | 5.912% | -0.824% | 0.375% | 47.8% | 0.015 | 77.3% |
| rv_5m | FAIL | 3.380% | -5.007% | -3.746% | 44.9% | 0.015 | 77.1% |
| rv_1m | FAIL | 5.056% | -1.849% | -1.301% | 47.5% | 0.016 | 77.1% |
| range_5m | FAIL | 4.320% | -4.109% | -2.445% | 44.9% | 0.015 | 77.1% |
| buys_m5_snap | FAIL | 2.107% | -2.661% | -3.398% | 39.2% | 0.014 | 100.0% |
| sells_m5_snap | FAIL | 1.835% | -0.514% | -1.150% | 40.2% | 0.014 | 100.0% |
| buy_count_ratio_m5_snap | FAIL | 3.626% | -0.531% | -0.541% | 44.4% | 0.018 | 90.5% |
| avg_trade_usd_m5_snap | FAIL | 2.912% | -0.745% | -1.262% | 40.6% | 0.021 | 90.5% |
| jup_vs_cpamm_diff_pct | FAIL | 2.991% | -0.598% | -1.237% | 49.3% | 0.017 | 77.4% |
| round_trip_pct | FAIL | 5.069% | 1.126% | 0.649% | 53.5% | 0.015 | 100.0% |
| impact_buy_pct | FAIL | 5.069% | 1.126% | 0.649% | 53.5% | 0.015 | 100.0% |
| impact_sell_pct | FAIL | 5.069% | 1.126% | 0.649% | 53.5% | 0.015 | 100.0% |
| impact_asymmetry_pct | FAIL | 5.969% | 1.398% | -6.417% | 54.2% | 0.047 | 100.0% |
| liq_change_pct | FAIL | 0.939% | -0.599% | -0.660% | 41.1% | 0.005 | 77.1% |
| liq_cliff_flag | FAIL | 0.968% | -0.614% | -0.600% | 41.4% | 0.004 | 77.3% |
| breadth_positive_pct | FAIL | 1.661% | -0.376% | -0.645% | 40.5% | 0.015 | 98.6% |
| breadth_negative_pct | FAIL | 1.727% | -0.267% | -0.645% | 42.2% | 0.017 | 98.6% |
| median_pool_r_m5 | FAIL | 1.116% | -0.443% | -0.406% | 38.6% | 0.006 | 98.6% |
| pool_dispersion_r_m5 | FAIL | 1.389% | -0.623% | -1.410% | 34.9% | 0.020 | 98.6% |
| median_pool_rv5m | FAIL | 1.068% | -0.788% | -1.818% | 33.1% | 0.019 | 98.6% |
| pool_liquidity_median | FAIL | 2.284% | -0.518% | -0.637% | 32.8% | 0.023 | 100.0% |
| pool_vol_h1_median | FAIL | 1.870% | -0.323% | -0.747% | 38.6% | 0.013 | 100.0% |
| pool_size_total | FAIL | 2.522% | -0.265% | -0.084% | 41.0% | 0.026 | 100.0% |
| pool_size_with_micro | FAIL | 1.470% | -0.283% | -2.024% | 40.5% | 0.030 | 100.0% |
| coverage_ratio_micro | FAIL | 1.277% | -0.319% | -1.061% | 40.9% | 0.016 | 100.0% |

**No features promoted from discovery. Program should proceed to next option or stop.**
