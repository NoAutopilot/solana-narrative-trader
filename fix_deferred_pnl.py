#!/usr/bin/env python3
"""
Fix: Add deferred PnL verification to live_executor.py

Problem: _verify_tx_on_chain has a 14s window (5s + 3*3s) which isn't enough
for Solana finality. TXs land on-chain but getTransaction returns null.

Solution: Add a background thread that runs every 60s and backfills any
live_trades rows where live_fill_price_sol IS NULL and tx_signature exists.
"""
import re

FILE = '/root/solana_trader/live_executor.py'

with open(FILE, 'r') as f:
    content = f.read()

# 1. Add the deferred backfill function after the imports/globals section
# Find the _execution_metrics dict and add after it

backfill_code = '''

# ── Deferred PnL Backfill ──────────────────────────────────────────────
# Runs every 60s to fill in sol_change for TXs that weren't confirmed in time
_backfill_running = False

def _start_deferred_backfill():
    """Start a background thread that periodically backfills missing on-chain data."""
    global _backfill_running
    if _backfill_running:
        return
    _backfill_running = True
    
    def _backfill_loop():
        import sqlite3
        while True:
            try:
                time.sleep(60)  # Run every 60 seconds
                
                db_path = os.path.join(os.path.dirname(__file__), 'data', 'solana_trader.db')
                conn = sqlite3.connect(db_path)
                
                # Find live_trades with missing fill data
                rows = conn.execute('''
                    SELECT id, tx_signature, token_name, action, sol_amount
                    FROM live_trades
                    WHERE tx_signature IS NOT NULL
                    AND tx_signature != 'ambiguous_but_confirmed'
                    AND success = 1
                    AND live_fill_price_sol IS NULL
                    ORDER BY executed_at ASC
                    LIMIT 20
                ''').fetchall()
                
                if not rows:
                    conn.close()
                    continue
                
                logger.info(f"[BACKFILL] Found {len(rows)} trades with missing on-chain data")
                
                rpc_url = os.environ.get('HELIUS_RPC_URL', '')
                wallet = os.environ.get('WALLET_ADDRESS', '')
                filled = 0
                
                for row_id, sig, name, action, sol_amount in rows:
                    try:
                        resp = requests.post(rpc_url, json={
                            'jsonrpc': '2.0', 'id': 1,
                            'method': 'getTransaction',
                            'params': [sig, {'encoding': 'jsonParsed', 'maxSupportedTransactionVersion': 0}]
                        }, timeout=15)
                        result = resp.json().get('result')
                        
                        if not result:
                            continue
                        
                        meta = result.get('meta', {})
                        err = meta.get('err')
                        if err:
                            # TX failed on-chain
                            conn.execute('UPDATE live_trades SET success = 0 WHERE id = ?', (row_id,))
                            conn.commit()
                            logger.warning(f"[BACKFILL] {name} ({action}) TX failed on-chain: {err}")
                            continue
                        
                        pre = meta.get('preBalances', [])
                        post = meta.get('postBalances', [])
                        
                        if pre and post:
                            sol_change = (post[0] - pre[0]) / 1e9
                            
                            # Calculate actual fill price and slippage
                            actual_sol = abs(sol_change)
                            expected_sol = sol_amount or 0.04
                            slippage = ((actual_sol - expected_sol) / expected_sol * 100) if expected_sol > 0 else 0
                            
                            conn.execute('''
                                UPDATE live_trades 
                                SET live_fill_price_sol = ?,
                                    live_slippage_pct = ?
                                WHERE id = ?
                            ''', (sol_change, slippage, row_id))
                            conn.commit()
                            filled += 1
                            
                            logger.info(f"[BACKFILL] {name} ({action}): sol_change={sol_change:+.6f} slippage={slippage:+.1f}%")
                    
                    except Exception as e:
                        logger.debug(f"[BACKFILL] Error processing {name}: {e}")
                        continue
                
                conn.close()
                if filled > 0:
                    logger.info(f"[BACKFILL] Filled {filled}/{len(rows)} missing on-chain records")
                    
            except Exception as e:
                logger.warning(f"[BACKFILL] Loop error: {e}")
                time.sleep(60)
    
    t = threading.Thread(target=_backfill_loop, daemon=True, name="pnl-backfill")
    t.start()
    logger.info("[BACKFILL] Deferred PnL backfill thread started (runs every 60s)")
'''

# Insert after the _execution_metrics block
# Find the line with "slippage_observations"
insert_marker = '"slippage_observations": [],  # List of (action, expected_sol, actual_sol_change)\n}'
if insert_marker in content:
    content = content.replace(insert_marker, insert_marker + backfill_code)
    print("✅ Inserted backfill code after _execution_metrics")
else:
    # Try alternate insertion point
    alt_marker = '"slippage_observations": [],'
    if alt_marker in content:
        # Find the closing brace of _execution_metrics
        idx = content.find(alt_marker)
        # Find the next closing brace
        brace_idx = content.find('}', idx)
        content = content[:brace_idx+1] + backfill_code + content[brace_idx+1:]
        print("✅ Inserted backfill code (alt marker)")
    else:
        print("❌ Could not find insertion point for backfill code")
        print("Looking for markers...")
        for line in content.split('\n'):
            if 'slippage' in line.lower():
                print(f"  Found: {line.strip()}")

# 2. Start the backfill thread when execute_buy is first called
# Add _start_deferred_backfill() call at the beginning of execute_buy
start_call = '    _start_deferred_backfill()\n'
buy_marker = 'def execute_buy('
if buy_marker in content:
    # Find the function body start (after the docstring)
    func_idx = content.find(buy_marker)
    # Find the first line of actual code (after def and docstring)
    # Look for 'global' or first assignment
    body_markers = ['global _live_halted', 'if not LIVE_ENABLED', '_execution_metrics']
    for bm in body_markers:
        bm_idx = content.find(bm, func_idx)
        if bm_idx > 0:
            content = content[:bm_idx] + start_call + content[bm_idx:]
            print(f"✅ Added _start_deferred_backfill() call before '{bm}'")
            break
    else:
        print("❌ Could not find execute_buy body insertion point")

# 3. Also increase the initial verification window slightly (5s -> 8s, 3 retries -> 5)
content = content.replace(
    'TX_CONFIRM_WAIT_SEC = 5           # Wait before checking TX on-chain',
    'TX_CONFIRM_WAIT_SEC = 8           # Wait before checking TX on-chain'
)
content = content.replace(
    'TX_CONFIRM_RETRIES = 3            # Number of retries for TX confirmation',
    'TX_CONFIRM_RETRIES = 5            # Number of retries for TX confirmation'
)
print("✅ Increased TX confirm window: 8s wait + 5 retries = 23s total")

with open(FILE, 'w') as f:
    f.write(content)

print("\n✅ All fixes applied to live_executor.py")
print("Next: restart solana-trader.service to activate")
