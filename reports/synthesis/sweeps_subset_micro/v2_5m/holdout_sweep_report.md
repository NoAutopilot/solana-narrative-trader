# Holdout Sweep Report — 5m

**Date:** 2026-03-15 02:19 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 5m (300s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 18
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| buys_m5 | FAIL | 0.209% | -0.514% | -1.380% | 12.3% | 0.023 | 77.3% |
| sells_m5 | FAIL | 0.611% | -0.514% | -0.956% | 13.2% | 0.024 | 77.3% |
| buys_h1 | FAIL | -0.515% | -0.516% | -2.102% | 11.0% | 0.022 | 77.3% |
| sells_h1 | FAIL | -0.513% | -0.515% | -1.831% | 12.0% | 0.022 | 77.3% |
| buy_sell_ratio_m5 | FAIL | -0.350% | -0.516% | -1.172% | 10.4% | 0.038 | 68.8% |
| buy_sell_ratio_h1 | FAIL | -0.078% | -0.517% | -1.262% | 9.9% | 0.038 | 75.0% |
| buy_count_ratio_m5 | FAIL | -0.350% | -0.516% | -1.172% | 10.4% | 0.038 | 68.8% |
| buy_count_ratio_h1 | FAIL | -0.078% | -0.517% | -1.262% | 9.9% | 0.038 | 75.0% |
| avg_trade_usd_m5 | FAIL | 0.827% | -0.513% | -0.483% | 11.8% | 0.038 | 68.8% |
| avg_trade_usd_h1 | FAIL | -0.088% | -0.512% | -0.955% | 11.1% | 0.029 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 1.154% | -0.512% | -0.112% | 15.3% | 0.031 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 0.576% | -0.513% | -0.749% | 14.2% | 0.029 | 75.0% |
| r_m5_micro | FAIL | 0.982% | -0.517% | -0.583% | 13.6% | 0.027 | 77.3% |
| rv_5m | FAIL | -0.297% | -0.516% | -1.436% | 13.0% | 0.024 | 77.1% |
| rv_1m | FAIL | -0.141% | -0.518% | -1.829% | 11.4% | 0.026 | 77.1% |
| range_5m | FAIL | 0.235% | -0.516% | -1.024% | 13.6% | 0.023 | 77.1% |
| liq_change_pct | FAIL | -0.645% | -0.516% | -2.046% | 11.2% | 0.035 | 77.1% |
| liq_cliff_flag | FAIL | -0.591% | -0.515% | -1.027% | 11.3% | 0.006 | 77.3% |

**No features promoted from discovery. Program should proceed to next option or stop.**
