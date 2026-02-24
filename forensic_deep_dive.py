"""
Deep dive: Fix slippage, understand execution gap, live moonshot rate
"""
import sqlite3
from collections import defaultdict

db_path = '/root/solana_trader/data/solana_trader.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=" * 80)
print("DEEP DIVE: THE THREE REAL QUESTIONS")
print("=" * 80)

# ═══════════════════════════════════════════════════════════════════════════════
# Q1: WHAT IS THE REAL SLIPPAGE?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ1: REAL SLIPPAGE (buy side)")
print("-" * 60)

c.execute("""
  SELECT slippage_pct, amount_sol, token_name
  FROM live_trades
  WHERE action='buy' AND success=1 AND slippage_pct IS NOT NULL
  ORDER BY slippage_pct
""")
buys = c.fetchall()
slippages = [b['slippage_pct'] for b in buys]
if slippages:
    # Remove extreme outliers (>500% is clearly a data error)
    clean = [s for s in slippages if abs(s) < 5.0]
    print(f"  Total buy records with slippage: {len(slippages)}")
    print(f"  After removing >500% outliers: {len(clean)}")
    if clean:
        avg = sum(clean) / len(clean)
        median = sorted(clean)[len(clean)//2]
        print(f"  Mean slippage: {avg*100:.1f}%")
        print(f"  Median slippage: {median*100:.1f}%")
        print(f"  Min: {min(clean)*100:.1f}%, Max: {max(clean)*100:.1f}%")
        
        # Distribution
        brackets = [(-9, -0.1, "Negative (got better price)"), (-0.1, 0, "Near zero neg"), (0, 0.05, "0-5%"), (0.05, 0.1, "5-10%"), (0.1, 0.2, "10-20%"), (0.2, 0.5, "20-50%"), (0.5, 5, ">50%")]
        print(f"\n  Slippage distribution:")
        for lo, hi, label in brackets:
            count = len([s for s in clean if lo <= s < hi])
            if count > 0:
                print(f"    {label}: {count} trades ({count/len(clean)*100:.0f}%)")
    
    # Show the outliers
    outliers = [s for s in slippages if abs(s) >= 5.0]
    if outliers:
        print(f"\n  Outliers removed (>500%): {len(outliers)}")
        for b in buys:
            if abs(b['slippage_pct']) >= 5.0:
                print(f"    {b['token_name']}: {b['slippage_pct']*100:.0f}% slippage, {b['amount_sol']} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# Q1b: SELL-SIDE SLIPPAGE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ1b: REAL SLIPPAGE (sell side)")
print("-" * 60)

c.execute("""
  SELECT slippage_pct, amount_sol, token_name
  FROM live_trades
  WHERE action='sell' AND success=1 AND slippage_pct IS NOT NULL
  ORDER BY slippage_pct
""")
sells = c.fetchall()
sell_slippages = [s['slippage_pct'] for s in sells if s['slippage_pct'] is not None]
clean_sells = [s for s in sell_slippages if abs(s) < 5.0]
if clean_sells:
    avg_sell = sum(clean_sells) / len(clean_sells)
    median_sell = sorted(clean_sells)[len(clean_sells)//2]
    print(f"  Mean sell slippage: {avg_sell*100:.1f}%")
    print(f"  Median sell slippage: {median_sell*100:.1f}%")

# ═══════════════════════════════════════════════════════════════════════════════
# Q2: WHY IS EXECUTION COVERAGE ONLY 11%?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ2: WHY DID 89% OF PROACTIVE TRADES NEVER EXECUTE LIVE?")
print("-" * 60)

# When was live trading enabled vs total paper trading time?
c.execute("SELECT MIN(entered_at) as first, MAX(exit_at) as last FROM trades WHERE status='closed'")
paper_range = c.fetchone()
c.execute("SELECT MIN(executed_at) as first, MAX(executed_at) as last FROM live_trades")
live_range = c.fetchone()
print(f"  Paper trading range: {paper_range['first']} → {paper_range['last']}")
print(f"  Live trading range:  {live_range['first']} → {live_range['last']}")

# How many proactive trades happened DURING live trading windows?
c.execute("""
  SELECT COUNT(*) FROM trades 
  WHERE status='closed' AND trade_mode='proactive' 
  AND entered_at >= '2026-02-23 22:21:00'
""")
proactive_during_live = c.fetchone()[0]
print(f"\n  Proactive trades during live window: {proactive_during_live}")
print(f"  Live buys attempted: 165")
print(f"  Coverage during live window: {165/proactive_during_live*100:.1f}%" if proactive_during_live > 0 else "")

# What about the trades that happened during live window but weren't attempted?
c.execute("""
  SELECT t.id, t.token_name, t.pnl_sol, t.pnl_pct, t.exit_reason, t.category
  FROM trades t
  WHERE t.status='closed' AND t.trade_mode='proactive'
  AND t.entered_at >= '2026-02-23 22:21:00'
  AND t.id NOT IN (SELECT DISTINCT paper_trade_id FROM live_trades WHERE action='buy')
  ORDER BY t.pnl_sol DESC
  LIMIT 15
""")
missed = c.fetchall()
print(f"\n  Top missed trades (proactive, during live window, no live buy):")
for m in missed:
    print(f"    {m['token_name']:<30} {m['pnl_sol']:>8.4f} SOL ({m['pnl_pct']*100 if m['pnl_pct'] else 0:.0f}%) {m['exit_reason']} cat={m['category']}")

# ═══════════════════════════════════════════════════════════════════════════════
# Q3: LIVE MOONSHOT RATE vs PAPER MOONSHOT RATE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ3: MOONSHOT CAPTURE RATE — PAPER vs LIVE")
print("-" * 60)

# Paper moonshots during live window
c.execute("""
  SELECT COUNT(*) as total,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN pnl_sol ELSE 0 END) as moonshot_pnl
  FROM trades
  WHERE status='closed' AND trade_mode='proactive'
  AND entered_at >= '2026-02-23 22:21:00'
""")
r = c.fetchone()
print(f"  Paper proactive during live window: {r['total']} trades, {r['moonshots']} moonshots ({r['moonshots']/r['total']*100:.1f}%)" if r['total'] > 0 else "")
print(f"  Paper moonshot PnL: {r['moonshot_pnl']:.4f} SOL" if r['moonshot_pnl'] else "  Paper moonshot PnL: 0")

# Live moonshots
c.execute("""
  SELECT COUNT(*) as total,
    SUM(CASE WHEN pnl_pct > 1.0 THEN 1 ELSE 0 END) as moonshots
  FROM live_trades
  WHERE action='sell' AND success=1
""")
lr = c.fetchone()
print(f"  Live sells: {lr['total']}, moonshots (>100%): {lr['moonshots']}")

# Show all live trades sorted by PnL
print(f"\n  All live round-trips by PnL (top 20):")
c.execute("""
  SELECT b.token_name, b.amount_sol as buy_sol, s.amount_sol as sell_sol,
    ROUND(s.amount_sol - b.amount_sol, 4) as pnl,
    ROUND((s.amount_sol - b.amount_sol) / b.amount_sol * 100, 1) as pnl_pct
  FROM live_trades b
  JOIN live_trades s ON b.paper_trade_id = s.paper_trade_id AND s.action='sell' AND s.success=1
  WHERE b.action='buy' AND b.success=1
  ORDER BY pnl DESC
  LIMIT 20
""")
for row in c.fetchall():
    print(f"    {row['token_name']:<30} buy={row['buy_sol']:.4f} sell={row['sell_sol']:.4f} pnl={row['pnl']:.4f} ({row['pnl_pct']:.1f}%)")

# ═══════════════════════════════════════════════════════════════════════════════
# Q4: WHAT DOES PROACTIVE MODE ACTUALLY ADD?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ4: DOES PROACTIVE MODE ADD VALUE OVER CONTROL?")
print("-" * 60)

c.execute("""
  SELECT trade_mode,
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots,
    ROUND(SUM(CASE WHEN pnl_pct >= 1.0 THEN pnl_sol ELSE 0 END), 4) as moonshot_pnl,
    ROUND(AVG(CASE WHEN pnl_pct >= 1.0 THEN pnl_sol ELSE NULL END), 4) as avg_moonshot
  FROM trades
  WHERE status='closed' AND entered_at >= '2026-02-23 22:21:00'
  GROUP BY trade_mode
""")
print(f"  {'Mode':<12} {'Trades':>7} {'PnL':>10} {'Avg':>10} {'Moon#':>6} {'MoonPnL':>10} {'AvgMoon':>10} {'MoonRate':>10}")
for row in c.fetchall():
    mr = f"{row['moonshots']/row['total']*100:.1f}%" if row['total'] > 0 else "0%"
    print(f"  {row['trade_mode']:<12} {row['total']:>7} {row['total_pnl']:>10.4f} {row['avg_pnl']:>10.6f} {row['moonshots']:>6} {row['moonshot_pnl']:>10.4f} {row['avg_moonshot'] or 0:>10.4f} {mr:>10}")

# ═══════════════════════════════════════════════════════════════════════════════
# Q5: THE LOTTERY TICKET MATH — DOES IT WORK LIVE?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ5: LOTTERY TICKET MATH — PAPER vs LIVE")
print("-" * 60)

# Paper math (proactive only, during live window)
c.execute("""
  SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots,
    AVG(CASE WHEN pnl_pct >= 1.0 THEN pnl_sol ELSE NULL END) as avg_moonshot_pnl,
    AVG(CASE WHEN pnl_pct < 1.0 THEN pnl_sol ELSE NULL END) as avg_bleed
  FROM trades
  WHERE status='closed' AND trade_mode='proactive' AND entered_at >= '2026-02-23 22:21:00'
""")
p = c.fetchone()
if p and p['total'] > 0:
    moon_rate = p['moonshots'] / p['total']
    avg_moon = p['avg_moonshot_pnl'] or 0
    avg_bleed = p['avg_bleed'] or 0
    ev_paper = moon_rate * avg_moon + (1 - moon_rate) * avg_bleed
    print(f"  PAPER (proactive, live window):")
    print(f"    Moonshot rate: {moon_rate*100:.2f}%")
    print(f"    Avg moonshot payoff: {avg_moon:.4f} SOL")
    print(f"    Avg bleed: {avg_bleed:.6f} SOL")
    print(f"    EV per trade: {ev_paper:.6f} SOL")
    print(f"    Formula: {moon_rate*100:.2f}% × {avg_moon:.4f} + {(1-moon_rate)*100:.2f}% × {avg_bleed:.6f} = {ev_paper:.6f}")

# Live math
print(f"\n  LIVE (actual on-chain):")
print(f"    157 round-trips, 2 moonshots (>100%)")
live_moon_rate = 2 / 157
live_avg_moon = (0.1013 + 0.0520) / 2  # TOP1 + stop selling
live_avg_bleed = (-0.6262 - 0.1013 - 0.0520) / 155  # total minus moonshots
live_ev = live_moon_rate * live_avg_moon + (1 - live_moon_rate) * live_avg_bleed
print(f"    Moonshot rate: {live_moon_rate*100:.2f}%")
print(f"    Avg moonshot payoff: {live_avg_moon:.4f} SOL")
print(f"    Avg bleed: {live_avg_bleed:.6f} SOL")
print(f"    EV per trade: {live_ev:.6f} SOL")
print(f"    Formula: {live_moon_rate*100:.2f}% × {live_avg_moon:.4f} + {(1-live_moon_rate)*100:.2f}% × {live_avg_bleed:.6f} = {live_ev:.6f}")

# ═══════════════════════════════════════════════════════════════════════════════
# Q6: WHAT IF WE JUST TRADED EVERYTHING (NO FILTER)?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ6: PROACTIVE vs CONTROL vs NARRATIVE — SAME WINDOW")
print("-" * 60)

c.execute("""
  SELECT trade_mode,
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots
  FROM trades
  WHERE status='closed' AND entered_at >= '2026-02-23 22:21:00'
  GROUP BY trade_mode
""")
for row in c.fetchall():
    mr = f"{row['moonshots']/row['total']*100:.1f}%" if row['total'] > 0 else "0%"
    print(f"  {row['trade_mode']:<12}: {row['total']} trades, PnL={row['total_pnl']}, avg={row['avg_pnl']}, moonshots={row['moonshots']} ({mr})")

# ═══════════════════════════════════════════════════════════════════════════════
# Q7: WHAT CATEGORIES ACTUALLY WORK?
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\nQ7: CATEGORY PERFORMANCE (proactive only, live window)")
print("-" * 60)

c.execute("""
  SELECT category,
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins
  FROM trades
  WHERE status='closed' AND trade_mode='proactive' AND entered_at >= '2026-02-23 22:21:00'
  GROUP BY category
  ORDER BY avg_pnl DESC
""")
print(f"  {'Category':<20} {'Trades':>7} {'PnL':>10} {'Avg':>10} {'WR':>7} {'Moons':>6}")
for row in c.fetchall():
    wr = f"{row['wins']/row['total']*100:.0f}%"
    print(f"  {(row['category'] or 'none'):<20} {row['total']:>7} {row['total_pnl']:>10.4f} {row['avg_pnl']:>10.6f} {wr:>7} {row['moonshots']:>6}")

conn.close()
print("\n" + "=" * 80)
print("END OF DEEP DIVE")
print("=" * 80)
