#!/usr/bin/env python3
"""
wallet_reconcile.py — Wallet reconciliation tool for the Solana narrative trader.

Reports:
  A) Total tx fees paid (sum of meta.fee for recent txs submitted by this wallet)
  B) SOL locked in token accounts (rent deposits for SPL token accounts)
  C) Open token balances (non-zero tokens that should be sold or intentionally held)
  D) WSOL temp accounts (should be closed/unwrapped)
  E) Reclaimable SOL (lamports in empty token accounts that can be closed)

Generates: close_empty_accounts.py — auto-close script for reclaimable accounts.

Usage:
  python3 wallet_reconcile.py [--close]   # --close runs the auto-close immediately
"""
import sys
import json
import time
import argparse
import requests
from typing import Optional

sys.path.insert(0, '/root/solana_trader')
from config.config import RPC_URL, WALLET_PRIVATE_KEY

# SPL Token program IDs
TOKEN_PROGRAM_ID      = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
TOKEN_2022_PROGRAM_ID = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
WSOL_MINT             = "So11111111111111111111111111111111111111112"

# Rent-exempt minimum for a token account (165 bytes * 6960 lamports/byte ≈ 2039280 lamports)
TOKEN_ACCOUNT_RENT_LAMPORTS = 2_039_280

LAMPORTS_PER_SOL = 1_000_000_000


def rpc(method: str, params: list, rpc_url: str = RPC_URL) -> dict:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    r = requests.post(rpc_url, json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def get_wallet_pubkey() -> str:
    """Derive pubkey from private key using solders."""
    import base58
    from solders.keypair import Keypair
    raw = base58.b58decode(WALLET_PRIVATE_KEY)
    kp = Keypair.from_bytes(raw)
    return str(kp.pubkey())


def get_sol_balance(pubkey: str) -> float:
    result = rpc("getBalance", [pubkey, {"commitment": "confirmed"}])
    return result["result"]["value"] / LAMPORTS_PER_SOL


def get_token_accounts(pubkey: str) -> list:
    """Return all SPL token accounts owned by pubkey (both Token and Token-2022)."""
    accounts = []
    for program_id in [TOKEN_PROGRAM_ID, TOKEN_2022_PROGRAM_ID]:
        result = rpc("getTokenAccountsByOwner", [
            pubkey,
            {"programId": program_id},
            {"encoding": "jsonParsed", "commitment": "confirmed"}
        ])
        accounts.extend(result.get("result", {}).get("value", []))
    return accounts


def get_recent_tx_fees(pubkey: str, limit: int = 50) -> dict:
    """
    Fetch recent transaction signatures and sum fees for txs where this wallet
    was the fee payer (first account in accountKeys).
    Returns dict with total_fees_sol, tx_count, fee_details list.
    Uses singular getTransaction calls (Helius does not support batch getTransactions).
    """
    sig_result = rpc("getSignaturesForAddress", [
        pubkey,
        {"limit": limit, "commitment": "confirmed"}
    ])
    signatures = sig_result.get("result", [])
    if not signatures:
        return {"total_fees_sol": 0.0, "tx_count": 0, "fee_details": []}

    total_fees = 0
    fee_details = []

    for sig_info in signatures:
        sig = sig_info["signature"]
        try:
            tx_result = rpc("getTransaction", [
                sig,
                {"encoding": "jsonParsed", "commitment": "confirmed", "maxSupportedTransactionVersion": 0}
            ])
            tx = tx_result.get("result")
            if tx is None:
                continue
            meta = tx.get("meta", {})
            if meta is None:
                continue
            fee = meta.get("fee", 0)
            # Only count if our wallet was fee payer (first account)
            msg = tx["transaction"]["message"]
            account_keys = msg.get("accountKeys", [])
            if account_keys:
                first_key = account_keys[0]
                if isinstance(first_key, dict):
                    first_key = first_key.get("pubkey", "")
                if first_key == pubkey:
                    total_fees += fee
                    fee_details.append({
                        "sig": sig[:20] + "...",
                        "fee_lamports": fee,
                        "fee_sol": fee / LAMPORTS_PER_SOL,
                        "slot": tx.get("slot", 0)
                    })
        except Exception:
            pass
        time.sleep(0.05)  # Rate limit

    return {
        "total_fees_sol": total_fees / LAMPORTS_PER_SOL,
        "tx_count": len(fee_details),
        "fee_details": fee_details
    }


def analyze_token_accounts(accounts: list, wallet_pubkey: str) -> dict:
    """
    Categorize token accounts into:
    - empty: zero balance, reclaimable rent
    - wsol: Wrapped SOL accounts (should be closed/unwrapped)
    - open: non-zero balance tokens
    """
    empty = []
    wsol = []
    open_balances = []

    for acct in accounts:
        pubkey = acct["pubkey"]
        info = acct["account"]["data"]["parsed"]["info"]
        mint = info["mint"]
        lamports = acct["account"].get("lamports", TOKEN_ACCOUNT_RENT_LAMPORTS)
        token_amount = info["tokenAmount"]
        ui_amount = token_amount.get("uiAmount") or 0
        raw_amount = int(token_amount.get("amount", 0))
        decimals = token_amount.get("decimals", 0)

        entry = {
            "account": pubkey,
            "mint": mint,
            "lamports": lamports,
            "sol": lamports / LAMPORTS_PER_SOL,
            "ui_amount": ui_amount,
            "raw_amount": raw_amount,
            "decimals": decimals
        }

        if mint == WSOL_MINT:
            wsol.append(entry)
        elif raw_amount == 0:
            empty.append(entry)
        else:
            open_balances.append(entry)

    return {
        "empty": empty,
        "wsol": wsol,
        "open": open_balances
    }


def generate_close_script(empty_accounts: list, wsol_accounts: list, wallet_pubkey: str) -> str:
    """Generate a Python script to close empty token accounts and unwrap WSOL."""
    accounts_to_close = empty_accounts + wsol_accounts
    if not accounts_to_close:
        return ""

    script = '''#!/usr/bin/env python3
"""
close_empty_accounts.py — Auto-generated by wallet_reconcile.py
Closes empty SPL token accounts to recover rent-exempt SOL.
Run: python3 close_empty_accounts.py
"""
import sys, base58, requests, time
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction
from solders.message import MessageV0

sys.path.insert(0, '/root/solana_trader')
from config.config import RPC_URL, WALLET_PRIVATE_KEY

LAMPORTS_PER_SOL = 1_000_000_000
TOKEN_PROGRAM_ID = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

def rpc(method, params):
    r = requests.post(RPC_URL, json={"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout=30)
    r.raise_for_status()
    return r.json()

def close_token_account_via_jupiter(account_pubkey: str, keypair: Keypair) -> bool:
    """
    Close a token account by sending a closeAccount instruction.
    Uses the Solana JSON-RPC directly to build and send the transaction.
    """
    import struct
    from solders.instruction import Instruction, AccountMeta
    from solders.pubkey import Pubkey
    from solders.hash import Hash

    wallet_pk = keypair.pubkey()
    account_pk = Pubkey.from_string(account_pubkey)
    token_program_pk = Pubkey.from_string(TOKEN_PROGRAM_ID)

    # closeAccount instruction = instruction index 9
    # Accounts: [token_account (writable), destination (writable), owner (signer)]
    close_ix = Instruction(
        program_id=token_program_pk,
        accounts=[
            AccountMeta(pubkey=account_pk, is_signer=False, is_writable=True),
            AccountMeta(pubkey=wallet_pk, is_signer=False, is_writable=True),
            AccountMeta(pubkey=wallet_pk, is_signer=True, is_writable=False),
        ],
        data=bytes([9])  # closeAccount = 9
    )

    # Get recent blockhash
    bh_result = rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
    blockhash_str = bh_result["result"]["value"]["blockhash"]
    blockhash = Hash.from_string(blockhash_str)

    msg = MessageV0.try_compile(
        payer=wallet_pk,
        instructions=[close_ix],
        address_lookup_table_accounts=[],
        recent_blockhash=blockhash
    )
    tx = VersionedTransaction(msg, [keypair])
    tx_bytes = bytes(tx)

    import base64
    encoded = base64.b64encode(tx_bytes).decode()
    result = rpc("sendTransaction", [encoded, {"encoding": "base64", "skipPreflight": False}])
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return False
    sig = result["result"]
    print(f"  TX: {sig}")
    return True

def main():
    raw = base58.b58decode(WALLET_PRIVATE_KEY)
    keypair = Keypair.from_bytes(raw)
    wallet = str(keypair.pubkey())
    print(f"Wallet: {wallet}")

    bal_before = rpc("getBalance", [wallet, {"commitment": "confirmed"}])["result"]["value"]
    print(f"SOL before: {bal_before / LAMPORTS_PER_SOL:.6f}")

    accounts_to_close = ''' + json.dumps([a["account"] for a in accounts_to_close], indent=4) + '''

    closed = 0
    for acct in accounts_to_close:
        print(f"Closing {acct[:20]}...")
        ok = close_token_account_via_jupiter(acct, keypair)
        if ok:
            closed += 1
        time.sleep(0.5)

    print(f"\\nClosed {closed}/{len(accounts_to_close)} accounts")
    time.sleep(2)
    bal_after = rpc("getBalance", [wallet, {"commitment": "confirmed"}])["result"]["value"]
    recovered = (bal_after - bal_before) / LAMPORTS_PER_SOL
    print(f"SOL after:  {bal_after / LAMPORTS_PER_SOL:.6f}")
    print(f"Recovered:  {recovered:+.6f} SOL")

if __name__ == "__main__":
    main()
'''
    return script


def main():
    parser = argparse.ArgumentParser(description="Wallet reconciliation tool")
    parser.add_argument("--close", action="store_true", help="Auto-close empty token accounts after reporting")
    parser.add_argument("--tx-limit", type=int, default=50, help="Number of recent txs to scan for fees (default: 50)")
    args = parser.parse_args()

    print("=" * 70)
    print("WALLET RECONCILIATION REPORT")
    print("=" * 70)

    wallet_pubkey = get_wallet_pubkey()
    print(f"Wallet: {wallet_pubkey}")

    sol_balance = get_sol_balance(wallet_pubkey)
    print(f"Current SOL balance: {sol_balance:.6f} SOL")
    print()

    # ── A) TX FEES ─────────────────────────────────────────────────────────────
    print("A) TRANSACTION FEES (last {} txs)".format(args.tx_limit))
    print("-" * 50)
    try:
        fee_data = get_recent_tx_fees(wallet_pubkey, limit=args.tx_limit)
        print(f"  Txs scanned (fee payer):  {fee_data['tx_count']}")
        print(f"  Total fees paid:          {fee_data['total_fees_sol']:.6f} SOL  ({fee_data['total_fees_sol'] * LAMPORTS_PER_SOL:.0f} lamports)")
        if fee_data["fee_details"]:
            avg_fee = fee_data["total_fees_sol"] / fee_data["tx_count"]
            print(f"  Avg fee per tx:           {avg_fee:.6f} SOL  ({avg_fee * LAMPORTS_PER_SOL:.0f} lamports)")
            print(f"  Min fee:                  {min(d['fee_sol'] for d in fee_data['fee_details']):.6f} SOL")
            print(f"  Max fee:                  {max(d['fee_sol'] for d in fee_data['fee_details']):.6f} SOL")
    except Exception as e:
        print(f"  Fee scan error: {e}")
        fee_data = {"total_fees_sol": 0.0, "tx_count": 0, "fee_details": []}

    # ── B/C/D) TOKEN ACCOUNTS ──────────────────────────────────────────────────
    print()
    print("B/C/D) SPL TOKEN ACCOUNTS")
    print("-" * 50)
    try:
        accounts = get_token_accounts(wallet_pubkey)
        categorized = analyze_token_accounts(accounts, wallet_pubkey)

        empty   = categorized["empty"]
        wsol    = categorized["wsol"]
        open_b  = categorized["open"]

        # lamports are in the categorized dicts (from analyze_token_accounts)
        # accounts list has nested account.lamports; use categorized dicts which have 'lamports' flat
        total_rent_locked = (sum(a["lamports"] for a in empty) +
                             sum(a["lamports"] for a in wsol) +
                             sum(a["lamports"] for a in open_b)) / LAMPORTS_PER_SOL
        reclaimable_sol   = sum(a["lamports"] for a in empty) / LAMPORTS_PER_SOL
        wsol_locked       = sum(a["lamports"] for a in wsol) / LAMPORTS_PER_SOL

        print(f"  Total token accounts:     {len(accounts)}")
        print(f"  Total SOL locked (rent):  {total_rent_locked:.6f} SOL")
        print()

        print(f"B) Rent-locked SOL breakdown:")
        print(f"   Empty accounts (zero balance):  {len(empty):3d}  \u2192  {sum(a['lamports'] for a in empty)/LAMPORTS_PER_SOL:.6f} SOL")
        print(f"   WSOL accounts:                  {len(wsol):3d}  \u2192  {wsol_locked:.6f} SOL")
        print(f"   Open balance accounts:          {len(open_b):3d}  \u2192  {sum(a['lamports'] for a in open_b)/LAMPORTS_PER_SOL:.6f} SOL")

        if open_b:
            print()
            print("C) Open token balances (non-zero \u2014 review before closing):")
            for a in open_b:
                symbol = "WSOL" if a["mint"] == WSOL_MINT else a["mint"][:8] + "..."
                print(f"   {a['account'][:20]}...  mint={symbol}  amount={a['ui_amount']:.4f}  rent={a['sol']:.6f} SOL")

        if wsol:
            print()
            print("D) WSOL accounts (should be closed/unwrapped):")
            for a in wsol:
                print(f"   {a['account'][:20]}...  lamports={a['lamports']}  ({a['sol']:.6f} SOL)")

        print()
        print("E) RECLAIMABLE SOL")
        print("-" * 50)
        reclaimable_total = reclaimable_sol + wsol_locked
        print(f"   Empty token accounts:    {reclaimable_sol:.6f} SOL  ({len(empty)} accounts)")
        print(f"   WSOL accounts:           {wsol_locked:.6f} SOL  ({len(wsol)} accounts)")
        print(f"   TOTAL RECLAIMABLE:       {reclaimable_total:.6f} SOL")

        if reclaimable_total > 0.0005:
            print(f"   >>> Reclaimable amount is material. Run with --close to recover.")
        else:
            print(f"   >>> Reclaimable amount is negligible (<0.0005 SOL). No action needed.")

    except Exception as e:
        print(f"  Token account scan error: {e}")
        import traceback; traceback.print_exc()
        empty, wsol, open_b = [], [], []
        reclaimable_total = 0.0

    # ── BALANCE RECONCILIATION ─────────────────────────────────────────────────
    print()
    print("BALANCE RECONCILIATION")
    print("-" * 50)
    STARTING_BALANCE = 0.145242  # Known starting balance before this session
    delta = sol_balance - STARTING_BALANCE
    print(f"  Starting balance (known):  {STARTING_BALANCE:.6f} SOL")
    print(f"  Current liquid balance:    {sol_balance:.6f} SOL")
    print(f"  Delta:                     {delta:+.6f} SOL")
    print()
    print(f"  Accounted for:")
    print(f"    Tx fees paid:            -{fee_data['total_fees_sol']:.6f} SOL")
    print(f"    Rent locked in accounts: -{total_rent_locked if 'total_rent_locked' in dir() else 0:.6f} SOL")
    accounted = fee_data["total_fees_sol"] + (total_rent_locked if 'total_rent_locked' in dir() else 0)
    unaccounted = abs(delta) - accounted
    print(f"  Unaccounted delta:         {unaccounted:+.6f} SOL")
    if abs(unaccounted) < 0.001:
        print(f"  RECONCILIATION: OK (unaccounted < 0.001 SOL)")
    else:
        print(f"  RECONCILIATION: REVIEW — {unaccounted:.6f} SOL unaccounted")
        print(f"    Possible causes: failed tx refunds, swap losses, priority fees not captured")

    # ── GENERATE CLOSE SCRIPT ──────────────────────────────────────────────────
    if empty or wsol:
        script = generate_close_script(empty, wsol, wallet_pubkey)
        script_path = "/root/solana_trader/close_empty_accounts.py"
        with open(script_path, "w") as f:
            f.write(script)
        print()
        print(f"Auto-close script written: {script_path}")
        print(f"Run: python3 {script_path}")

    print("=" * 70)

    # ── AUTO-CLOSE IF REQUESTED ────────────────────────────────────────────────
    if args.close and (empty or wsol):
        print()
        print("AUTO-CLOSE: Running close_empty_accounts.py...")
        import subprocess
        result = subprocess.run(
            ["python3", "/root/solana_trader/close_empty_accounts.py"],
            capture_output=True, text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print("STDERR:", result.stderr)


if __name__ == "__main__":
    main()
