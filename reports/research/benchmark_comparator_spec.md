# Benchmark Comparator Specification

**Date:** 2026-03-12
**Author:** Manus AI
**Status:** RATIFIED — cold-path documentation

---

## Purpose

The benchmark comparator ensures that any new feature family result is evaluated against two reference registries before promotion decisions are made. This prevents re-testing of exhausted hypotheses and provides a consistent baseline for comparison.

---

## Reference Registries

### Benchmark Suite v1

The benchmark suite contains the best results from the `feature_tape_v1` sweep across all tested features, horizons, and tracks. These represent the **ceiling** of what the momentum/direction family achieved.

**Source:** `reports/synthesis/feature_family_sweep_ranked_summary.csv` (5m), `feature_family_sweep_15m.csv` (15m), `feature_family_sweep_30m.csv` (30m)

| Metric | Best v1 Result | Feature | Horizon |
|--------|---------------|---------|---------|
| Best gross mean (winsorized) | +0.304% | r_m5 (micro) | +5m |
| Best gross median | 0.000% | All features | All |
| Best net mean (winsorized) | -0.197% to +0.051% | Various | +5m |
| Best net median | 0.000% or negative | All features | All |
| Best win rate | ~50% | All features | All |

### No-Go Registry v1

The no-go registry contains features and hypotheses that have been conclusively tested and rejected. Any new result that is structurally equivalent to a no-go entry must be flagged.

| Entry | Hypothesis | Verdict | Reason |
|-------|-----------|---------|--------|
| NG-001 | Momentum (r_m5) predicts +5m returns | REJECTED | Median = 0, CI crosses zero |
| NG-002 | Order-flow ratio (buy_sell_ratio_m5) predicts +5m returns | REJECTED | Median = 0, mean outlier-driven |
| NG-003 | Volume acceleration predicts +5m returns | REJECTED | Median = 0 |
| NG-004 | Transaction acceleration predicts +5m returns | REJECTED | Median = 0 |
| NG-005 | Execution quality (round_trip_pct, impact) predicts +5m returns | REJECTED | Near-zero tercile differentiation |
| NG-006 | Liquidity level predicts +5m returns | REJECTED | Median = 0 |
| NG-007 | Age predicts +5m returns | REJECTED | Median = 0 |
| NG-008 | Market breadth predicts +5m returns | REJECTED | Median = 0 |
| NG-009 | Any momentum/direction variant at +15m | REJECTED | Same structural failure |
| NG-010 | Any momentum/direction variant at +30m (full universe) | REJECTED | Same structural failure |
| NG-011 | Product-form pivot (basket) fixes weak signal | REJECTED | Cannot fix zero-median signal |

---

## Comparator Logic

The comparator script (`scripts/benchmark_comparator_v2.py`) performs three checks for each new feature result:

### Check 1: Novelty Gate

Does the new feature belong to a family already in the no-go registry?

```
IF new_feature is structurally_equivalent_to(no_go_entry):
    FLAG: "This feature is structurally equivalent to {no_go_entry}. 
           The hypothesis was already rejected."
    RECOMMENDATION: SKIP unless the new feature has a documented 
                    structural distinction.
```

Structural equivalence is determined by feature family membership. The following families are exhausted:

- **Momentum/direction:** r_m5, r_h1, continuation, reversion, rank-lift
- **Aggregated order-flow:** buy_sell_ratio_m5/h1, signed_flow, vol_accel, txn_accel
- **Execution quality:** round_trip_pct, impact_buy/sell, jup_vs_cpamm_diff_pct
- **Static fundamentals:** age_hours, liquidity_usd, vol_h1/h24

### Check 2: Improvement Gate

Does the new feature's best result exceed the v1 benchmark ceiling?

```
IF new_result.mean_net > best_v1_mean_net AND
   new_result.median_net > best_v1_median_net AND
   new_result.win_rate > best_v1_win_rate:
    STATUS: "Exceeds v1 benchmark on all three metrics."
ELSE:
    FLAG: "Does not exceed v1 benchmark on {failed_metrics}."
```

### Check 3: Structural Distinction

Does the new feature address at least one of the three binding constraints identified in v1?

| Constraint | How to Address |
|-----------|---------------|
| C1: Round-trip cost consumes gross alpha | Feature must produce gross mean >> 0.51% |
| C2: Median is zero (outlier-driven mean) | Feature must produce positive median |
| C3: Non-random micro coverage gap | Feature must have >= 70% coverage or use non-micro source |

```
IF new_result addresses C1 OR C2 OR C3:
    STATUS: "Addresses binding constraint {constraint}."
ELSE:
    FLAG: "Does not address any binding constraint from v1."
```

---

## Script Interface

```
python3 scripts/benchmark_comparator_v2.py \
    --results-json reports/sweeps/v2_5m/holdout_sweep_results.json \
    --output-dir reports/sweeps/v2_5m/
```

The script reads the holdout sweep results JSON and produces:

- `benchmark_comparison.md` — human-readable comparison report
- `benchmark_comparison.json` — machine-readable comparison results
