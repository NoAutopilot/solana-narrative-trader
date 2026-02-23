#!/usr/bin/env python3
"""Reclaim SOL rent from zero-balance token accounts."""
import os, sys, time, json, requests, base58
sys.path.insert(0, '/root/solana_trader')
os.chdir('/root/solana_trader')
from dotenv import load_dotenv
load_dotenv('trader_env.conf')

from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from solders.message import MessageV0
from solders.hash import Hash

RPC = os.getenv('HELIUS_RPC_URL')
WALLET = os.getenv('WALLET_ADDRESS')
PRIV = os.getenv('SOLANA_PRIVATE_KEY')

print(f'Wallet: {WALLET}')

# Get all token accounts
resp = requests.post(RPC, json={
    'jsonrpc': '2.0', 'id': 1,
    'method': 'getTokenAccountsByOwner',
    'params': [WALLET, {'programId': 'TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'}, {'encoding': 'jsonParsed'}]
}, timeout=15)
accounts = resp.json().get('result', {}).get('value', [])
print(f'Token accounts found: {len(accounts)}')

# Find closeable accounts (zero balance)
closeable = []
for acct in accounts:
    info = acct['account']['data']['parsed']['info']
    amount = int(info['tokenAmount']['amount'])
    if amount == 0:
        closeable.append(acct['pubkey'])

print(f'Zero-balance accounts to close: {len(closeable)}')
potential_sol = len(closeable) * 0.00203928
print(f'Potential SOL to reclaim: ~{potential_sol:.4f} SOL')

# Get pre-balance
bal_resp = requests.post(RPC, json={'jsonrpc':'2.0','id':1,'method':'getBalance','params':[WALLET]}, timeout=10)
pre_bal = bal_resp.json().get('result',{}).get('value',0) / 1e9
print(f'Pre-balance: {pre_bal:.6f} SOL')

if not closeable:
    print('No accounts to close.')
    sys.exit(0)

kp = Keypair.from_base58_string(PRIV)
token_program = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
owner = kp.pubkey()

closed = 0
failed = 0

for pubkey in closeable:
    try:
        account_to_close = Pubkey.from_string(pubkey)
        
        # CloseAccount instruction (index 9 in token program)
        ix = Instruction(
            token_program,
            bytes([9]),
            [
                AccountMeta(account_to_close, False, True),
                AccountMeta(owner, False, True),   # destination for rent
                AccountMeta(owner, True, False),    # authority
            ]
        )
        
        bh_resp = requests.post(RPC, json={
            'jsonrpc':'2.0','id':1,'method':'getLatestBlockhash',
            'params':[{'commitment':'finalized'}]
        }, timeout=10)
        blockhash = Hash.from_string(bh_resp.json()['result']['value']['blockhash'])
        
        msg = MessageV0.try_compile(owner, [ix], [], blockhash)
        tx = VersionedTransaction(msg, [kp])
        tx_bytes = bytes(tx)
        
        send_resp = requests.post(RPC, json={
            'jsonrpc':'2.0','id':1,'method':'sendTransaction',
            'params': [base58.b58encode(tx_bytes).decode(), {'skipPreflight': True}]
        }, timeout=10)
        
        sig = send_resp.json().get('result')
        if sig:
            closed += 1
            if closed % 10 == 0:
                print(f'  Closed {closed}/{len(closeable)}...')
        else:
            err = send_resp.json().get('error', {})
            failed += 1
            if failed <= 3:
                print(f'  Failed: {err}')
    except Exception as e:
        failed += 1
        if failed <= 3:
            print(f'  Error: {e}')

print(f'\nClosed: {closed} | Failed: {failed}')

time.sleep(5)
bal_resp = requests.post(RPC, json={'jsonrpc':'2.0','id':1,'method':'getBalance','params':[WALLET]}, timeout=10)
post_bal = bal_resp.json().get('result',{}).get('value',0) / 1e9
reclaimed = post_bal - pre_bal
print(f'Post-balance: {post_bal:.6f} SOL')
print(f'SOL reclaimed: {reclaimed:+.6f} SOL')
