# Holdout Sweep Report — 15m

**Date:** 2026-03-15 02:20 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 15m (900s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 18
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| buys_m5 | FAIL | 1.263% | -0.514% | -1.309% | 26.8% | 0.014 | 77.3% |
| sells_m5 | FAIL | 1.600% | -0.513% | -0.783% | 26.3% | 0.015 | 77.3% |
| buys_h1 | FAIL | 0.364% | -0.516% | -1.945% | 23.4% | 0.015 | 77.3% |
| sells_h1 | FAIL | 0.170% | -0.516% | -2.382% | 23.6% | 0.015 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 0.217% | -0.517% | -1.719% | 25.6% | 0.020 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 0.022% | -0.518% | -1.513% | 21.1% | 0.027 | 75.0% |
| buy_count_ratio_m5 | FAIL | 0.217% | -0.517% | -1.719% | 25.6% | 0.020 | 68.8% |
| buy_count_ratio_h1 | FAIL | 0.022% | -0.518% | -1.513% | 21.1% | 0.027 | 75.0% |
| avg_trade_usd_m5 | FAIL | 1.233% | -0.514% | -0.726% | 23.0% | 0.022 | 68.8% |
| avg_trade_usd_h1 | FAIL | 0.228% | -0.519% | -1.756% | 22.3% | 0.019 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 2.097% | -0.511% | 0.386% | 26.9% | 0.022 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 0.798% | -0.514% | -0.953% | 25.7% | 0.019 | 75.0% |
| r_m5_micro | FAIL | 2.787% | -0.517% | 0.658% | 28.5% | 0.017 | 77.3% |
| rv_5m | FAIL | 0.378% | -0.515% | -1.381% | 26.4% | 0.014 | 77.1% |
| rv_1m | FAIL | 0.902% | -0.518% | -1.822% | 24.8% | 0.017 | 77.1% |
| range_5m | FAIL | 0.558% | -0.516% | -1.131% | 25.9% | 0.014 | 77.1% |
| liq_change_pct | FAIL | -0.039% | -0.516% | -2.375% | 21.2% | 0.030 | 77.1% |
| liq_cliff_flag | FAIL | -0.492% | -0.517% | -1.129% | 21.4% | 0.004 | 77.3% |

**No features promoted from discovery. Program should proceed to next option or stop.**
