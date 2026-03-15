# Feature Tape v2 — Label Maturity Report
**Date:** 2026-03-15T02:20:31Z
**Dataset:** frozen 96-fire (first 96 successful fires)
**DB:** /root/solana_trader/reports/synthesis/feature_tape_v2_frozen_96fires_20260314T150050Z.db

## Label Coverage by Horizon (eligible-only, N=4065)

| Horizon | Offset | Labeled Rows | Coverage | Mature? |
|---------|--------|-------------|----------|---------|
| +5m | 300s | 3943 | 97.0% | YES |
| +15m | 900s | 3857 | 94.9% | YES |
| +30m | 1800s | 3703 | 91.1% | YES |
| +1h | 3600s | 3448 | 84.8% | YES |
| +4h | 14400s | 2772 | 68.2% | YES (gap-reduced) |
| +1d | — | — | EXCLUDED | N/A |

## Notes
- +4h coverage is reduced because the 12h gap window (06:27Z–18:43Z Mar 13)
  removes fires whose +4h horizon falls within the gap.
- All horizons are wall-clock mature: the 96th fire was at 2026-03-14T09:30Z,
  and +4h matured at 13:30Z. Current time is well past maturity for all horizons.
- Labels derived via epoch-based universe_snapshot price lookup with ±120s window.
- Gap-affected rows (borderline fire dc1485fe at 06:30Z) excluded per
  feature_tape_v2_gap_note.md.

## Verdict
**ALL PRIMARY HORIZONS MATURE. Proceed to final sweep.**
