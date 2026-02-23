"""
Fix live PnL tracking to use actual on-chain data.

Changes:
1. live_executor.py: After buy verification, update DB with sol_change (fill price proxy)
2. paper_trader.py: Use sell_result["sol_received"] for real PnL instead of paper estimates
3. database.py: Add update_live_trade_fill() method
"""

import re

# ═══════════════════════════════════════════════════════════════════════════════
# FIX 1: database.py — Add method to update live trade fill data after async verify
# ═══════════════════════════════════════════════════════════════════════════════

db_path = "/root/solana_trader/database.py"
with open(db_path, "r") as f:
    db_content = f.read()

# Add update_live_trade_fill method if not already present
if "update_live_trade_fill" not in db_content:
    # Find the last method in the class (before the end)
    # We'll add it right before the last line that's a method
    new_method = '''
    def update_live_trade_fill(self, paper_trade_id, action, sol_change=None, slippage_pct=None, live_fill_price_sol=None):
        """Update a live trade record with actual on-chain fill data (called after async verification)."""
        try:
            updates = []
            params = []
            if sol_change is not None and action == "buy":
                # For buys, sol_change is negative (SOL spent). Store absolute value as the actual amount.
                updates.append("amount_sol = ?")
                params.append(round(abs(sol_change), 8))
            if slippage_pct is not None:
                updates.append("slippage_pct = ?")
                params.append(round(slippage_pct, 4))
            if live_fill_price_sol is not None:
                updates.append("live_fill_price_sol = ?")
                params.append(live_fill_price_sol)
            if not updates:
                return
            params.extend([paper_trade_id, action.upper()])
            sql = f"UPDATE live_trades SET {', '.join(updates)} WHERE paper_trade_id = ? AND UPPER(action) = ?"
            self.conn.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update live trade fill: {e}")

    def update_live_trade_sell_pnl(self, paper_trade_id, amount_sol, pnl_sol, pnl_pct, slippage_pct=None):
        """Update a live sell record with actual on-chain PnL data."""
        try:
            updates = ["amount_sol = ?", "pnl_sol = ?", "pnl_pct = ?"]
            params = [round(amount_sol, 8), round(pnl_sol, 8), round(pnl_pct, 6)]
            if slippage_pct is not None:
                updates.append("slippage_pct = ?")
                params.append(round(slippage_pct, 4))
            params.append(paper_trade_id)
            sql = f"UPDATE live_trades SET {', '.join(updates)} WHERE paper_trade_id = ? AND UPPER(action) = 'SELL'"
            self.conn.execute(sql, params)
            self.conn.commit()
        except Exception as e:
            logger.error(f"Failed to update live sell PnL: {e}")
'''
    # Insert before the last occurrence of a class-level comment or at end of class
    # Find a good insertion point — after the last method definition
    # We'll append it before the very end of the file
    db_content = db_content.rstrip() + "\n" + new_method + "\n"
    with open(db_path, "w") as f:
        f.write(db_content)
    print("✅ database.py: Added update_live_trade_fill() and update_live_trade_sell_pnl()")
else:
    print("⏭️  database.py: update_live_trade_fill already exists")


# ═══════════════════════════════════════════════════════════════════════════════
# FIX 2: live_executor.py — Update DB after buy verification with sol_change
# ═══════════════════════════════════════════════════════════════════════════════

le_path = "/root/solana_trader/live_executor.py"
with open(le_path, "r") as f:
    le_content = f.read()

# The _bg_verify_buy function already has sol_change. We need to add a DB update call.
# Find the section where it logs "[LIVE BUY CONFIRMED]" and add DB update after it.

old_buy_confirm = '''                else:
                    logger.info(f"[LIVE BUY CONFIRMED] {token_name}: tx={signature} confirm={confirm_elapsed:.1f}s sol_change={sol_change}")'''

new_buy_confirm = '''                else:
                    logger.info(f"[LIVE BUY CONFIRMED] {token_name}: tx={signature} confirm={confirm_elapsed:.1f}s sol_change={sol_change}")
                    # Update DB with actual on-chain fill data
                    if paper_trade_id is not None and sol_change is not None:
                        try:
                            from database import Database
                            _db = Database()
                            actual_spent = abs(sol_change)
                            slippage = ((actual_spent - trade_amount) / trade_amount * 100) if trade_amount > 0 else 0
                            _db.update_live_trade_fill(
                                paper_trade_id=paper_trade_id,
                                action="buy",
                                sol_change=sol_change,
                                slippage_pct=slippage,
                            )
                            logger.info(f"[LIVE BUY FILL UPDATED] {token_name}: actual_spent={actual_spent:.6f} slippage={slippage:+.1f}%")
                        except Exception as e:
                            logger.warning(f"[LIVE BUY FILL UPDATE FAILED] {token_name}: {e}")'''

if "LIVE BUY FILL UPDATED" not in le_content:
    le_content = le_content.replace(old_buy_confirm, new_buy_confirm)
    with open(le_path, "w") as f:
        f.write(le_content)
    print("✅ live_executor.py: Added DB update after buy verification")
else:
    print("⏭️  live_executor.py: Buy fill update already exists")


# ═══════════════════════════════════════════════════════════════════════════════
# FIX 3: paper_trader.py — Use actual sell proceeds instead of paper estimates
# ═══════════════════════════════════════════════════════════════════════════════

pt_path = "/root/solana_trader/paper_trader.py"
with open(pt_path, "r") as f:
    pt_content = f.read()

old_sell_section = '''            # Estimate returned SOL from the buy amount + paper PnL %
            buy_amount = live_buy.get("amount_sol", LIVE_TRADE_SIZE_SOL)
            returned_sol = buy_amount * (1 + pnl_pct) if pnl_pct else 0  # pnl_pct is a ratio (4.41 = 441%), not percentage
            live_pnl = returned_sol - buy_amount
            db.log_live_trade(
                paper_trade_id=trade_id,
                mint_address=trade_info["mint"],
                token_name=trade_info["name"],
                token_symbol=trade_info["symbol"],
                action="sell",
                amount_sol=round(returned_sol, 6),
                tx_signature=sell_result.get("tx_signature"),
                success=sell_result.get("success", False),
                error=sell_result.get("error"),
                paper_price_sol=current_price_sol,
                pnl_sol=round(live_pnl, 6),
                pnl_pct=pnl_pct,
                hold_time_sec=hold_time_sec,
            )'''

new_sell_section = '''            # Use actual on-chain sell proceeds if available, fall back to paper estimate
            buy_amount = live_buy.get("amount_sol", LIVE_TRADE_SIZE_SOL)
            sol_received = sell_result.get("sol_received")  # Actual SOL from on-chain verification
            
            if sol_received is not None and sol_received > 0:
                # REAL on-chain data available
                returned_sol = sol_received
                live_pnl = returned_sol - buy_amount
                live_pnl_pct = live_pnl / buy_amount if buy_amount > 0 else 0
                logger.info(f"[LIVE SELL PNL] {trade_info['name']}: REAL on-chain — received={returned_sol:.6f} buy={buy_amount:.4f} pnl={live_pnl:+.6f} SOL ({live_pnl_pct:+.1%})")
            else:
                # Fallback to paper estimate (sol_received unavailable)
                returned_sol = buy_amount * (1 + pnl_pct) if pnl_pct else 0
                live_pnl = returned_sol - buy_amount
                live_pnl_pct = pnl_pct
                logger.info(f"[LIVE SELL PNL] {trade_info['name']}: PAPER ESTIMATE — no on-chain data, using paper pnl={live_pnl:+.6f} SOL")
            
            db.log_live_trade(
                paper_trade_id=trade_id,
                mint_address=trade_info["mint"],
                token_name=trade_info["name"],
                token_symbol=trade_info["symbol"],
                action="sell",
                amount_sol=round(returned_sol, 6),
                tx_signature=sell_result.get("tx_signature"),
                success=sell_result.get("success", False),
                error=sell_result.get("error"),
                paper_price_sol=current_price_sol,
                pnl_sol=round(live_pnl, 6),
                pnl_pct=round(live_pnl_pct, 6) if live_pnl_pct else pnl_pct,
                hold_time_sec=hold_time_sec,
            )'''

if "REAL on-chain" not in pt_content:
    if old_sell_section in pt_content:
        pt_content = pt_content.replace(old_sell_section, new_sell_section)
        with open(pt_path, "w") as f:
            f.write(pt_content)
        print("✅ paper_trader.py: Updated sell PnL to use actual on-chain data when available")
    else:
        print("❌ paper_trader.py: Could not find the exact sell section to replace")
        # Print what we're looking for vs what exists
        print("Looking for:")
        print(repr(old_sell_section[:100]))
else:
    print("⏭️  paper_trader.py: On-chain sell PnL already implemented")

print("\n✅ All fixes applied. Restart solana-trader.service to activate.")
