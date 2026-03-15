# Meteora LP State Study — Stage A Summary

**Program:** meteora_lp_state_stageA  
**Date:** 2026-03-15  
**Experiment:** 013  
**Status:** Stage A Complete  
**Author:** Manus AI  

---

## Verdict: CONDITIONAL GO

One of 18 hypothesis × horizon combinations passed all six gates. The passing result — **H2 toxic flow filter at +4h** — is structurally plausible and not a mean-reversion artifact. However, it depends on proxy metrics and has a concentration concern that must be resolved before Stage B.

---

## What Was Tested

This study asked whether Meteora DLMM LP positions show positive expected LP economics (fee income > impermanent loss + friction) under three identifiable pool states:

**H1 — Volatility-Fee State:** Do elevated fee/TVL ratio periods produce positive LP proxy? **No.** Mean is positive at +4h but median is consistently negative. The distribution is right-skewed; the majority of LP deployments in elevated-fee states lose money.

**H2 — Toxic Flow Filter:** Do large price moves (>5% per hour) produce positive LP proxy at extended horizons? **Yes, at +4h only.** The mechanism is fee income: in high-volatility periods, the fee proxy (base_fee × volume / TVL × 4 hours) exceeds the IL proxy in 68.7% of events. This is driven by fee income, not mean reversion.

**H3 — Launch/Bootstrap Toxicity:** Are launch pools (base_fee ≥ 2%, max_fee ≥ 5%) systematically bad for LPs? **Yes.** Launch pools show negative mean LP proxy at +1h and +4h. The elevated fees do not compensate for the extreme IL from early-trading volatility.

---

## The Passing Result

| Metric | Value |
|--------|-------|
| Hypothesis | H2 toxic flow filter |
| Horizon | +4h |
| N | 844 events |
| Winsorized mean net LP proxy | +1.033% |
| Median net LP proxy | +0.080% |
| % Positive | 54.9% |
| Bootstrap CI (mean) | [+0.580%, +2.909%] |
| Bootstrap CI (median) | [+0.023%, +0.217%] |
| Top-1 contributor share | 4.9% |
| Top-3 contributor share | 10.8% |

All six gates pass. The result survives exclusion of the two Memehouse-SOL pools (N=35) in mean terms, though the median becomes borderline (~+0.02%).

---

## Robustness Concerns

Three concerns must be addressed in Stage B before this result is actionable:

**1. Proxy accuracy.** The fee proxy uses base fee only (lower bound) and current-state TVL (not historical). The IL proxy uses constant-product AMM formula, not DLMM concentrated liquidity IL. Exact LP PnL from on-chain position data would resolve both.

**2. Memehouse-SOL concentration.** Two pools with 1 day of data each show +14% to +31% mean net LP proxy. These are economically implausible for sustained deployment (fee/TVL ratio of 80–97% per hour). Excluding them reduces the mean from +1.68% to ~+0.8% and makes the median borderline. Stage B must use a longer, more stable pool universe.

**3. Pool coverage.** Only 15 of 60 candidate pools had GeckoTerminal OHLCV data. The 45 missing pools may have different LP economics. The working sample skews toward more established pools.

---

## Stage B Criteria

Stage B (live LP state monitoring and exact PnL measurement) is justified only if:

1. Exact LP PnL data (from Helius or Bitquery) confirms positive net PnL for LP positions opened during toxic flow periods at +4h
2. The result holds across a broader pool universe (≥30 pools, ≥60 days of data)
3. Memehouse-style short-lived pools are excluded from the primary analysis
4. The CI lower bound remains > 0 after excluding the top 5% of events

**Stage B data requirement:** Helius API (paid) or Bitquery (paid) for position-level LP transaction data. Estimated cost: $50–200/month depending on query volume.

---

## Key Learnings

1. **Median is the right primary metric for LP proxy studies.** The mean is dominated by a few extreme events (Memehouse-SOL). The median tells the true story: most LP deployments in toxic-flow periods break even or slightly positive at +4h.

2. **Launch pools are systematically bad for LPs.** H3 is confirmed. High base fees do not compensate for early-trading IL. This is a useful negative result: avoid LP deployment in newly-launched pools regardless of fee level.

3. **The fee proxy is a lower bound.** Dynamic fees in DLMM can be significantly higher than base fee during volatile periods. If the fee proxy already shows positive expected value at +4h, the actual fee income is likely higher, strengthening the case for Stage B.

4. **The toxic-flow filter is counterintuitive but mechanically sound.** Large price moves generate large trading volume, which generates large fee income. If the LP position stays in range (not guaranteed), the fee income can exceed IL. This is the core hypothesis for Stage B.

---

## Files

| File | Path |
|------|------|
| Design | `reports/new_programs/meteora_lp_state_stageA_design.md` |
| Data | `reports/new_programs/meteora_lp_state_stageA_data.md` |
| Results | `reports/new_programs/meteora_lp_state_stageA_results.md` |
| Summary | `reports/new_programs/meteora_lp_state_stageA_summary.md` |
| Results CSV | `reports/new_programs/meteora_stageA_results.csv` |
| Analysis script | `scripts/meteora_lp_state_stageA.py` |

---

*End of Summary*
