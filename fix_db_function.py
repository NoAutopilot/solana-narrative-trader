#!/usr/bin/env python3
"""
Fix the update_live_trade_fill and update_live_trade_sell_pnl functions in database.py.
They're currently inside if __name__ == "__main__" and have 'self' parameter.
Move them to module-level and remove 'self', use get_conn() instead.
Also fix the import in live_executor.py background threads.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# FIX database.py: Move functions out of __main__ block
# ═══════════════════════════════════════════════════════════════════════════════

with open("/root/solana_trader/database.py", "r") as f:
    db_content = f.read()

# Remove the broken functions from inside __main__
# They start after "if __name__ == '__main__':" and "init_db()"
# Replace the entire __main__ block

# Find where __main__ starts
main_idx = db_content.find('if __name__ == "__main__":')
if main_idx == -1:
    print("Could not find __main__ block")
else:
    # Keep everything before __main__
    before_main = db_content[:main_idx]
    
    # Add the proper module-level functions
    new_functions = '''
def update_live_trade_fill(paper_trade_id, action, sol_change=None, slippage_pct=None, live_fill_price_sol=None):
    """Update a live trade record with actual on-chain fill data (called after async verification)."""
    try:
        conn = get_conn()
        updates = []
        params = []
        if sol_change is not None and action == "buy":
            updates.append("amount_sol = ?")
            params.append(round(abs(sol_change), 8))
        if slippage_pct is not None:
            updates.append("slippage_pct = ?")
            params.append(round(slippage_pct, 4))
        if live_fill_price_sol is not None:
            updates.append("live_fill_price_sol = ?")
            params.append(live_fill_price_sol)
        if not updates:
            conn.close()
            return
        params.extend([paper_trade_id, action.upper()])
        sql = f"UPDATE live_trades SET {', '.join(updates)} WHERE paper_trade_id = ? AND UPPER(action) = ?"
        conn.execute(sql, params)
        conn.commit()
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger("database").error(f"Failed to update live trade fill: {e}")


def update_live_trade_sell_pnl(paper_trade_id, amount_sol, pnl_sol, pnl_pct, slippage_pct=None):
    """Update a live sell record with actual on-chain PnL data."""
    try:
        conn = get_conn()
        updates = ["amount_sol = ?", "pnl_sol = ?", "pnl_pct = ?"]
        params = [round(amount_sol, 8), round(pnl_sol, 8), round(pnl_pct, 6)]
        if slippage_pct is not None:
            updates.append("slippage_pct = ?")
            params.append(round(slippage_pct, 4))
        params.append(paper_trade_id)
        sql = f"UPDATE live_trades SET {', '.join(updates)} WHERE paper_trade_id = ? AND UPPER(action) = 'SELL'"
        conn.execute(sql, params)
        conn.commit()
        conn.close()
    except Exception as e:
        import logging
        logging.getLogger("database").error(f"Failed to update live trade sell PnL: {e}")


if __name__ == "__main__":
    init_db()
'''
    
    db_content = before_main + new_functions
    
    with open("/root/solana_trader/database.py", "w") as f:
        f.write(db_content)
    print("FIX DB ✅ Moved update_live_trade_fill and update_live_trade_sell_pnl to module level")

# ═══════════════════════════════════════════════════════════════════════════════
# FIX live_executor.py: Update imports in background threads
# ═══════════════════════════════════════════════════════════════════════════════

with open("/root/solana_trader/live_executor.py", "r") as f:
    le_content = f.read()

# Replace "from database import Database" + "_db = Database()" + "_db.update_live_trade_fill(...)"
# with "from database import update_live_trade_fill" + "update_live_trade_fill(...)"

# Fix in buy background thread
le_content = le_content.replace(
    '''                                from database import Database
                                _db = Database()
                                _db.update_live_trade_fill(''',
    '''                                from database import update_live_trade_fill as _update_fill
                                _update_fill('''
)

# Fix in sell background thread  
le_content = le_content.replace(
    '''                    from database import Database
                                    _db = Database()
                                    _db.update_live_trade_fill(''',
    '''                    from database import update_live_trade_fill as _update_fill
                                    _update_fill('''
)

# Also try the exact indentation from the async sell block we inserted
le_content = le_content.replace(
    'from database import Database\n                                    _db = Database()\n                                    _db.update_live_trade_fill(',
    'from database import update_live_trade_fill as _update_fill\n                                    _update_fill('
)

# Try another pattern - the sell bg thread uses different indentation
le_content = le_content.replace(
    '''                        from database import Database
                        _db = Database()
                        _db.update_live_trade_fill(''',
    '''                        from database import update_live_trade_fill as _update_fill
                        _update_fill('''
)

# Catch any remaining Database imports in bg threads
import re
le_content = re.sub(
    r'from database import Database\n(\s+)_db = Database\(\)\n(\s+)_db\.update_live_trade_fill\(',
    r'from database import update_live_trade_fill as _update_fill\n\1_update_fill(',
    le_content
)

with open("/root/solana_trader/live_executor.py", "w") as f:
    f.write(le_content)

print("FIX LE ✅ Updated imports in background threads to use module-level function")
print("\nDone. Restart service: systemctl restart solana-trader")
