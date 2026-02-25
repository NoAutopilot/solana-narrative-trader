# Solana ET Trader — Session Handoff Prompt (v1.6)
**Last updated:** 2026-02-25 ~18:00 UTC  
**GitHub:** `NoAutopilot/solana-narrative-trader` @ commit `b2fc3e7`  
**VPS:** `root@142.93.24.227` | Service: `solana-trader.service`  
**DB:** `/root/solana_trader/data/solana_trader.db` → table `shadow_trades_v1`

---

## How to Resume

```bash
ssh root@142.93.24.227
cd /root/solana_trader
python3 et_daily_report_v7.py --hours 4
```

---

## System State

### Processes (managed by `solana-trader.service` via `supervisor.py`)
| Process | Script | Status |
|---|---|---|
| universe_scanner | et_universe_scanner.py (v1.1) | Running |
| microstructure | et_microstructure.py | Running |
| shadow_trader_v1 | et_shadow_trader_v1.py (v1.6) | Running |
| pf_graduation | pf_graduation_stream.py | Running |

**Old harness (`et_shadow_trader.py`) — RETIRED.**

### Jupiter API
- Endpoint: `api.jup.ag/ultra/v1/order` + `x-api-key` header ✅
- Real RT quotes confirmed active (~0.21–0.24% for pumpswap tokens)

### Universe
38–75 eligible tokens per scan: 20 large-cap + pumpswap graduated (DexScreener, refreshed 30min).

---

## ET v1 Strategy Variants

| Variant | Type | Entry Conditions |
|---|---|---|
| `momentum_strict` | Strict | r_m5≥0.8%, buy_ratio≥0.6, vol_accel≥1.5, avg_trade≥$100 |
| `pullback_strict` | Strict | r_h1≥2.0%, r_m5≤-0.6% + confirm r_m5≥-0.3% within 75s |
| `momentum_rank` | Score/rank | top-1 per 30min, floors: r_m5≥0, buy_ratio≥0.25, vol_accel≥0.20 |
| `pullback_rank` | Score/rank | top-1 per 30min, floors: r_h1≥0.5%, r_m5≤0, buy_ratio≥0.25 |

Exits (unified): TP +4.0% / SL -2.0% / Timeout 12min / Hard max 30min / LP cliff 5% k-drop  
Each variant has matched baseline: `baseline_matched_{variant}`

**Hard lane gates (v1.6):** `age >= 4h`, `liq >= $100k`, `vol_24h >= $250k` — applied to ALL strategies.

---

## v1.6 Changes (This Session)

1. **Lane tagging** — 7 columns stamped at every trade entry: `lane`, `age_at_entry_h`, `liq_usd_at_entry`, `vol_24h_at_entry`, `pool_type_at_entry`, `venue_at_entry`, `spam_flag_at_entry`
2. **Hard lane gates** — enforced in `open_trade()` for ALL strategies: age≥4h, liq≥$100k, vol24h≥$250k
3. **Lane classification** — `classify_lane()`: `large_cap` (age>30d), `mature_raydium`, `mature_pumpswap`, `fresh_pumpswap`
4. **Rank timer fix** — `_last_rank_entry[strategy] = now` moved BEFORE `open_trade()` call — prevents repeated firing every 2s when position cap is full
5. **Report v7.1** — `--hours N` CLI arg, lane-separated paired delta section (Section 6)

---

## Report v7 Findings (2026-02-25 ~18:00 UTC, 74 closed in 2h window)

### Friction Floor (final)
| Component | Value |
|---|---|
| DEX fee (RT) | 0.500% |
| Network/prio (RPC backfill) | 0.142% (7,092 lam/tx) |
| **Total RT floor at 0.01 SOL** | **0.644%** |

### Overshoot Audit (v1.5+ data)
- **SL exits**: avg detection delay = **0.6s** ✅ — exit mechanism is working
- **Worst trade**: NIRE -19.87% in 2s (0.9s detection) — genuine fast crash, not poll-gap
- **Conclusion**: SL overshoot is market risk (fast rugs), not a polling problem

### Per-Variant Paired Delta (2h window)
| Variant | n_pairs | delta_fee060 | Verdict |
|---|---|---|---|
| `momentum_strict` | 10 | INSUFFICIENT_DATA | — |
| `pullback_strict` | 8 | -2.40% | DOES NOT BEAT |
| `momentum_rank` | 8 | INSUFFICIENT_DATA | — |
| `pullback_rank` | 6 | INSUFFICIENT_DATA | — |

**Lane-separated section**: accumulating — trades before v1.6 have `lane=NULL`. Data will be meaningful after ~4h of v1.6 running.

### LIVE_CANARY_READY_V1: NO
Blocking: `n_closed=74 < 150`, no strategy beats matched baseline.

---

## P0 Actions for Next Session (in order)

### 1. Run report with 4h window
```bash
cd /root/solana_trader && python3 et_daily_report_v7.py --hours 4
```

### 2. Check lane-separated paired delta
After 4h of v1.6 running, Section 6 should show `mature_pumpswap` data.
- If `mature_pumpswap` paired delta > 0 under fee100: entry signal has edge in this lane
- If still negative: entry signal needs redesign

### 3. Check for duplicate process issue
```bash
ps aux | grep et_shadow_trader_v1 | grep -v grep
```
If two PIDs: the log shows duplicate lines. Fix: check supervisor.py MANAGED_PROCESSES.

### 4. Fix friction audit discrepancy (minor)
The report's empirical fee section shows `median=5,000 lam` but smoke test shows `7,092 lam/tx`.
The `meta_fee_lamports` column stores base fee only (5,000). Fix: store `meta.fee` (total including priority) from `getTransaction` RPC response in smoke_test_log.

### 5. If paired delta still negative after n≥20
Consider:
- **Token age filter tighten**: raise from 4h to 8h
- **SL widening**: -2% → -3% (only if whipsaw confirmed, not rugs)
- **Entry signal redesign**: if all variants negative vs random, redesign from scratch

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
| `et_shadow_trader_v1.py` (v1.6) | Main v1 harness — lane tagging, hard gates, rank timer fix |
| `et_universe_scanner.py` (v1.1) | Universe scanner — large-cap + pumpswap lanes |
| `et_daily_report_v7.py` | **USE THIS** — `--hours N`, lane-separated paired delta, overshoot audit |
| `et_microstructure.py` | 15s price/volume scanner |
| `supervisor.py` | Systemd-managed process supervisor (v1 only) |
| `config/config.py` | JUPITER_API_KEY, DB_PATH, TRADE_SIZE_SOL |

---

## Wallet
- Live: **0.14 SOL** (DO NOT touch until GO/NO-GO met)
- Paper trade size: 0.01 SOL (virtual)
- Mode: `research_mode`
