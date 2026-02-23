#!/usr/bin/env python3
"""
0.5 SOL Cycling Profitability Model
====================================
Question: If we had 0.5 SOL and cycled it through paper trades one at a time
(with realistic fees/slippage), would we have been profitable?

Approach:
- Use actual paper trade data (chronological order, closed trades only)
- Simulate cycling: invest a fixed % of balance per trade, wait for close, reinvest
- Apply realistic friction: 0.00074 SOL TX fees + 3.2% buy slippage + 1.5% sell slippage
- Track balance over time
- Answer: what's the final balance? What's the max drawdown? Break-even point?

Key constraint: We can only be in ONE trade at a time (cycling = sequential)
"""

import sqlite3
import json
from datetime import datetime

# Connect to the paper trader DB (use the S3 backup copy on dashboard server)
DB_PATH = "/home/ubuntu/solana_trader/data/solana_trader.db"

# Try VPS backup first, fall back to dashboard copy
import os
if not os.path.exists(DB_PATH):
    DB_PATH = "/home/ubuntu/solana-trading-dashboard/data/solana_trader.db"
    if not os.path.exists(DB_PATH):
        # Try to download from S3
        print("No local DB found. Using backup...")
        DB_PATH = None

if DB_PATH is None:
    print("ERROR: No database found. Run backup restore first.")
    exit(1)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS (from on-chain analysis of 191 real trades)
# ═══════════════════════════════════════════════════════════════════
TX_FEE_PER_TRADE = 0.00074      # buy + sell round trip
BUY_SLIPPAGE_PCT = 0.032        # 3.2% average
SELL_SLIPPAGE_PCT = 0.015       # 1.5% average
STARTING_BALANCE = 0.5          # SOL

# ═══════════════════════════════════════════════════════════════════
# LOAD ALL CLOSED TRADES IN CHRONOLOGICAL ORDER
# ═══════════════════════════════════════════════════════════════════
trades = conn.execute("""
    SELECT id, token_name, trade_mode, pnl_sol, pnl_pct, entry_sol,
           entered_at, exit_at, exit_reason, hold_minutes,
           narrative_keyword, category
    FROM trades 
    WHERE status='closed' AND pnl_sol IS NOT NULL AND exit_at IS NOT NULL
    ORDER BY exit_at ASC
""").fetchall()

print(f"Loaded {len(trades)} closed trades")
print(f"Date range: {trades[0]['entered_at']} to {trades[-1]['exit_at']}")
print()

# ═══════════════════════════════════════════════════════════════════
# SCENARIO 1: Fixed 0.04 SOL per trade (current paper size), cycling
# ═══════════════════════════════════════════════════════════════════
def simulate_cycling(trades, starting_bal, trade_size, apply_fees=True):
    """
    Simulate sequential cycling through trades.
    Each trade uses a fixed SOL amount. We can only be in one trade at a time.
    """
    balance = starting_bal
    peak_balance = starting_bal
    max_drawdown = 0
    trade_count = 0
    wins = 0
    losses = 0
    history = []
    skipped = 0
    
    for t in trades:
        # Can we afford this trade?
        actual_trade_size = min(trade_size, balance)
        if actual_trade_size < 0.001:  # minimum viable trade
            skipped += 1
            continue
        
        # Calculate PnL for this trade size
        # pnl_pct is stored as a ratio (e.g., 0.30 = 30% gain)
        pnl_pct = t['pnl_pct'] if t['pnl_pct'] is not None else 0
        raw_pnl = actual_trade_size * pnl_pct
        
        # Apply friction
        if apply_fees:
            friction = TX_FEE_PER_TRADE + actual_trade_size * (BUY_SLIPPAGE_PCT + SELL_SLIPPAGE_PCT)
        else:
            friction = 0
        
        net_pnl = raw_pnl - friction
        balance += net_pnl
        trade_count += 1
        
        if net_pnl > 0:
            wins += 1
        else:
            losses += 1
        
        # Track drawdown
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd
        
        history.append({
            'trade_num': trade_count,
            'token': t['token_name'],
            'mode': t['trade_mode'],
            'pnl_pct': pnl_pct,
            'raw_pnl': raw_pnl,
            'friction': friction,
            'net_pnl': net_pnl,
            'balance': balance,
            'exit_at': t['exit_at'],
        })
    
    return {
        'final_balance': balance,
        'total_return': (balance - starting_bal) / starting_bal * 100,
        'trade_count': trade_count,
        'wins': wins,
        'losses': losses,
        'win_rate': wins / trade_count * 100 if trade_count > 0 else 0,
        'max_drawdown_pct': max_drawdown * 100,
        'skipped': skipped,
        'history': history,
    }

# ═══════════════════════════════════════════════════════════════════
# RUN SCENARIOS
# ═══════════════════════════════════════════════════════════════════

print("=" * 70)
print("SCENARIO 1: Fixed 0.04 SOL per trade, 0.5 SOL starting, WITH fees")
print("=" * 70)
s1 = simulate_cycling(trades, 0.5, 0.04, apply_fees=True)
print(f"  Final balance:  {s1['final_balance']:.4f} SOL")
print(f"  Total return:   {s1['total_return']:+.1f}%")
print(f"  Trades taken:   {s1['trade_count']}")
print(f"  Win rate:       {s1['win_rate']:.1f}% ({s1['wins']}/{s1['trade_count']})")
print(f"  Max drawdown:   {s1['max_drawdown_pct']:.1f}%")
print(f"  Skipped:        {s1['skipped']} (insufficient balance)")
print()

print("=" * 70)
print("SCENARIO 1b: Same but WITHOUT fees (fantasy mode)")
print("=" * 70)
s1b = simulate_cycling(trades, 0.5, 0.04, apply_fees=False)
print(f"  Final balance:  {s1b['final_balance']:.4f} SOL")
print(f"  Total return:   {s1b['total_return']:+.1f}%")
print(f"  Fee impact:     {s1b['final_balance'] - s1['final_balance']:.4f} SOL lost to friction")
print()

print("=" * 70)
print("SCENARIO 2: 10% of balance per trade (Kelly-ish), WITH fees")
print("=" * 70)
# For this we need a custom simulation
def simulate_pct_cycling(trades, starting_bal, pct_per_trade, apply_fees=True):
    balance = starting_bal
    peak_balance = starting_bal
    max_drawdown = 0
    trade_count = 0
    wins = 0
    losses = 0
    history = []
    
    for t in trades:
        trade_size = balance * pct_per_trade
        if trade_size < 0.001:
            continue
        
        pnl_pct = t['pnl_pct'] if t['pnl_pct'] is not None else 0
        raw_pnl = trade_size * pnl_pct
        
        if apply_fees:
            friction = TX_FEE_PER_TRADE + trade_size * (BUY_SLIPPAGE_PCT + SELL_SLIPPAGE_PCT)
        else:
            friction = 0
        
        net_pnl = raw_pnl - friction
        balance += net_pnl
        trade_count += 1
        
        if net_pnl > 0:
            wins += 1
        else:
            losses += 1
        
        if balance > peak_balance:
            peak_balance = balance
        dd = (peak_balance - balance) / peak_balance if peak_balance > 0 else 0
        if dd > max_drawdown:
            max_drawdown = dd
        
        history.append({
            'trade_num': trade_count,
            'balance': balance,
            'trade_size': trade_size,
            'net_pnl': net_pnl,
        })
    
    return {
        'final_balance': balance,
        'total_return': (balance - starting_bal) / starting_bal * 100,
        'trade_count': trade_count,
        'wins': wins,
        'losses': losses,
        'win_rate': wins / trade_count * 100 if trade_count > 0 else 0,
        'max_drawdown_pct': max_drawdown * 100,
        'history': history,
    }

s2 = simulate_pct_cycling(trades, 0.5, 0.10, apply_fees=True)
print(f"  Final balance:  {s2['final_balance']:.4f} SOL")
print(f"  Total return:   {s2['total_return']:+.1f}%")
print(f"  Trades taken:   {s2['trade_count']}")
print(f"  Win rate:       {s2['win_rate']:.1f}%")
print(f"  Max drawdown:   {s2['max_drawdown_pct']:.1f}%")
print()

print("=" * 70)
print("SCENARIO 3: 5% of balance per trade, WITH fees")
print("=" * 70)
s3 = simulate_pct_cycling(trades, 0.5, 0.05, apply_fees=True)
print(f"  Final balance:  {s3['final_balance']:.4f} SOL")
print(f"  Total return:   {s3['total_return']:+.1f}%")
print(f"  Trades taken:   {s3['trade_count']}")
print(f"  Win rate:       {s3['win_rate']:.1f}%")
print(f"  Max drawdown:   {s3['max_drawdown_pct']:.1f}%")
print()

# ═══════════════════════════════════════════════════════════════════
# CRITICAL: ONLY NARRATIVE TRADES (remove control group)
# ═══════════════════════════════════════════════════════════════════
narrative_trades = [t for t in trades if t['trade_mode'] == 'narrative']
control_trades = [t for t in trades if t['trade_mode'] == 'control']
proactive_trades = [t for t in trades if t['trade_mode'] == 'proactive']

print("=" * 70)
print("SCENARIO 4: NARRATIVE-ONLY trades, 0.04 SOL, WITH fees")
print("=" * 70)
s4 = simulate_cycling(narrative_trades, 0.5, 0.04, apply_fees=True)
print(f"  Final balance:  {s4['final_balance']:.4f} SOL")
print(f"  Total return:   {s4['total_return']:+.1f}%")
print(f"  Trades taken:   {s4['trade_count']}")
print(f"  Win rate:       {s4['win_rate']:.1f}%")
print(f"  Max drawdown:   {s4['max_drawdown_pct']:.1f}%")
print()

print("=" * 70)
print("SCENARIO 5: CONTROL-ONLY trades (baseline), 0.04 SOL, WITH fees")
print("=" * 70)
s5 = simulate_cycling(control_trades, 0.5, 0.04, apply_fees=True)
print(f"  Final balance:  {s5['final_balance']:.4f} SOL")
print(f"  Total return:   {s5['total_return']:+.1f}%")
print(f"  Trades taken:   {s5['trade_count']}")
print(f"  Win rate:       {s5['win_rate']:.1f}%")
print(f"  Max drawdown:   {s5['max_drawdown_pct']:.1f}%")
print()

# ═══════════════════════════════════════════════════════════════════
# ROBUSTNESS CHECK: Remove top 5 trades, re-run
# ═══════════════════════════════════════════════════════════════════
print("=" * 70)
print("ROBUSTNESS: Remove top 5 winners, re-run Scenario 1")
print("=" * 70)
# Sort by pnl_sol descending, remove top 5
sorted_trades = sorted(trades, key=lambda t: t['pnl_sol'] if t['pnl_sol'] else 0, reverse=True)
top5_ids = set(t['id'] for t in sorted_trades[:5])
top5_pnl = sum(t['pnl_sol'] for t in sorted_trades[:5])
print(f"  Top 5 trades PnL: {top5_pnl:.4f} SOL")
for t in sorted_trades[:5]:
    print(f"    #{t['id']} {t['token_name']}: {t['pnl_sol']:.4f} SOL ({t['pnl_pct']*100:.0f}%)")

robust_trades = [t for t in trades if t['id'] not in top5_ids]
s_robust = simulate_cycling(robust_trades, 0.5, 0.04, apply_fees=True)
print(f"\n  Without top 5:")
print(f"  Final balance:  {s_robust['final_balance']:.4f} SOL")
print(f"  Total return:   {s_robust['total_return']:+.1f}%")
print(f"  Trades taken:   {s_robust['trade_count']}")
print(f"  Win rate:       {s_robust['win_rate']:.1f}%")
print(f"  Max drawdown:   {s_robust['max_drawdown_pct']:.1f}%")
print()

# ═══════════════════════════════════════════════════════════════════
# BREAK-EVEN ANALYSIS
# ═══════════════════════════════════════════════════════════════════
print("=" * 70)
print("BREAK-EVEN ANALYSIS: When does balance first exceed starting?")
print("=" * 70)
for name, scenario in [("All trades (0.04)", s1), ("Narrative only", s4)]:
    first_profitable = None
    for h in scenario['history']:
        if h['balance'] > STARTING_BALANCE:
            first_profitable = h
            break
    if first_profitable:
        print(f"  {name}: Trade #{first_profitable['trade_num']} ({first_profitable['token']}) at {first_profitable['exit_at']}")
    else:
        print(f"  {name}: NEVER breaks even")

# ═══════════════════════════════════════════════════════════════════
# THE HONEST ANSWER
# ═══════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print("THE HONEST ANSWER")
print("=" * 70)
print(f"""
Starting with 0.5 SOL and cycling through {len(trades)} paper trades sequentially:

  With fees:    {s1['final_balance']:.4f} SOL ({s1['total_return']:+.1f}%)
  Without fees: {s1b['final_balance']:.4f} SOL ({s1b['total_return']:+.1f}%)
  Fee drag:     {s1b['final_balance'] - s1['final_balance']:.4f} SOL

  Narrative only: {s4['final_balance']:.4f} SOL ({s4['total_return']:+.1f}%)
  Control only:   {s5['final_balance']:.4f} SOL ({s5['total_return']:+.1f}%)

  Without top 5:  {s_robust['final_balance']:.4f} SOL ({s_robust['total_return']:+.1f}%)

KEY INSIGHT: The profitability is {"REAL but concentrated" if s1['final_balance'] > 0.5 else "NEGATIVE — the system loses money with fees"}.
The top 5 trades account for {top5_pnl:.2f} SOL of paper PnL.
{"Without those outliers, the system is net negative." if s_robust['final_balance'] < 0.5 else "Even without outliers, the system is profitable."}

CYCLING CONSTRAINT: In reality, you can only be in one trade at a time.
Many of the best trades happened simultaneously. Sequential cycling would
miss most of them. This model assumes you could have taken every trade
in sequence, which overstates real-world performance.
""")

# Save results to JSON for dashboard integration
results = {
    'scenarios': {
        'fixed_004_with_fees': {
            'final_balance': round(s1['final_balance'], 4),
            'total_return_pct': round(s1['total_return'], 1),
            'trades': s1['trade_count'],
            'win_rate': round(s1['win_rate'], 1),
            'max_drawdown_pct': round(s1['max_drawdown_pct'], 1),
        },
        'fixed_004_no_fees': {
            'final_balance': round(s1b['final_balance'], 4),
            'total_return_pct': round(s1b['total_return'], 1),
        },
        'pct_10_with_fees': {
            'final_balance': round(s2['final_balance'], 4),
            'total_return_pct': round(s2['total_return'], 1),
            'trades': s2['trade_count'],
            'max_drawdown_pct': round(s2['max_drawdown_pct'], 1),
        },
        'pct_5_with_fees': {
            'final_balance': round(s3['final_balance'], 4),
            'total_return_pct': round(s3['total_return'], 1),
            'trades': s3['trade_count'],
            'max_drawdown_pct': round(s3['max_drawdown_pct'], 1),
        },
        'narrative_only': {
            'final_balance': round(s4['final_balance'], 4),
            'total_return_pct': round(s4['total_return'], 1),
            'trades': s4['trade_count'],
            'win_rate': round(s4['win_rate'], 1),
        },
        'control_only': {
            'final_balance': round(s5['final_balance'], 4),
            'total_return_pct': round(s5['total_return'], 1),
            'trades': s5['trade_count'],
            'win_rate': round(s5['win_rate'], 1),
        },
        'without_top5': {
            'final_balance': round(s_robust['final_balance'], 4),
            'total_return_pct': round(s_robust['total_return'], 1),
            'trades': s_robust['trade_count'],
        },
    },
    'fee_model': {
        'tx_fee_per_trade': TX_FEE_PER_TRADE,
        'buy_slippage_pct': BUY_SLIPPAGE_PCT,
        'sell_slippage_pct': SELL_SLIPPAGE_PCT,
    },
    'total_trades': len(trades),
    'narrative_trades': len(narrative_trades),
    'control_trades': len(control_trades),
    'proactive_trades': len(proactive_trades),
}

with open('/home/ubuntu/cycling_model_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print("Results saved to /home/ubuntu/cycling_model_results.json")

conn.close()
