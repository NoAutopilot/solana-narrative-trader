# Holdout Sweep Report — 30m

**Date:** 2026-03-15 02:20 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 30m (1800s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 18
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| buys_m5 | FAIL | 2.597% | 0.411% | -1.375% | 50.1% | 0.013 | 77.3% |
| sells_m5 | FAIL | 2.544% | 0.427% | -1.646% | 51.0% | 0.013 | 77.3% |
| buys_h1 | FAIL | 1.168% | -0.554% | -2.925% | 46.6% | 0.013 | 77.3% |
| sells_h1 | FAIL | 0.941% | -0.534% | -3.350% | 47.3% | 0.012 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 0.291% | -0.798% | -2.954% | 45.3% | 0.019 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 0.855% | -0.409% | -1.515% | 46.2% | 0.013 | 75.0% |
| buy_count_ratio_m5 | FAIL | 0.291% | -0.798% | -2.954% | 45.3% | 0.019 | 68.8% |
| buy_count_ratio_h1 | FAIL | 0.855% | -0.409% | -1.515% | 46.2% | 0.013 | 75.0% |
| avg_trade_usd_m5 | FAIL | 2.316% | -0.554% | -0.422% | 45.3% | 0.016 | 68.8% |
| avg_trade_usd_h1 | FAIL | 0.965% | -0.619% | -1.972% | 46.2% | 0.012 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 3.221% | -0.260% | 0.651% | 45.6% | 0.014 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 2.262% | -0.354% | -0.245% | 43.9% | 0.014 | 75.0% |
| r_m5_micro | PASS | 5.748% | 2.389% | 2.484% | 57.5% | 0.013 | 77.3% |
| rv_5m | FAIL | 1.028% | -0.565% | -3.471% | 48.4% | 0.011 | 77.1% |
| rv_1m | FAIL | 2.152% | 0.038% | -1.909% | 50.1% | 0.013 | 77.1% |
| range_5m | FAIL | 0.894% | -0.554% | -1.516% | 48.9% | 0.012 | 77.1% |
| liq_change_pct | FAIL | 0.065% | -0.572% | -3.485% | 46.4% | 0.017 | 77.1% |
| liq_cliff_flag | FAIL | -0.293% | -0.585% | -1.364% | 41.2% | 0.003 | 77.3% |

**Promoted to holdout:** r_m5_micro

## Holdout Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| r_m5_micro | PASS | 13.588% | 3.534% | 8.388% | 60.1% | 0.039 | 79.4% |
