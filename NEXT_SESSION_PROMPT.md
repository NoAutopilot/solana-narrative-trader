# Solana Narrative Trader — Session Handoff Prompt
**Last updated:** 2026-02-25 (UTC)  
**GitHub repo:** `NoAutopilot/solana-narrative-trader` (private)  
**VPS:** `root@142.93.24.227` (DigitalOcean)  
**Working dir on VPS:** `/root/solana_trader/`  
**DB path:** `/root/solana_trader/data/solana_trader.db`  
**Logs dir:** `/root/solana_trader/logs/`

---

## Project Summary

This is a **Solana paper-trading research system** for "Existing Tokens" (ET) — tokens that have graduated from pump.fun and are now trading on Raydium/Orca CPAMM pools. The goal is to validate two entry strategies (momentum + pullback) in shadow/paper mode before risking the 0.14 SOL live wallet.

The system runs on a VPS managed by `supervisor.py` (via systemd `solana-trader.service`).

---

## Current System Architecture

### Processes managed by `supervisor.py` (systemd: `solana-trader.service`)
| Process | Script | Purpose |
|---|---|---|
| `universe_scanner` | `et_universe_scanner.py` | Discovers eligible tokens, updates `universe_snapshot` |
| `microstructure` | `et_microstructure.py` | Polls DexScreener every 15s, writes `microstructure_log` |
| `shadow_trader_v1` | `et_shadow_trader_v1.py` | **ACTIVE** v1 paper harness, writes `shadow_trades_v1` |
| `pf_graduation` | `pf_graduation_stream.py` | Monitors pump.fun graduation events |

### Retired processes (DO NOT restart)
- `et_shadow_trader.py` — old harness, writes to `shadow_trades` table (NOT `shadow_trades_v1`)
- `et_shadow_trader_v2.py` — experimental, not in production

---

## ET v1 Playbook (Current Strategy Spec)

### Entry Conditions
**Momentum v1:**
- `r_m5 >= +0.8%`
- `buy_count_ratio_m5 >= 0.60`
- `vol_accel_m5_vs_h1 >= 1.5`
- `spam_flag = 0` AND `avg_trade_usd_m5 >= $100`

**Pullback v1 (two-stage):**
- Stage 1: `r_h1 >= +2.0%` AND `r_m5 <= -0.6%` → sets `_pullback_pending[mint]`
- Stage 2 (within 75s): `r_m5 >= -0.3%` AND `buy_count_ratio_m5 >= 0.55` → opens trade

**Score/Rank Fallback (added this session):**
- Fires at most 1 trade per strategy per hour when strict thresholds not met
- `momentum_rank`: top-1 by `r_m5 * buy_ratio * vol_accel * avg_trade_norm`
- `pullback_rank`: top-1 by `r_h1 * (-r_m5) * buy_ratio`
- Relaxed floors: `r_m5 >= 0`, `buy_ratio >= 0.40`, `vol_accel >= 0.50`

### Exits (unified across all strategies)
- Take profit: `+4.0%`
- Stop loss: `-2.0%`
- Timeout: `12 minutes`
- LP cliff: `5% k-invariant drop` (CPAMM only)

### Position Caps
- `research_mode`: `MAX_OPEN_PER_STRATEGY = 1`, no global cap
- `live_sim_mode`: `MAX_OPEN_PER_STRATEGY = 1`, `MAX_OPEN_GLOBAL = 1`

### Baselines
- `baseline_matched_momentum`: fires when momentum enters, random eligible token
- `baseline_matched_pullback`: fires when pullback enters, random eligible token

---

## GO/NO-GO Rules for Live Canary (0.14 SOL wallet)

Run `python3 et_daily_report_v4.py` to check `LIVE_CANARY_READY_V1`.

All of these must be met:
1. `min_closed_trades(strategy) >= 20` (else `INSUFFICIENT_DATA`)
2. Strategy beats its matched baseline under `fee060` (preferably `fee100`)
3. Stability: `>= 2` 6-hour blocks with `n >= 10`
4. Concentration: top-3 tokens `< 50%` of trades
5. Smoke test: `PASS` (already green)

**Current status: INSUFFICIENT_DATA** — `shadow_trades_v1` has 0 closed trades.

---

## Known Issues (as of 2026-02-25)

### 1. Jupiter API Key Expired (CRITICAL)
- **Symptom:** `et_shadow_trader_v1.log` shows `"Jupiter API 401 — switching to CPAMM fallback mode"`
- **Impact:** Jupiter friction gate uses CPAMM math fallback instead of real RT quotes
- **Fix:** Renew key at https://portal.jup.ag → update `config/config.py`:
  ```python
  JUPITER_API_KEY = "your-new-key-here"
  ```
  Then restart v1: `pkill -f et_shadow_trader_v1.py` (supervisor will restart it)

### 2. Signal Starvation (ACTIVE)
- **Symptom:** 0 trades in `shadow_trades_v1`, log shows "no qualifying candidates"
- **Root cause:** Universe scanner scans 20 large-cap tokens (BONK, WIF, etc.) in bear/flat market
- **Secondary cause:** `get_latest_microstructure()` requires `cpamm_valid_flag=1`, but only 7 tokens qualify, and none currently meet even the relaxed rank thresholds
- **Fix options:**
  - Option A: Relax score/rank to use ALL eligible tokens (not just CPAMM) — edit `get_latest_microstructure()` or add a separate query for rank mode
  - Option B: Expand universe scanner to scan pump.fun graduated tokens (the intended ET universe)
  - Option C: Wait for market conditions to improve (large-caps are in bear mode)

### 3. Universe Scanner: Wrong Token Universe
- **Symptom:** Scanner only finds 21 tokens (fixed list of large-cap Solana tokens)
- **Root cause:** `KNOWN_SOLANA_MINTS` in `et_universe_scanner.py` is a hardcoded list of large-cap tokens, not pump.fun graduates
- **Fix:** Update universe scanner to use DexScreener's `pumpswap` filter to find recently graduated pump.fun tokens with CPAMM pools

---

## Quick Diagnostic Commands

```bash
# SSH to VPS
ssh root@142.93.24.227

# Check running processes
ps aux | grep -E 'shadow_trader|universe|microstructure|supervisor|pf_grad' | grep -v grep

# Check v1 harness log (last 30 lines)
tail -30 /root/solana_trader/logs/et_shadow_trader_v1.log

# Check trade count
python3 -c "
import sqlite3
conn = sqlite3.connect('/root/solana_trader/data/solana_trader.db')
c = conn.cursor()
c.execute('SELECT strategy, COUNT(*), SUM(CASE WHEN status=\"closed\" THEN 1 ELSE 0 END) FROM shadow_trades_v1 GROUP BY strategy')
for r in c.fetchall():
    print(f'{r[0]}: total={r[1]}, closed={r[2]}')
"

# Check microstructure freshness
python3 -c "
import sqlite3
conn = sqlite3.connect('/root/solana_trader/data/solana_trader.db')
c = conn.cursor()
c.execute('SELECT MAX(logged_at), COUNT(DISTINCT mint_address) FROM microstructure_log WHERE logged_at >= datetime(\"now\", \"-5 minutes\")')
r = c.fetchone()
print(f'Latest: {r[0]}, Tokens in last 5min: {r[1]}')
"

# Run daily report
cd /root/solana_trader && python3 et_daily_report_v4.py

# Restart v1 harness (supervisor will restart it)
pkill -f et_shadow_trader_v1.py
sleep 20
tail -10 /root/solana_trader/logs/et_shadow_trader_v1.log

# Restart full service (nuclear option)
systemctl restart solana-trader.service
sleep 10
systemctl status solana-trader.service
```

---

## Key Files

| File | Purpose |
|---|---|
| `et_shadow_trader_v1.py` | **PRIMARY** v1 paper harness (Playbook Edition) |
| `et_daily_report_v4.py` | Daily report + `LIVE_CANARY_READY_V1` gate |
| `et_universe_scanner.py` | Universe discovery (currently scanning large-caps) |
| `et_microstructure.py` | Microstructure data collector |
| `supervisor.py` | Process supervisor (managed by systemd) |
| `config/config.py` | All config: DB_PATH, JUPITER_API_KEY, etc. |
| `cpamm_math.py` | CPAMM math: `cpamm_round_trip()`, `k_lp_cliff()` |
| `live_canary.py` | Live trading script (DO NOT run until GO/NO-GO met) |

---

## Database Tables

| Table | Purpose |
|---|---|
| `shadow_trades_v1` | **PRIMARY** v1 paper trades (momentum, pullback, baselines, rank) |
| `shadow_trades` | Old harness trades (DO NOT use for v1 evaluation) |
| `microstructure_log` | 15s price/flow snapshots per token |
| `universe_snapshot` | Eligible token list per minute |
| `discovery_log` | Universe scanner audit log |

---

## What Was Done This Session (2026-02-25)

1. **Retired old harness** — `et_shadow_trader.py` was being respawned by `supervisor.py` (systemd service). Fixed by updating `MANAGED_PROCESSES` in `supervisor.py` to use `et_shadow_trader_v1` instead.

2. **Added score/rank fallback** to `et_shadow_trader_v1.py`:
   - `SCORE_RANK_ENABLED = True`, `SCORE_RANK_INTERVAL_SEC = 3600`
   - `momentum_rank` and `pullback_rank` strategies
   - Fires top-1 candidate per strategy per hour

3. **Added Jupiter CPAMM fallback** to `et_shadow_trader_v1.py`:
   - `_jupiter_api_available` flag
   - On 401: uses CPAMM math + 0.006 DEX fee floor
   - Prevents all trades being blocked by expired API key

4. **Pushed all changes to GitHub** — commit `dfdfcde` on `master`

---

## Next Session Priorities

**P0 (blockers for any data):**
1. Fix Jupiter API key (401 error) — renew at https://portal.jup.ag
2. Fix signal starvation — either relax CPAMM filter in rank mode OR expand universe to pump.fun tokens

**P1 (once trades start accumulating):**
3. Monitor `shadow_trades_v1` for trade accumulation (need 20+ per strategy)
4. Run `et_daily_report_v4.py` to check `LIVE_CANARY_READY_V1`

**P2 (improvements):**
5. Implement r_1m from 15s price series (replace r_m5 proxy in pullback confirmation)
6. Expand universe scanner to pump.fun graduated tokens (pumpswap pools)
7. Add signal_frequency section to daily report (signals_seen, trades_opened, trades_closed per strategy)

---

## Wallet Info
- **Live wallet:** 0.14 SOL (DO NOT touch until GO/NO-GO criteria met)
- **Paper trade size:** 0.01 SOL (virtual)
- **Mode:** `research_mode` (no global cap, per-strategy cap=1)
