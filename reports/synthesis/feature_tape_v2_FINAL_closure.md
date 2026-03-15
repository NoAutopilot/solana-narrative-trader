# Feature Tape v2 — FINAL Closure Memo

**Date:** 2026-03-15  
**Status:** CLOSED  
**Verdict:** No new live observer approved. Feature Acquisition v2 line is closed.

---

## Program Summary

Feature Acquisition v2 was the third and final attempt to identify a viable signal family from public on-chain data (universe_snapshot and microstructure_log) for a long-only token selection strategy on Solana. The program collected a full-universe dataset across 96 successful fires over approximately 36 hours, tested 42 features across 5 forward-return horizons (210 feature-horizon combinations), and found that no feature passed the discovery gates at any horizon.

---

## Dataset Specification

| Parameter | Value |
|-----------|-------|
| Primary dataset | First 96 successful fires |
| Primary analysis view | Eligible-only (4,065 rows) |
| Secondary audit view | Full universe (4,222 rows) |
| Primary horizons | +5m, +15m, +30m, +1h, +4h |
| Excluded horizon | +1d (deferred, not part of primary decision) |
| Collection period | 2026-03-12T21:45Z to 2026-03-14T09:30Z |
| Features tested | 42 (of 62 columns; 2 skipped due to zero coverage) |
| Feature-horizon combinations | 210 |
| Discovery / holdout split | 72 fires / 24 fires (75/25) |
| Discovery rows | 3,038 (eligible) |
| Holdout rows | 1,027 (eligible) |
| Frozen DB | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.db` |
| Frozen CSV | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.csv` |
| Manifest | `reports/synthesis/feature_tape_v2_final_manifest.json` |

---

## Gap Exclusions

A 12-hour data gap occurred on 2026-03-13 between 06:27Z and 18:43Z due to an upstream scanner failure (root cause: systemd daemon-reexec triggered by apt-daily-upgrade killed the supervisor process, and preflight_unified.py was missing from disk). Gap exclusions were applied on a per-horizon basis as documented in `reports/ops/feature_tape_v2_gap_note.md`. The borderline fire at 06:30Z (fire ID dc1485fe) was marked `borderline_all_horizons = 1` and excluded from primary analysis at all horizons.

| Horizon | Excluded Rows | Excluded Fires |
|---------|--------------|----------------|
| +5m | 47 | 1 |
| +15m | 94 | 2 |
| +30m | 140 | 3 |
| +1h | 227 | 5 |
| +4h | 763 | 17 |

---

## Label Coverage (Eligible-Only, N=4,065)

Labels were derived via epoch-based universe_snapshot price lookup with a +/-120 second matching window. Coverage is reduced at longer horizons due to the gap window.

| Horizon | Labeled Rows | Coverage |
|---------|-------------|----------|
| +5m | 3,943 | 97.0% |
| +15m | 3,857 | 94.9% |
| +30m | 3,703 | 91.1% |
| +1h | 3,448 | 84.8% |
| +4h | 2,772 | 68.2% |

---

## Results

**0 of 210 feature-horizon combinations passed discovery gates.**

The sweep tested each feature by sorting eligible rows into quintile buckets and evaluating the top bucket against eight promotion gates (G1 through G8). The dominant failure modes were G2 (median net-proxy negative), G3/G4 (confidence interval crosses zero), and G5 (win rate below threshold). The best-bucket net proxy was consistently negative or near zero across all features and horizons, indicating that no feature reliably separates future winners from the baseline.

**0 features reached holdout evaluation** because no feature passed discovery.

The full-sample sweep, subset-micro sweep, holdout evaluation, and benchmark comparison all confirm the same conclusion: the current feature space does not contain a viable signal for any of the tested horizons.

---

## Coverage Clarification: jup_vs_cpamm_diff_pct

| View | Non-Null | Total | Coverage |
|------|----------|-------|----------|
| Eligible-only | 2,629 | 4,065 | 64.7% |
| Full universe | 2,629 | 4,222 | 62.3% |

The approximately 35% null rate is structural: tokens without Jupiter quotes cannot have this field populated. This is not a data quality issue.

---

## Conclusion

Feature Acquisition v2 produced no viable signal family. No new live observer is approved. The Feature Acquisition v2 research line is closed.

This result, combined with the prior closures of the Momentum/Direction family (experiments 001-007), the Public-Data Long-Only Selection family (experiment 008, Feature Tape v1), and the current result (experiment 009, Feature Tape v2), establishes that the current public on-chain feature space (universe_snapshot + microstructure_log) does not contain a signal strong enough to overcome round-trip costs in a long-only token selection framework on Solana memecoins.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Final recommendation | `reports/synthesis/feature_family_sweep_v2_final_recommendation.md` |
| Full-sample sweep | `reports/synthesis/feature_family_sweep_v2_full_sample.md` |
| Subset-micro sweep | `reports/synthesis/feature_family_sweep_v2_subset_micro.md` |
| Holdout evaluation | `reports/synthesis/feature_family_sweep_v2_holdout.md` |
| Label maturity | `reports/synthesis/feature_tape_v2_label_maturity.md` |
| Manifest | `reports/synthesis/feature_tape_v2_final_manifest.json` |
| Gap note | `reports/ops/feature_tape_v2_gap_note.md` |
| 10-fire checkpoint | `reports/ops/feature_tape_v2_10_fire_checkpoint.md` |
| Preflight follow-up | `reports/ops/preflight_unified_followup.md` |
| Frozen DB | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.db` |
| Frozen CSV | `reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.csv` |
| Per-horizon sweep results | `reports/synthesis/sweeps_full_sample/v2_{5m,15m,30m,1h,4h}/` |
| This memo | `reports/synthesis/feature_tape_v2_FINAL_closure.md` |

---

## What Must Not Happen Next

No re-run of the same features with minor parameter changes is permitted. No live observer may be launched from this feature space. The no-go registry has been updated to reflect this closure. Any future research must use a fundamentally different data source or market structure, as documented in `reports/synthesis/post_v2_options.md`.
