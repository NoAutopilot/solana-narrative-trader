# Claims Extracted from Reasoning Chain (Sessions 5-8)

## INFRASTRUCTURE CLAIMS
1. TP at 30% doesn't cap moonshots — they blow past between 10-sec checks
2. Moonshots exited at +1,915% and +1,788%, not at 30%
3. Wait — contradicts itself: "moonshots hit 30% TP and closed" vs "they exited at 1,900%"
4. live_executor.py has no own exit logic, just executes paper_trader signals
5. System throttles at 80+ concurrent positions (entry gap 15s → 398s)

## TIMEOUT CLAIMS
6. All 4 moonshots closed within 4.72 minutes
7. 99% of paper profit comes from trades closing within 5 min
8. Trades between 5-15 min total +0.0006 SOL (negligible)
9. 1,391 trades sitting 15+ min contribute +0.04 SOL total (dead weight)
10. 5-min timeout reduces capital from ~2 SOL to ~0.92 SOL (P95)
11. 5-min timeout eliminates throttling → ~45% more trades (~1,077 additional)
12. Force-closing at 5 min costs essentially nothing

## PROFITABILITY CLAIMS
13. At 0.10 SOL/trade with 1 SOL capital, paper model projects +7.8 SOL over 17.7h
14. Realistic projection is 40-60% of +7.8 SOL (slippage nonlinear)
15. Break-even is at 3.24x (224% gain) — 4.0% of trades exceed this
16. Base trades (bonding-curve-only) are -1.54 SOL net
17. Capturing 1% of post-migration gains → net positive (+1.90 SOL)
18. Capturing 10% of post-migration gains → +32.22 SOL
19. System's edge is in taking every trade, not picking winners
20. Average loss per losing trade: ~0.004 SOL

## SIGNAL/SELECTION CLAIMS
21. No strong differentiating signal exists for moonshot prediction
22. Moonshots look like every other trade at entry
23. 4.7% moonshot rate is uniform across modes, categories, signal types
24. Conviction filter misses 60% of moonshots and 71% of moonshot PnL
25. Conviction filter is "actively counterproductive"
26. Narrative matching: p=0.09, NOT significant
27. Control group produces 40% of moonshots (37 of 92)
28. Win rate is 15% regardless of filter

## EXECUTION CLAIMS
29. Live PnL% matches paper PnL% — 131/131 trades match
30. Post-migration sells work on-chain — 5/5 successful
31. Sell execution speed: median 2 seconds
32. System runs 114 trades/hour
33. On-chain sell recovery: 96.8% of buy cost (187 sells)
34. TX fees: 0.13% of avg buy — negligible

## UNPROVEN CLAIMS (acknowledged)
35. Can hold through migration and sell at peak — UNPROVEN
36. 4.6% moonshot rate persists across days — UNPROVEN (17h data)
37. Market regime independence — UNPROVEN
38. Slippage at larger trade sizes — UNPROVEN
