# ET v1 Session Handoff — 2026-02-25 (Session 2)

**GitHub repo:** `NoAutopilot/solana-narrative-trader` (private, latest: `c9fe2cd`)
**VPS:** `root@142.93.24.227` (DigitalOcean)
**Working dir:** `/root/solana_trader/`
**DB:** `/root/solana_trader/data/solana_trader.db`
**Service:** `solana-trader.service` (systemd → supervisor.py)

---

## System State (as of session end)

### Processes (all single-instance, managed by supervisor.py)
| Process | Script | Status |
|---|---|---|
| universe_scanner | et_universe_scanner.py | Running |
| microstructure | et_microstructure.py | Running |
| shadow_trader_v1 | et_shadow_trader_v1.py | **Running (v2 code)** |
| pf_graduation | pf_graduation_stream.py | Running |
| flask_dashboard | flask_dashboard.py | Running |

### Old harness status
- `et_shadow_trader.py` — **RETIRED**. Removed from supervisor.py MANAGED_PROCESSES. Will not respawn.

---

## ET v1 Playbook (Current Spec)

### Strategy Variants (4 total)
| Variant | Type | Thresholds |
|---|---|---|
| `momentum_strict` | Strict | r_m5>=0.8%, buy_ratio>=0.6, vol_accel>=1.5, avg_trade>=$100 |
| `pullback_strict` | Strict | r_h1>=2.0%, r_m5<=-0.6% + confirm r_m5>=-0.3% within 75s |
| `momentum_rank` | Score/rank | top-1 per 30min, floors: buy_ratio>=0.25, vol_accel>=0.20, r_m5>=0 |
| `pullback_rank` | Score/rank | top-1 per 30min, floors: buy_ratio>=0.25, vol_accel>=0.20, r_h1>=0.5%, r_m5<=0 |

Each variant has a matched baseline: `baseline_matched_{variant}` (random eligible token, same timestamp).

### Exits (unified)
- TP: +4.0% / SL: -2.0% / Timeout: 12min / LP cliff: 5% k-drop

### Position Caps
- `MAX_OPEN_PER_STRATEGY = 1` (research mode, no global cap)

---

## GO/NO-GO Rules for Live Canary

Run `python3 et_daily_report_v5.py` to check `LIVE_CANARY_READY_V1`.

1. `min_closed_trades(strategy) >= 20` (else INSUFFICIENT_DATA)
2. Strategy beats matched baseline under `fee060` (preferably `fee100`)
3. Stability: `>= 2` 6h blocks with `n >= 10`
4. Concentration: top-3 tokens `< 50%`
5. Smoke test: PASS ✅

**Current status: INSUFFICIENT_DATA** — rank mode just started firing (2 trades as of session end).

---

## Known Issues

### 1. Jupiter API Key Expired (P1 — non-blocking)
- Symptom: log shows `"Jupiter API 401 — switching to CPAMM fallback mode"`
- Impact: friction gate uses CPAMM math (conservative) instead of real RT quotes
- CPAMM fallback is working correctly — trades are opening
- Fix: renew at https://portal.jup.ag → update `config/config.py` → `JUP_API_KEY = "new_key"` → restart service

### 2. Pullback rank not firing (P2 — market condition)
- No tokens currently have r_h1>=0.5% AND r_m5<=0 simultaneously
- This is a market condition, not a code issue
- Will resolve as market moves

### 3. Strict strategies not firing (P2 — market condition)
- Large-cap tokens in flat/bearish mode; no tokens meeting strict thresholds
- Rank mode is the primary data accumulation path

### 4. Universe is large-cap tokens, not pump.fun ETs (P3 — future work)
- Current: 20 fixed large-cap tokens (BONK, WIF, POPCAT, etc.)
- Desired: pump.fun graduated tokens with CPAMM pools
- Fix: update et_universe_scanner.py to query DexScreener pumpswap filter

---

## Quick Diagnostic Commands

```bash
# SSH
ssh root@142.93.24.227

# Check processes
ps aux | grep -E 'shadow_trader|universe|microstructure|supervisor|pf_grad' | grep -v grep

# Check v1 log
tail -30 /root/solana_trader/logs/et_shadow_trader_v1.log

# Check trade count
python3 -c "
import sqlite3
conn = sqlite3.connect('/root/solana_trader/data/solana_trader.db')
rows = conn.execute('SELECT strategy, COUNT(*), SUM(CASE WHEN status=\"closed\" THEN 1 ELSE 0 END) FROM shadow_trades_v1 GROUP BY strategy').fetchall()
for r in rows: print(f'{r[0]}: total={r[1]}, closed={r[2]}')
"

# Run daily report
cd /root/solana_trader && python3 et_daily_report_v5.py

# Restart service
systemctl restart solana-trader.service && sleep 10 && systemctl status solana-trader.service
```

---

## Key Files

| File | Purpose |
|---|---|
| `et_shadow_trader_v1.py` | Main v1 harness (v2 code: strategy split + rank mode) |
| `et_daily_report_v5.py` | **USE THIS** — empirical fee + all 4 variants |
| `et_daily_report_v4.py` | Old report (still works) |
| `et_universe_scanner.py` | Universe discovery (large-caps, 20 tokens) |
| `et_microstructure.py` | 15s price/volume scanner |
| `supervisor.py` | Process supervisor |
| `config/config.py` | JUP_API_KEY, DB_PATH, TRADE_SIZE_SOL |
| `cpamm_math.py` | CPAMM math helpers |

---

## DB Tables

| Table | Purpose |
|---|---|
| `shadow_trades_v1` | v1 paper trades (all 4 variants + baselines) |
| `signal_frequency_log` | Per-cycle signals_seen/trades_opened per strategy |
| `microstructure_log` | 15s price/flow snapshots |
| `universe_snapshot` | Eligible token list per scan |
| `live_trades` | On-chain trades (meta_fee for empirical cost) |
| `smoke_test_log` | Smoke test results |

---

## What Was Done This Session

1. **Retired old harness** — supervisor.py updated, et_shadow_trader.py no longer managed
2. **Strategy variant split** — momentum/pullback → strict/rank variants
3. **Score/rank fallback** — uses ALL eligible tokens (no cpamm_valid_flag filter), 30min interval
4. **Jupiter CPAMM fallback** — accurate 0.50% RT DEX fee (was 0.60%), non-blocking on 401
5. **DB migrations** — added entry_avg_trade_usd, mode columns; created signal_frequency_log
6. **Daily report v5** — empirical fee measurement, all 4 variants, signal frequency section
7. **Rank mode confirmed working** — Fartcoin momentum_rank fired at 07:48 UTC, jup_rt=1.00%
8. **GitHub pushed** — commit c9fe2cd on master

---

## Next Session Priorities

**P0 (run first):**
```bash
ssh root@142.93.24.227
cd /root/solana_trader
python3 et_daily_report_v5.py
```
Check: are rank trades accumulating? Is signal_frequency_log populated?

**P1 (if n_closed < 5 after 4h):**
- Check if pullback_rank is firing at all
- Consider lowering pullback_rank r_h1 floor from 0.5% to 0.2%

**P2 (once n_closed >= 20 per strategy):**
- Inspect MFE/MAE distribution — are TP/SL appropriate for large-cap tokens?
- Run LIVE_CANARY_READY_V1 gate check

**P3 (universe expansion):**
- Update et_universe_scanner.py to query DexScreener for pump.fun graduated tokens
- Filter: graduated in last 48h, liq_usd > $50k, has CPAMM pool

**P4 (Jupiter key):**
- Renew at https://portal.jup.ag
- Update config/config.py → JUP_API_KEY
- Restart service

---

## Wallet
- Live: 0.14 SOL (DO NOT touch until GO/NO-GO met)
- Paper trade size: 0.01 SOL (virtual)
- Mode: research_mode
