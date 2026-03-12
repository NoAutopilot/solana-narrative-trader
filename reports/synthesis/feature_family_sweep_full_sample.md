# Feature Family Sweep — Track A — Full-Sample Features

Generated: 2026-03-12T05:17:46.342839+00:00

## Net-Proxy Formula

```
net_proxy = r_forward_5m - round_trip_pct

Where:
  r_forward_5m   = (price_at_fire_plus_5m / price_at_fire) - 1
                   Source: universe_snapshot.price_usd
                   Entry:  latest snapshot with ts <= fire_time_epoch
                   Forward: closest snapshot to fire_time_epoch + 300s,
                            strictly after fire, within ±60s tolerance

  round_trip_pct = impact_buy_pct + impact_sell_pct
                   = CPAMM-based round-trip cost at fire snapshot time
                   Source: feature_tape_v1.round_trip_pct
                   PROXY ONLY: actual execution cost varies by venue,
                   size, and timing. Does not include fees or slippage.
```

## Exclusions

Rows with `label_quality IN (missing, missing_disk_gap)` are excluded
from all denominators. These correspond to the 20 fires missed during
the 11:15–15:45 UTC disk-full gap on 2026-03-11.

## Ranked Summary Table

| Feature | Coverage | Best Bucket Gross | Best Bucket Net | Gross Median | Tercile Diff (Gross) | Outlier Risk | Recommendation |
|---------|----------|-------------------|-----------------|--------------|----------------------|--------------|----------------|
| median_pool_r_m5 | 100.0% | +0.566% | +0.051% | +0.000% | +0.910% | LOW | CANDIDATE |
| breadth_positive_pct | 100.0% | +0.512% | -0.002% | +0.000% | +0.722% | LOW | SKIP |
| round_trip_pct | 100.0% | +0.336% | -0.197% | +0.000% | +0.341% | LOW | SKIP |
| impact_buy_pct | 100.0% | +0.336% | -0.197% | +0.000% | +0.348% | LOW | SKIP |
| impact_sell_pct | 100.0% | +0.336% | -0.198% | +0.000% | +0.348% | LOW | SKIP |
| liquidity_usd | 100.0% | +0.318% | -0.215% | +0.000% | -0.331% | LOW | SKIP |
| age_hours | 100.0% | +0.215% | -0.298% | +0.000% | -0.121% | LOW | SKIP |
| vol_h1 | 100.0% | +0.179% | -0.332% | +0.000% | -0.060% | LOW | SKIP |
| jup_vs_cpamm_diff_pct | 100.0% | +0.168% | -0.341% | +0.000% | +0.153% | LOW | SKIP |
| pool_dispersion_r_m5 | 100.0% | +0.136% | -0.378% | +0.000% | +0.013% | LOW | SKIP |

## Per-Feature Detail

### jup_vs_cpamm_diff_pct

- **Coverage**: 3773/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.168%
- **Best bucket net mean**: -0.341%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.153%
- **Tercile diff (net)**: +0.124%
- **Quintile top/bot (gross)**: -0.234% / +0.024%
- **Quintile top/bot (net)**: -0.775% / -0.477%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1257 | 0.0381 | 0.2540 | +0.002% | +0.000% | 0.0138 |
| 2 | 1257 | 0.2540 | 0.2732 | +0.168% | +0.000% | 0.0618 |
| 3 | 1259 | 0.2732 | 1.7631 | +0.155% | +0.000% | 0.0865 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1257 | 0.0381 | 0.2540 | -0.499% | -0.500% |
| 2 | 1257 | 0.2540 | 0.2732 | -0.341% | -0.510% |
| 3 | 1259 | 0.2732 | 1.7631 | -0.375% | -0.522% |

### round_trip_pct

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.336%
- **Best bucket net mean**: -0.197%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.341%
- **Tercile diff (net)**: +0.308%
- **Quintile top/bot (gross)**: +0.472% / -0.002%
- **Quintile top/bot (net)**: -0.071% / -0.501%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 0.0050 | 0.0050 | -0.005% | +0.000% | 0.0086 |
| 2 | 1258 | 0.0050 | 0.0051 | -0.005% | +0.000% | 0.0550 |
| 3 | 1258 | 0.0051 | 0.0063 | +0.336% | +0.000% | 0.0916 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 0.0050 | 0.0050 | -0.505% | -0.500% |
| 2 | 1258 | 0.0050 | 0.0051 | -0.513% | -0.510% |
| 3 | 1258 | 0.0051 | 0.0063 | -0.197% | -0.523% |

### impact_buy_pct

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.336%
- **Best bucket net mean**: -0.197%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.348%
- **Tercile diff (net)**: +0.315%
- **Quintile top/bot (gross)**: +0.460% / +0.000%
- **Quintile top/bot (net)**: -0.084% / -0.499%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 0.0025 | 0.0025 | -0.013% | +0.000% | 0.0076 |
| 2 | 1258 | 0.0025 | 0.0026 | +0.003% | +0.000% | 0.0552 |
| 3 | 1258 | 0.0026 | 0.0032 | +0.336% | +0.000% | 0.0916 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 0.0025 | 0.0025 | -0.513% | -0.500% |
| 2 | 1258 | 0.0025 | 0.0026 | -0.505% | -0.510% |
| 3 | 1258 | 0.0026 | 0.0032 | -0.197% | -0.523% |

### impact_sell_pct

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.336%
- **Best bucket net mean**: -0.198%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.348%
- **Tercile diff (net)**: +0.315%
- **Quintile top/bot (gross)**: +0.472% / -0.000%
- **Quintile top/bot (net)**: -0.071% / -0.500%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 0.0025 | 0.0025 | -0.012% | +0.000% | 0.0076 |
| 2 | 1258 | 0.0025 | 0.0026 | +0.002% | +0.000% | 0.0552 |
| 3 | 1258 | 0.0026 | 0.0032 | +0.336% | +0.000% | 0.0916 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 0.0025 | 0.0025 | -0.513% | -0.500% |
| 2 | 1258 | 0.0025 | 0.0026 | -0.506% | -0.510% |
| 3 | 1258 | 0.0026 | 0.0032 | -0.197% | -0.523% |

### breadth_positive_pct

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.512%
- **Best bucket net mean**: -0.002%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.722%
- **Tercile diff (net)**: +0.720%
- **Quintile top/bot (gross)**: +0.905% / +0.005%
- **Quintile top/bot (net)**: +0.391% / -0.509%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 20.5882 | 37.9310 | -0.209% | +0.000% | 0.0422 |
| 2 | 1258 | 37.9310 | 46.4286 | +0.022% | +0.000% | 0.0749 |
| 3 | 1258 | 46.4286 | 65.6250 | +0.512% | +0.000% | 0.0638 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 20.5882 | 37.9310 | -0.723% | -0.513% |
| 2 | 1258 | 37.9310 | 46.4286 | -0.491% | -0.513% |
| 3 | 1258 | 46.4286 | 65.6250 | -0.002% | -0.513% |

### median_pool_r_m5

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.566%
- **Best bucket net mean**: +0.051%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.910%
- **Tercile diff (net)**: +0.909%
- **Quintile top/bot (gross)**: +0.888% / -0.523%
- **Quintile top/bot (net)**: +0.373% / -1.036%
- **Recommendation**: CANDIDATE

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | -1.0900 | -0.0300 | -0.345% | +0.000% | 0.0663 |
| 2 | 1258 | -0.0300 | 0.0000 | +0.105% | +0.000% | 0.0458 |
| 3 | 1258 | 0.0000 | 0.5600 | +0.566% | +0.000% | 0.0704 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | -1.0900 | -0.0300 | -0.858% | -0.513% |
| 2 | 1258 | -0.0300 | 0.0000 | -0.409% | -0.512% |
| 3 | 1258 | 0.0000 | 0.5600 | +0.051% | -0.513% |

### pool_dispersion_r_m5

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.136%
- **Best bucket net mean**: -0.378%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.013%
- **Tercile diff (net)**: +0.012%
- **Quintile top/bot (gross)**: +0.218% / -0.310%
- **Quintile top/bot (net)**: -0.296% / -0.823%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 17.3500 | 31.8800 | +0.123% | +0.000% | 0.0899 |
| 2 | 1258 | 31.8800 | 48.2600 | +0.066% | +0.000% | 0.0369 |
| 3 | 1258 | 48.2600 | 140.2200 | +0.136% | +0.000% | 0.0452 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 17.3500 | 31.8800 | -0.391% | -0.514% |
| 2 | 1258 | 31.8800 | 48.2600 | -0.447% | -0.513% |
| 3 | 1258 | 48.2600 | 140.2200 | -0.378% | -0.513% |

### age_hours

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.215%
- **Best bucket net mean**: -0.298%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: -0.121%
- **Tercile diff (net)**: -0.094%
- **Quintile top/bot (gross)**: -0.013% / +0.115%
- **Quintile top/bot (net)**: -0.514% / -0.421%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 1.0436 | 18.7043 | +0.116% | +0.000% | 0.0960 |
| 2 | 1258 | 18.7672 | 11741.1380 | +0.215% | +0.000% | 0.0475 |
| 3 | 1258 | 11741.3880 | 28802.5597 | -0.005% | +0.000% | 0.0041 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 1.0436 | 18.7043 | -0.412% | -0.518% |
| 2 | 1258 | 18.7672 | 11741.1380 | -0.298% | -0.512% |
| 3 | 1258 | 11741.3880 | 28802.5597 | -0.506% | -0.500% |

### liquidity_usd

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.318%
- **Best bucket net mean**: -0.215%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: -0.331%
- **Tercile diff (net)**: -0.298%
- **Quintile top/bot (gross)**: -0.002% / +0.486%
- **Quintile top/bot (net)**: -0.502% / -0.057%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 5052.1300 | 46922.0100 | +0.318% | +0.000% | 0.0917 |
| 2 | 1258 | 46922.0100 | 358308.8300 | +0.020% | +0.000% | 0.0552 |
| 3 | 1258 | 358461.3000 | 9686735.3500 | -0.013% | +0.000% | 0.0058 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 5052.1300 | 46922.0100 | -0.215% | -0.523% |
| 2 | 1258 | 46922.0100 | 358308.8300 | -0.488% | -0.509% |
| 3 | 1258 | 358461.3000 | 9686735.3500 | -0.513% | -0.500% |

### vol_h1

- **Coverage**: 3774/3774 (100.0%)
- **Outlier risk**: LOW (top contributor share: 0.0261)
- **Best bucket gross mean**: +0.179%
- **Best bucket net mean**: -0.332%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: -0.060%
- **Tercile diff (net)**: -0.063%
- **Quintile top/bot (gross)**: -0.337% / +0.129%
- **Quintile top/bot (net)**: -0.850% / -0.379%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 1258 | 0.0000 | 11795.0800 | +0.179% | +0.000% | 0.0362 |
| 2 | 1258 | 11810.5900 | 45448.8500 | +0.028% | +0.000% | 0.0424 |
| 3 | 1258 | 45498.7500 | 4619205.5100 | +0.119% | +0.000% | 0.0916 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 1258 | 0.0000 | 11795.0800 | -0.332% | -0.513% |
| 2 | 1258 | 11810.5900 | 45448.8500 | -0.489% | -0.519% |
| 3 | 1258 | 45498.7500 | 4619205.5100 | -0.395% | -0.511% |

## Decision

**CANDIDATE FEATURES FOUND**: median_pool_r_m5

At least one feature shows positive net-proxy mean, non-negative median,
acceptable outlier risk, and sufficient coverage.
Recommend further evaluation for new live observer.
