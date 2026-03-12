# Next Phase Decision

**Date:** 2026-03-12  
**Context:** Public-data long-only selection line closed. No new live observer approved from `feature_tape_v1`.  
**Author:** Manus AI

---

## Background

The momentum/direction family has been fully exhausted across six branches (PFM continuation, PFM reversion, LCR continuation, LCR rank-lift, age-conditioned retrospective, and the full feature-tape sweep at +5m/+15m/+30m). No branch produced a deployable edge. The public-data long-only selection line is closed.

This document presents exactly two forward paths. No other paths are in scope.

---

## PATH A — STOP PROGRAM

**Recommendation: Archive and halt.**

No further experimental work is conducted. The current infrastructure remains operational for the live observers already running, but no new observer development is initiated.

**Rationale:**

The feature-family sweep across 96 fires and three horizons produced no feature with positive mean net-proxy, positive median net-proxy, and acceptable concentration simultaneously — except `r_m5` at +30m in a subset-only, momentum-adjacent, CI-uncomputed result. This does not meet the promotion bar. The market structure tested (public-data, 15-minute fire cadence, CPAMM-based cost model) may be fundamentally incompatible with the long-only selection approach at these horizons given current transaction costs.

**What is preserved:**

All data, code, reports, and infrastructure remain intact on the VPS and GitHub. The observer framework, backup stack, and dashboard are operational. If conditions change (e.g., transaction costs fall, a genuinely new data source becomes available, or the program is restarted with a different hypothesis), the infrastructure is ready.

**What stops:**

No new feature collection. No new observer design. No new retrospective sweeps on the current dataset or any variant of the current feature families.

---

## PATH B — FEATURE ACQUISITION v2

**Recommendation: Build a genuinely new data family only. No live observer until the retrospective sweep passes all gates.**

No live observer is launched under Path B until a new retrospective sweep on a new feature family shows:

- positive net-proxy mean (winsorized)
- non-negative net-proxy median (winsorized)
- bootstrap 95% CI lower bound > 0
- acceptable concentration (top-1 contributor share < 0.30)
- adequate coverage (≥ 70% of candidate universe, or explicitly bounded subset with documented non-randomness)
- conceptually distinct from the momentum/direction family

**Candidate new feature families (in priority order):**

| Priority | Family | Rationale for novelty |
|----------|--------|-----------------------|
| 1 | Trade-by-trade order flow / urgency | Captures buyer/seller urgency at the individual trade level, not aggregated over 5m windows. Distinct from `r_m5`, `buy_sell_ratio_m5`, `signed_flow_m5` which are already tested. |
| 2 | Route / quote quality | Captures execution quality relative to fair value at fire time. `jup_vs_cpamm_diff_pct` was tested and failed; the new family would use multi-hop route depth, quote freshness, and cross-venue spread. |
| 3 | Market-state gating | Captures macro Solana market conditions (overall DEX volume, SOL price trend, network congestion) as a gate on whether any selection signal is valid. Not a selection feature itself — a validity gate. |

**Design note:** See `reports/synthesis/feature_acquisition_v2_design_note.md`.

**What does NOT happen under Path B:**

- No live observer is launched before the retrospective sweep passes all gates.
- No continuation, reversion, age-conditioned, or rank-lift variant of the current feature tape is re-run.
- No dashboard redesign.
- No strategy changes to existing live observers.

---

## Decision Required

Select one path. No hybrid or partial path is in scope.

| | Path A | Path B |
|--|--------|--------|
| New feature collection | No | Yes (new family only) |
| New live observer | No | No (until gates pass) |
| Infrastructure changes | No | Minimal (new capture script only) |
| Timeline | Immediate closure | 2–4 weeks for new collection |
| Risk | Program ends | New collection may also fail |
| Upside | Clean exit | Genuine new signal possible |
