# Track B Robustness Report — Final (96 fires)

Generated: 2026-03-12T05:19:14.917522+00:00

> **SUBSET-ONLY**: Track B results reflect non-random missingness.
> Missing rows = Orca/Meteora micro scope gap (~21-29%).
> Do NOT generalise to full universe.

## Net-Proxy Formula

```
net_proxy = r_forward_5m - round_trip_pct
```

Bootstrap: 10,000 resamples, 95% CI, seed=42.

## r_m5 — Best Bucket (Top Tercile)

Feature range in bucket: [0.380 → 75.590]

| Metric | Value |
|--------|-------|
| n | 988 |
| Mean gross | +0.824% |
| Mean net-proxy | +0.304% |
| Median gross | +0.000% |
| Median net-proxy | -0.514% |
| Bootstrap 95% CI — mean net | [-0.230% → +0.859%] |
| Bootstrap 95% CI — median net | [-0.515% → -0.513%] |
| Top-1 contributor share | 0.034 |
| Top-3 contributor share | 0.101 |

### Venue Split

**PumpSwap** (n=0)
  insufficient sample (n<5)

**Raydium** (n=0)
  insufficient sample (n<5)

## vol_accel_m5_vs_h1 — Best Bucket (Top Tercile)

Feature range in bucket: [0.846 → 12.000]

| Metric | Value |
|--------|-------|
| n | 988 |
| Mean gross | +0.706% |
| Mean net-proxy | +0.192% |
| Median gross | +0.000% |
| Median net-proxy | -0.513% |
| Bootstrap 95% CI — mean net | [-0.209% → +0.627%] |
| Bootstrap 95% CI — median net | [-0.513% → -0.512%] |
| Top-1 contributor share | 0.045 |
| Top-3 contributor share | 0.124 |

### Venue Split

**PumpSwap** (n=0)
  insufficient sample (n<5)

**Raydium** (n=0)
  insufficient sample (n<5)

## Final Decision

**CANDIDATES PASSED ROBUSTNESS GATE:**
  - r_m5: mean_net>0=True, median_net>0=False, CI_lo>0=False, conc_ok=True
  - vol_accel_m5_vs_h1: mean_net>0=True, median_net>0=False, CI_lo>0=False, conc_ok=True

However: median net-proxy must also be > 0 for a YES recommendation.

**RECOMMENDATION: NO NEW LIVE OBSERVER**
Mean net-proxy is positive but median is zero or negative.
Effect is mean-driven by tail events. Not robust enough for live deployment.
