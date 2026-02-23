#!/usr/bin/env python3
"""
reclaim_all.py — Burn dead tokens and close ALL token accounts to reclaim rent.
Handles both empty accounts and accounts with worthless tokens.
"""

import os
import sys
import json
import time
import requests
import base64
import struct
from dotenv import load_dotenv

load_dotenv()

HELIUS_RPC_URL = os.getenv("HELIUS_RPC_URL")
WALLET_ADDRESS = os.getenv("WALLET_ADDRESS")
PRIVATE_KEY = os.getenv("SOLANA_PRIVATE_KEY")

TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
SPL_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

def get_all_token_accounts():
    """Get all token accounts for the wallet."""
    all_accounts = []
    for program_id, program_name in [
        (TOKEN_2022_PROGRAM, "Token-2022"),
        (SPL_TOKEN_PROGRAM, "SPL"),
    ]:
        resp = requests.post(HELIUS_RPC_URL, json={
            "jsonrpc": "2.0", "id": 1,
            "method": "getTokenAccountsByOwner",
            "params": [
                WALLET_ADDRESS,
                {"programId": program_id},
                {"encoding": "jsonParsed"}
            ]
        }, timeout=15)
        accounts = resp.json().get("result", {}).get("value", [])
        for acc in accounts:
            info = acc["account"]["data"]["parsed"]["info"]
            all_accounts.append({
                "pubkey": acc["pubkey"],
                "mint": info["mint"],
                "amount": int(info["tokenAmount"]["amount"]),
                "decimals": info["tokenAmount"]["decimals"],
                "lamports": acc["account"]["lamports"],
                "program_id": program_id,
                "program_name": program_name,
            })
    return all_accounts


def burn_and_close_account(account):
    """Burn tokens (if any) and close the account using PumpPortal or direct RPC."""
    pubkey = account["pubkey"]
    mint = account["mint"]
    amount = account["amount"]
    program_id = account["program_id"]
    
    print(f"  Processing: {pubkey[:20]}... (mint: {mint[:20]}...)")
    
    # Try using rent_reclaim's close function
    try:
        from rent_reclaim import close_account_via_rpc
        
        if amount > 0:
            print(f"    Has {amount} tokens — attempting burn+close...")
            # For accounts with tokens, we need to burn first then close
            # close_account_via_rpc handles this if the account is empty
            # For non-empty accounts, try selling via PumpPortal first (will burn effectively)
            from live_executor import _submit_trade
            try:
                result = _submit_trade(
                    action="sell",
                    mint_address=mint,
                    pool="auto",
                    amount="100%",
                    slippage=50,
                    priorityFee=0.0001,
                )
                print(f"    Sell attempt: {result}")
                time.sleep(3)
            except Exception as e:
                print(f"    Sell failed (expected for dead tokens): {e}")
            
            # Check if tokens are gone now
            resp = requests.post(HELIUS_RPC_URL, json={
                "jsonrpc": "2.0", "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [WALLET_ADDRESS, {"mint": mint}, {"encoding": "jsonParsed"}]
            }, timeout=10)
            accs = resp.json().get("result", {}).get("value", [])
            if accs:
                remaining = int(accs[0]["account"]["data"]["parsed"]["info"]["tokenAmount"]["amount"])
                if remaining > 0:
                    print(f"    Still has {remaining} tokens — trying direct close anyway...")
        
        # Now close the account
        tx_sig, error = close_account_via_rpc(pubkey, program_id)
        if tx_sig:
            print(f"    CLOSED! TX: {tx_sig}")
            return True
        else:
            print(f"    Close failed: {error}")
            return False
            
    except Exception as e:
        print(f"    Error: {e}")
        return False


def main():
    print("=== Reclaiming ALL SOL from token accounts ===")
    print()
    
    # Get starting balance
    r = requests.post(HELIUS_RPC_URL, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "getBalance",
        "params": [WALLET_ADDRESS]
    })
    start_sol = r.json()["result"]["value"] / 1e9
    print(f"Starting SOL balance: {start_sol:.6f} SOL")
    print()
    
    # Get all accounts
    accounts = get_all_token_accounts()
    print(f"Found {len(accounts)} token accounts:")
    
    empty = [a for a in accounts if a["amount"] == 0]
    with_tokens = [a for a in accounts if a["amount"] > 0]
    
    total_rent = sum(a["lamports"] for a in accounts) / 1e9
    print(f"  Empty: {len(empty)} (easy close)")
    print(f"  With tokens: {len(with_tokens)} (burn + close)")
    print(f"  Total reclaimable rent: {total_rent:.6f} SOL")
    print()
    
    # Close empty accounts first (easy)
    print("--- Closing empty accounts ---")
    for acc in empty:
        burn_and_close_account(acc)
        time.sleep(2)
    
    print()
    
    # Then handle accounts with dead tokens
    print("--- Closing accounts with dead tokens ---")
    for acc in with_tokens:
        burn_and_close_account(acc)
        time.sleep(3)
    
    print()
    
    # Check final balance
    time.sleep(5)
    r = requests.post(HELIUS_RPC_URL, json={
        "jsonrpc": "2.0", "id": 1,
        "method": "getBalance",
        "params": [WALLET_ADDRESS]
    })
    end_sol = r.json()["result"]["value"] / 1e9
    
    # Check remaining accounts
    remaining = get_all_token_accounts()
    
    print(f"=== RESULTS ===")
    print(f"Starting balance: {start_sol:.6f} SOL")
    print(f"Ending balance:   {end_sol:.6f} SOL")
    print(f"SOL reclaimed:    {end_sol - start_sol:.6f} SOL")
    print(f"Remaining token accounts: {len(remaining)}")
    if remaining:
        for r in remaining:
            print(f"  STUCK: {r['pubkey'][:20]}... | tokens={r['amount']} | rent={r['lamports']/1e9:.6f} SOL")


if __name__ == "__main__":
    main()
