"""
Forensic analysis: Paper vs Live gap decomposition.
Nothing sacred. What does the data actually say?
"""
import sqlite3
import json
from collections import defaultdict

db_path = '/root/solana_trader/data/solana_trader.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print("FORENSIC ANALYSIS: PAPER vs LIVE — GROUND TRUTH")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. ALL-TIME LIVE TRADING: WHAT ACTUALLY HAPPENED ON-CHAIN?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n1. ALL-TIME LIVE TRADING RESULTS")
print("-" * 60)

c.execute("""
  SELECT 
    action,
    COUNT(*) as total,
    SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as success,
    SUM(CASE WHEN success=0 THEN 1 ELSE 0 END) as failed,
    ROUND(SUM(CASE WHEN success=1 THEN amount_sol ELSE 0 END), 4) as total_sol
  FROM live_trades
  GROUP BY action
""")
for row in c.fetchall():
    print(f"  {row['action'].upper()}: {row['total']} total, {row['success']} success, {row['failed']} failed, {row['total_sol']} SOL")

c.execute("""
  SELECT 
    ROUND(SUM(CASE WHEN action='buy' AND success=1 THEN amount_sol ELSE 0 END), 4) as total_spent,
    ROUND(SUM(CASE WHEN action='sell' AND success=1 THEN amount_sol ELSE 0 END), 4) as total_received,
    COUNT(DISTINCT CASE WHEN action='buy' AND success=1 THEN paper_trade_id END) as unique_buys,
    COUNT(DISTINCT CASE WHEN action='sell' AND success=1 THEN paper_trade_id END) as unique_sells,
    MIN(executed_at) as first_trade,
    MAX(executed_at) as last_trade
  FROM live_trades
""")
r = c.fetchone()
print(f"\n  Total spent on buys: {r['total_spent']} SOL")
print(f"  Total received from sells: {r['total_received']} SOL")
print(f"  GROSS PnL: {round(r['total_received'] - r['total_spent'], 4)} SOL")
print(f"  Unique buy round-trips: {r['unique_buys']}")
print(f"  Unique sell round-trips: {r['unique_sells']}")
print(f"  Time range: {r['first_trade']} → {r['last_trade']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. ROUND-TRIP ANALYSIS: PAIR EACH BUY WITH ITS SELL
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n2. ROUND-TRIP ANALYSIS (buy→sell pairs)")
print("-" * 60)

c.execute("""
  SELECT paper_trade_id, token_name, action, amount_sol, success, pnl_sol, pnl_pct, hold_time_sec, slippage_pct
  FROM live_trades
  WHERE success = 1
  ORDER BY paper_trade_id, action
""")
all_trades = c.fetchall()

# Group by paper_trade_id
trade_map = defaultdict(lambda: {"buys": [], "sells": []})
for t in all_trades:
    trade_map[t['paper_trade_id']][f"{t['action']}s"].append(dict(t))

complete_rts = []
buy_only = []
sell_only = []

for ptid, data in trade_map.items():
    if data['buys'] and data['sells']:
        buy = data['buys'][0]
        sell = data['sells'][0]
        rt_pnl = sell['amount_sol'] - buy['amount_sol']
        rt_pct = (rt_pnl / buy['amount_sol']) * 100 if buy['amount_sol'] > 0 else 0
        complete_rts.append({
            'ptid': ptid,
            'name': buy['token_name'],
            'buy_sol': buy['amount_sol'],
            'sell_sol': sell['amount_sol'],
            'pnl_sol': rt_pnl,
            'pnl_pct': rt_pct,
            'hold_sec': sell.get('hold_time_sec', 0),
            'buy_slippage': buy.get('slippage_pct', 0),
        })
    elif data['buys'] and not data['sells']:
        buy_only.append(data['buys'][0])
    elif data['sells'] and not data['buys']:
        sell_only.append(data['sells'][0])

print(f"  Complete round-trips: {len(complete_rts)}")
print(f"  Buy-only (no sell): {len(buy_only)}")
print(f"  Sell-only (no buy): {len(sell_only)}")

if complete_rts:
    total_pnl = sum(rt['pnl_sol'] for rt in complete_rts)
    winners = [rt for rt in complete_rts if rt['pnl_sol'] > 0]
    losers = [rt for rt in complete_rts if rt['pnl_sol'] <= 0]
    
    print(f"\n  Total PnL from round-trips: {total_pnl:.4f} SOL")
    print(f"  Win rate: {len(winners)}/{len(complete_rts)} = {len(winners)/len(complete_rts)*100:.1f}%")
    print(f"  Avg winner: {sum(w['pnl_sol'] for w in winners)/len(winners):.4f} SOL ({sum(w['pnl_pct'] for w in winners)/len(winners):.1f}%)" if winners else "  No winners")
    print(f"  Avg loser: {sum(l['pnl_sol'] for l in losers)/len(losers):.4f} SOL ({sum(l['pnl_pct'] for l in losers)/len(losers):.1f}%)" if losers else "  No losers")
    
    # Best and worst
    best = max(complete_rts, key=lambda x: x['pnl_sol'])
    worst = min(complete_rts, key=lambda x: x['pnl_sol'])
    print(f"\n  Best trade: {best['name']} → {best['pnl_sol']:.4f} SOL ({best['pnl_pct']:.1f}%)")
    print(f"  Worst trade: {worst['name']} → {worst['pnl_sol']:.4f} SOL ({worst['pnl_pct']:.1f}%)")
    
    # Distribution
    print(f"\n  PnL distribution:")
    brackets = [(-999, -0.01, "Big loss (>0.01)"), (-0.01, -0.005, "Medium loss"), (-0.005, 0, "Small loss"), (0, 0.005, "Small win"), (0.005, 0.01, "Medium win"), (0.01, 999, "Big win (>0.01)")]
    for lo, hi, label in brackets:
        count = len([rt for rt in complete_rts if lo <= rt['pnl_sol'] < hi])
        pnl = sum(rt['pnl_sol'] for rt in complete_rts if lo <= rt['pnl_sol'] < hi)
        print(f"    {label}: {count} trades, {pnl:.4f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. BUY-ONLY TRADES: SOL STUCK IN TOKENS WE NEVER SOLD
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n3. BUY-ONLY TRADES (SOL deployed, never sold)")
print("-" * 60)
if buy_only:
    total_stuck = sum(b['amount_sol'] for b in buy_only)
    print(f"  Count: {len(buy_only)}")
    print(f"  Total SOL stuck: {total_stuck:.4f}")
    for b in buy_only[:10]:
        print(f"    {b['token_name']}: {b['amount_sol']:.4f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. FAILED BUYS: WHAT WE TRIED TO BUY BUT COULDN'T
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n4. FAILED BUYS (attempted but failed on-chain)")
print("-" * 60)
c.execute("""
  SELECT token_name, error, COUNT(*) as cnt
  FROM live_trades
  WHERE action='buy' AND success=0
  GROUP BY token_name, error
  ORDER BY cnt DESC
  LIMIT 20
""")
failed_buys = c.fetchall()
print(f"  Total failed buy attempts: {sum(f['cnt'] for f in failed_buys)}")
for f in failed_buys:
    err_short = (f['error'] or 'unknown')[:60]
    print(f"    {f['token_name']}: {err_short} (x{f['cnt']})")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. PAPER TRADES THAT WENT LIVE vs PAPER-ONLY: COMPARE SAME TOKENS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n5. PAPER vs LIVE: SAME TOKENS, DIFFERENT OUTCOMES")
print("-" * 60)

# Get all paper trade IDs that had live buys
live_ptids = set()
for rt in complete_rts:
    live_ptids.add(rt['ptid'])

if live_ptids:
    placeholders = ','.join(['?' for _ in live_ptids])
    c.execute(f"""
      SELECT id, token_name, trade_mode, category, pnl_sol, pnl_pct, exit_reason
      FROM trades
      WHERE id IN ({placeholders}) AND status='closed'
    """, list(live_ptids))
    paper_for_live = {r['id']: dict(r) for r in c.fetchall()}
    
    print(f"  Matched paper records: {len(paper_for_live)}")
    
    # Compare paper PnL vs live PnL for same trades
    comparisons = []
    for rt in complete_rts:
        if rt['ptid'] in paper_for_live:
            paper = paper_for_live[rt['ptid']]
            comparisons.append({
                'name': rt['name'],
                'paper_pnl': paper['pnl_sol'],
                'paper_pct': paper['pnl_pct'],
                'live_pnl': rt['pnl_sol'],
                'live_pct': rt['pnl_pct'],
                'exit_reason': paper['exit_reason'],
                'category': paper['category'],
                'mode': paper['trade_mode'],
            })
    
    if comparisons:
        paper_total = sum(c['paper_pnl'] or 0 for c in comparisons)
        live_total = sum(c['live_pnl'] for c in comparisons)
        print(f"\n  Same tokens, paper PnL: {paper_total:.4f} SOL")
        print(f"  Same tokens, live PnL:  {live_total:.4f} SOL")
        print(f"  Gap: {paper_total - live_total:.4f} SOL")
        
        # Where does the gap come from?
        print(f"\n  Gap decomposition by exit reason:")
        by_exit = defaultdict(lambda: {'paper': 0, 'live': 0, 'count': 0})
        for comp in comparisons:
            er = comp['exit_reason'] or 'unknown'
            by_exit[er]['paper'] += comp['paper_pnl'] or 0
            by_exit[er]['live'] += comp['live_pnl']
            by_exit[er]['count'] += 1
        for er, data in sorted(by_exit.items(), key=lambda x: x[1]['paper'] - x[1]['live'], reverse=True):
            gap = data['paper'] - data['live']
            print(f"    {er}: paper={data['paper']:.4f}, live={data['live']:.4f}, gap={gap:.4f} ({data['count']} trades)")
        
        # By trade mode
        print(f"\n  Gap decomposition by trade mode:")
        by_mode = defaultdict(lambda: {'paper': 0, 'live': 0, 'count': 0})
        for comp in comparisons:
            m = comp['mode'] or 'unknown'
            by_mode[m]['paper'] += comp['paper_pnl'] or 0
            by_mode[m]['live'] += comp['live_pnl']
            by_mode[m]['count'] += 1
        for m, data in sorted(by_mode.items(), key=lambda x: x[1]['paper'] - x[1]['live'], reverse=True):
            gap = data['paper'] - data['live']
            print(f"    {m}: paper={data['paper']:.4f}, live={data['live']:.4f}, gap={gap:.4f} ({data['count']} trades)")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. THE CORE QUESTION: IS THE STRATEGY PROFITABLE EVEN ON PAPER?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n6. PAPER TRADING REALITY CHECK")
print("-" * 60)

c.execute("""
  SELECT 
    trade_mode,
    COUNT(*) as total,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    ROUND(SUM(CASE WHEN pnl_sol > 0 THEN pnl_sol ELSE 0 END), 4) as win_pnl,
    ROUND(SUM(CASE WHEN pnl_sol <= 0 THEN pnl_sol ELSE 0 END), 4) as loss_pnl,
    MAX(pnl_sol) as best_trade,
    COUNT(CASE WHEN pnl_pct > 10 THEN 1 END) as moonshots_10x
  FROM trades
  WHERE status='closed'
  GROUP BY trade_mode
""")
print(f"  {'Mode':<12} {'Trades':>7} {'WR':>6} {'PnL':>10} {'Avg':>10} {'Best':>10} {'10x+':>5}")
for row in c.fetchall():
    wr = f"{row['wins']/row['total']*100:.1f}%" if row['total'] > 0 else "0%"
    print(f"  {row['trade_mode']:<12} {row['total']:>7} {wr:>6} {row['total_pnl']:>10.4f} {row['avg_pnl']:>10.6f} {row['best_trade']:>10.4f} {row['moonshots_10x']:>5}")

# Paper PnL with phantom trades removed
c.execute("""
  SELECT 
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as raw_pnl,
    ROUND(SUM(CASE WHEN phantom_exit=1 THEN pnl_sol ELSE 0 END), 4) as phantom_pnl,
    COUNT(CASE WHEN phantom_exit=1 THEN 1 END) as phantom_count
  FROM trades
  WHERE status='closed'
""")
r = c.fetchone()
if r:
    print(f"\n  Raw paper PnL: {r['raw_pnl']} SOL")
    print(f"  Phantom PnL: {r['phantom_pnl']} SOL ({r['phantom_count']} trades)")
    print(f"  Realistic paper PnL: {(r['raw_pnl'] or 0) - (r['phantom_pnl'] or 0):.4f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. CONCENTRATION RISK: HOW MANY TRADES CARRY THE PAPER PNL?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n7. CONCENTRATION RISK")
print("-" * 60)

c.execute("""
  SELECT token_name, pnl_sol, pnl_pct, trade_mode, exit_reason, category
  FROM trades
  WHERE status='closed'
  ORDER BY pnl_sol DESC
  LIMIT 20
""")
top20 = c.fetchall()
top20_pnl = sum(t['pnl_sol'] for t in top20)

c.execute("SELECT SUM(pnl_sol) FROM trades WHERE status='closed'")
total_paper_pnl = c.fetchone()[0] or 0

print(f"  Total paper PnL: {total_paper_pnl:.4f} SOL")
print(f"  Top 20 trades PnL: {top20_pnl:.4f} SOL ({top20_pnl/total_paper_pnl*100:.1f}% of total)" if total_paper_pnl != 0 else "")
print(f"\n  Top 20 trades:")
for t in top20:
    print(f"    {t['token_name']:<30} {t['pnl_sol']:>10.4f} SOL ({t['pnl_pct']*100 if t['pnl_pct'] else 0:.0f}%) {t['trade_mode']:<12} {t['exit_reason']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 8. THE REAL QUESTION: WHAT WOULD LIVE PNL BE IF WE CAPTURED EVERY PAPER TRADE?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n8. SLIPPAGE MODEL: IF WE CAPTURED EVERY PAPER TRADE, WHAT WOULD LIVE PNL BE?")
print("-" * 60)

# Average buy slippage from live data
avg_slippages = [rt['buy_slippage'] for rt in complete_rts if rt['buy_slippage'] is not None and rt['buy_slippage'] != 0]
avg_buy_slip = sum(avg_slippages) / len(avg_slippages) if avg_slippages else 0.13
print(f"  Measured avg buy slippage: {avg_buy_slip*100:.1f}%")

# Apply slippage to all paper trades
c.execute("""
  SELECT pnl_pct, trade_mode, pnl_sol
  FROM trades
  WHERE status='closed' AND trade_mode='proactive'
""")
paper_proactive = c.fetchall()
slippage_adjusted_pnl = 0
for p in paper_proactive:
    paper_return = p['pnl_pct'] or 0
    # Slippage reduces the effective return
    # If paper says +50%, but we pay 13% slippage on buy and ~5% on sell, effective is +50% - 18% = +32%
    # More accurately: buy at 1.13x paper price, sell at 0.95x paper price
    adjusted_return = (1 + paper_return) / (1 + avg_buy_slip) * 0.97 - 1  # 3% sell slippage estimate
    slippage_adjusted_pnl += adjusted_return * 0.04  # 0.04 SOL base

print(f"  Paper proactive trades: {len(paper_proactive)}")
print(f"  Paper proactive PnL: {sum(p['pnl_sol'] for p in paper_proactive):.4f} SOL")
print(f"  Slippage-adjusted PnL estimate: {slippage_adjusted_pnl:.4f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 9. WHAT PERCENTAGE OF PAPER TRADES COULD WE ACTUALLY EXECUTE?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n9. EXECUTION COVERAGE")
print("-" * 60)

c.execute("""
  SELECT COUNT(*) FROM trades WHERE status='closed' AND trade_mode='proactive'
""")
total_proactive_paper = c.fetchone()[0]

c.execute("""
  SELECT COUNT(DISTINCT paper_trade_id) FROM live_trades WHERE action='buy' AND success=1
""")
total_live_buys = c.fetchone()[0]

c.execute("""
  SELECT COUNT(DISTINCT paper_trade_id) FROM live_trades WHERE action='buy' AND success=0
""")
total_failed_buys = c.fetchone()[0]

print(f"  Total proactive paper trades: {total_proactive_paper}")
print(f"  Successful live buys: {total_live_buys}")
print(f"  Failed live buys: {total_failed_buys}")
print(f"  Never attempted: {total_proactive_paper - total_live_buys - total_failed_buys}")
print(f"  Execution rate: {total_live_buys/total_proactive_paper*100:.1f}%" if total_proactive_paper > 0 else "")

# ═══════════════════════════════════════════════════════════════════════════════
# 10. BLEED RATE: HOW FAST DO WE LOSE ON NON-MOONSHOTS?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n10. BLEED RATE (the real enemy)")
print("-" * 60)

c.execute("""
  SELECT 
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl
  FROM trades
  WHERE status='closed' AND trade_mode='proactive' AND pnl_pct < 1.0
""")
r = c.fetchone()
print(f"  Non-moonshot proactive trades (<100% gain): {r['total']}")
print(f"  Total bleed: {r['total_pnl']} SOL")
print(f"  Avg bleed per trade: {r['avg_pnl']} SOL")

c.execute("""
  SELECT 
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl
  FROM trades
  WHERE status='closed' AND trade_mode='proactive' AND pnl_pct >= 1.0
""")
r2 = c.fetchone()
print(f"\n  Moonshot proactive trades (>=100% gain): {r2['total']}")
print(f"  Total moonshot PnL: {r2['total_pnl']} SOL")
print(f"\n  Moonshot rate: {r2['total']/r['total']*100:.2f}%" if r['total'] > 0 else "")
print(f"  Moonshot PnL per trade: {r2['total_pnl']/r2['total']:.4f} SOL" if r2['total'] > 0 else "")
print(f"  Bleed PnL per trade: {r['avg_pnl']} SOL")
print(f"  Break-even moonshot rate needed: {abs(r['avg_pnl']) / (r2['total_pnl']/r2['total']) * 100:.2f}%" if r2['total'] > 0 and r2['total_pnl'] > 0 else "  Cannot compute")

conn.close()
print("\n" + "=" * 80)
print("END OF FORENSIC ANALYSIS")
print("=" * 80)
