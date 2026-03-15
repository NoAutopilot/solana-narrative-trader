# Who Family Pilot v1 — Data Document

**Program:** who_family_pilot_v1
**Date:** 2026-03-15

---

## 1. Data Sources

| Source | Purpose | Access Method |
|--------|---------|--------------|
| Frozen 96-fire DB | Token universe, performance labels | Local SQLite on VPS |
| Solana RPC (Helius) | Mint account info (deployer proxy) | `getAccountInfo` jsonParsed |
| Solana RPC (Helius) | Early transaction signatures | `getSignaturesForAddress` |
| Helius Enhanced API | Parsed transaction details | REST POST `/v0/transactions` |

## 2. Sample Achieved

Twenty tokens were sampled: 10 stronger (top performers by avg +1h return) and 10 weaker (bottom performers). All are pumpfun-origin Solana tokens observed in the feature_tape_v2 collection window.

| Group | Tokens Sampled | With Mint Authority | With Early Buyers | Avg Buyers Found |
|-------|---------------|--------------------|--------------------|-----------------|
| Stronger | 10 | 0 | 4 | 4.9 |
| Weaker | 10 | 0 | 7 | 7.8 |
| **Total** | **20** | **0** | **11** | **6.5** |

## 3. Critical Data Gaps

### 3.1 Deployer Identification — BLOCKED

All 20 sampled tokens returned `mint_authority = None` from `getAccountInfo`. This is expected behavior for pumpfun tokens: the pumpfun protocol revokes mint authority upon token graduation. The mint authority field therefore cannot serve as a deployer proxy for this token class.

To identify the actual deployer, one would need to trace the original token creation transaction (the first signature for the mint address) and extract the fee payer or the wallet that invoked the pumpfun `create` instruction. This requires parsing the raw transaction data at a deeper level than the Helius Enhanced API provides in its current output format, or using a dedicated indexer (e.g., Helius DAS API with creation event tracking).

**Impact:** Deployer recidivism analysis (Question A) is entirely blocked. Zero deployer wallets were identified.

### 3.2 Early Buyer Extraction — Partial

Only 11 of 20 tokens yielded any early buyer wallets from the parsed transaction data. The extraction relies on Helius Enhanced Transactions API identifying `tokenTransfers` with the correct mint address. Several tokens returned 50 parsed transactions but zero token transfers matching the mint — likely because the earliest transactions were liquidity additions, pumpfun bonding curve interactions, or other non-standard transfer types that the parser does not classify as `tokenTransfers`.

| Token | Group | Buyers Found | Notes |
|-------|-------|-------------|-------|
| MEMECARD | stronger | 0 | No matching token transfers |
| NEO | stronger | 0 | No matching token transfers |
| SMITH | stronger | 0 | No matching token transfers |
| HAMSTER | stronger | 0 | No matching token transfers |
| EXPRESSION | stronger | 7 | Partial |
| LUFFY | stronger | 0 | No matching token transfers |
| SHEEPAGENT | stronger | 1 | Minimal |
| MACROHARD | stronger | 0 | No matching token transfers |
| Snorp | stronger | 18 | Good |
| SOS | stronger | 23 | Good |
| NORWOOD | weaker | 19 | Good |
| Out | weaker | 0 | No matching token transfers |
| SMORT | weaker | 16 | Good |
| WENDYS | weaker | 0 | No matching token transfers |
| $2 | weaker | 15 | Good |
| 01001000 | weaker | 21 | Good |
| NOTGAY | weaker | 3 | Minimal |
| Distorted | weaker | 3 | Minimal |
| butthole | weaker | 0 | No matching token transfers |
| Life | weaker | 1 | Minimal |

**Impact:** The stronger group has only 4 tokens with buyer data (and only 2 with >= 10 buyers), making within-group overlap analysis severely underpowered. The weaker group has 7 tokens with data (4 with >= 10 buyers), which is marginally better but still small.

### 3.3 What Could Not Be Obtained Cheaply

The following data would be needed for a full "who" program but was not obtainable in this pilot:

1. **Deployer wallets** — requires raw transaction parsing of pumpfun `create` instructions, not available via standard RPC or Helius Enhanced API without custom indexing
2. **Complete early buyer lists** — the Helius Enhanced API misses many early transactions (bonding curve buys, Raydium migration swaps) that do not appear as standard `tokenTransfers`
3. **Historical wallet profiles** — determining whether an early buyer is a "smart money" wallet requires historical trade data across many tokens, which is a large indexing task
4. **Deployer wallet clustering** — even if deployers were identified, linking related wallets (same entity, different addresses) requires on-chain graph analysis

## 4. Data Quality Assessment

The pilot data is **insufficient for reliable statistical inference**. The combination of zero deployer identification and partial early-buyer extraction (55% of tokens, with severe asymmetry between groups) means that any analysis results should be treated as directional at best and unreliable at worst.
