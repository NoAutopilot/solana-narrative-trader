#!/usr/bin/env python3
"""
Tiny HTTP API for force-closing token accounts (burn tokens + reclaim rent).
Runs on port 9877. Called by the dashboard's tRPC backend.
"""
import json
import logging
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

from rent_reclaim import find_token_account_for_mint, close_account_via_rpc

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
logger = logging.getLogger(__name__)

SPL_TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"


class ForceCloseHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/force-close':
            content_length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(content_length)) if content_length else {}
            mint_address = body.get('mint_address', '')
            
            if not mint_address:
                self._respond(400, {'error': 'mint_address required'})
                return
            
            logger.info(f"Force-close request for mint: {mint_address}")
            
            # Find the token account
            account_info = find_token_account_for_mint(mint_address)
            if not account_info:
                self._respond(404, {'error': 'No token account found for this mint'})
                return
            
            amount = account_info['amount']
            pubkey = account_info['pubkey']
            program_id = account_info['program_id']
            rent_lamports = account_info['lamports']
            
            logger.info(f"Found account {pubkey}, amount={amount}, rent={rent_lamports/1e9:.6f} SOL")
            
            # If tokens still present, we need to burn them first
            if amount > 0:
                burn_result = self._burn_tokens(pubkey, mint_address, amount, program_id)
                if not burn_result['success']:
                    self._respond(500, {'error': f"Burn failed: {burn_result['error']}"})
                    return
                logger.info(f"Burned {amount} tokens, tx={burn_result['tx']}")
                import time
                time.sleep(2)  # Wait for confirmation
            
            # Now close the account to reclaim rent
            tx_sig, error = close_account_via_rpc(pubkey, program_id)
            if tx_sig:
                rent_sol = rent_lamports / 1e9
                logger.info(f"Account closed! Reclaimed {rent_sol:.6f} SOL, tx={tx_sig}")
                self._respond(200, {
                    'success': True,
                    'burned_tokens': amount,
                    'reclaimed_rent_sol': rent_sol,
                    'close_tx': tx_sig,
                })
            else:
                self._respond(500, {'error': f"Close failed: {error}"})
        else:
            self._respond(404, {'error': 'Not found'})
    
    def _burn_tokens(self, token_account_pubkey, mint_address, amount, program_id):
        """Burn all tokens in the account before closing."""
        try:
            from solders.keypair import Keypair
            from solders.pubkey import Pubkey
            from solders.instruction import Instruction, AccountMeta
            from solders.transaction import Transaction
            from solders.message import Message
            from solders.hash import Hash
            import base58
            import base64
            import struct
            import requests
            
            WALLET_PRIVATE_KEY = os.environ.get('SOLANA_PRIVATE_KEY', '')
            HELIUS_RPC_URL = os.environ.get('HELIUS_RPC_URL', '')
            
            private_key_bytes = base58.b58decode(WALLET_PRIVATE_KEY)
            keypair = Keypair.from_bytes(private_key_bytes)
            owner_pubkey = keypair.pubkey()
            
            account_pubkey = Pubkey.from_string(token_account_pubkey)
            mint_pubkey = Pubkey.from_string(mint_address)
            program_pubkey = Pubkey.from_string(program_id)
            
            # Burn instruction (index 8 in SPL Token program)
            # Accounts: [account, mint, owner]
            # Data: [8] + u64 amount (little-endian)
            burn_data = bytes([8]) + struct.pack('<Q', amount)
            
            burn_ix = Instruction(
                program_id=program_pubkey,
                accounts=[
                    AccountMeta(pubkey=account_pubkey, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=mint_pubkey, is_signer=False, is_writable=True),
                    AccountMeta(pubkey=owner_pubkey, is_signer=True, is_writable=False),
                ],
                data=burn_data,
            )
            
            # Get recent blockhash
            resp = requests.post(HELIUS_RPC_URL, json={
                "jsonrpc": "2.0", "id": 1,
                "method": "getLatestBlockhash",
                "params": [{"commitment": "finalized"}]
            }, timeout=10)
            blockhash_str = resp.json()["result"]["value"]["blockhash"]
            recent_blockhash = Hash.from_string(blockhash_str)
            
            # Build and sign transaction
            msg = Message.new_with_blockhash([burn_ix], owner_pubkey, recent_blockhash)
            tx = Transaction.new_unsigned(msg)
            tx.sign([keypair], recent_blockhash)
            
            tx_bytes = bytes(tx)
            tx_b64 = base64.b64encode(tx_bytes).decode("utf-8")
            
            resp = requests.post(HELIUS_RPC_URL, json={
                "jsonrpc": "2.0", "id": 1,
                "method": "sendTransaction",
                "params": [tx_b64, {"encoding": "base64", "skipPreflight": False}]
            }, timeout=30)
            
            result = resp.json()
            if "error" in result:
                return {'success': False, 'error': str(result["error"])}
            
            return {'success': True, 'tx': result.get("result")}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _respond(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        logger.info(f"HTTP: {args[0]}")


if __name__ == '__main__':
    port = 9877
    server = HTTPServer(('127.0.0.1', port), ForceCloseHandler)
    logger.info(f"Force-close API running on http://127.0.0.1:{port}")
    server.serve_forever()
