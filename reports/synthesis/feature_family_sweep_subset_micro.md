# Feature Family Sweep — Track B — Micro-Derived Features (SUBSET-ONLY — non-random missingness)

Generated: 2026-03-12T05:17:46.451553+00:00

> **SUBSET-ONLY: Track B results reflect non-random missingness (Orca/Meteora micro scope gap). Do not generalise to full universe.**

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
| r_m5 | 78.5% | +0.824% | +0.304% | +0.000% | +1.222% | LOW | CANDIDATE |
| vol_accel_m5_vs_h1 | 78.5% | +0.706% | +0.192% | +0.000% | +1.079% | LOW | CANDIDATE |
| txn_accel_m5_vs_h1 | 78.5% | +0.616% | +0.101% | +0.000% | +0.954% | LOW | CANDIDATE |
| avg_trade_usd_m5 | 70.9% | +0.469% | -0.039% | +0.000% | +0.623% | LOW | SKIP |
| buy_sell_ratio_m5 | 70.9% | +0.433% | -0.086% | +0.000% | -0.080% | LOW | SKIP |
| signed_flow_m5 | 70.9% | +0.433% | -0.086% | +0.000% | -0.080% | LOW | SKIP |
| liq_change_pct | 78.4% | +0.389% | -0.128% | +0.000% | +0.654% | LOW | SKIP |

## Per-Feature Detail

### r_m5

- **Coverage**: 2964/3774 (78.5%)
- **Outlier risk**: LOW (top contributor share: 0.0269)
- **Best bucket gross mean**: +0.824%
- **Best bucket net mean**: +0.304%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +1.222%
- **Tercile diff (net)**: +1.226%
- **Quintile top/bot (gross)**: +1.325% / -0.372%
- **Quintile top/bot (net)**: +0.802% / -0.900%
- **Recommendation**: CANDIDATE

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 988 | -92.0300 | -1.1900 | -0.397% | +0.000% | 0.0774 |
| 2 | 988 | -1.1800 | 0.3700 | -0.010% | +0.000% | 0.0336 |
| 3 | 988 | 0.3800 | 75.5900 | +0.824% | +0.000% | 0.0862 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 988 | -92.0300 | -1.1900 | -0.921% | -0.518% |
| 2 | 988 | -1.1800 | 0.3700 | -0.518% | -0.509% |
| 3 | 988 | 0.3800 | 75.5900 | +0.304% | -0.514% |

### buy_sell_ratio_m5

- **Coverage**: 2677/3774 (70.9%)
- **Outlier risk**: LOW (top contributor share: 0.0273)
- **Best bucket gross mean**: +0.433%
- **Best bucket net mean**: -0.086%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: -0.080%
- **Tercile diff (net)**: -0.077%
- **Quintile top/bot (gross)**: +0.197% / +0.079%
- **Quintile top/bot (net)**: -0.316% / -0.441%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 892 | 0.0000 | 0.5000 | +0.065% | +0.000% | 0.0508 |
| 2 | 892 | 0.5000 | 0.6591 | +0.433% | +0.000% | 0.1063 |
| 3 | 893 | 0.6591 | 1.0000 | -0.015% | +0.000% | 0.0479 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 892 | 0.0000 | 0.5000 | -0.455% | -0.515% |
| 2 | 892 | 0.5000 | 0.6591 | -0.086% | -0.514% |
| 3 | 893 | 0.6591 | 1.0000 | -0.532% | -0.514% |

### signed_flow_m5

- **Coverage**: 2677/3774 (70.9%)
- **Outlier risk**: LOW (top contributor share: 0.0273)
- **Best bucket gross mean**: +0.433%
- **Best bucket net mean**: -0.086%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: -0.080%
- **Tercile diff (net)**: -0.077%
- **Quintile top/bot (gross)**: +0.197% / +0.079%
- **Quintile top/bot (net)**: -0.316% / -0.441%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 892 | -1.0000 | 0.0000 | +0.065% | +0.000% | 0.0508 |
| 2 | 892 | 0.0000 | 0.3182 | +0.433% | +0.000% | 0.1063 |
| 3 | 893 | 0.3182 | 1.0000 | -0.015% | +0.000% | 0.0479 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 892 | -1.0000 | 0.0000 | -0.455% | -0.515% |
| 2 | 892 | 0.0000 | 0.3182 | -0.086% | -0.514% |
| 3 | 893 | 0.3182 | 1.0000 | -0.532% | -0.514% |

### txn_accel_m5_vs_h1

- **Coverage**: 2964/3774 (78.5%)
- **Outlier risk**: LOW (top contributor share: 0.0269)
- **Best bucket gross mean**: +0.616%
- **Best bucket net mean**: +0.101%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.954%
- **Tercile diff (net)**: +0.960%
- **Quintile top/bot (gross)**: +0.597% / -0.279%
- **Quintile top/bot (net)**: +0.083% / -0.799%
- **Recommendation**: CANDIDATE

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 988 | 0.0000 | 0.4389 | -0.338% | +0.000% | 0.0534 |
| 2 | 988 | 0.4395 | 0.8692 | +0.139% | +0.000% | 0.0819 |
| 3 | 988 | 0.8693 | 12.0000 | +0.616% | +0.000% | 0.0709 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 988 | 0.0000 | 0.4389 | -0.859% | -0.516% |
| 2 | 988 | 0.4395 | 0.8692 | -0.378% | -0.514% |
| 3 | 988 | 0.8693 | 12.0000 | +0.101% | -0.513% |

### vol_accel_m5_vs_h1

- **Coverage**: 2964/3774 (78.5%)
- **Outlier risk**: LOW (top contributor share: 0.0269)
- **Best bucket gross mean**: +0.706%
- **Best bucket net mean**: +0.192%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +1.079%
- **Tercile diff (net)**: +1.083%
- **Quintile top/bot (gross)**: +0.473% / -0.247%
- **Quintile top/bot (net)**: -0.041% / -0.761%
- **Recommendation**: CANDIDATE

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 988 | 0.0000 | 0.3160 | -0.373% | +0.000% | 0.0375 |
| 2 | 988 | 0.3173 | 0.8463 | +0.083% | +0.000% | 0.0926 |
| 3 | 988 | 0.8463 | 12.0000 | +0.706% | +0.000% | 0.0677 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 988 | 0.0000 | 0.3160 | -0.891% | -0.514% |
| 2 | 988 | 0.3173 | 0.8463 | -0.435% | -0.515% |
| 3 | 988 | 0.8463 | 12.0000 | +0.192% | -0.513% |

### avg_trade_usd_m5

- **Coverage**: 2677/3774 (70.9%)
- **Outlier risk**: LOW (top contributor share: 0.0273)
- **Best bucket gross mean**: +0.469%
- **Best bucket net mean**: -0.039%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.623%
- **Tercile diff (net)**: +0.641%
- **Quintile top/bot (gross)**: +0.229% / +0.037%
- **Quintile top/bot (net)**: -0.276% / -0.487%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 892 | 0.0000 | 32.6051 | -0.154% | +0.000% | 0.0671 |
| 2 | 892 | 32.6416 | 65.5043 | +0.167% | +0.000% | 0.0805 |
| 3 | 893 | 65.5047 | 1554.0350 | +0.469% | +0.000% | 0.0719 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 892 | 0.0000 | 32.6051 | -0.681% | -0.518% |
| 2 | 892 | 32.6416 | 65.5043 | -0.353% | -0.518% |
| 3 | 893 | 65.5047 | 1554.0350 | -0.039% | -0.509% |

### liq_change_pct

- **Coverage**: 2958/3774 (78.4%)
- **Outlier risk**: LOW (top contributor share: 0.0269)
- **Best bucket gross mean**: +0.389%
- **Best bucket net mean**: -0.128%
- **Best bucket gross median**: +0.000%
- **Tercile diff (gross)**: +0.654%
- **Tercile diff (net)**: +0.655%
- **Quintile top/bot (gross)**: +0.609% / -0.439%
- **Quintile top/bot (net)**: +0.089% / -0.958%
- **Recommendation**: SKIP

**Tercile buckets (gross label):**

| Bucket | N | Feat Min | Feat Max | Label Mean | Label Median | Label Stdev |
|--------|---|----------|----------|------------|--------------|-------------|
| 1 | 986 | -0.9714 | 0.0000 | -0.265% | +0.000% | 0.0509 |
| 2 | 986 | 0.0000 | 0.0000 | +0.293% | +0.000% | 0.0647 |
| 3 | 986 | 0.0000 | 0.9858 | +0.389% | +0.000% | 0.0887 |

**Tercile buckets (net-proxy label):**

| Bucket | N | Feat Min | Feat Max | Net Mean | Net Median |
|--------|---|----------|----------|----------|------------|
| 1 | 986 | -0.9714 | 0.0000 | -0.783% | -0.516% |
| 2 | 986 | 0.0000 | 0.0000 | -0.223% | -0.513% |
| 3 | 986 | 0.0000 | 0.9858 | -0.128% | -0.513% |

## Decision

**CANDIDATE FEATURES FOUND**: r_m5, txn_accel_m5_vs_h1, vol_accel_m5_vs_h1

At least one feature shows positive net-proxy mean, non-negative median,
acceptable outlier risk, and sufficient coverage.
Recommend further evaluation for new live observer.
