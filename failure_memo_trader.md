# FAILURE MEMO: TRADER

**Date:** 2026-03-15T02:30:01.367493+00:00

**Reason:** Trader canary exception: no such table: selection_tick_log

**Command that failed:**
```
python3 /root/solana_trader/canary_unified.py trader
```

**Why it failed:** Trader canary exception: no such table: selection_tick_log

**File to edit / verify:**
- Check logs: `journalctl -u solana-trader.service -n 50`
- Check DB: `sqlite3 /root/solana_trader/data/solana_trader.db '.tables'`

**How to verify fix in <5 minutes:**
```bash
python3 /root/solana_trader/canary_unified.py trader
```

