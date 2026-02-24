"""
Extract all key data for ChatGPT briefing document
"""
import sqlite3
import json
from collections import defaultdict

db_path = '/root/solana_trader/data/solana_trader.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

output = {}

# ═══════════════════════════════════════════════════════════════════════════════
# 1. PAPER TRADING SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
print("=== PAPER TRADING DATA ===")

c.execute("SELECT COUNT(*) FROM trades WHERE status='closed'")
total_paper = c.fetchone()[0]

c.execute("""
  SELECT trade_mode,
    COUNT(*) as total,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    ROUND(MIN(pnl_sol), 4) as worst,
    ROUND(MAX(pnl_sol), 4) as best,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots_100pct,
    SUM(CASE WHEN pnl_pct >= 5.0 THEN 1 ELSE 0 END) as moonshots_500pct,
    SUM(CASE WHEN pnl_pct >= 10.0 THEN 1 ELSE 0 END) as moonshots_1000pct,
    SUM(CASE WHEN phantom_exit = 1 THEN 1 ELSE 0 END) as phantom_count,
    SUM(CASE WHEN phantom_exit = 1 THEN pnl_sol ELSE 0 END) as phantom_pnl
  FROM trades WHERE status='closed'
  GROUP BY trade_mode
""")
print(f"\nBy Trade Mode:")
print(f"{'Mode':<12} {'Total':>7} {'Wins':>6} {'WR':>7} {'PnL':>10} {'Avg':>10} {'Best':>10} {'Moon100':>8} {'Moon500':>8} {'Moon1k':>8} {'Phantom':>8} {'PhantPnL':>10}")
for r in c.fetchall():
    wr = f"{r['wins']/r['total']*100:.1f}%"
    print(f"{r['trade_mode']:<12} {r['total']:>7} {r['wins']:>6} {wr:>7} {r['total_pnl']:>10.4f} {r['avg_pnl']:>10.6f} {r['best']:>10.4f} {r['moonshots_100pct']:>8} {r['moonshots_500pct']:>8} {r['moonshots_1000pct']:>8} {r['phantom_count']:>8} {r['phantom_pnl'] or 0:>10.2f}")

# By exit reason
c.execute("""
  SELECT exit_reason,
    COUNT(*) as total,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl
  FROM trades WHERE status='closed'
  GROUP BY exit_reason
""")
print(f"\nBy Exit Reason:")
print(f"{'Reason':<15} {'Total':>7} {'Wins':>6} {'WR':>7} {'PnL':>10} {'Avg':>10}")
for r in c.fetchall():
    wr = f"{r['wins']/r['total']*100:.1f}%"
    print(f"{r['exit_reason']:<15} {r['total']:>7} {r['wins']:>6} {wr:>7} {r['total_pnl']:>10.4f} {r['avg_pnl']:>10.6f}")

# By category (proactive only)
c.execute("""
  SELECT category,
    COUNT(*) as total,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots
  FROM trades WHERE status='closed' AND trade_mode='proactive'
  GROUP BY category ORDER BY total_pnl DESC
""")
print(f"\nBy Category (proactive only):")
print(f"{'Category':<15} {'Total':>7} {'Wins':>6} {'WR':>7} {'PnL':>10} {'Avg':>10} {'Moons':>6}")
for r in c.fetchall():
    wr = f"{r['wins']/r['total']*100:.1f}%"
    print(f"{(r['category'] or 'none'):<15} {r['total']:>7} {r['wins']:>6} {wr:>7} {r['total_pnl']:>10.4f} {r['avg_pnl']:>10.6f} {r['moonshots']:>6}")

# By platform
c.execute("""
  SELECT platform,
    COUNT(*) as total,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots
  FROM trades WHERE status='closed' AND trade_mode='proactive'
  GROUP BY platform
""")
print(f"\nBy Platform (proactive only):")
for r in c.fetchall():
    print(f"  {r['platform'] or 'unknown'}: {r['total']} trades, PnL={r['total_pnl']}, moonshots={r['moonshots']}")

# Top 30 paper trades
c.execute("""
  SELECT token_name, trade_mode, category, pnl_sol, pnl_pct, exit_reason, phantom_exit, platform,
    ROUND(hold_minutes, 2) as hold_min
  FROM trades WHERE status='closed'
  ORDER BY pnl_sol DESC LIMIT 30
""")
print(f"\nTop 30 Paper Trades:")
print(f"{'Token':<35} {'Mode':<11} {'Cat':<10} {'PnL SOL':>10} {'PnL%':>10} {'Exit':<12} {'Phantom':>8} {'Platform':<10} {'HoldMin':>8}")
for r in c.fetchall():
    pct = f"{r['pnl_pct']*100:.0f}%" if r['pnl_pct'] else "N/A"
    print(f"{r['token_name'][:34]:<35} {r['trade_mode']:<11} {(r['category'] or 'n/a'):<10} {r['pnl_sol']:>10.4f} {pct:>10} {r['exit_reason']:<12} {r['phantom_exit'] or 0:>8} {(r['platform'] or 'unk'):<10} {r['hold_min'] or 0:>8.2f}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. LIVE TRADING DATA
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== LIVE TRADING DATA ===")

c.execute("SELECT COUNT(*) FROM live_trades WHERE action='buy'")
total_buys = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM live_trades WHERE action='buy' AND success=1")
success_buys = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM live_trades WHERE action='sell'")
total_sells = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM live_trades WHERE action='sell' AND success=1")
success_sells = c.fetchone()[0]

print(f"Total buy attempts: {total_buys}, successful: {success_buys} ({success_buys/total_buys*100:.1f}%)")
print(f"Total sell attempts: {total_sells}, successful: {success_sells} ({success_sells/total_sells*100:.1f}%)" if total_sells > 0 else "")

# Failed buys detail
c.execute("""
  SELECT token_name, error
  FROM live_trades WHERE action='buy' AND success=0
""")
print(f"\nFailed Buys:")
for r in c.fetchall():
    print(f"  {r['token_name']}: {(r['error'] or 'unknown')[:80]}")

# All live round trips
c.execute("""
  SELECT b.token_name, 
    ROUND(b.amount_sol, 4) as buy_sol, 
    ROUND(s.amount_sol, 4) as sell_sol,
    ROUND(s.amount_sol - b.amount_sol, 4) as pnl,
    ROUND((s.amount_sol - b.amount_sol) / b.amount_sol * 100, 1) as pnl_pct,
    b.executed_at as buy_time,
    s.executed_at as sell_time
  FROM live_trades b
  JOIN live_trades s ON b.paper_trade_id = s.paper_trade_id AND s.action='sell' AND s.success=1
  WHERE b.action='buy' AND b.success=1
  ORDER BY pnl DESC
""")
rows = c.fetchall()
print(f"\nAll {len(rows)} Live Round Trips (sorted by PnL):")
print(f"{'Token':<35} {'Buy':>7} {'Sell':>7} {'PnL':>8} {'PnL%':>8}")
total_buy_sol = 0
total_sell_sol = 0
wins = 0
for r in rows:
    total_buy_sol += r['buy_sol']
    total_sell_sol += r['sell_sol']
    if r['pnl'] > 0: wins += 1
    print(f"{r['token_name'][:34]:<35} {r['buy_sol']:>7.4f} {r['sell_sol']:>7.4f} {r['pnl']:>8.4f} {r['pnl_pct']:>7.1f}%")

print(f"\nLive Summary:")
print(f"  Total bought: {total_buy_sol:.4f} SOL")
print(f"  Total sold: {total_sell_sol:.4f} SOL")
print(f"  Net PnL: {total_sell_sol - total_buy_sol:.4f} SOL")
print(f"  Win rate: {wins}/{len(rows)} = {wins/len(rows)*100:.1f}%")
print(f"  Avg PnL/trade: {(total_sell_sol - total_buy_sol)/len(rows):.6f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. PAPER vs LIVE SAME TOKEN COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== PAPER vs LIVE: SAME TOKENS ===")

c.execute("""
  SELECT b.paper_trade_id, b.token_name,
    ROUND(s.amount_sol - b.amount_sol, 4) as live_pnl,
    ROUND((s.amount_sol - b.amount_sol) / b.amount_sol * 100, 1) as live_pnl_pct
  FROM live_trades b
  JOIN live_trades s ON b.paper_trade_id = s.paper_trade_id AND s.action='sell' AND s.success=1
  WHERE b.action='buy' AND b.success=1
""")
live_by_ptid = {}
for r in c.fetchall():
    live_by_ptid[r['paper_trade_id']] = {'live_pnl': r['live_pnl'], 'live_pnl_pct': r['live_pnl_pct'], 'name': r['token_name']}

if live_by_ptid:
    ptids = list(live_by_ptid.keys())
    placeholders = ','.join(['?' for _ in ptids])
    c.execute(f"""
      SELECT id, token_name, pnl_sol, pnl_pct, exit_reason, category
      FROM trades WHERE id IN ({placeholders}) AND status='closed'
    """, ptids)
    
    print(f"{'Token':<30} {'PaperPnL':>10} {'Paper%':>8} {'LivePnL':>10} {'Live%':>8} {'Exit':<12} {'Cat':<10}")
    paper_total = 0
    live_total = 0
    for r in c.fetchall():
        lid = live_by_ptid.get(r['id'], {})
        paper_pct = f"{r['pnl_pct']*100:.1f}%" if r['pnl_pct'] else "N/A"
        live_pct = f"{lid.get('live_pnl_pct', 0):.1f}%"
        paper_total += r['pnl_sol'] or 0
        live_total += lid.get('live_pnl', 0)
        print(f"{r['token_name'][:29]:<30} {r['pnl_sol'] or 0:>10.4f} {paper_pct:>8} {lid.get('live_pnl', 0):>10.4f} {live_pct:>8} {r['exit_reason']:<12} {(r['category'] or 'n/a'):<10}")
    
    print(f"\nSame-token totals: Paper={paper_total:.4f} SOL, Live={live_total:.4f} SOL, Gap={paper_total - live_total:.4f} SOL")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. VIRTUAL STRATEGY COMPARISON
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== VIRTUAL STRATEGY COMPARISON ===")

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='virtual_exits'")
if c.fetchone():
    c.execute("""
      SELECT strategy_id,
        COUNT(*) as total,
        SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
        ROUND(SUM(pnl_sol), 4) as total_pnl,
        ROUND(AVG(pnl_sol), 6) as avg_pnl,
        SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots
      FROM virtual_exits
      GROUP BY strategy_id
      ORDER BY avg_pnl DESC
    """)
    print(f"{'Strategy':<20} {'Total':>7} {'Wins':>6} {'WR':>7} {'PnL':>10} {'Avg':>10} {'Moons':>6}")
    for r in c.fetchall():
        wr = f"{r['wins']/r['total']*100:.1f}%"
        print(f"{r['strategy_id']:<20} {r['total']:>7} {r['wins']:>6} {wr:>7} {r['total_pnl']:>10.4f} {r['avg_pnl']:>10.6f} {r['moonshots']:>6}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. CONCENTRATION AND DISTRIBUTION
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== PNL DISTRIBUTION (paper, proactive) ===")

c.execute("""
  SELECT 
    SUM(CASE WHEN pnl_pct < -0.5 THEN 1 ELSE 0 END) as loss_50plus,
    SUM(CASE WHEN pnl_pct >= -0.5 AND pnl_pct < -0.1 THEN 1 ELSE 0 END) as loss_10_50,
    SUM(CASE WHEN pnl_pct >= -0.1 AND pnl_pct < 0 THEN 1 ELSE 0 END) as loss_0_10,
    SUM(CASE WHEN pnl_pct >= 0 AND pnl_pct < 0.1 THEN 1 ELSE 0 END) as gain_0_10,
    SUM(CASE WHEN pnl_pct >= 0.1 AND pnl_pct < 0.5 THEN 1 ELSE 0 END) as gain_10_50,
    SUM(CASE WHEN pnl_pct >= 0.5 AND pnl_pct < 1.0 THEN 1 ELSE 0 END) as gain_50_100,
    SUM(CASE WHEN pnl_pct >= 1.0 AND pnl_pct < 5.0 THEN 1 ELSE 0 END) as gain_100_500,
    SUM(CASE WHEN pnl_pct >= 5.0 AND pnl_pct < 50.0 THEN 1 ELSE 0 END) as gain_500_5000,
    SUM(CASE WHEN pnl_pct >= 50.0 THEN 1 ELSE 0 END) as gain_5000plus
  FROM trades WHERE status='closed' AND trade_mode='proactive'
""")
r = c.fetchone()
print(f"  Loss >50%: {r['loss_50plus']}")
print(f"  Loss 10-50%: {r['loss_10_50']}")
print(f"  Loss 0-10%: {r['loss_0_10']}")
print(f"  Gain 0-10%: {r['gain_0_10']}")
print(f"  Gain 10-50%: {r['gain_10_50']}")
print(f"  Gain 50-100%: {r['gain_50_100']}")
print(f"  Gain 100-500%: {r['gain_100_500']}")
print(f"  Gain 500-5000%: {r['gain_500_5000']}")
print(f"  Gain >5000%: {r['gain_5000plus']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 6. HOLD TIME ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== HOLD TIME ANALYSIS (paper, proactive) ===")

c.execute("""
  SELECT 
    CASE 
      WHEN hold_minutes < 0.5 THEN '0-30s'
      WHEN hold_minutes < 1.0 THEN '30-60s'
      WHEN hold_minutes < 2.0 THEN '1-2min'
      WHEN hold_minutes < 5.0 THEN '2-5min'
      ELSE '5min+'
    END as bucket,
    COUNT(*) as total,
    SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
    ROUND(SUM(pnl_sol), 4) as total_pnl,
    ROUND(AVG(pnl_sol), 6) as avg_pnl,
    SUM(CASE WHEN pnl_pct >= 1.0 THEN 1 ELSE 0 END) as moonshots
  FROM trades WHERE status='closed' AND trade_mode='proactive'
  GROUP BY bucket
  ORDER BY MIN(hold_minutes)
""")
print(f"{'Bucket':<10} {'Total':>7} {'Wins':>6} {'WR':>7} {'PnL':>10} {'Avg':>10} {'Moons':>6}")
for r in c.fetchall():
    wr = f"{r['wins']/r['total']*100:.1f}%"
    print(f"{r['bucket']:<10} {r['total']:>7} {r['wins']:>6} {wr:>7} {r['total_pnl']:>10.4f} {r['avg_pnl']:>10.6f} {r['moonshots']:>6}")

# ═══════════════════════════════════════════════════════════════════════════════
# 7. CURRENT CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
print("\n\n=== CURRENT CONFIG ===")
import importlib.util, sys
spec = importlib.util.spec_from_file_location("config", "/root/solana_trader/config.py")
cfg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfg)

config_keys = ['TRADE_SIZE_SOL', 'STOP_LOSS_PCT', 'TAKE_PROFIT_PCT', 'TRAILING_TP_ACTIVATION_PCT',
               'TRAILING_TP_DISTANCE_PCT', 'TIMEOUT_MINUTES', 'CONVICTION_FILTER', 
               'BLOCKED_CATEGORIES', 'VIRTUAL_STRATEGIES', 'LIVE_EXPERIMENT_DURATION_SEC']
for k in config_keys:
    if hasattr(cfg, k):
        print(f"  {k} = {getattr(cfg, k)}")

conn.close()
print("\n=== END DATA EXTRACT ===")
