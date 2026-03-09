# LEARNINGS LEDGER

Canonical record of completed experiments, their outcomes, and durable learnings.
Each entry is immutable once written. Append only.

---

## Entry 001 — PFM Continuation Observer
**run_id:** `1677a7da`
**Period:** 2026-03-07T01:15Z → 2026-03-09T06:28Z (≈53 hours)
**Service:** `solana-pfm-cont-observer.service` (stopped and disabled 2026-03-09T06:28Z)
**Final classification:** `RANKING FEATURE ONLY / NOT PROMOTABLE`

### Hypothesis tested
> Among matched token pairs in the `pumpfun_mature` lane, the token with higher recent 5-minute momentum (`entry_r_m5 > 0`, signal) outperforms the token with lower momentum (`entry_r_m5 < 0`, control) at a +5 minute horizon.

### Final metrics (canonical View B, n=212)

| Metric | Value |
|---|---|
| n_pairs_complete_5m | 212 |
| mean_delta_+5m | +0.007804 |
| median_delta_+5m | +0.000057 |
| % delta > 0 | 50.0% (106/212) |
| 95% CI | [−0.007806, +0.023414] |
| mean_signal_net_+5m | −0.022255 |
| mean_control_net_+5m | −0.030059 |

### Data quality
All gates passed: entry_coverage=100%, 5m_coverage=100%, row_valid=100%, HTTP_429=0.

### Why not promotable
The signal token outperforms its control on average, but loses money in absolute terms (mean_signal_net = −0.022). The CI crosses zero. The median delta is near zero. The relative edge is real but not large enough or consistent enough to constitute a tradeable directional signal.

### Regime filter sidecar result
`pfm_continuation_regime_filter_sidecar_v1`: tested breadth_positive, median_r_m5_positive, signal_r_m5_strong (tercile + quintile) across 187 pairs with pool data. No subgroup produced mean_signal_net > 0. Verdict: `RANKING FEATURE ONLY`.

### Durable learnings
1. **Positive relative delta ≠ promotable signal.** A signal that loses less than its control is a ranking feature, not a directional edge. Promotion requires mean_signal_net > 0.
2. **Regime filters did not rescue continuation.** The breadth and median-r_m5 filters did not improve absolute signal net. The `median_r_m5_positive` filter actually worsened mean delta (−0.004 vs +0.010 baseline), suggesting continuation is weaker during rising-pool regimes.
3. **Outlier sensitivity is high.** top_contributor_share ≈ 0.038 across all subgroups; 54/212 pairs were outliers (|delta| ≥ 0.10). The mean is driven by a fat tail, not a consistent edge.
4. **Data quality infrastructure is solid.** The observer framework, canonical report script, and reconciliation tooling all worked correctly. The reporting discrepancy (dashboard vs reconciliation) was a sample-size snapshot issue, not a data bug.
5. **Reversion hypothesis is now the natural next test.** If continuation is a ranking feature, the inverse (r_m5 < 0 signal) may produce a reversion edge. This is the next preregistered experiment.

---

## Entry 002 — LCR Continuation Observer
**run_id:** `0c5337dd-2488-4730-90b6-e371fd1e9511` (primary; 2 additional runs pooled)
**Family:** `lcr_continuation_observer_v1`
**Lane:** `lcr`
**Direction:** continuation
**Final classification:** `SUPPORTED AS RANKING FEATURE / NOT PROMOTABLE`

### Hypothesis tested
> Among matched token pairs in the `lcr` lane, the token with higher recent momentum (signal) outperforms the token with lower momentum (control) at a +5 minute horizon.

### Final metrics (ALL_COMPLETED_VIEW, n=122 primary; n=286 pooled)

| Metric | Value (primary) | Value (pooled) |
|--------|----------------|----------------|
| n_pairs_complete_5m | 122 | 286 |
| mean_delta_+5m | +0.001238 | — |
| % delta > 0 | 62.5% | — |
| mean_signal_net_+5m | −0.010902 | — |
| mean_control_net_+5m | −0.012139 | — |

### Durable learnings
1. **LCR continuation shows a persistent positive relative delta** across multiple runs, but absolute signal net is negative in all runs. The edge is real as a ranking signal only.
2. **LCR continuation is not a standalone promotable long signal at +5m.**
3. **Next branch:** Test whether LCR continuation signal can be used as a filter or ranking layer on top of another entry criterion that produces positive absolute net.

---

## Entry 003 — PFM Reversion Observer (in progress)
**run_id:** `99ed0fd1`
**Family:** `pfm_reversion_observer_v1`
**Lane:** `pumpfun_mature`
**Direction:** reversion
**Classification:** `ACCUMULATING` (n=20 of 50 required for decision)

### Hypothesis tested
> Among matched token pairs in the `pumpfun_mature` lane, the token with the most negative recent 5-minute momentum (`entry_r_m5 < 0`, signal) outperforms the token with non-negative momentum (`entry_r_m5 >= 0`, control) at a +5 minute horizon.

### Current metrics (ALL_COMPLETED_VIEW, n=20)

| Metric | Value |
|--------|-------|
| n_pairs_complete_5m | 20 |
| mean_delta_+5m | +0.003549 |
| median_delta_+5m | +0.003377 |
| mean_signal_net_+5m | −0.045398 |
| mean_control_net_+5m | −0.048946 |
| entry_coverage | 100% |
| row_valid | 100% |

### Notes
Early data quality is clean. Relative delta is mildly positive but n is too small for classification. Decision checkpoint at n=50.

---
