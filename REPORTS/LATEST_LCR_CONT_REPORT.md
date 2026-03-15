================================================================================
  LCR CONTINUATION OBSERVER v1 — REPORT
  Report time:  2026-03-15T02:30:01.414132+00:00
  run_id:       95b3ad8a-30fb-4f22-9d97-641f77c60c1b
================================================================================

  ── INTEGRITY CHECKS ──────────────────────────────────────────────────────
  n_signals:                10
  n_controls:               10
  signals == controls:      OK
  duplicate fires:          NONE

  ── FIRE LOG ──────────────────────────────────────────────────────────────
  n_fires_total:            11
    no_signal             1
    ok                    10

  ── QUOTE COVERAGE (ok/due — pending excluded from denominator) ────────────
  now_epoch = 1773541801
  [SIGNAL]
  horizon    due    ok  fail  pending  coverage (ok/due)
  -------- ----- ----- ----- -------- ------------------
  +1m          9     3     6        0              33.3%  *** BELOW 95% ***
  +5m          9     8     1        0              88.9%  *** BELOW 95% ***
  +15m         9     8     1        0              88.9%  *** BELOW 95% ***
  +30m         9     7     2        0              77.8%  *** BELOW 95% ***

  [CONTROL]
  horizon    due    ok  fail  pending  coverage (ok/due)
  -------- ----- ----- ----- -------- ------------------
  +1m          9     5     4        0              55.6%  *** BELOW 95% ***
  +5m          9     8     1        0              88.9%  *** BELOW 95% ***
  +15m         9     8     1        0              88.9%  *** BELOW 95% ***
  +30m         9     7     2        0              77.8%  *** BELOW 95% ***

  pairs_complete_5m:        8/10 (80.0%)

  ── ROW VALIDITY (B2: row_valid invariant check) ──────────────────────────
  rows with fwd_quote_ok_5m=1: 16
  row_valid=1 (or NULL):        16
  row_valid=0 (invariant fail): 0
  No invalid rows.
  Paired delta invariant: delta computed as (sig_net - ctrl_net) at query time.
  max_abs(delta - (sig_net - ctrl_net)) = 0.00e+00  (0 by construction — no stored delta column)
  INVARIANT: PASS

  ── THIS TABLE IS: ABSOLUTE NET MARKOUT (net_fee100) ─────────────────────
  Group     Horizon     n        Mean      Median     %>0
  --------------------------------------------------------------------------------
  signal        +1m     3     -1.1784%     -1.0811%    0.0%
  signal        +5m     8     -1.0902%     -1.0299%    0.0% <-- PRIMARY
  signal       +15m     8     -1.2065%     -1.1720%    0.0%
  signal       +30m     7     -1.0569%     -1.0038%    0.0%
  control       +1m     5     -1.1412%     -1.0827%    0.0%
  control       +5m     8     -1.2139%     -1.2935%    0.0%
  control      +15m     8     -1.1933%     -1.2935%    0.0%
  control      +30m     7     -1.2177%     -1.2934%    0.0%

  ── THIS TABLE IS: SIGNAL-MINUS-CONTROL DELTA (net_fee100) ───────────────
  Horizon     n        Mean      Median     95% CI Lo     95% CI Hi     %>0
  --------------------------------------------------------------------------------
      +1m     3     +0.1135%     +0.0016%       -0.3714%       +0.5984%   66.7%
      +5m     8     +0.1238%     +0.1512%       -0.0275%       +0.2750%   62.5% <-- PRIMARY
     +15m     8     -0.0132%     +0.0570%       -0.2424%       +0.2161%   62.5%
     +30m     7     +0.1608%     +0.2896%       -0.1840%       +0.5056%   71.4%

  ── KILL / PROMOTION CHECK ────────────────────────────────────────────────
  Insufficient data for kill check (n_pairs_5m=8 < 30).

  ── OUTLIER DEBUG DUMP (C2: abs(delta_5m) >= 10%) ────────────────────────
  No outliers with abs(delta_5m) >= 10%.

  ── SAMPLE ROWS (3 most recent signal+control pairs) ─────────────────────
  Fire: 20260306_2115
    Signal:  ukHH6c7mMyiW... (BOME) r_m5=0.4000  entry_ok=1  out=2157538985
    Control: 7GCihgDB8fe6... (POPCAT) r_m5=-0.5900  entry_ok=1  out=16688735098  dist=1.037
  Fire: 20260306_2100
    Signal:  HZ1JovNiVvGr... (PYTH) r_m5=0.2100  entry_ok=1  out=17860678
    Control: A8C3xuqscfmy... (FWOG) r_m5=0.0000  entry_ok=1  out=147908638  dist=2.857
  Fire: 20260306_2045
    Signal:  7GCihgDB8fe6... (POPCAT) r_m5=1.3100  entry_ok=1  out=16705327800
    Control: A8C3xuqscfmy... (FWOG) r_m5=0.0000  entry_ok=1  out=147908806  dist=2.276

================================================================================
