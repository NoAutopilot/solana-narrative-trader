# Solana ET Trader — Session Handoff Prompt (v1.4)
**Last updated:** 2026-02-25 ~17:00 UTC  
**GitHub:** `NoAutopilot/solana-narrative-trader` @ commit `8981eb7`  
**VPS:** `root@142.93.24.227` | Service: `solana-trader.service`  
**DB:** `/root/solana_trader/data/solana_trader.db` → table `shadow_trades_v1`

---

## How to Resume

```bash
ssh root@142.93.24.227
cd /root/solana_trader
python3 et_daily_report_v7.py
```

---

## System State

### Processes (managed by `solana-trader.service` via `supervisor.py`)
| Process | Script | Status |
|---|---|---|
| universe_scanner | et_universe_scanner.py (v1.1) | Running |
| microstructure | et_microstructure.py | Running |
| shadow_trader_v1 | et_shadow_trader_v1.py (v1.4) | Running |
| pf_graduation | pf_graduation_stream.py | Running |

**Old harness (`et_shadow_trader.py`) — RETIRED.**

### Jupiter API
- Endpoint: `api.jup.ag/ultra/v1/order` + `x-api-key` header ✅
- Startup health check: `JUP_HEALTH: OK` logged on each restart
- Real RT quotes confirmed active (~0.21–0.23% for pumpswap tokens)

### Universe
75 eligible tokens per scan: 20 large-cap + ~55 PumpSwap graduated (DexScreener, refreshed 30min).

---

## ET v1 Strategy Variants

| Variant | Type | Entry Conditions |
|---|---|---|
| `momentum_strict` | Strict | r_m5≥0.8%, buy_ratio≥0.6, vol_accel≥1.5, avg_trade≥$100 |
| `pullback_strict` | Strict | r_h1≥2.0%, r_m5≤-0.6% + confirm r_m5≥-0.3% within 75s |
| `momentum_rank` | Score/rank | top-1 per 30min, floors: r_m5≥0, buy_ratio≥0.25, vol_accel≥0.20 |
| `pullback_rank` | Score/rank | top-1 per 30min, floors: r_h1≥0.5%, r_m5≤0, buy_ratio≥0.25 |

Exits (unified): TP +4.0% / SL -2.0% / Timeout 12min / LP cliff 5% k-drop  
Each variant has matched baseline: `baseline_matched_{variant}`

---

## v1.4 Changes (This Session)

1. **Adaptive exit polling**: `POLL_INTERVAL_SEC = 4` (was 15s). When any position is open: polls every 2s. Eliminates poll-gap SL overshoot (TripleT -13.97% in 14s was the worst case at 15s polling).
2. **Timeout exit filter**: At timeout, skip exit if `gross < RT_floor + 0.25%` — avoids crystallizing fee-negative tiny wins.
3. **Overshoot audit columns**: `sl_threshold_crossed_at`, `tp_threshold_crossed_at`, `exit_overshoot_pct`, `exit_overshoot_sec` — populated on every SL/TP exit going forward.
4. **Report v7**: Section 5b OVERSHOOT AUDIT, worst trade shows overshoot detail, legacy fallback for old trades.

---

## Report v7 Findings (2026-02-25 17:00 UTC, 121 closed trades)

### Friction Floor (corrected and final)
| Component | Value |
|---|---|
| DEX fee (RT) | 0.500% |
| Network/prio (RPC backfill) | 0.142% (7,092 lam/tx) |
| **Total RT floor at 0.01 SOL** | **0.644%** |
| Total RT floor at 0.02 SOL | 0.576% |

### Per-Variant Status
| Variant | n_closed | vs Baseline | Status |
|---|---|---|---|
| `momentum_rank` | 21 | DOES NOT BEAT (ev060=-1.39% vs baseline +0.80%) | QUALIFIED but failing |
| `pullback_rank` | 15 | N/A | INSUFFICIENT_DATA |
| `momentum_strict` | 19 | N/A | INSUFFICIENT_DATA |
| `pullback_strict` | 19 | N/A | INSUFFICIENT_DATA |

### Exit Breakdown — Pre-fix (old 15s polling)
- SL exits: avg -4% to -6% gross (target -2%) — overshoot audit will show improvement after v1.4 accumulates data
- Timeout exits: avg +0.06% to +1.28% gross — below 0.64% RT floor; timeout filter now active
- TP exits: avg +5% to +16% gross — only reliably profitable exit type

### LIVE_CANARY_READY_V1: NO
Blocking: `n_closed=121 < 150`, `momentum_rank does not beat baseline`, others INSUFFICIENT_DATA.

---

## P0 Actions for Next Session (in order)

### 1. Verify overshoot audit is working
After ~2h of v1.4 running, check that `exit_overshoot_sec` is being populated:
```bash
python3 -c "
import sqlite3
from config.config import DB_PATH
conn = sqlite3.connect(DB_PATH)
rows = conn.execute('''
  SELECT strategy, exit_reason, round(exit_overshoot_pct,3), exit_overshoot_sec
  FROM shadow_trades_v1
  WHERE exit_overshoot_pct IS NOT NULL
  ORDER BY exited_at DESC LIMIT 20
''').fetchall()
for r in rows: print(r)
"
```
Expected: SL exits show `exit_overshoot_sec < 6s` (was up to 14s at 15s polling).

### 2. Fix paired delta query bug
Report shows "no matched pairs found (baseline_trigger_id not set)". Check:
```bash
python3 -c "
import sqlite3
from config.config import DB_PATH
conn = sqlite3.connect(DB_PATH)
rows = conn.execute('''
  SELECT strategy, trade_id, baseline_trigger_id
  FROM shadow_trades_v1
  WHERE strategy LIKE 'baseline%'
  ORDER BY entered_at DESC LIMIT 5
''').fetchall()
for r in rows: print(r)
"
```
If `baseline_trigger_id` is NULL for all rows, the harness is not storing it. Fix in `open_trade()` — after inserting baseline trade, update the strategy trade's `baseline_trigger_id` column.

### 3. Re-evaluate momentum_rank after overshoot fix
After 20+ new trades with v1.4 polling, re-run `et_daily_report_v7.py`. If paired delta is still negative under fee100, the entry signal needs redesign (not more exit tuning).

### 4. pullback_strict signal starvation
19 closed trades after a full day. Consider lowering `r_h1 >= 2.0%` to `1.5%` after 24h.

---

## GO/NO-GO Rules (unchanged)
```
min_closed_trades(strategy) >= 20        → else INSUFFICIENT_DATA
strategy beats matched baseline (fee100) → paired delta mean > 0
stability: >=2 six-hour blocks n>=10     → else INSUFFICIENT_DATA
concentration top-3 < 50%               → else CONCENTRATED
smoke test: PASS ✅                      → already done
```
**LIVE_CANARY_READY_V1 = YES** only when ALL above are met.  
No live canary with 0.14 SOL bankroll until gate passes.

---

## Key Files

| File | Purpose |
|---|---|
| `et_shadow_trader_v1.py` (v1.4) | Main v1 harness — adaptive polling, overshoot audit |
| `et_universe_scanner.py` (v1.1) | Universe scanner — large-cap + pumpswap lanes |
| `et_daily_report_v7.py` | **USE THIS** — overshoot audit, paired delta, exit breakdown |
| `et_microstructure.py` | 15s price/volume scanner |
| `supervisor.py` | Systemd-managed process supervisor (v1 only) |
| `config/config.py` | JUPITER_API_KEY, DB_PATH, TRADE_SIZE_SOL |

---

## Wallet
- Live: **0.14 SOL** (DO NOT touch until GO/NO-GO met)
- Paper trade size: 0.01 SOL (virtual)
- Mode: `research_mode`
