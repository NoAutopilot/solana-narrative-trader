# Closure Memo — Feature Tape v1 / Public-Data Long-Only Selection Line

**Date:** 2026-03-12  
**Status:** CLOSED — NO NEW LIVE OBSERVER APPROVED  
**Author:** Manus AI

---

## Decision

The public-data long-only selection line is **abandoned**.

No new live observer is approved from the current `feature_tape_v1` dataset or any variant of the features tested within it. No continuation, reversion, age-conditioned, rank-lift, or horizon-extended variant of the current feature families will be re-run.

---

## What Was Done

`feature_tape_v1` collected pre-fire features for 96 fires over a 24-hour window (2026-03-11T00:45 UTC → 2026-03-12T05:15 UTC), producing 3,943 rows across ~103 unique candidate mints per fire. Labels were derived from `universe_snapshot` at +5m, +15m, and +30m horizons. Net-proxy labels were computed as `r_forward_Xm - round_trip_pct` (CPAMM-based round-trip cost, 100% coverage).

---

## Branches Tested and Final Classifications

| Branch | Horizon | Coverage | Best Net Mean (winsorized) | Best Net Median | Verdict |
|--------|---------|----------|---------------------------|-----------------|---------|
| **Track A — Full-Sample Features** | | | | | |
| median_pool_r_m5 | +5m | 100% | +0.051% | 0.000% | SKIP |
| breadth_positive_pct | +5m | 100% | −0.002% | 0.000% | SKIP |
| impact_buy/sell_pct | +5m | 100% | −0.197% | 0.000% | SKIP |
| round_trip_pct | +5m | 100% | −0.197% | 0.000% | SKIP |
| liquidity_usd | +5m | 100% | −0.215% | 0.000% | SKIP |
| pool_dispersion_r_m5 | +5m | 100% | −0.378% | 0.000% | SKIP |
| vol_h1 | +5m | 100% | −0.332% | 0.000% | SKIP |
| age_hours | +5m | 100% | −0.298% | 0.000% | SKIP |
| jup_vs_cpamm_diff_pct | +5m | 100% | −0.341% | 0.000% | SKIP |
| All Track A features | +15m | 100% | ≤ +0.091% | ≤ −0.400% | ALL SKIP |
| All Track A features | +30m | 100% | ≤ +0.910% | ≤ −0.400% | ALL SKIP |
| **Track B — Micro-Derived (Subset-Only)** | | | | | |
| r_m5 | +5m | 78.5% | +0.304% | −0.514% | SKIP (median < 0) |
| vol_accel_m5_vs_h1 | +5m | 78.5% | +0.192% | −0.513% | SKIP (median < 0) |
| txn_accel_m5_vs_h1 | +5m | 78.5% | +0.101% | 0.000% | SKIP |
| All Track B features | +15m | ~78% | ≤ +1.387% | ≤ −0.513% | ALL SKIP |
| r_m5 | +30m | 77.2% | +4.815% | +1.440% | SKIP — subset-only, momentum-adjacent, CI uncomputed |
| All other Track B | +30m | ~77% | ≤ +1.761% | ≤ −0.385% | ALL SKIP |

---

## Horizon Sweep Conclusion

The feature-family sweep was extended to +15m and +30m horizons to test whether the +5m failure was specific to transaction costs dominating at short horizons. The conclusion is that the failure is structural, not horizon-specific.

At +15m and +30m, raw means are dominated by a single extreme event (FURY token, +34,070% at +15m). After winsorization at p1/p99, Track A features remain negative at all horizons. The only combination that passes both the mean and median net-proxy gates is `r_m5` at +30m (winsorized), but this result is subset-only (Orca/Meteora excluded, ~22% of universe missing non-randomly), momentum-adjacent (same structural family as the abandoned momentum observer), and the bootstrap CI was not computed for the winsorized run. This is insufficient evidence for a new live observer.

---

## Root Cause Summary

The current public-data long-only selection line fails for two compounding reasons. First, round-trip transaction costs (~0.51%) consume all gross alpha at the +5m horizon. The gross return distributions are highly right-skewed: means are positive in the best bucket for several features, but medians are uniformly zero, indicating that the mean is driven by rare large-move events rather than a consistent per-trade edge. Second, the micro-derived features (Track B) that show the most promise are available only for Raydium/PumpSwap pools (~78% of the candidate universe), excluding Orca and Meteora pools in a non-random way that prevents generalisation.

---

## Durable Learnings

**Learning 1 — Round-trip cost is the binding constraint at short horizons.** At ~0.51% round-trip (CPAMM-based), a feature must produce a best-bucket gross mean well above 0.51% *and* a positive gross median to survive to a positive net-proxy median. No feature in the current family achieves this consistently.

**Learning 2 — Median is the correct primary gate, not mean.** The gross return distribution in this market is highly right-skewed. A positive mean net-proxy with a zero or negative median indicates an outlier-driven effect, not a deployable edge. The decision rule requiring both positive mean and positive median net-proxy is validated.

**Learning 3 — Non-random missingness in Track B invalidates generalisation.** The Orca/Meteora micro coverage gap is not random — it is correlated with pool type and liquidity tier. Any result from the micro-derived subset cannot be generalised to the full candidate universe without first closing the coverage gap.

**Learning 4 — The momentum/direction family is exhausted.** Continuation, reversion, age-conditioned, rank-lift, and now feature-tape-based momentum variants have all been tested. None produced a deployable edge. This family is closed.

**Learning 5 — The infrastructure built is durable.** The observer framework, feature tape collection pipeline, label derivation system, backup/compression/retention stack, dashboard sync policy, and GitHub workflow are all production-quality and reusable for any future feature acquisition effort.

---

## Artifacts

| Artifact | Path |
|----------|------|
| Feature tape dataset | `/root/solana_trader/data/solana_trader.db` → `feature_tape_v1` |
| Label dataset | `/root/solana_trader/data/solana_trader.db` → `feature_tape_v1_labels` |
| +5m sweep (full-sample) | `reports/synthesis/feature_family_sweep_full_sample.md` |
| +5m sweep (subset-micro) | `reports/synthesis/feature_family_sweep_subset_micro.md` |
| Track B robustness report | `reports/synthesis/trackb_robustness_report.md` |
| +15m sweep (raw + winsorized) | `reports/synthesis/feature_family_sweep_15m*.md` |
| +30m sweep (raw + winsorized) | `reports/synthesis/feature_family_sweep_30m*.md` |
| Label path proof | `reports/ops/label_path_proof_snapshot.csv` |
| Ranked summary | `reports/synthesis/feature_family_sweep_ranked_summary.csv` |

---

## Status After This Memo

- `feature_tape_v1` collection: **STOPPED** (96/96 fires complete)
- `derive_labels` loop: **STOPPED** (all labels derived)
- All artifacts: **BACKED UP** (local + GitHub)
- Public-data long-only selection line: **CLOSED**
- Next step: see `reports/synthesis/next_phase_decision.md`
