# Feature Tape v2 — Final Recommendation Memo

**Date:** 2026-03-15 02:21 UTC
**View:** PRIMARY (eligible-only)
**Horizons evaluated:** +5m, +15m, +30m, +1h, +4h
**+1d:** EXCLUDED from primary decision (deferred)

---

## VERDICT: NO NEW LIVE OBSERVER — STOP PROGRAM

No feature passed discovery gates, or all passing features are in the no-go registry. The signal is fundamentally weak across all tested features and horizons.

### Evidence Summary

- Features tested: 210
- Discovery passes: 0
- Novel discovery passes: 0

### Recommended Next Step

**Stop the feature_tape_v2 program.**

The current feature space has been exhaustively tested. Options:

1. **Pivot to a fundamentally different data source** (e.g., on-chain transaction-level data, social sentiment, cross-chain flow)
2. **Pivot to a different market** (e.g., established tokens with deeper liquidity)
3. **Accept that the edge does not exist** in the current market microstructure and stop

Do NOT re-run the same features with minor parameter changes.
Do NOT launch any live observer.

---

## Horizon-Level Summary

| Horizon | Features Tested | Discovery Pass | Holdout Pass | Novel + Constraint |
|---------|----------------:|---------------:|-------------:|-------------------:|
| +5m | 42 | 0 | 0 | 0 |
| +15m | 42 | 0 | 0 | 0 |
| +30m | 42 | 0 | 0 | 0 |
| +1h | 42 | 0 | 0 | 0 |
| +4h | 42 | 0 | 0 | 0 |

---

## Safety Confirmation

- Collector STOPPED at 2026-03-14T15:00:14Z (118 fires at stop; primary dataset = first 96)
- Live tape NOT mutated (frozen 96-fire DB used for all analysis)
- No live observer started
- No scanner/strategy changes made
- +1d horizon EXCLUDED from primary decision
