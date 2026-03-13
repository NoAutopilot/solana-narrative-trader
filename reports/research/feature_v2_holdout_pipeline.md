# Feature v2 — Holdout Pipeline Specification

**Date:** 2026-03-12
**Author:** Manus AI
**Status:** PRE-REGISTERED — written before any v2 sweep data is examined

---

## Overview

This document defines the complete holdout pipeline for evaluating features derived from `feature_tape_v2` data. The pipeline is implemented in `scripts/holdout_sweep_v2.py` and must be run exactly once per holdout evaluation.

---

## Temporal Split

| Set | Fires | Fraction | Estimated Rows (eligible-only) |
|-----|-------|----------|-------------------------------|
| Discovery | First 72 fires (chronological) | 75% | ~2,100-2,700 |
| Holdout | Last 24 fires (chronological) | 25% | ~700-900 |

The split boundary is fire 73 by chronological order. There is no gap between sets because all features are strictly pre-fire (no lookahead). The split is strictly temporal — no random sampling, no stratified sampling.

### Minimum Sample Sizes

| Metric | Minimum | Action if Not Met |
|--------|---------|-------------------|
| Discovery rows (eligible) | 1,500 | Sweep is invalid; extend collection |
| Holdout rows (eligible) | 500 | Sweep is invalid; extend collection |
| Discovery fires | 50 | Sweep is invalid; extend collection |
| Holdout fires | 15 | Sweep is invalid; extend collection |
| Micro-covered rows in holdout (eligible) | 350 | Micro-native features cannot be evaluated on holdout |

---

## 8 Promotion Gates

A feature is promoted from discovery to holdout evaluation if it passes **all 8 gates** on the discovery set. It is then evaluated on the holdout set with the same 8 gates.

| Gate | Metric | Threshold | Computed On |
|------|--------|-----------|-------------|
| G1 | Mean net-proxy (winsorized p1/p99) | > 0 | Best bucket (tercile or quintile) |
| G2 | Median net-proxy (winsorized p1/p99) | > 0 | Best bucket |
| G3 | Bootstrap 95% CI lower bound (mean) | > 0 | 10,000 resamples on best bucket |
| G4 | Bootstrap 95% CI lower bound (median) | > -0.001 | 10,000 resamples on best bucket |
| G5 | Win rate (pct_positive_net) | > 52% | Best bucket |
| G6 | Top-1 contributor share | < 0.30 | Best bucket |
| G7 | Top-3 contributor share | < 0.50 | Best bucket |
| G8 | Coverage (eligible-only) | >= 70% | Full discovery set |

### Net-Proxy Formula

```
net_proxy = r_forward_{horizon} - round_trip_pct
```

Where `round_trip_pct` is from `universe_snapshot` (CPAMM-based). Rows where `round_trip_pct` is NULL are excluded from net-proxy computation.

### Winsorization

All net-proxy values are winsorized at the 1st and 99th percentiles before computing means, medians, and CIs. This is applied independently within each bucket.

### Bucketing

Features are bucketed into terciles (3 buckets) by default. If the discovery set has more than 2,000 eligible rows, quintiles (5 buckets) are used instead. Bucket boundaries are computed on the discovery set and frozen before holdout evaluation.

---

## 6 Kill Gates

These gates apply to a future live observer, not to the retrospective sweep. They are documented here for completeness and are implemented in `scripts/holdout_sweep_v2.py` as reference thresholds.

| Kill Gate | Metric | Threshold | Evaluation Window |
|-----------|--------|-----------|-------------------|
| K1 | Cumulative mean delta | < -1.0% | After 50 pairs |
| K2 | Cumulative median delta | < -0.5% | After 50 pairs |
| K3 | Win rate | < 45% | After 100 pairs |
| K4 | Maximum drawdown (cumulative) | < -5.0% | Any time |
| K5 | Consecutive losses | > 15 | Any time |
| K6 | Single-pair loss | < -20% | Any time |

---

## Multiple Testing Correction

| Features Tested on Holdout | Correction | Adjusted CI Level |
|---------------------------|------------|-------------------|
| 1-3 | None (pre-registered) | 95% |
| 4-5 | Bonferroni | 98.75% (for K=5) |
| 6+ | Not permitted; reduce feature list first | N/A |

The Bonferroni correction adjusts the significance level for G3 and G4 only. The other gates (G1, G2, G5, G6, G7, G8) are not adjusted because they are deterministic thresholds, not statistical tests.

---

## Pipeline Execution Steps

1. **Load data:** Read `feature_tape_v2` with `WHERE eligible = 1`.
2. **Validate sample sizes:** Check all minimum sample size requirements.
3. **Split:** Assign fires to discovery (first 75%) and holdout (last 25%).
4. **Label derivation:** Compute forward returns from `universe_snapshot` price data at each horizon.
5. **Discovery sweep:** For each candidate feature, bucket into terciles/quintiles, compute all 8 gate metrics.
6. **Feature selection:** Select features that pass all 8 gates on discovery.
7. **Freeze parameters:** Record bucket boundaries, cost assumptions, feature list.
8. **Holdout evaluation:** Apply frozen parameters to holdout set. Compute all 8 gate metrics.
9. **Report:** Generate `holdout_sweep_report.md` with full results.
10. **Manifest:** Generate provenance manifest (see `provenance_manifest_spec.md`).

---

## Script Location

```
scripts/holdout_sweep_v2.py
```

The script accepts the following arguments:

```
--db-path       Path to SQLite database (default: /root/solana_trader/data/solana_trader.db)
--horizon       Forward return horizon: 5m, 15m, 30m, 1h, 4h (required)
--view          Analysis view: primary (default) or secondary
--features      Comma-separated list of features to evaluate (default: all numeric features)
--output-dir    Output directory for reports and manifests
--dry-run       Validate sample sizes and split without running sweep
```

---

## Pre-Run Checklist

Before running the holdout sweep, the following must be confirmed:

- [ ] Collection is complete (96+ fires with no gaps)
- [ ] 10-fire health checkpoint has passed
- [ ] No hot-path changes since collection started
- [ ] Feature list is pre-registered (documented before running)
- [ ] Cost assumption is documented (round_trip_pct or fixed)
- [ ] This document has not been modified since collection started
