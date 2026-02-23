# Live Deployment Preflight Checklist (v2 — Post-Audit)

**System:** Pre-bonding paper trader (pump.fun lottery tickets)
**Date:** Feb 23, 2026
**Parameters:** 0.02 SOL/trade, narrative_only filter, 5000-trade lifetime cap, max 15 concurrent, 100/hr rate limit, pool=pump for buys

---

## Audit Corrections Applied (v2 changes)

| Issue Found | Old Value | New Value | Status |
|------------|-----------|-----------|--------|
| Rate limit too low (missed 77% of trades) | 20/hr hardcoded | 100/hr env-configurable | **DEPLOYED** |
| Lifetime cap too low (hit in 6 hrs) | 500 hardcoded | 5000 env-configurable | **DEPLOYED** |
| No concurrent limit | None | 15 env-configurable | **DEPLOYED** |
| Buy pool adds 100ms latency | pool="auto" | pool="pump" env-configurable | **DEPLOYED** |
| No failure/slippage logging | Minimal | Full execution metrics | **DEPLOYED** |
| paper_trade_id not passed to live executor | Missing | Added to buy + sell calls | **DEPLOYED** |
| Trade size | 0.005 | 0.02 | **DEPLOYED** |
| Conviction filter | "all" (default) | "narrative_only" | **DEPLOYED** |

All code changes deployed to VPS and pushed to GitHub (commit fe6e895). `LIVE_ENABLED` remains `false`.

---

## Current State

| Item | Value | Status |
|------|-------|--------|
| LIVE_ENABLED | false | Waiting for preflight |
| LIVE_TRADE_SIZE_SOL | 0.02 | Set |
| LIVE_SLIPPAGE_PCT | 20 | Set (keeping per user decision) |
| LIVE_CONVICTION_FILTER | narrative_only | Set |
| LIVE_BUY_POOL | pump | Set |
| MAX_LIVE_TRADES_PER_HOUR | 100 | Set |
| MAX_TOTAL_LIVE_TRADES | 5000 | Set |
| MAX_CONCURRENT_LIVE_TRADES | 15 | Set |
| MAX_SOL_PER_TRADE | 0.05 | Set (our 0.02 is under this) |
| MIN_WALLET_BALANCE_SOL | 0.01 | Set |
| Wallet balance | ~0.005 SOL | **NEEDS FUNDING** |
| PUMPPORTAL_API_KEY | SET (206 chars) | OK |
| HELIUS_RPC_URL | SET | OK |
| WALLET_ADDRESS | D714dunm...8rw9 | OK |
| live_executor.py | v3 deployed | OK |
| paper_trader.py | Updated (paper_trade_id) | OK |
| Execution metrics logging | Active | OK |

---

## Phase 1: Wallet Funding

- [ ] **Fund wallet with 0.6 SOL** (0.5 for trades + 0.1 buffer for TX fees and rent)
  - Wallet: `REDACTED_WALLET_ADDRESS`
  - Current balance: ~0.005 SOL
  - Send from your main wallet or exchange
- [ ] **Verify balance on-chain** after funding

---

## Phase 2: Pre-Bonding Buy/Sell Test

### 2.1 — Manual Buy Test (Pre-Bonding Token)
Purpose: Verify PumpPortal API key works and buy execution succeeds on a token still on the bonding curve.

```bash
ssh root@142.93.24.227
cd /root/solana_trader
python3 -c "
import sys; sys.path.insert(0, '.')
from live_executor import execute_buy
import sqlite3

conn = sqlite3.connect('data/solana_trader.db')
c = conn.cursor()
open_trade = c.execute('''
    SELECT mint_address, token_name FROM trades 
    WHERE status='open' ORDER BY entered_at DESC LIMIT 1
''').fetchone()
conn.close()

if open_trade:
    mint, name = open_trade
    print(f'Test token: {name} ({mint})')
    result = execute_buy(mint, name, amount_sol=0.001)
    print(f'Result: {result}')
else:
    print('No open paper trades to test with')
"
```

**Check:**
- [ ] Buy TX submitted successfully (tx_signature returned)
- [ ] TX confirmed on-chain (check Solscan)
- [ ] `confirm_time_sec` logged (new v3 metric)
- [ ] `sol_change` logged (new v3 metric)
- [ ] Pool used was "pump" (not "auto")

### 2.2 — Manual Sell Test (Pre-Bonding Token)

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from live_executor import execute_sell

MINT = '<paste_mint_from_buy_test>'
NAME = '<paste_name_from_buy_test>'

result = execute_sell(MINT, NAME, sell_pct=100)
print(f'Result: {result}')
print(f'Pools tried: {result.get(\"pools_tried\", [])}')
print(f'Confirm time: {result.get(\"confirm_time_sec\")}s')
print(f'SOL received: {result.get(\"sol_received\")}')
print(f'Rent reclaimed: {result.get(\"rent_reclaimed\")}')
"
```

**Check:**
- [ ] Sell TX submitted successfully
- [ ] TX confirmed on-chain
- [ ] SOL returned to wallet
- [ ] `pools_tried` logged (new v3 metric)
- [ ] `confirm_time_sec` logged
- [ ] Rent reclaimed (should be ~0.002 SOL)

---

## Phase 3: Post-Bonding Buy/Sell Test

### 3.1 — Manual Buy Test (Graduated / Raydium Token)

```bash
python3 -c "
import sys, sqlite3; sys.path.insert(0, '.')
conn = sqlite3.connect('post_bonding/post_bonding.db')
c = conn.cursor()
token = c.execute('''
    SELECT mint_address, token_name, peak_mcap_usd 
    FROM graduated_tokens 
    WHERE peak_mcap_usd > 50000
    ORDER BY discovered_at DESC LIMIT 1
''').fetchone()
conn.close()
if token:
    print(f'Test token: {token[1]} ({token[0]}) peak mcap: \${token[2]:,.0f}')
else:
    print('No graduated tokens with sufficient mcap found')
"

# Then buy with pool=auto (PumpPortal routes to Raydium)
python3 -c "
import sys; sys.path.insert(0, '.')
import os; os.environ['LIVE_BUY_POOL'] = 'auto'  # Override for post-bonding test
from live_executor import execute_buy
MINT = '<paste_graduated_mint>'
NAME = '<paste_graduated_name>'
result = execute_buy(MINT, NAME, amount_sol=0.001)
print(f'Result: {result}')
"
```

**Check:**
- [ ] Buy TX submitted for graduated token
- [ ] TX confirmed on-chain (PumpPortal routed to Raydium)
- [ ] Tokens received in wallet

### 3.2 — Manual Sell Test (Graduated / Raydium Token)

```bash
python3 -c "
import sys; sys.path.insert(0, '.')
from live_executor import execute_sell
MINT = '<paste_graduated_mint>'
NAME = '<paste_graduated_name>'
result = execute_sell(MINT, NAME, sell_pct=100)
print(f'Result: {result}')
print(f'Pools tried: {result.get(\"pools_tried\", [])}')
"
```

**Check:**
- [ ] Sell TX submitted for graduated token
- [ ] Pool retry logic worked if needed (auto → pump-amm → raydium)
- [ ] SOL returned to wallet
- [ ] Rent reclaimed

---

## Phase 4: Conviction Filter Verification

After restarting with `LIVE_ENABLED=true`, monitor logs:

```bash
journalctl -u solana-trader -f | grep -E "LIVE|conviction|FILTER"
```

**Expected behavior:**
- Control trades: `[LIVE FILTER] token_name: Control trade filtered (mode=control)`
- Narrative trades: `[LIVE BUY] Executing: token_name ... pool=pump`
- Proactive trades: `[LIVE BUY] Executing: token_name ... pool=pump`

**Check:**
- [ ] Control trades are filtered
- [ ] Narrative trades pass filter and attempt live buy
- [ ] Proactive trades pass filter and attempt live buy

---

## Phase 5: Go-Live Sequence

### 5.1 — Flip the Switch

```bash
# Only change needed: LIVE_ENABLED=false -> LIVE_ENABLED=true
# All other config is already deployed

# Edit trader_env.conf
sed -i 's/LIVE_ENABLED=false/LIVE_ENABLED=true/' /root/solana_trader/trader_env.conf

# Restart
systemctl restart solana-trader

# Monitor
journalctl -u solana-trader -f | grep -E "LIVE|live|conviction|SLIPPAGE"
```

**Check:**
- [ ] Service restarted cleanly
- [ ] First live buy executes within ~5-10 minutes
- [ ] Execution metrics logging visible (confirm_time_sec, sol_change, slippage)

### 5.2 — First Hour Monitoring

- [ ] At least 1 live buy executed and confirmed on-chain
- [ ] At least 1 live sell executed (if any paper trades exit)
- [ ] Wallet balance decreasing by ~0.02 per buy, recovering on sells
- [ ] No unexpected errors in logs
- [ ] Paper trading continues unaffected (all modes still paper trading)
- [ ] Execution metrics accumulating (check `get_live_stats()`)

---

## Phase 6: Ongoing Monitoring

### Kill Switches (in order of severity)

| Action | How | When |
|--------|-----|------|
| Pause new buys | `sed -i 's/LIVE_ENABLED=true/LIVE_ENABLED=false/' /root/solana_trader/trader_env.conf && systemctl restart solana-trader` | Unusual errors |
| Emergency stop | `systemctl stop solana-trader` | Critical failure |
| Sell all positions | Manual sell script for each open position | Exit everything |

### Expected Behavior (first 24 hours)

| Metric | Expected Range | Alert If |
|--------|---------------|----------|
| Live trades/hour | 40-80 (narrative+proactive, rate limit 100) | > 100 or 0 |
| SOL spent/hour | 0.80-1.60 | > 2.0 |
| Wallet balance | Fluctuating, net positive if strategy works | < 0.1 SOL |
| Win rate (live) | 15-22% | 0% after 50+ trades |
| Largest single loss | -0.02 SOL (1 trade) | > -0.05 SOL |
| Concurrent open | 5-15 | > 15 (should be capped) |

### Data Points to Collect (for slippage/MEV analysis)

These are now automatically logged by v3 execution metrics:
- **Buy success rate** — what % of buy attempts actually succeed on-chain?
- **Sell success rate** — what % of sells succeed on first pool attempt?
- **TX confirmation time** — how long from submit to on-chain confirmation?
- **Slippage observations** — expected vs actual SOL change per trade
- **Failed sell details** — which tokens fail to sell, which pools were tried, error codes
- **Pool retry frequency** — how often do sells need to retry with different pools?

Access via: `python3 -c "from live_executor import get_live_stats; import json; print(json.dumps(get_live_stats(), indent=2))"`

---

## Risk Budget

| Scenario | SOL Impact | Probability |
|----------|-----------|-------------|
| Best case: moonshot carries us | +1-5 SOL | 10% |
| Expected: small profit from narrative edge | +0.1-0.5 SOL | 30% |
| Neutral: break even after fees | ±0.05 SOL | 25% |
| Bad case: slow bleed, no moonshots | -0.2-0.4 SOL | 30% |
| Worst case: all trades lose + TX fees | -0.5 SOL | 5% |

**Maximum loss is bounded** by MIN_WALLET_BALANCE_SOL (0.01) — the system stops trading when balance drops below this.

---

## Summary: What You Need To Do

1. **Fund the wallet** with 0.6 SOL → `REDACTED_WALLET_ADDRESS`
2. **Tell me when funded** and I'll run the buy/sell tests (Phase 2 & 3)
3. **Review test results** together
4. **Green light** → I flip `LIVE_ENABLED=true` and restart
5. **Monitor together** for 15 minutes to confirm everything works
