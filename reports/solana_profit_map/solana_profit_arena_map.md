# Solana Profit Arena Map

**Date:** 2026-03-14
**Author:** Manus AI
**Purpose:** Adversarial business-fit assessment of Solana-adjacent profit arenas
**Premise:** Direct Solana trading-signal research is closed (7 programs, 11 no-go rulings, ~15,000 events, 0 surviving edges). This document evaluates what remains.

---

## Preamble: What We Learned From Failure

Seven rigorous research programs produced a consistent set of binding constraints that any Solana profit path must confront. These are not opinions; they are empirical findings from 210+ feature-horizon combinations, 27 perps scenarios, 2,365 LP events, and 124 swing-trade signals.

**Constraint A — The Cost Floor.** Round-trip execution cost on Solana DEX swaps is approximately 0.50%, composed of AMM fees, slippage, and priority fees. Every directional signal must produce gross alpha exceeding this floor. None of the 210 features tested in Feature Acquisition v2 achieved this at any horizon from +5m to +4h. [1]

**Constraint B — Fat-Tailed, Outlier-Dominated Returns.** Solana memecoin returns are dominated by rare extreme events. Positive mean returns are almost always driven by 2–3 outlier tokens. Medians are consistently zero or negative. Any strategy relying on mean performance is a disguised lottery ticket. [2]

**Constraint C — Non-Stationarity.** Patterns that appear in one 24-hour window do not persist. The Meteora LP toxic-flow filter showed +1.033% mean in Stage A and reversed to -0.278% in Stage B when two short-lived anomalous pools expired. The market regime changes faster than any signal can be validated. [3]

**Constraint D — Public Data Has No Predictive Power.** Across 42 features derived from universe snapshots and microstructure logs — including order-flow ratios, trade acceleration, microstructure volatility, Jupiter vs CPAMM spread, round-trip cost, price impact, breadth, and cross-pool dispersion — zero combinations passed all promotion gates. Public on-chain data, at the granularity available to retail participants, does not predict short-to-medium-horizon returns after costs. [4]

These constraints define the landscape. Any arena that requires overcoming them without structural advantages is a repeat of the same failure.

---

## Arena 1: Searcher / Low-Latency / Bundle Business

### What the business actually is

MEV searchers monitor pending or recently landed transactions on Solana and extract profit by inserting their own transactions in advantageous positions. The primary strategies are sandwich attacks (frontrunning and backrunning a victim trade), arbitrage (exploiting price discrepancies across DEXs within the same block), and liquidation (triggering and capturing collateral from undercollateralized positions). On Solana, this requires Jito bundle submission, co-located infrastructure near validators, and sub-second execution pipelines.

### What kind of edge it relies on

Speed, infrastructure, and information asymmetry. The edge is not analytical — it is engineering and capital. Searchers compete on latency (who can detect and respond to opportunities fastest), compute efficiency (who can simulate and submit bundles most cheaply), and validator relationships (who gets preferential bundle inclusion).

### Why people make money there

MEV revenue on Solana reached $720.1 million in 2025, overtaking priority fees as the largest revenue component on the network. [5] The Jito Block Engine alone generated $4.7 million in fees in Q3 2025. [6] This is real, large-scale profit. The winners are teams like Temporal (which operates HumidiFi, Nozomi, and Harmonic), firms with Jump/Paradigm alumni, and established searcher shops that have been optimizing for years.

### Why I probably cannot win there

This arena has the highest barrier to entry of any Solana profit path. It requires co-located servers near major validators, deep Rust/Solana runtime expertise, Jito bundle integration, and continuous optimization against other searchers who are doing the same. The competition is professional HFT firms and crypto-native teams with years of accumulated infrastructure. There is no "research your way in" — the edge is purely operational. Starting from zero infrastructure today means competing against teams that have been compounding their speed advantage since 2023. The capital requirement for inventory and priority fee bidding is also non-trivial.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | HIGH | $720M/year market, clear extraction mechanism |
| Speed requirement | HIGH | Sub-second, co-located, Jito bundles |
| Capital requirement | MEDIUM | Inventory + priority fees, not massive but real |
| Private data requirement | HIGH | Validator relationships, private mempools |
| Engineering burden | HIGH | Rust, Solana runtime, continuous optimization |
| Time to first dollar | HIGH (long) | 6-12+ months to be competitive |
| Fit with my strengths | LOW | Research/analysis skills irrelevant here |
| Drift risk | LOW | Clear success/failure metrics |
| Defensibility | MEDIUM | Speed moats are real but can be disrupted |
| **Overall verdict** | **BAD FIT** | Wrong skill set, wrong starting position |

---

## Arena 2: LP / Liquidity Provision / Market-Making Style Business

### What the business actually is

Two distinct sub-arenas exist here. **Passive LP** means depositing tokens into AMM pools (Meteora DLMM, Raydium, Orca) and earning fees while bearing impermanent loss. **Active market-making** means running a prop AMM or quoting engine that dynamically manages inventory, hedges exposure, and adjusts quotes based on oracle prices — essentially operating as a professional market maker.

### What kind of edge it relies on

Passive LP relies on pool selection and timing — picking pools where fee income exceeds impermanent loss. Active market-making relies on speed (updating quotes before being picked off by informed flow), inventory management, and hedging infrastructure.

### Why people make money there

Prop AMMs now account for over 50% of all Solana spot DEX volume. HumidiFi leads with 65% market share among prop AMMs, followed by Tessera (18%) and GoonFi (7%). [7] These are profitable because they operate as professional market makers with oracle-updated quotes, multiple updates per second, and vertically integrated transaction landing infrastructure. Passive LPs on long-tail tokens can earn fees, but our own Meteora LP State research (NG-010, NG-011) showed that after accounting for impermanent loss, the median passive LP position is negative.

### Why I probably cannot win there

We tested passive LP directly. The Meteora LP toxic-flow filter was the only signal across 7 programs that initially passed Stage A — and it was falsified in Stage B. The median passive LP return was -0.083% after costs, with only 6/20 pools showing positive median. [3] Passive LP on Solana memecoins is a losing proposition for retail participants.

Active market-making is a fundamentally different business, but it requires the same infrastructure as Arena 1: co-located servers, Rust expertise, Jito integration, and significant capital for inventory. HumidiFi's cofounder came from Jump and Paradigm. Lifinity, the original Solana prop AMM, shut down in November 2025 because it could not compete. [7] If Lifinity — a pioneer with years of head start — was forced out, a new entrant without HFT infrastructure has no realistic path.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | HIGH | Clear fee/spread capture mechanism |
| Speed requirement | HIGH (active) / LOW (passive) | Active requires sub-second; passive is slow |
| Capital requirement | HIGH | Significant inventory for active; moderate for passive |
| Private data requirement | MEDIUM | Oracle feeds, flow data helpful |
| Engineering burden | HIGH (active) / LOW (passive) | Active is full HFT stack; passive is simple |
| Time to first dollar | MEDIUM | Passive is immediate but negative EV; active is 6+ months |
| Fit with my strengths | LOW | Neither passive (proven negative EV) nor active (wrong skills) fits |
| Drift risk | LOW (active) / HIGH (passive) | Active has clear P&L; passive invites endless "maybe this pool" research |
| Defensibility | HIGH (active) / LOW (passive) | Active has speed moat; passive is commoditized |
| **Overall verdict** | **BAD FIT** | Passive LP is empirically negative EV. Active MM requires HFT infrastructure we don't have. |

---

## Arena 3: Routing / Quote-Quality / Execution Tooling

### What the business actually is

Building tools or services that improve trade execution quality for Solana users. This could mean a DEX aggregator (competing with Jupiter), a smart order router, a transaction landing service (competing with Jito/Nozomi), or execution-quality analytics that help traders measure and reduce slippage.

### What kind of edge it relies on

Technical excellence in routing algorithms, deep integration with multiple DEX venues, and network-level optimization for transaction inclusion. The edge is engineering depth and venue coverage.

### Why people make money there

Jupiter commands 93.6% of Solana's aggregator market share. [8] Jito dominates block building and bundle inclusion. Nozomi (Temporal) is emerging as a transaction landing service. These are winner-take-most markets where the best router gets the most flow, which generates the most data, which makes the router better — a powerful flywheel.

### Why I probably cannot win there

Jupiter has 93.6% market share. This is not a market waiting for a new entrant. The aggregator business requires deep integration with every DEX on Solana, continuous maintenance as protocols upgrade, and massive scale to justify the engineering investment. Transaction landing services require the same co-located infrastructure as Arena 1. Execution analytics is a possible niche, but the TAM is small (only sophisticated traders care) and the data required to measure execution quality is the same public data we already proved has no predictive power for returns.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Aggregator fees are real but market is locked |
| Speed requirement | HIGH | Routing and landing are latency-sensitive |
| Capital requirement | LOW | Software business, but engineering cost is high |
| Private data requirement | MEDIUM | Venue integration, flow data |
| Engineering burden | HIGH | Multi-venue integration, continuous maintenance |
| Time to first dollar | HIGH (long) | Months to build, then must win flow from Jupiter |
| Fit with my strengths | LOW | This is a pure engineering/infrastructure play |
| Drift risk | MEDIUM | Clear product but unclear path to market share |
| Defensibility | HIGH | Network effects protect incumbents |
| **Overall verdict** | **BAD FIT** | Winner-take-most market already won by Jupiter. No realistic entry path. |

---

## Arena 4: Launch / Token Diligence / Risk Filtering

### What the business actually is

Building tools or services that help traders evaluate newly launched tokens for rug-pull risk, contract safety, deployer history, liquidity characteristics, and other red flags. Products in this space include RugCheck, Token Sniffer (Solidus Labs), and various Telegram bots that score new tokens.

### What kind of edge it relies on

Domain expertise in Solana token mechanics, pattern recognition for scam signatures, and speed of analysis (new tokens launch continuously on Pump.fun, and traders want instant risk scores).

### Why people make money there

Eleven million tokens were launched on Solana in 2025. [9] The vast majority are scams, rugs, or worthless. Traders who participate in new launches face enormous adverse selection. A tool that reliably filters out the worst tokens has clear value. Chainalysis, which operates in the adjacent compliance/anti-fraud space, reached $190M ARR in 2023. [10] However, Chainalysis serves enterprises and governments, not retail traders.

### Why I probably cannot win there

The retail-facing token screening space is crowded with free tools (RugCheck, Token Sniffer, Axiom's built-in checks). The willingness to pay is low because the target users are memecoin traders who are inherently cost-sensitive and risk-seeking. Our own Who Family Pilot (NG-008) attempted deployer and early-buyer analysis and found: zero deployer wallets identifiable for pumpfun tokens, anti-signal on early-buyer overlap (z = -3.12), and poor data feasibility. [11] The structural data blockers we encountered would apply to any token diligence tool.

That said, there is a meaningful distinction between "screening tool for retail" (low willingness to pay, crowded) and "risk intelligence for funds/desks" (higher willingness to pay, less crowded). The latter is closer to Chainalysis territory and could leverage our falsification discipline. But it requires sales capability, enterprise relationships, and a fundamentally different go-to-market than anything we have built.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | LOW-MEDIUM | Retail: low WTP. Enterprise: higher but requires sales |
| Speed requirement | MEDIUM | New tokens launch continuously; analysis must be fast |
| Capital requirement | LOW | Software/data product |
| Private data requirement | MEDIUM | Deployer data is hard to get (proven in NG-008) |
| Engineering burden | MEDIUM | Scraping, analysis pipeline, UI |
| Time to first dollar | MEDIUM | 2-4 months to build, then must find paying users |
| Fit with my strengths | MEDIUM | Falsification discipline is relevant but data blockers are real |
| Drift risk | HIGH | Easy to keep adding features without revenue |
| Defensibility | LOW | Free alternatives exist; easy to replicate |
| **Overall verdict** | **MARGINAL** | Data blockers proven. Retail WTP is low. Enterprise path exists but requires different skills. |

---

## Arena 5: Research / Falsification / Anti-Bullshit Engine

### What the business actually is

Packaging rigorous, falsification-oriented research as a product. This could take the form of a paid newsletter, a research subscription service, a consulting practice for crypto funds, or a "strategy audit" service that stress-tests trading strategies before deployment. The core value proposition is: "We will tell you the truth about whether your strategy works, using the same discipline that produced 7 honest no-go verdicts."

### What kind of edge it relies on

Credibility, methodology, and communication skill. The edge is not data or speed — it is the ability to rigorously test claims and communicate results honestly. This is the rarest skill in crypto, where most "research" is marketing.

### Why people make money there

Paid crypto research newsletters and services exist at multiple scales. The Milk Road newsletter reached $2M+ ARR. Blockworks Research operates a paid subscription. Messari charges $25K+/year for enterprise research. [12] The common thread is that the successful ones either serve institutions (high price, low volume) or build large audiences (low price, high volume through advertising). Chainalysis ($190M ARR) proves that "telling the truth about crypto" can be an enormous business — but at enterprise scale.

### Why I probably can or cannot win there

**This is the strongest fit with demonstrated strengths.** The 7-program research arc demonstrates exactly the capability that would differentiate a research product: rigorous methodology, honest negative results, statistical discipline, and clear communication. The no-go registry itself is a compelling proof of concept.

However, the honest risks are significant. First, **audience building is a separate skill from research.** Writing rigorous analysis is necessary but not sufficient — distribution, marketing, and community building are required to monetize. Second, **the crypto research market is noisy.** Standing out requires either institutional sales (which requires relationships) or viral content (which requires a different writing style than academic rigor). Third, **revenue takes time.** Newsletter businesses typically take 6-12 months to reach meaningful revenue, and many never do.

The most realistic version of this arena is not a newsletter — it is a **strategy audit / falsification service** for crypto funds and trading desks. The pitch: "Before you deploy capital on a Solana strategy, we will stress-test it with the same 6-gate framework that killed 7 of our own programs." This targets a small number of high-value clients rather than a large audience.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Newsletter: slow. Audit service: clearer but small TAM |
| Speed requirement | LOW | Research is not latency-sensitive |
| Capital requirement | LOW | Minimal — writing and analysis tools |
| Private data requirement | LOW | Uses public data; value is in methodology, not data |
| Engineering burden | LOW | Existing infrastructure sufficient |
| Time to first dollar | MEDIUM | Newsletter: 3-6 months. Audit: 1-3 months if clients exist |
| Fit with my strengths | HIGH | Directly leverages demonstrated falsification discipline |
| Drift risk | MEDIUM | Risk of endless research without monetization |
| Defensibility | MEDIUM | Credibility is hard to fake but also hard to prove to strangers |
| **Overall verdict** | **BEST FIT** | Strongest alignment with proven skills. Revenue path exists but requires deliberate go-to-market. |

---

## Arena 6: Wallet / On-Chain Intelligence Product

### What the business actually is

Building tools that track, label, and analyze Solana wallet behavior. Products include smart-money trackers (following profitable wallets), whale alerts, wallet profiling (identifying deployers, insiders, market makers), and copy-trading infrastructure. Existing players include Nansen ($75M+ raised), Arkham ($150M+ raised), and Birdeye (Solana-native).

### What kind of edge it relies on

Data coverage (how many wallets are labeled), label accuracy (is this wallet actually a "smart money" wallet), and speed of updates (real-time alerts vs. batch analysis). The edge is data infrastructure and labeling quality.

### Why people make money there

Nansen charges $150-$2,500/month for wallet analytics. Arkham operates a token-incentivized intelligence marketplace. Birdeye offers paid API access for wallet PnL data. The market is real — traders want to know what profitable wallets are doing. Copy-trading bots on Solana have surpassed $1B in cumulative DeFi revenue. [13]

### Why I probably cannot win there

This space is dominated by well-funded incumbents. Nansen has raised $75M+, Arkham $150M+, and both have years of accumulated wallet labels and infrastructure. Our own Who Family Pilot (NG-008) demonstrated the difficulty of wallet-level analysis on Solana: zero deployer wallets identified for pumpfun tokens, and early-buyer overlap showed anti-signal. [11] The data infrastructure required to label millions of wallets, track them in real-time, and maintain accuracy is a massive engineering project — exactly the kind of "giant infra science project" the user explicitly does not want.

A niche version — focused specifically on Solana memecoin deployer/insider behavior — might be defensible, but we already proved the data is hard to get and the signal does not exist.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Subscription/API model is proven by incumbents |
| Speed requirement | MEDIUM | Real-time alerts require streaming infrastructure |
| Capital requirement | LOW-MEDIUM | Data infrastructure, not trading capital |
| Private data requirement | HIGH | Wallet labels are the product; building them is the moat |
| Engineering burden | HIGH | Streaming data, labeling pipeline, UI, API |
| Time to first dollar | HIGH (long) | 6-12 months to build competitive product |
| Fit with my strengths | LOW-MEDIUM | Analysis skills relevant but engineering burden dominates |
| Drift risk | HIGH | Easy to keep building features without revenue |
| Defensibility | HIGH | Data moats are real for incumbents; hard for new entrants |
| **Overall verdict** | **BAD FIT** | Dominated by well-funded incumbents. Data infrastructure is exactly the "giant infra science project" to avoid. |

---

## Arena 7: Data / Monitoring / Alerts / Analytics

### What the business actually is

Building dashboards, alert systems, or analytics products that serve Solana traders, protocols, or institutions. This ranges from simple price/volume alert bots to comprehensive analytics platforms like Dune, Flipside, or The Block's on-chain data products. Revenue comes from subscriptions, API access, or advertising.

### What kind of edge it relies on

Data pipeline reliability, unique data transformations, and user experience. The edge is either unique data (that no one else has) or unique presentation (that makes existing data more actionable).

### Why people make money there

QuickNode reached $17.6M revenue in 2023 with 127 employees. [14] Dune Analytics raised $69.4M. The Block operates a subscription data business. At the smaller end, niche Telegram alert bots charge $10-50/month and can reach $10K-50K MRR with a few hundred subscribers. One Solana analytics SaaS was listed for sale at $138K TTM revenue. [15]

### Why I probably can or cannot win there

The full-scale analytics platform is another "giant infra science project" dominated by well-funded incumbents. However, **niche monitoring products** are a realistic entry point. A focused alert/monitoring product — for example, one that monitors specific on-chain conditions and alerts users — can be built with existing infrastructure and reach revenue quickly.

The key question is: what monitoring product would be differentiated? Our research infrastructure already collects universe snapshots, microstructure data, and protocol state from multiple sources. A monitoring product that leverages this existing pipeline — rather than requiring new infrastructure — could reach first dollar faster than most alternatives.

The honest risk: monitoring/alert products have low switching costs and are easy to replicate. Defensibility comes from data quality and user trust, both of which take time to build.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Subscription model proven at multiple scales |
| Speed requirement | LOW-MEDIUM | Alerts need near-real-time but not HFT-speed |
| Capital requirement | LOW | Software product, existing infrastructure |
| Private data requirement | LOW | Public data with unique transformations |
| Engineering burden | MEDIUM | Pipeline exists; UI/delivery is new work |
| Time to first dollar | LOW-MEDIUM | 1-3 months for niche product |
| Fit with my strengths | MEDIUM | Data pipeline exists; analysis skills relevant |
| Drift risk | MEDIUM | Risk of feature creep without revenue focus |
| Defensibility | LOW | Easy to replicate; low switching costs |
| **Overall verdict** | **POSSIBLE** | Niche monitoring product is realistic. Must be tightly scoped to avoid becoming another infra project. |

---

## Arena 8: Cross-Chain / Cross-Venue Tooling

### What the business actually is

Building tools that operate across multiple blockchains or between on-chain and off-chain venues. This includes bridge aggregators, cross-chain arbitrage tools, CEX-DEX execution bridges, and multi-chain portfolio management. The Blockworks research notes that CEX-DEX arbitrage is increasingly moving on-chain, with Wintermute's public market-making bot being a major source of flow. [7]

### What kind of edge it relies on

Multi-venue integration, speed of cross-chain settlement, and capital efficiency across chains. The edge is infrastructure breadth and execution reliability.

### Why people make money there

Cross-chain bridges processed billions in volume in 2025. CEX-DEX arbitrage is a proven profit center for firms like Wintermute and Jump. The opportunity exists because price discrepancies between venues are real and persistent, especially during volatile periods.

### Why I probably cannot win there

Cross-chain tooling requires deep integration with multiple blockchains, each with different consensus mechanisms, finality times, and programming models. Bridge security is a major concern — bridges accounted for over 50% of laundered crypto funds in 2025. [16] The engineering burden is enormous, the security risk is existential, and the competition includes well-funded firms with years of multi-chain infrastructure.

CEX-DEX arbitrage specifically requires CEX API access, significant capital for inventory on both sides, and the same low-latency infrastructure as Arena 1. This is Wintermute's core business — competing with them on their home turf is not realistic.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Arb profits are real but require scale |
| Speed requirement | HIGH | Cross-venue arb is latency-sensitive |
| Capital requirement | HIGH | Inventory on multiple venues |
| Private data requirement | MEDIUM | CEX API access, multi-chain data |
| Engineering burden | HIGH | Multi-chain integration, security concerns |
| Time to first dollar | HIGH (long) | 6-12+ months of infrastructure work |
| Fit with my strengths | LOW | Pure infrastructure/engineering play |
| Drift risk | LOW | Clear success metrics |
| Defensibility | MEDIUM | Integration depth is a moat |
| **Overall verdict** | **BAD FIT** | Requires massive engineering, capital, and multi-chain expertise. Competing with Wintermute. |

---

## Arena 9: Solana Protocol / Ecosystem Consulting

### What the business actually is

Providing advisory, analytics, or operational support to Solana protocols, DAOs, and token projects. This includes tokenomics consulting, liquidity strategy advisory, market microstructure analysis for protocols considering AMM designs, and grant-funded research for the Solana Foundation or ecosystem funds.

### What kind of edge it relies on

Deep understanding of Solana market microstructure, credibility from published research, and relationships with protocol teams. The edge is domain expertise and trust.

### Why people make money there

The Solana ecosystem generated $2.39B in app revenue in 2025. [9] Protocols making this much money need advisory services — tokenomics design, liquidity bootstrapping strategy, market microstructure analysis, risk assessment. Consulting firms like Gauntlet (risk management for DeFi protocols) have built significant businesses in this space. The Solana Foundation also funds ecosystem research through grants.

### Why I probably can or cannot win there

This arena leverages the same strengths as Arena 5 (research/falsification) but targets protocols rather than traders. The 7-program research arc demonstrates deep understanding of Solana market microstructure — AMM mechanics, LP economics, perps funding dynamics, token launch patterns, and execution costs. This is exactly the knowledge that protocol teams need when designing or optimizing their products.

The honest risks: consulting is relationship-dependent, revenue is lumpy (project-based, not recurring), and scaling requires hiring. Grant funding is competitive and politically influenced. However, the barrier to entry is lower than most other arenas, and a single consulting engagement could generate more revenue than months of newsletter subscriptions.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | MEDIUM | Project-based revenue; lumpy but real |
| Speed requirement | LOW | Advisory work is not latency-sensitive |
| Capital requirement | LOW | Minimal — expertise is the product |
| Private data requirement | LOW | Public data + methodology |
| Engineering burden | LOW | Existing tools sufficient |
| Time to first dollar | LOW-MEDIUM | 1-3 months if relationships exist |
| Fit with my strengths | HIGH | Directly leverages microstructure expertise and research discipline |
| Drift risk | LOW | Project-scoped work with clear deliverables |
| Defensibility | MEDIUM | Reputation-based; hard to build, hard to lose |
| **Overall verdict** | **GOOD FIT** | Strong skill alignment. Revenue path is real but requires business development. |

---

## Arena 10: Sniper / Copy-Trade Bot Product

### What the business actually is

Building and selling (or operating as a service) automated trading bots that either snipe new token launches or copy-trade profitable wallets. Products include BonkBot, Trojan, Photon, and Axiom. Revenue comes from per-transaction fees (typically 0.5-1% of trade value) charged to bot users.

### What kind of edge it relies on

Speed of execution (for sniping), wallet identification quality (for copy-trading), and user experience (for retention). The edge is product quality and distribution.

### Why people make money there

Solana trading bots surpassed $1B in cumulative DeFi revenue by mid-2025. [13] This is a proven, large market. The business model is attractive: per-transaction fees on volume that users generate themselves. The bot operator does not need to be profitable at trading — they just need users who trade.

### Why I probably cannot win there

The bot market is already crowded with well-established players (BonkBot, Trojan, Photon, Axiom) that have large user bases, Telegram integrations, and brand recognition. The product is largely commoditized — all bots do roughly the same thing (fast execution, wallet tracking, token screening). Differentiation is difficult, and user acquisition in Telegram bot ecosystems requires marketing spend and community building.

More fundamentally, our research proved that the strategies these bots enable (momentum trading, copy-trading, new token sniping) do not produce positive expected value for users after costs. Building a product that facilitates negative-EV activity raises both ethical and business sustainability questions — users who consistently lose money eventually stop using the product.

| Criterion | Rating | Justification |
|-----------|--------|---------------|
| Profit path clarity | HIGH | Per-transaction fees on user volume |
| Speed requirement | HIGH | Sniping requires sub-second execution |
| Capital requirement | LOW-MEDIUM | Infrastructure, not trading capital |
| Private data requirement | LOW | Public mempool/transaction data |
| Engineering burden | MEDIUM-HIGH | Telegram integration, execution engine, wallet tracking |
| Time to first dollar | MEDIUM | 2-4 months to build, then user acquisition |
| Fit with my strengths | LOW | Product/marketing play, not research play |
| Drift risk | LOW | Clear product with clear metrics |
| Defensibility | LOW | Commoditized; easy to replicate |
| **Overall verdict** | **BAD FIT** | Crowded market, commoditized product, facilitates negative-EV user behavior. |

---

## References

[1] Feature Acquisition v2 Final Recommendation — 210 feature-horizon combinations, 0 passed. `reports/synthesis/feature_family_sweep_v2_final_recommendation.md`

[2] Learnings Ledger entries 011-016, concentration analysis across all programs. `reports/research/LEARNINGS_LEDGER.md`

[3] Meteora LP State Stage B Summary — Stage A false positive falsified. `reports/new_programs/meteora_lp_state_stageB_summary.md`

[4] No-Go Registry NG-006 — Feature Acquisition v2. `reports/research/no_go_registry_v1.md`

[5] RPC Fast, "Solana RPC for MEV," Feb 2026. https://rpcfast.com/blog/solana-rpc-for-mev

[6] RPC Fast, "Solana MEV Infrastructure," Mar 2026. https://rpcfast.com/blog/solana-mev-infrastructure

[7] Blockworks Research, "Solana DEX Winners: All About Order Flow," Jan 2026. https://app.blockworksresearch.com/unlocked/solana-dex-winners-all-about-order-flow

[8] Solana Floor, "Jupiter Reclaims Dominance with 93.6% Market Share," Dec 2025. https://solanafloor.com/news/jupiter-reclaims-dominance-with-93-6-market-share-in-solana-s-aggregator-landscape

[9] Solana Foundation, "2025: The Year of Revenue," Jan 2026. https://solana.com/news/solana-breakpoint-2025

[10] Sacra, "Chainalysis Revenue, Valuation & Funding." https://sacra.com/c/chainalysis/

[11] No-Go Registry NG-008 — Wallet / Deployer / Early-Buyer Signal Family. `reports/research/no_go_registry_v1.md`

[12] Gaps.com, "12 Newsletter Business Success Stories (2025 Revenues)." https://gaps.com/newsletters/

[13] Bitget News, "Solana Bots Surpass $1 Billion in Trading Revenue," May 2025. https://www.bitget.com/news/detail/12560604757184

[14] GetLatka, "QuickNode Revenue." https://getlatka.com/companies/quicknode.com

[15] Acquire.com, "All-in-One Solana On-Chain Analytics Platform for Traders." https://app.acquire.com/startup/trwe7me31q

[16] BitcoinKE, "Bridges Accounted for 50%+ of Laundered Funds in 2025," Jan 2026. https://bitcoinke.io/2026/01/bridges-in-2025/
