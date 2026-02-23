#!/usr/bin/env python3
"""Fix the buy bg thread to use module-level update_live_trade_fill instead of Database class."""

with open("/root/solana_trader/live_executor.py", "r") as f:
    content = f.read()

old = '''                            from database import Database
                            _db = Database()
                            actual_spent = abs(sol_change)
                            slippage = ((actual_spent - trade_amount) / trade_amount * 100) if trade_amount > 0 else 0
                            _db.update_live_trade_fill(
                                paper_trade_id=paper_trade_id,
                                action="buy",
                                sol_change=sol_change,
                                slippage_pct=slippage,
                            )'''

new = '''                            from database import update_live_trade_fill as _update_fill
                            actual_spent = abs(sol_change)
                            slippage = ((actual_spent - trade_amount) / trade_amount * 100) if trade_amount > 0 else 0
                            _update_fill(
                                paper_trade_id=paper_trade_id,
                                action="buy",
                                sol_change=sol_change,
                                slippage_pct=slippage,
                            )'''

if old in content:
    content = content.replace(old, new)
    print("FIX ✅ Buy bg thread import fixed")
else:
    print("FIX ❌ Could not find exact match")

with open("/root/solana_trader/live_executor.py", "w") as f:
    f.write(content)
