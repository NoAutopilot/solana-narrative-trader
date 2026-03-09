# Run Scorecard

**run_id**: `0c5337dd-2488-4730-90b6-e371fd1e9511`  
**observer**: `lcr_continuation_observer_v1`  
**decision_threshold**: n=50  
**generated_at**: `2026-03-09T15:28:11Z`  

---

## PRIMARY VIEW: ALL_COMPLETED_VIEW

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 124 |
| n_entry_ok_pairs | 123 |
| n_due_5m | 122 |
| n_pairs_complete_5m | 122 |
| n_fail_5m | 0 |
| entry_quote_coverage_pct | 99.19 |
| conditional_5m_coverage_pct | 100.0 |
| unconditional_5m_completion_pct | 98.39 |
| row_valid_signal | 122 |
| row_invalid_signal | 0 |
| row_valid_control | 122 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 2 |
| other_fail_control | 2 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 9 |
| jitter_1m.max | 11 |
| jitter_5m.p50 | 4 |
| jitter_5m.p95 | 9 |
| jitter_5m.max | 10 |
| dt_from_entry_1m.p50 | 60 |
| dt_from_entry_1m.p95 | 61 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 301 |
| dt_from_entry_5m.p95 | 302 |
| dt_from_entry_5m.max | 303 |

### Performance

| Metric | Value |
|--------|-------|
| n | 122 |
| mean_delta_5m | +0.001227 |
| median_delta_5m | +0.001031 |
| pct_delta_positive | +68.030000 |
| std_delta_5m | +0.003951 |
| ci_95_t | [0.000512, 0.001942] |
| ci_95_bootstrap_mean | [0.000505, 0.001964] |
| ci_95_bootstrap_median | [0.000354, 0.002503] |
| sign_test_p_value | +0.000100 |
| mean_signal_net_5m | -0.012407 |
| mean_control_net_5m | -0.013634 |
| outlier_count | 0 |
| top_contributor_share | +0.031900 |
| trimmed_mean_delta_5m | +0.001326 |
| winsorized_mean_delta_5m | +0.001200 |

### Classification (Primary)

**`SUPPORTED AS RANKING FEATURE / NOT PROMOTABLE`**  
Reason: mean>0, median>0, CI_lo>0, but signal net <=0  

---

## ROBUSTNESS VIEW: TIMING_VALID_VIEW
(gate: row_valid=1, entry_ok=1, fwd_ok=1, abs(jitter_5m)<=20s)

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 124 |
| n_entry_ok_pairs | 123 |
| n_due_5m | 122 |
| n_pairs_complete_5m | 122 |
| n_fail_5m | 0 |
| entry_quote_coverage_pct | 99.19 |
| conditional_5m_coverage_pct | 100.0 |
| unconditional_5m_completion_pct | 98.39 |
| row_valid_signal | 122 |
| row_invalid_signal | 0 |
| row_valid_control | 122 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 2 |
| other_fail_control | 2 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 9 |
| jitter_1m.max | 11 |
| jitter_5m.p50 | 4 |
| jitter_5m.p95 | 9 |
| jitter_5m.max | 10 |
| dt_from_entry_1m.p50 | 60 |
| dt_from_entry_1m.p95 | 61 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 301 |
| dt_from_entry_5m.p95 | 302 |
| dt_from_entry_5m.max | 303 |

### Performance

| Metric | Value |
|--------|-------|
| n | 122 |
| mean_delta_5m | +0.001227 |
| median_delta_5m | +0.001031 |
| pct_delta_positive | +68.030000 |
| std_delta_5m | +0.003951 |
| ci_95_t | [0.000512, 0.001942] |
| ci_95_bootstrap_mean | [0.000505, 0.001964] |
| ci_95_bootstrap_median | [0.000354, 0.002503] |
| sign_test_p_value | +0.000100 |
| mean_signal_net_5m | -0.012407 |
| mean_control_net_5m | -0.013634 |
| outlier_count | 0 |
| top_contributor_share | +0.031900 |
| trimmed_mean_delta_5m | +0.001326 |
| winsorized_mean_delta_5m | +0.001200 |

### Classification (Robustness)

**`SUPPORTED AS RANKING FEATURE / NOT PROMOTABLE`**  
Reason: mean>0, median>0, CI_lo>0, but signal net <=0  
