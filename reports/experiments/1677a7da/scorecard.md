# Run Scorecard

**run_id**: `1677a7da`  
**observer**: `pfm_continuation_observer_v1`  
**decision_threshold**: n=50  
**generated_at**: `2026-03-09T15:28:10Z`  

---

## PRIMARY VIEW: ALL_COMPLETED_VIEW

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 212 |
| n_entry_ok_pairs | 212 |
| n_due_5m | 212 |
| n_pairs_complete_5m | 212 |
| n_fail_5m | 0 |
| entry_quote_coverage_pct | 100.0 |
| conditional_5m_coverage_pct | 100.0 |
| unconditional_5m_completion_pct | 100.0 |
| row_valid_signal | 212 |
| row_invalid_signal | 0 |
| row_valid_control | 212 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 0 |
| other_fail_control | 0 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 9 |
| jitter_1m.max | 738 |
| jitter_5m.p50 | 5 |
| jitter_5m.p95 | 9 |
| jitter_5m.max | 499 |
| dt_from_entry_1m.p50 | 61 |
| dt_from_entry_1m.p95 | 62 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 293 |
| dt_from_entry_5m.p95 | 303 |
| dt_from_entry_5m.max | 304 |

### Performance

| Metric | Value |
|--------|-------|
| n | 212 |
| mean_delta_5m | +0.007804 |
| median_delta_5m | +0.000057 |
| pct_delta_positive | +50.000000 |
| std_delta_5m | +0.111305 |
| ci_95_t | [-0.007485, 0.023093] |
| ci_95_bootstrap_mean | [-0.00682, 0.023222] |
| ci_95_bootstrap_median | [-0.012173, 0.012034] |
| sign_test_p_value | +1.000000 |
| mean_signal_net_5m | -0.022255 |
| mean_control_net_5m | -0.030059 |
| outlier_count | 54 |
| top_contributor_share | +0.038300 |
| trimmed_mean_delta_5m | +0.001681 |
| winsorized_mean_delta_5m | +0.004049 |

### Classification (Primary)

**`FRAGILE / INCONCLUSIVE`**  
Reason: mean>0 but median<=0 or CI_lo<=0  

---

## ROBUSTNESS VIEW: TIMING_VALID_VIEW
(gate: row_valid=1, entry_ok=1, fwd_ok=1, abs(jitter_5m)<=20s)

### Health

| Metric | Value |
|--------|-------|
| n_fires_total | 212 |
| n_entry_ok_pairs | 212 |
| n_due_5m | 212 |
| n_pairs_complete_5m | 211 |
| n_fail_5m | 1 |
| entry_quote_coverage_pct | 100.0 |
| conditional_5m_coverage_pct | 99.53 |
| unconditional_5m_completion_pct | 99.53 |
| row_valid_signal | 211 |
| row_invalid_signal | 0 |
| row_valid_control | 211 |
| row_invalid_control | 0 |
| http_429_signal | 0 |
| http_429_control | 0 |
| other_fail_signal | 0 |
| other_fail_control | 0 |
| jitter_1m.p50 | 5 |
| jitter_1m.p95 | 9 |
| jitter_1m.max | 10 |
| jitter_5m.p50 | 5 |
| jitter_5m.p95 | 9 |
| jitter_5m.max | 11 |
| dt_from_entry_1m.p50 | 61 |
| dt_from_entry_1m.p95 | 62 |
| dt_from_entry_1m.max | 62 |
| dt_from_entry_5m.p50 | 293 |
| dt_from_entry_5m.p95 | 303 |
| dt_from_entry_5m.max | 304 |

### Performance

| Metric | Value |
|--------|-------|
| n | 211 |
| mean_delta_5m | +0.007729 |
| median_delta_5m | -0.000513 |
| pct_delta_positive | +49.760000 |
| std_delta_5m | +0.111564 |
| ci_95_t | [-0.007632, 0.02309] |
| ci_95_bootstrap_mean | [-0.007171, 0.022736] |
| ci_95_bootstrap_median | [-0.012174, 0.010599] |
| sign_test_p_value | +1.000000 |
| mean_signal_net_5m | -0.022337 |
| mean_control_net_5m | -0.030066 |
| outlier_count | 54 |
| top_contributor_share | +0.038400 |
| trimmed_mean_delta_5m | +0.001551 |
| winsorized_mean_delta_5m | +0.003956 |

### Classification (Robustness)

**`FRAGILE / INCONCLUSIVE`**  
Reason: mean>0 but median<=0 or CI_lo<=0  
