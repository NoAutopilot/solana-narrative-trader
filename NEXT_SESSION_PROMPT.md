# Next Session Prompt

Copy-paste this into a new Manus session to restore full context:

---

Continue the solana narrative trader project. Here is the context:

**VPS Access:**
- IP: 142.93.24.227
- User: root
- Password: 1987Foxsex
- SSH: `sshpass -p "1987Foxsex" ssh -o StrictHostKeyChecking=no root@142.93.24.227`

**Repo:** github.com/NoAutopilot/solana-narrative-trader (branch: master)

**VPS Architecture:**
- Paper trader running as systemd service: `solana-trader.service`
- Auto-restart on crash, auto-start on reboot
- DB: `/root/solana_trader/data/solana_trader.db`
- Hourly cron backup pushes DB snapshot to GitHub
- 512MB swap configured

**Read these files from the repo FIRST (clone or read from VPS):**
1. `OPERATING_PRINCIPLES.md` — our trading rules and scientific method
2. `RESEARCH_TRACKER.md` — hypothesis status and what is proven/unproven
3. `SESSION_8_SUMMARY.md` — what was done last session
4. `RECOVERY.md` — full system architecture and restore instructions
5. `ADVERSARIAL_REVIEW_FINAL.md` — honest assessment of strategy

**Dashboard:** Manus webdev project "solana-trading-dashboard"

**Current Task:** Pull 24+ hours of VPS paper trade data and analyze:
1. Moonshot rate (>100% return on 0.04 SOL entry) — does 5-6% hold over a full day?
2. Max drought between moonshots (longest gap with no >100% winner)
3. Time-of-day patterns (US hours vs Asia hours vs Europe hours)
4. Bleed rate stability (is -1 SOL/hr consistent or does it spike?)
5. Decision gate: is it safe to do a 1 SOL live test at 0.02 SOL/trade?

**Key numbers from Session 8:**
- Win rate: 17.8% (stable across 2 independent samples)
- Moonshot rate: 5.6% (>100% return)
- Bleed rate: ~1 SOL/hr at 0.04 SOL/trade
- Net: +0.26 SOL/hr (thin, moonshot-dependent)
- Fee friction: 6.6% at 0.04 SOL, 8.4% at 0.02 SOL, 12.1% at 0.01 SOL
- pnl_pct column records PRICE CHANGE not return — must calculate real return as pnl_sol/entry_sol

**Live test plan (if data supports it):**
- Phase 1: 0.02 SOL/trade, 2 hours, alongside paper
- Kill switch: pause if wallet drops below 0.5 SOL
- Success criteria: on-chain fill within 2x of paper fill
