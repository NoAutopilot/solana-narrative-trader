# Holdout Sweep Report — 1h

**Date:** 2026-03-15 02:21 UTC
**View:** PRIMARY (eligible-only)
**Horizon:** 1h (3600s)
**Fires:** 96 total (72 discovery, 24 holdout)
**Rows:** 4065 eligible (3038 discovery, 1027 holdout)
**Buckets:** 5 (quintile)
**Features tested:** 18
**Bonferroni correction:** Yes

---

## Discovery Results

| Feature | Status | Mean Net | Median Net | CI Lower (Mean) | Win Rate | Top-1 Share | Coverage |
|---------|--------|--------:|----------:|----------------:|--------:|------------:|---------:|
| buys_m5 | FAIL | 5.960% | -2.856% | -0.403% | 45.2% | 0.015 | 77.3% |
| sells_m5 | FAIL | 5.681% | -1.849% | -0.648% | 46.2% | 0.015 | 77.3% |
| buys_h1 | FAIL | 3.738% | -3.901% | -2.298% | 44.0% | 0.015 | 77.3% |
| sells_h1 | FAIL | 3.194% | -5.464% | -2.949% | 42.5% | 0.015 | 77.3% |
| buy_sell_ratio_m5 | FAIL | 3.145% | -0.719% | -1.758% | 47.0% | 0.023 | 68.8% |
| buy_sell_ratio_h1 | FAIL | 2.555% | -0.507% | -1.103% | 47.2% | 0.017 | 75.0% |
| buy_count_ratio_m5 | FAIL | 3.145% | -0.719% | -1.758% | 47.0% | 0.023 | 68.8% |
| buy_count_ratio_h1 | FAIL | 2.555% | -0.507% | -1.103% | 47.2% | 0.017 | 75.0% |
| avg_trade_usd_m5 | FAIL | 3.420% | -0.600% | -0.527% | 46.3% | 0.021 | 68.8% |
| avg_trade_usd_h1 | FAIL | 5.011% | -0.689% | 0.313% | 46.1% | 0.019 | 75.0% |
| vol_accel_m5_vs_h1 | FAIL | 4.447% | -0.208% | 1.011% | 47.8% | 0.023 | 75.0% |
| txn_accel_m5_vs_h1 | FAIL | 3.482% | -0.435% | -0.061% | 44.6% | 0.023 | 75.0% |
| r_m5_micro | FAIL | 5.912% | -0.824% | 0.797% | 47.8% | 0.015 | 77.3% |
| rv_5m | FAIL | 3.380% | -5.007% | -2.992% | 44.9% | 0.015 | 77.1% |
| rv_1m | FAIL | 5.056% | -1.849% | -0.794% | 47.5% | 0.016 | 77.1% |
| range_5m | FAIL | 4.320% | -4.109% | -1.907% | 44.9% | 0.015 | 77.1% |
| liq_change_pct | FAIL | 0.939% | -0.599% | -0.506% | 41.1% | 0.005 | 77.1% |
| liq_cliff_flag | FAIL | 0.968% | -0.614% | -0.458% | 41.4% | 0.004 | 77.3% |

**No features promoted from discovery. Program should proceed to next option or stop.**
