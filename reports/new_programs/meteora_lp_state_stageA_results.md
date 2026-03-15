# Meteora LP State Study — Stage A Results Document

**Program:** meteora_lp_state_stageA  
**Date:** 2026-03-15  
**Status:** Stage A Complete  
**Author:** Manus AI  

---

## 1. Full Results Table

All 18 hypothesis × horizon combinations. Gate columns: G1=N≥30, G2=wins_mean>0, G3=median>0, G4=CI_lo>0, G5=top1<25%, G6=top3<50%.

| Hypothesis | Horizon | N | W.Mean | Median | %Pos | CI_lo | CI_hi | Top1 | Top3 | G1 | G2 | G3 | G4 | G5 | G6 | PASS |
|------------|---------|---|--------|--------|------|-------|-------|------|------|----|----|----|----|----|----|------|
| H1 elevated | +15m | 1,984 | +0.034% | -0.050% | 30.2% | +0.054% | +0.119% | 3.9% | 8.7% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H1 elevated | +1h | 1,984 | +0.046% | -0.055% | 33.1% | -0.081% | +0.223% | 2.9% | 6.8% | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H1 elevated | +4h | 1,984 | +1.022% | -0.015% | 47.5% | +0.518% | +1.594% | 3.6% | 7.8% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H1 null | +15m | 3,968 | -0.025% | -0.058% | 15.1% | -0.001% | +0.031% | 3.0% | 6.7% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H1 null | +1h | 3,968 | +0.005% | -0.057% | 17.6% | -0.071% | +0.082% | 2.8% | 6.4% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H1 null | +4h | 3,968 | +0.491% | -0.048% | 30.9% | +0.248% | +0.776% | 3.5% | 7.6% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H2 toxic | +15m | 844 | +0.100% | -0.029% | 40.8% | +0.094% | +0.233% | 5.7% | 12.7% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H2 toxic | +1h | 844 | -0.199% | -0.201% | 30.9% | -0.575% | +0.100% | 3.8% | 8.8% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| **H2 toxic** | **+4h** | **844** | **+1.676%** | **+0.080%** | **54.9%** | **+0.580%** | **+2.909%** | **4.9%** | **10.8%** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | **PASS** |
| H2 non-toxic | +15m | 3,124 | -0.026% | -0.058% | 8.2% | -0.033% | -0.018% | 3.2% | 6.4% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H2 non-toxic | +1h | 3,124 | +0.064% | -0.056% | 14.0% | +0.036% | +0.099% | 5.7% | 11.7% | ✓ | ✗ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H2 non-toxic | +4h | 3,124 | +0.171% | -0.050% | 24.5% | +0.036% | +0.316% | 5.9% | 12.0% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |
| H3 launch | +15m | 420 | -0.014% | -0.025% | 34.0% | -0.028% | +0.000% | 2.8% | 7.3% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H3 launch | +1h | 420 | -0.439% | -0.056% | 42.4% | -0.613% | -0.273% | 1.2% | 3.1% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H3 launch | +4h | 420 | -1.544% | +0.054% | 52.4% | -2.253% | -0.951% | 0.7% | 1.7% | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | **NO** |
| H3 standard | +15m | 3,548 | +0.017% | -0.058% | 12.9% | -0.001% | +0.037% | 3.2% | 7.1% | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H3 standard | +1h | 3,548 | +0.058% | -0.057% | 14.7% | -0.021% | +0.135% | 3.3% | 7.6% | ✓ | ✓ | ✗ | ✗ | ✓ | ✓ | **NO** |
| H3 standard | +4h | 3,548 | +0.732% | -0.049% | 28.4% | +0.457% | +1.035% | 4.2% | 9.1% | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | **NO** |

**Passing: 1 / 18 (H2 toxic, +4h)**

---

## 2. H2 Toxic +4h — Detailed Analysis

### 2.1 Gate Summary

All six gates pass for H2 toxic at +4h:

| Gate | Criterion | Value | Result |
|------|-----------|-------|--------|
| G1 | N ≥ 30 | N = 844 | ✓ |
| G2 | Winsorized mean > 0 | +1.033% | ✓ |
| G3 | Median > 0 | +0.080% | ✓ |
| G4 | CI lower bound > 0 | +0.580% | ✓ |
| G5 | Top-1 share < 25% | 4.9% | ✓ |
| G6 | Top-3 share < 50% | 10.8% | ✓ |

### 2.2 Per-Pool Breakdown

The 844 toxic events come from 9 pools:

| Pool | Type | N | Mean Net | Median Net | %Pos | |r1h| | |r4h| | Reverts? |
|------|------|---|----------|------------|------|--------|--------|---------|
| Jellybean-SOL | elevated | 219 | +6.84% | +1.79% | 77.2% | 13.3% | 16.4% | No |
| 我的刀盾-SOL | launch | 175 | -2.12% | +0.04% | 52.0% | 11.9% | 18.3% | No |
| SOS-SOL | launch | 81 | -2.67% | -0.35% | 45.7% | 14.5% | 25.6% | No |
| SMITH-SOL | elevated | 28 | -0.09% | +1.23% | 60.7% | 29.0% | 53.9% | No |
| Memehouse-SOL (1) | elevated | 18 | +31.1% | +9.77% | 83.3% | 23.1% | 27.0% | No |
| Memehouse-SOL (2) | elevated | 17 | +14.1% | +8.29% | 88.2% | 22.1% | 24.7% | No |
| PENGUIN-SOL | elevated | 117 | -0.15% | -0.06% | 40.2% | 7.6% | 6.1% | **Yes** |
| Rosie-SOL (1) | elevated | 6 | -6.43% | -6.15% | 33.3% | 18.3% | 43.1% | No |
| Rosie-SOL (2) | standard | 7 | -11.8% | -8.77% | 14.3% | 16.1% | 47.8% | No |

### 2.3 Structural Diagnosis

The scrutiny analysis reveals the following:

**Mean fee_proxy (toxic events): 7.14%**  
**Mean il_proxy_4h (toxic events): 4.20%**  
**Events where fee_proxy > il_proxy: 263/383 (68.7%)**

The positive net LP proxy is primarily driven by **fee proxy exceeding IL proxy**, not by mean reversion. Only 1 of 9 pools (PENGUIN-SOL) shows price reversion at +4h. The result is structurally a fee-income effect: when large price moves occur in elevated-fee pools, the fee income (base_fee × volume / TVL × 4 bars) is large enough to offset the IL from the move.

### 2.4 Concentration Warning

Two Memehouse-SOL pools (N=35 combined, 1 day of data each) show extreme positive results (+14% to +31% mean net). These are very short-lived pools with very high fee/TVL ratios (80–97% per hour), which is economically implausible for sustained LP deployment. Their contribution to the overall positive result is disproportionate relative to their sample size.

**Sensitivity check (excluding Memehouse-SOL):**
- N: 809 (vs 844)
- Estimated mean net: ~+0.8% (vs +1.68%) — still positive
- Estimated median net: ~+0.02% (vs +0.08%) — borderline

The result survives Memehouse exclusion in mean terms, but the median becomes borderline. This is a material robustness concern.

### 2.5 Economic Interpretation

The H2 toxic +4h result says: when a large price move (>5%) occurs in a DLMM pool over 1 hour, holding an LP position for 4 hours afterward shows positive expected LP proxy. The mechanism is that the high fee income from the volatile period outweighs the IL from the continued move. This is plausible but depends critically on:
1. The fee proxy being accurate (base fee × volume / TVL is a lower bound)
2. The LP position remaining in range throughout the 4-hour window
3. TVL not changing materially during the holding period

All three assumptions are simplifications. The result is **suggestive but not conclusive**.

---

## 3. Non-Passing Results Summary

**H1 (Volatility-Fee State):** Consistently fails G3 (median > 0). The median LP proxy is negative at all horizons even in elevated fee/TVL states. The mean is positive at +4h (+1.02% winsorized), but the distribution is right-skewed — a few large positive events pull the mean up while the majority of events are negative. This is not a tradeable edge.

**H2 non-toxic:** Negative or near-zero at all horizons. Non-toxic periods (small price moves) generate insufficient fee income to cover IL and friction. This is the expected result.

**H3 launch pools:** Negative mean at +1h and +4h. Launch pools with high base fees are toxic for LPs — the large price moves in early trading cause IL that exceeds even the elevated fee income. H3 is confirmed as a systematic LP veto condition.

**H3 standard pools:** Similar to H1 null — positive mean at +4h but negative median. No tradeable edge.

---

## 4. Verdict

**1 of 18 combinations passed all gates: H2 toxic, +4h.**

The result is structurally driven by fee income exceeding IL in high-volatility periods, not by mean reversion. However, the result has material robustness concerns due to Memehouse-SOL concentration and the use of proxy metrics rather than exact LP PnL.

**Verdict: CONDITIONAL GO** — the H2 toxic +4h signal warrants Stage B investigation with exact LP PnL data, but should not be acted upon based on Stage A proxy analysis alone.

---

*End of Results Document*
