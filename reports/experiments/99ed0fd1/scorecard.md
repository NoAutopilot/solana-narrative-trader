# Run Scorecard

**run_id**: `99ed0fd1`  
**observer**: `pfm_reversion_observer_v1`  
**decision_threshold**: n=50  
**generated_at**: `2026-03-09T15:28:09Z`  

---

## PRIMARY VIEW: ALL_COMPLETED_VIEW

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 20 |
| n_entry_ok_pairs | 20 |
| n_due_5m | 20 |
| n_pairs_complete_5m | 20 |
| n_fail_5m | 0 |
| entry_quote_coverage_pct | 100.0 |
| conditional_5m_coverage_pct | 100.0 |
| unconditional_5m_completion_pct | 100.0 |
| row_valid_signal | 20 |
| row_invalid_signal | 0 |
| row_valid_control | 20 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 0 |
| other_fail_control | 0 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 461 |
| jitter_1m.max | 462 |
| jitter_5m.p50 | 5 |
| jitter_5m.p95 | 222 |
| jitter_5m.max | 223 |
| dt_from_entry_1m.p50 | 60 |
| dt_from_entry_1m.p95 | 61 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 293 |
| dt_from_entry_5m.p95 | 303 |
| dt_from_entry_5m.max | 303 |

### Performance

| Metric | Value |
|--------|-------|
| n | 20 |
| mean_delta_5m | +0.003549 |
| median_delta_5m | +0.000200 |
| pct_delta_positive | +50.000000 |
| std_delta_5m | +0.076256 |
| ci_95_t | [-0.030554, 0.037652] |
| ci_95_bootstrap_mean | [-0.028121, 0.038439] |
| ci_95_bootstrap_median | [-0.053541, 0.032134] |
| sign_test_p_value | +1.000000 |
| mean_signal_net_5m | -0.045398 |
| mean_control_net_5m | -0.048946 |
| outlier_count | 2 |
| top_contributor_share | +0.155200 |
| trimmed_mean_delta_5m | -0.004975 |
| winsorized_mean_delta_5m | -0.003875 |

### Classification (Primary)

**`ACCUMULATING`**  
Reason: n=20 < decision_threshold=50  

---

## ROBUSTNESS VIEW: TIMING_VALID_VIEW
(gate: row_valid=1, entry_ok=1, fwd_ok=1, abs(jitter_5m)<=20s)

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 20 |
| n_entry_ok_pairs | 20 |
| n_due_5m | 20 |
| n_pairs_complete_5m | 19 |
| n_fail_5m | 1 |
| entry_quote_coverage_pct | 100.0 |
| conditional_5m_coverage_pct | 95.0 |
| unconditional_5m_completion_pct | 95.0 |
| row_valid_signal | 19 |
| row_invalid_signal | 0 |
| row_valid_control | 19 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 0 |
| other_fail_control | 0 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 9 |
| jitter_1m.max | 10 |
| jitter_5m.p50 | 4 |
| jitter_5m.p95 | 9 |
| jitter_5m.max | 9 |
| dt_from_entry_1m.p50 | 61 |
| dt_from_entry_1m.p95 | 61 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 293 |
| dt_from_entry_5m.p95 | 303 |
| dt_from_entry_5m.max | 303 |

### Performance

| Metric | Value |
|--------|-------|
| n | 19 |
| mean_delta_5m | +0.003918 |
| median_delta_5m | +0.003377 |
| pct_delta_positive | +52.630000 |
| std_delta_5m | +0.078328 |
| ci_95_t | [-0.032022, 0.039857] |
| ci_95_bootstrap_mean | [-0.029317, 0.039215] |
| ci_95_bootstrap_median | [-0.065606, 0.03403] |
| sign_test_p_value | +1.000000 |
| mean_signal_net_5m | -0.046424 |
| mean_control_net_5m | -0.050341 |
| outlier_count | 2 |
| top_contributor_share | +0.155700 |
| trimmed_mean_delta_5m | -0.000700 |
| winsorized_mean_delta_5m | +0.002754 |

### Classification (Robustness)

**`ACCUMULATING`**  
Reason: n=19 < decision_threshold=50  
