"""
ChatGPT Suggestion Evaluator — Test each hypothesis against current data.

ChatGPT's suggestions are qualitatively different from Grok's. Grok gave
6 specific hypotheses with test procedures. ChatGPT gave 7 strategic
observations, some testable, some architectural. We test what we can.

Key claims to validate:
  1. TP exits average ~24x return (execution realism question)
  2. Slippage haircut sensitivity analysis
  3. TP convergence is caused by price jumps between 10s checks
  4. Narrative scan interval (15 min) is too slow
  5. Timeout reduction via microstructure filter
  6. First-token-per-narrative (already tested by Grok eval)
  7. Twitter as dead-on-arrival filter (already tested by Grok eval)
"""

import sqlite3
import json
import numpy as np
from datetime import datetime, timedelta

DB_PATH = "/home/ubuntu/solana_trader/data/solana_trader.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
c = conn.cursor()

def section(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 1: Execution Realism — Are the TP exits really 24x returns?
# ═══════════════════════════════════════════════════════════════════════════
section("1. EXECUTION REALISM: TP EXIT ANATOMY")

c.execute("""
    SELECT id, token_name, mint_address, pnl_sol, pnl_pct, 
           entry_price_usd, exit_price_usd, entry_sol, exit_sol, hold_minutes,
           trade_mode, category, exit_reason
    FROM trades WHERE status='closed' AND exit_reason='take_profit'
    ORDER BY pnl_sol DESC
""")
tp_trades = c.fetchall()
print(f"Take-profit exits: {len(tp_trades)}")

if tp_trades:
    pnls = [t['pnl_sol'] for t in tp_trades]
    pcts = [t['pnl_pct'] for t in tp_trades if t['pnl_pct'] is not None]
    holds = [t['hold_minutes'] for t in tp_trades if t['hold_minutes'] is not None]
    
    print(f"\nPnL distribution of TP exits:")
    print(f"  Mean: {np.mean(pnls):.4f} SOL")
    print(f"  Median: {np.median(pnls):.4f} SOL")
    print(f"  Min: {min(pnls):.4f} SOL")
    print(f"  Max: {max(pnls):.4f} SOL")
    print(f"  Std: {np.std(pnls):.4f} SOL")
    
    if pcts:
        print(f"\nReturn % distribution of TP exits:")
        print(f"  Mean return: {np.mean(pcts)*100:.1f}%")
        print(f"  Median return: {np.median(pcts)*100:.1f}%")
        print(f"  Min return: {min(pcts)*100:.1f}%")
        print(f"  Max return: {max(pcts)*100:.1f}%")
    
    if holds:
        print(f"\nHold time distribution of TP exits:")
        print(f"  Mean: {np.mean(holds):.1f} min")
        print(f"  Median: {np.median(holds):.1f} min")
        print(f"  Min: {min(holds):.1f} min")
        print(f"  Max: {max(holds):.1f} min")
    
    # ChatGPT's claim: avg TP win is ~24x return
    # Let's check: 0.955 SOL / 0.04 SOL trade size = 23.9x
    print(f"\nChatGPT's claim: avg TP = ~24x return")
    print(f"  Actual avg TP PnL: {np.mean(pnls):.4f} SOL")
    # Use entry_sol as actual trade size
    entry_sols = [t['entry_sol'] for t in tp_trades if t['entry_sol']]
    avg_entry = np.mean(entry_sols) if entry_sols else 0.04
    print(f"  Avg entry size: {avg_entry:.4f} SOL")
    print(f"  At avg entry size: {np.mean(pnls)/avg_entry:.1f}x return")
    print(f"  Median TP PnL: {np.median(pnls):.4f} SOL")
    print(f"  At avg entry size: {np.median(pnls)/avg_entry:.1f}x return")
    
    # Show top 10 TP trades
    print(f"\nTop 10 TP exits:")
    for t in tp_trades[:10]:
        pct_str = f"{t['pnl_pct']*100:.0f}%" if t['pnl_pct'] else "n/a"
        hold_str = f"{t['hold_minutes']:.0f}min" if t['hold_minutes'] else "n/a"
        print(f"  {t['token_name']}: +{t['pnl_sol']:.4f} SOL ({pct_str}) hold={hold_str} mode={t['trade_mode']} cat={t['category']}")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 2: Slippage Sensitivity Analysis
# ═══════════════════════════════════════════════════════════════════════════
section("2. SLIPPAGE SENSITIVITY (ChatGPT's 'sanity check')")

c.execute("SELECT pnl_sol, exit_reason FROM trades WHERE status='closed'")
all_closed = c.fetchall()

# Current total PnL
current_total = sum(t['pnl_sol'] for t in all_closed)
tp_total = sum(t['pnl_sol'] for t in all_closed if t['exit_reason'] == 'take_profit')
non_tp_total = current_total - tp_total

print(f"Current total PnL: {current_total:.4f} SOL")
print(f"  From TP exits: {tp_total:.4f} SOL")
print(f"  From non-TP exits: {non_tp_total:.4f} SOL")

# Apply haircuts to TP exits only (ChatGPT's test)
print(f"\nHaircut sensitivity on TP exits:")
print(f"  (Assumes you only realize X% of displayed TP profit)")
for haircut_pct in [100, 80, 60, 50, 40, 30, 20, 10]:
    adjusted_tp = tp_total * (haircut_pct / 100)
    adjusted_total = adjusted_tp + non_tp_total
    print(f"  {haircut_pct}% of TP realized: total PnL = {adjusted_total:+.4f} SOL {'PROFITABLE' if adjusted_total > 0 else '*** NEGATIVE ***'}")

# Find the breakeven haircut
# non_tp_total + tp_total * x = 0 => x = -non_tp_total / tp_total
if tp_total > 0:
    breakeven_haircut = -non_tp_total / tp_total * 100
    print(f"\n  Breakeven haircut: {breakeven_haircut:.1f}%")
    print(f"  (You need to realize at least {breakeven_haircut:.1f}% of displayed TP profit to break even)")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 3: Are TP exits "price jump" artifacts?
# ═══════════════════════════════════════════════════════════════════════════
section("3. TP EXIT OVERSHOOT ANALYSIS")

# ChatGPT claims: TP threshold is 30%, but avg TP return is way higher
# This means price jumped past 30% between checks
if pcts:
    print(f"TP threshold: 30%")
    print(f"Actual TP exit returns:")
    below_50 = sum(1 for p in pcts if p < 0.50)
    between_50_100 = sum(1 for p in pcts if 0.50 <= p < 1.0)
    between_100_500 = sum(1 for p in pcts if 1.0 <= p < 5.0)
    above_500 = sum(1 for p in pcts if p >= 5.0)
    
    print(f"  30-50% return: {below_50} trades")
    print(f"  50-100% return: {between_50_100} trades")
    print(f"  100-500% return: {between_100_500} trades")
    print(f"  >500% return: {above_500} trades")
    print(f"  Total: {len(pcts)} trades")
    
    # What % of TP exits were "near threshold" vs "massive overshoot"?
    near_threshold = sum(1 for p in pcts if p < 0.50)
    overshoot = sum(1 for p in pcts if p >= 0.50)
    print(f"\n  Near threshold (<50%): {near_threshold} ({near_threshold/len(pcts)*100:.0f}%)")
    print(f"  Overshoot (>50%): {overshoot} ({overshoot/len(pcts)*100:.0f}%)")
    
    if overshoot > 0:
        overshoot_pnls = [t['pnl_sol'] for t in tp_trades if t['pnl_pct'] and t['pnl_pct'] >= 0.50]
        near_pnls = [t['pnl_sol'] for t in tp_trades if t['pnl_pct'] and t['pnl_pct'] < 0.50]
        print(f"\n  PnL from near-threshold TP: {sum(near_pnls):.4f} SOL")
        print(f"  PnL from overshoot TP: {sum(overshoot_pnls):.4f} SOL")
        print(f"  Overshoot share of TP profit: {sum(overshoot_pnls)/tp_total*100:.1f}%")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 4: Timeout Analysis — Can we reduce the 63% timeout rate?
# ═══════════════════════════════════════════════════════════════════════════
section("4. TIMEOUT TRADE ANALYSIS (63% of exits)")

c.execute("""
    SELECT id, pnl_sol, pnl_pct, hold_minutes, trade_mode, category,
           entry_price_usd, exit_price_usd, entry_sol, exit_sol
    FROM trades WHERE status='closed' AND exit_reason='timeout'
""")
timeout_trades = c.fetchall()
print(f"Timeout trades: {len(timeout_trades)}")

if timeout_trades:
    to_pnls = [t['pnl_sol'] for t in timeout_trades]
    to_pcts = [t['pnl_pct'] for t in timeout_trades if t['pnl_pct'] is not None]
    
    print(f"  Mean PnL: {np.mean(to_pnls):.6f} SOL")
    print(f"  Total PnL: {sum(to_pnls):.4f} SOL")
    
    if to_pcts:
        # How many were "dead on arrival" (never moved much)?
        dead = sum(1 for p in to_pcts if abs(p) < 0.05)  # Within 5% of entry
        slight_up = sum(1 for p in to_pcts if 0.05 <= p < 0.30)
        slight_down = sum(1 for p in to_pcts if -0.25 < p <= -0.05)
        
        print(f"\n  Timeout return distribution:")
        print(f"    Dead on arrival (within 5%): {dead} ({dead/len(to_pcts)*100:.0f}%)")
        print(f"    Slight up (5-30%): {slight_up} ({slight_up/len(to_pcts)*100:.0f}%)")
        print(f"    Slight down (5-25%): {slight_down} ({slight_down/len(to_pcts)*100:.0f}%)")
        
        # ChatGPT's microstructure filter idea:
        # If we could identify "dead on arrival" tokens early and skip them,
        # what would the portfolio look like?
        dead_pnl = sum(t['pnl_sol'] for t in timeout_trades if t['pnl_pct'] and abs(t['pnl_pct']) < 0.05)
        print(f"\n  PnL from 'dead on arrival' timeouts: {dead_pnl:.4f} SOL")
        print(f"  If we skipped all dead-on-arrival trades:")
        print(f"    Trades saved: {dead}")
        print(f"    PnL impact: {-dead_pnl:+.4f} SOL")
        print(f"    But: would we also skip some future moonshots? UNKNOWN")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 5: Entry Timing — How fast after token creation do we enter?
# ═══════════════════════════════════════════════════════════════════════════
section("5. ENTRY TIMING ANALYSIS")

c.execute("""
    SELECT id, entered_at, token_name, trade_mode, pnl_sol, exit_reason
    FROM trades WHERE status='closed'
    ORDER BY entered_at ASC
""")
all_trades = c.fetchall()

# Check time between consecutive trades
if len(all_trades) >= 2:
    gaps = []
    for i in range(1, len(all_trades)):
        try:
            t1 = datetime.fromisoformat(all_trades[i-1]['entered_at'])
            t2 = datetime.fromisoformat(all_trades[i]['entered_at'])
            gap = (t2 - t1).total_seconds()
            if gap > 0:
                gaps.append(gap)
        except:
            pass
    
    if gaps:
        print(f"Time between consecutive entries:")
        print(f"  Mean: {np.mean(gaps):.0f} sec ({np.mean(gaps)/60:.1f} min)")
        print(f"  Median: {np.median(gaps):.0f} sec ({np.median(gaps)/60:.1f} min)")
        print(f"  Min: {min(gaps):.0f} sec")
        print(f"  Max: {max(gaps):.0f} sec ({max(gaps)/3600:.1f} hr)")

# How many trades per hour?
c.execute("SELECT COUNT(*) as cnt FROM trades WHERE status='closed'")
total_closed = c.fetchone()['cnt']
c.execute("SELECT MIN(entered_at) as first_t, MAX(entered_at) as last_t FROM trades")
times = c.fetchone()
if times['first_t'] and times['last_t']:
    try:
        t_first = datetime.fromisoformat(times['first_t'])
        t_last = datetime.fromisoformat(times['last_t'])
        hours = (t_last - t_first).total_seconds() / 3600
        print(f"\nTrading rate: {total_closed/hours:.1f} trades/hour over {hours:.1f} hours")
    except:
        pass

# ═══════════════════════════════════════════════════════════════════════════
# TEST 6: "Cover costs + keep a runner" — Partial exit feasibility
# ═══════════════════════════════════════════════════════════════════════════
section("6. PARTIAL EXIT ANALYSIS")

# ChatGPT suggests: sell enough to cover fees at 30%, keep remainder for moonshot
# Let's model this on our TP exits
print("Modeling 'cover costs + runner' on actual TP exits:")
print("  Strategy: sell 50% at 30% profit, hold 50% for actual exit price")

if tp_trades:
    current_tp_total = sum(t['pnl_sol'] for t in tp_trades)
    partial_total = 0
    for t in tp_trades:
        if t['pnl_pct'] is not None and t['entry_sol'] and t['pnl_pct']:
            entry = t['entry_price_usd'] or 0
            actual_exit = t['exit_price_usd'] or 0
            trade_size = t['entry_sol'] or 0.04
            
            # Current: sell 100% at actual exit price
            # Partial: sell 50% at 30% profit, sell 50% at actual exit
            half_size = trade_size / 2
            
            # First half: exit at 30% profit (guaranteed by TP threshold)
            first_half_pnl = half_size * 0.30 * (1 - 0.08)  # Net of fees
            
            # Second half: exit at actual price
            if entry > 0:
                actual_return = (actual_exit - entry) / entry
                second_half_pnl = half_size * actual_return * (1 - 0.08)
            else:
                second_half_pnl = t['pnl_sol'] / 2
            
            partial_total += first_half_pnl + second_half_pnl
    
    print(f"  Current TP total: {current_tp_total:.4f} SOL")
    print(f"  Partial exit TP total: {partial_total:.4f} SOL")
    print(f"  Difference: {partial_total - current_tp_total:+.4f} SOL")
    print(f"  Note: Partial exit locks in some profit but caps upside on the first half")

# ═══════════════════════════════════════════════════════════════════════════
# TEST 7: Concurrency utilization
# ═══════════════════════════════════════════════════════════════════════════
section("7. CONCURRENCY UTILIZATION")

c.execute("SELECT COUNT(*) FROM trades WHERE status='open'")
current_open = c.fetchone()[0]
print(f"Current open positions: {current_open} / 50 max")
print(f"Utilization: {current_open/50*100:.0f}%")

# Are we ever hitting the cap?
# Check max concurrent by looking at overlapping time windows
c.execute("""
    SELECT entered_at, exit_at FROM trades 
    WHERE status='closed' AND entered_at IS NOT NULL AND exit_at IS NOT NULL
    ORDER BY entered_at
""")
closed_with_times = c.fetchall()
if closed_with_times:
    # Simple: count max overlapping trades
    events = []
    for t in closed_with_times:
        try:
            enter = datetime.fromisoformat(t['entered_at'])
            exit_t = datetime.fromisoformat(t['exit_at'])
            events.append((enter, 1))
            events.append((exit_t, -1))
        except:
            pass
    events.sort(key=lambda x: x[0])
    max_concurrent = 0
    current = 0
    for _, delta in events:
        current += delta
        max_concurrent = max(max_concurrent, current)
    print(f"Peak concurrent positions observed: {max_concurrent}")
    print(f"{'HIT CAP' if max_concurrent >= 50 else 'Never hit cap'}")

# ═══════════════════════════════════════════════════════════════════════════
# OVERALL ASSESSMENT
# ═══════════════════════════════════════════════════════════════════════════
section("OVERALL ASSESSMENT: CHATGPT vs OUR PRINCIPLES")

print("""
ChatGPT's analysis is QUALITATIVELY different from Grok's.

Grok gave 6 specific hypotheses to test. We tested them. 2 disproven, 0 actionable.

ChatGPT identified STRUCTURAL RISKS in the system design:
  1. Execution realism (are our wins real?)
  2. Price check granularity (10s gaps cause overshoot)
  3. Narrative scan latency (15 min is too slow)
  4. Timeout bleed (63% of trades are dead weight)

These are not "features to build." They are VALIDITY THREATS to the experiment.

Per our principles:
  - "Trust nothing, prove everything"
  - "Fees are the enemy, not an afterthought"
  - "Real slippage on pump.fun is likely 15-25%, not 8%"

ChatGPT's execution realism concern aligns DIRECTLY with Principle 7.
The slippage sensitivity test tells us exactly how fragile our results are.
""")

conn.close()
print("Done.")
