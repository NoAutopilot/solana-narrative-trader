# Feature Tape v2 — 10-Fire Health Checkpoint

**Run:** feature_tape_v2 (current run, started 2026-03-12T21:34:41Z)
**Checkpoint window:** Fires 1–10 (2026-03-12T21:45:00Z → 2026-03-13T00:00:00Z)
**Report generated:** 2026-03-13T18:50Z (retro-generated; collection was healthy through fire 36)
**Verdict:** **PASS**

---

## 1. Fire Coverage

All 10 fires completed successfully with zero missed fires and zero hard errors. Each fire
wrote exactly the number of candidates found, confirming no partial-write failures.

| Fire # | Fire ID  | Fire Time (UTC)       | Candidates | Rows Written | Duration (s) |
|--------|----------|-----------------------|------------|--------------|--------------|
| 1      | 4578ac6b | 2026-03-12T21:45:00Z  | 38         | 38           | 0.02         |
| 2      | b96da477 | 2026-03-12T22:00:00Z  | 43         | 43           | 0.01         |
| 3      | bc3dd0a8 | 2026-03-12T22:15:00Z  | 42         | 42           | 0.01         |
| 4      | e593e168 | 2026-03-12T22:30:00Z  | 44         | 44           | 0.01         |
| 5      | de2f92ce | 2026-03-12T22:45:00Z  | 42         | 42           | 0.01         |
| 6      | 65443c57 | 2026-03-12T23:00:00Z  | 47         | 47           | 0.02         |
| 7      | 8ecbccd5 | 2026-03-12T23:15:00Z  | 44         | 44           | 0.01         |
| 8      | b6fa4827 | 2026-03-12T23:30:00Z  | 47         | 47           | 0.01         |
| 9      | 4ddb9333 | 2026-03-12T23:45:00Z  | 43         | 43           | 0.01         |
| 10     | 7c77cb51 | 2026-03-13T00:00:00Z  | 48         | 48           | 0.01         |

**Total rows in first 10 fires:** 438
**Rows per fire range:** 38–48 (stable, no outliers)
**Missed fires:** 0
**Hard errors:** 0

---

## 2. Null Lane Check

**Null lanes: 0 / 438 rows.** All rows have a derived lane value. This confirms the lane
derivation logic introduced in commit d5bcf3f is functioning correctly across all 10 fires.

Lane distribution across first 10 fires:

| Lane             | Count | % of Total |
|------------------|-------|------------|
| pumpswap_live    | 273   | 62.3%      |
| raydium_live     | 85    | 19.4%      |
| orca_live        | 58    | 13.2%      |
| spam_filtered    | 12    | 2.7%       |
| meteora_live     | 10    | 2.3%       |

---

## 3. Eligibility

| Status      | Count | % of Total |
|-------------|-------|------------|
| Eligible    | 426   | 97.3%      |
| Ineligible  | 12    | 2.7%       |

The 12 ineligible rows are all `spam_filtered` (gate reason: `spam:avg_trade_usd=<value>`),
which is expected behaviour per the semantic rules. These rows are intentionally retained in
the table for completeness.

---

## 4. Feature Coverage

Coverage computed over all 438 rows in fires 1–10. Microstructure-family features are gated
by the availability of a matching `microstructure_log` record within the fire window; the
~25–34% null rate for those fields is expected and consistent with the source-map specification.
Quote, breadth, and pool family features are near-universal.

| Feature                  | Family          | % Non-null | Assessment         |
|--------------------------|-----------------|------------|--------------------|
| r_m5_micro               | Microstructure  | 75.3%      | Expected (gated)   |
| buy_sell_ratio_m5        | Microstructure  | 66.0%      | Expected (gated)   |
| txn_accel_m5_vs_h1       | Microstructure  | 70.8%      | Expected (gated)   |
| vol_accel_m5_vs_h1       | Microstructure  | 70.8%      | Expected (gated)   |
| avg_trade_usd_m5         | Microstructure  | 66.0%      | Expected (gated)   |
| jup_vs_cpamm_diff_pct    | Quote           | 97.3%      | Healthy            |
| round_trip_pct           | Quote           | 100.0%     | Healthy            |
| impact_buy_pct           | Quote           | 100.0%     | Healthy            |
| impact_sell_pct          | Quote           | 100.0%     | Healthy            |
| breadth_positive_pct     | Breadth         | 100.0%     | Healthy            |
| median_pool_r_m5         | Pool            | 100.0%     | Healthy            |
| pool_dispersion_r_m5     | Pool            | 100.0%     | Healthy            |

**Missingness bias:** No obvious fire-local instability or new missingness regression observed in the first 10 fires. Structural missingness bias remains to be assessed in the full run.

---

## 5. Label Coverage

Labels are not yet derived. The `derive_labels.py` script is triggered by the autopilot at
step 2, after 96 fires are complete. At the time of this checkpoint (fires 1–10), no label
columns exist in the schema. This is expected.

**Label columns present:** None (expected at this stage)
**missing_disk_gap rows:** N/A (column not yet in schema)

---

## 6. Service Status at Checkpoint Time

The collector service (`solana-feature-tape-v2.service`, PID 179477) was active and running
continuously throughout fires 1–10. No restarts, no gaps, no WAL corruption events.

---

## 7. Venue Distribution

| Venue     | Count | % of Total |
|-----------|-------|------------|
| pumpswap  | 278   | 63.5%      |
| raydium   | 90    | 20.5%      |
| orca      | 60    | 13.7%      |
| meteora   | 10    | 2.3%       |

---

## 8. Gate Reason Summary

All ineligible rows are spam-filtered on `avg_trade_usd` (dollar value per trade below
threshold). No unexpected gate reasons observed.

| Gate Reason                  | Count |
|------------------------------|-------|
| spam:avg_trade_usd=0.07      | 3     |
| spam:avg_trade_usd=0.11      | 2     |
| spam:avg_trade_usd=0.00      | 2     |
| spam:avg_trade_usd=0.43      | 1     |
| spam:avg_trade_usd=0.20      | 1     |
| spam:avg_trade_usd=0.19      | 1     |
| spam:avg_trade_usd=0.18      | 1     |
| spam:avg_trade_usd=0.16      | 1     |

---

## 9. Checkpoint Verdict

**PASS.** All gate checks pass:

- Zero null lanes across 438 rows
- Zero missed fires in the 10-fire window
- Zero hard errors or service restarts
- Feature coverage consistent with semantic rules (microstructure gating expected)
- Eligibility rate 97.3% (12 spam-filtered rows, all expected)
- No label-quality issues (labels not yet derived, as expected)
- Collection path intact: collect → 96 fires → label maturity → final sweep

*Note: This report was retro-generated on 2026-03-13T18:50Z from the first 10 fire records
in the live database. The collection run was healthy through fire 36 before the upstream
snapshot writer (et_universe_scanner.py, managed by supervisor.py under solana-trader.service)
stalled due to a missing preflight_unified.py file. That issue was resolved and collection
resumed at fire 37 (2026-03-13T18:45:00Z).*
