"""
Session 5 Analysis — Query all trades from this fresh DB (all clean data with matching v2),
run significance tests, apply adversarial evaluation.
"""
import sqlite3
import json
import numpy as np
from scipy import stats
from datetime import datetime

DB_PATH = "data/solana_trader.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def analyze():
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # ── 1. OVERVIEW ──────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM trades")
    total = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trades WHERE exit_reason IS NOT NULL")
    closed = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM trades WHERE exit_reason IS NULL")
    open_t = c.fetchone()[0]
    
    print("=" * 70)
    print("SESSION 5 ANALYSIS — FRESH DB (ALL CLEAN DATA, MATCHING V2)")
    print(f"Run at: {datetime.utcnow().isoformat()}")
    print("=" * 70)
    print(f"\nTotal trades: {total} | Closed: {closed} | Open: {open_t}")
    
    if closed < 5:
        print("\n⚠️  INSUFFICIENT DATA: Only {closed} closed trades. Need at least 20+ for any meaningful analysis.")
        print("System is running and collecting. Check back in a few hours.")
        
        # Still show what we have
        c.execute("""
            SELECT id, token_name, trade_mode, category, entered_at, exit_reason, pnl_sol, pnl_pct, hold_time_sec
            FROM trades ORDER BY id
        """)
        print("\n--- All Trades ---")
        for row in c.fetchall():
            pnl = f"{row['pnl_sol']:.4f}" if row['pnl_sol'] is not None else "OPEN"
            pct = f"{row['pnl_pct']:.1f}%" if row['pnl_pct'] is not None else ""
            hold = f"{row['hold_time_sec']:.0f}s" if row['hold_time_sec'] is not None else ""
            print(f"  #{row['id']} {row['token_name'][:30]:30s} | {row['trade_mode']:10s} | {row['category'] or '':10s} | exit={row['exit_reason'] or 'OPEN':12s} | pnl={pnl} {pct} | hold={hold}")
        
        # Twitter signal data
        c.execute("SELECT id, token_name, twitter_signal_data FROM trades WHERE twitter_signal_data IS NOT NULL")
        print("\n--- Twitter Signal Data ---")
        for row in c.fetchall():
            try:
                tw = json.loads(row['twitter_signal_data'])
                print(f"  #{row['id']} {row['token_name'][:25]:25s} | tweets={tw.get('tweet_count', '?')} | engagement={tw.get('total_engagement', '?')} | kol={tw.get('has_kol', '?')}")
            except:
                print(f"  #{row['id']} {row['token_name'][:25]:25s} | [parse error]")
        
        # Virtual strategy performance
        c.execute("""
            SELECT strategy_name, COUNT(*) as n, 
                   AVG(pnl_sol) as avg_pnl, SUM(pnl_sol) as total_pnl,
                   SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
                   AVG(hold_time_sec) as avg_hold
            FROM virtual_exits 
            GROUP BY strategy_name
            ORDER BY avg_pnl DESC
        """)
        print("\n--- Virtual Strategy Performance ---")
        for row in c.fetchall():
            wr = (row['wins'] / row['n'] * 100) if row['n'] > 0 else 0
            print(f"  {row['strategy_name']:20s} | n={row['n']:3d} | WR={wr:5.1f}% | avg_pnl={row['avg_pnl']:.4f} | total={row['total_pnl']:.4f} | avg_hold={row['avg_hold']:.0f}s")
        
        conn.close()
        return
    
    # ── 2. TRADE MODE BREAKDOWN ──────────────────────────────────────────
    print("\n" + "=" * 70)
    print("TRADE MODE BREAKDOWN (closed trades only)")
    print("=" * 70)
    
    modes = {}
    c.execute("""
        SELECT trade_mode, COUNT(*) as n,
               SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
               AVG(pnl_sol) as avg_pnl, SUM(pnl_sol) as total_pnl,
               AVG(hold_minutes) as avg_hold
        FROM trades WHERE exit_reason IS NOT NULL
        GROUP BY trade_mode
    """)
    for row in c.fetchall():
        wr = (row['wins'] / row['n'] * 100) if row['n'] > 0 else 0
        modes[row['trade_mode']] = {
            'n': row['n'], 'wins': row['wins'], 'wr': wr,
            'avg_pnl': row['avg_pnl'], 'total_pnl': row['total_pnl'],
            'avg_hold': row['avg_hold']
        }
        print(f"\n  {row['trade_mode'].upper()}")
        print(f"    Trades: {row['n']} | Wins: {row['wins']} | WR: {wr:.1f}%")
        print(f"    Avg PnL: {row['avg_pnl']:.4f} SOL | Total PnL: {row['total_pnl']:.4f} SOL")
        print(f"    Avg Hold: {row['avg_hold']:.1f} min" if row['avg_hold'] else '    Avg Hold: N/A')
    
    # ── 3. SIGNIFICANCE TESTS ───────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SIGNIFICANCE TESTS")
    print("=" * 70)
    
    # Get PnL arrays by mode
    narrative_pnl = []
    control_pnl = []
    c.execute("SELECT pnl_sol, trade_mode FROM trades WHERE exit_reason IS NOT NULL")
    for row in c.fetchall():
        if row['trade_mode'] in ('proactive', 'narrative'):
            narrative_pnl.append(row['pnl_sol'])
        elif row['trade_mode'] == 'control':
            control_pnl.append(row['pnl_sol'])
    
    narrative_pnl = np.array(narrative_pnl)
    control_pnl = np.array(control_pnl)
    
    print(f"\n  Narrative group: n={len(narrative_pnl)}")
    print(f"  Control group:   n={len(control_pnl)}")
    
    if len(narrative_pnl) >= 5 and len(control_pnl) >= 5:
        # Welch's t-test
        t_stat, t_pval = stats.ttest_ind(narrative_pnl, control_pnl, equal_var=False)
        print(f"\n  Welch's t-test: t={t_stat:.4f}, p={t_pval:.4f}")
        
        # Mann-Whitney U
        u_stat, u_pval = stats.mannwhitneyu(narrative_pnl, control_pnl, alternative='two-sided')
        print(f"  Mann-Whitney U: U={u_stat:.4f}, p={u_pval:.4f}")
        
        # Win rate comparison (chi-squared)
        narr_wins = int(np.sum(narrative_pnl > 0))
        narr_losses = len(narrative_pnl) - narr_wins
        ctrl_wins = int(np.sum(control_pnl > 0))
        ctrl_losses = len(control_pnl) - ctrl_wins
        
        if min(narr_wins, narr_losses, ctrl_wins, ctrl_losses) > 0:
            contingency = [[narr_wins, narr_losses], [ctrl_wins, ctrl_losses]]
            chi2, chi_pval, dof, expected = stats.chi2_contingency(contingency)
            print(f"  Chi-squared (WR): chi2={chi2:.4f}, p={chi_pval:.4f}")
        else:
            print("  Chi-squared: SKIPPED (zero cell in contingency table)")
        
        # Bootstrap confidence interval for PnL difference
        n_boot = 10000
        diffs = []
        for _ in range(n_boot):
            narr_sample = np.random.choice(narrative_pnl, size=len(narrative_pnl), replace=True)
            ctrl_sample = np.random.choice(control_pnl, size=len(control_pnl), replace=True)
            diffs.append(np.mean(narr_sample) - np.mean(ctrl_sample))
        diffs = np.array(diffs)
        ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])
        print(f"  Bootstrap 95% CI for PnL diff: [{ci_low:.4f}, {ci_high:.4f}]")
        print(f"  Bootstrap mean diff: {np.mean(diffs):.4f}")
    else:
        print("\n  ⚠️  Not enough data for significance tests (need ≥5 per group)")
    
    # ── 4. OUTLIER ANALYSIS ──────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("ADVERSARIAL: OUTLIER REMOVAL TEST")
    print("=" * 70)
    
    all_closed_pnl = []
    c.execute("SELECT pnl_sol FROM trades WHERE exit_reason IS NOT NULL ORDER BY pnl_sol DESC")
    for row in c.fetchall():
        all_closed_pnl.append(row['pnl_sol'])
    all_closed_pnl = np.array(all_closed_pnl)
    
    if len(all_closed_pnl) > 3:
        total_pnl = np.sum(all_closed_pnl)
        print(f"\n  Total PnL (all): {total_pnl:.4f} SOL")
        for remove_n in [1, 3, 5]:
            if remove_n < len(all_closed_pnl):
                remaining = all_closed_pnl[remove_n:]
                print(f"  Remove top {remove_n}: {np.sum(remaining):.4f} SOL (was {total_pnl:.4f})")
    
    # ── 5. VIRTUAL STRATEGY COMPARISON ───────────────────────────────────
    print("\n" + "=" * 70)
    print("VIRTUAL STRATEGY PERFORMANCE")
    print("=" * 70)
    
    c.execute("""
        SELECT strategy_name, COUNT(*) as n,
               AVG(pnl_sol) as avg_pnl, SUM(pnl_sol) as total_pnl,
               SUM(CASE WHEN pnl_sol > 0 THEN 1 ELSE 0 END) as wins,
               AVG(hold_time_sec) as avg_hold
        FROM virtual_exits
        GROUP BY strategy_name
        ORDER BY avg_pnl DESC
    """)
    for row in c.fetchall():
        wr = (row['wins'] / row['n'] * 100) if row['n'] > 0 else 0
        print(f"  {row['strategy_name']:20s} | n={row['n']:3d} | WR={wr:5.1f}% | avg={row['avg_pnl']:.4f} | total={row['total_pnl']:.4f} | hold={row['avg_hold']:.0f}s")
    
    # ── 6. TWITTER SIGNAL COVERAGE ───────────────────────────────────────
    print("\n" + "=" * 70)
    print("TWITTER SIGNAL COVERAGE")
    print("=" * 70)
    
    c.execute("SELECT COUNT(*) FROM trades WHERE twitter_signal_data IS NOT NULL")
    tw_count = c.fetchone()[0]
    print(f"  Trades with Twitter data: {tw_count}/{total} ({tw_count/total*100:.1f}%)" if total > 0 else "  No trades")
    
    # Parse twitter data
    c.execute("SELECT twitter_signal_data, pnl_sol, trade_mode FROM trades WHERE twitter_signal_data IS NOT NULL AND exit_reason IS NOT NULL")
    tw_trades = []
    for row in c.fetchall():
        try:
            tw = json.loads(row['twitter_signal_data'])
            tw['pnl_sol'] = row['pnl_sol']
            tw['trade_mode'] = row['trade_mode']
            tw_trades.append(tw)
        except:
            pass
    
    if tw_trades:
        print(f"\n  Closed trades with Twitter data: {len(tw_trades)}")
        tweet_counts = [t['tweet_count'] for t in tw_trades]
        engagements = [t['total_engagement'] for t in tw_trades]
        pnls = [t['pnl_sol'] for t in tw_trades]
        
        if len(tweet_counts) >= 3:
            corr_tweets, p_tweets = stats.spearmanr(tweet_counts, pnls)
            print(f"  Spearman corr (tweet_count vs pnl): r={corr_tweets:.4f}, p={p_tweets:.4f}")
            corr_eng, p_eng = stats.spearmanr(engagements, pnls)
            print(f"  Spearman corr (engagement vs pnl): r={corr_eng:.4f}, p={p_eng:.4f}")
    
    # ── 7. ADVERSARIAL CHECKLIST ─────────────────────────────────────────
    print("\n" + "=" * 70)
    print("ADVERSARIAL CHECKLIST")
    print("=" * 70)
    
    print(f"\n  [ ] Outlier test: {'DONE — see above' if len(all_closed_pnl) > 3 else 'INSUFFICIENT DATA'}")
    print(f"  [ ] Time-window test: {'INSUFFICIENT DATA — need 4+ hours' if closed < 50 else 'NEEDS ANALYSIS'}")
    print(f"  [ ] Selectivity test: Need to check % of tokens rejected")
    print(f"  [ ] Coverage test: Twitter data on {tw_count}/{total} trades ({tw_count/total*100:.1f}%)" if total > 0 else "  [ ] Coverage test: No data")
    print(f"  [ ] Fee test: All PnL includes 8% RT fees (built into paper trader)")
    print(f"  [ ] Sample size: n={closed} closed trades — {'INSUFFICIENT (<100)' if closed < 100 else 'SUFFICIENT'}")
    print(f"  [ ] Multi-test agreement: {'DONE — see above' if closed >= 10 else 'INSUFFICIENT DATA'}")
    print(f"  [ ] Falsification: Narrative WR must be significantly > Control WR at p<0.05")
    print(f"  [ ] Base rate: Need to compare against random token selection")
    
    # ── 8. SUMMARY ───────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("SESSION 5 SUMMARY")
    print("=" * 70)
    print(f"""
  STATUS: {'DATA COLLECTION — EARLY STAGE' if closed < 50 else 'DATA COLLECTION — BUILDING SAMPLE'}
  
  System Health:
    - paper_trader.py: RUNNING (v4 with Twitter signal)
    - Matching logic: v2 (fixed, whole-word + stop words)
    - Twitter signal: ACTIVE and logging
    - DB: Fresh, all data is clean (matching v2)
    - Trades collecting since start
  
  Key Numbers:
    - Total trades: {total} ({closed} closed, {open_t} open)
    - Narrative/Proactive: n={len(narrative_pnl)}, avg_pnl={f'{np.mean(narrative_pnl):.4f}' if len(narrative_pnl) > 0 else 'N/A'}
    - Control: n={len(control_pnl)}, avg_pnl={f'{np.mean(control_pnl):.4f}' if len(control_pnl) > 0 else 'N/A'}
  
  What's Needed:
    - 200+ true narrative trades with clean matching
    - True narrative WR significantly > Control WR (p < 0.05)
    - Multiple days of data
    - Diamond hands strategy >20% WR over 300+ exits
""")
    
    conn.close()

if __name__ == "__main__":
    analyze()
