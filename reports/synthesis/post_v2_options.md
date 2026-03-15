# Post-Feature-Acquisition-v2 Options

**Date:** 2026-03-15  
**Context:** Feature Acquisition v2 is closed. No viable signal was found in the public on-chain feature space for memecoin long-only selection. This note enumerates the three allowed next moves.

---

## Option A: Stop

Shut down the program entirely. Archive all artifacts, stop the upstream scanner if no other consumer depends on it, and accept that the current market microstructure does not support a systematic long-only edge at the tested horizons.

**What this means in practice:** No new data collection. No new experiments. No new observers. The VPS continues running only for backup retention and any unrelated services. The research memory layer is the final deliverable.

**When to choose this option:** The operator concludes that the opportunity cost of further research exceeds the expected value of finding an edge, or that the Solana memecoin market is structurally unsuitable for systematic trading at the current scale.

---

## Option B: New Program — Large-Cap Swing / Different Market

Start a brand-new research program targeting a different market segment: established tokens with deeper liquidity, longer holding periods, and fundamentally different return dynamics. This is the "pivot to a different market" option referenced in the final recommendation memo.

**What this requires before any collection begins:**

| Requirement | Detail |
|-------------|--------|
| New market definition | Explicit criteria for token inclusion (e.g., market cap > $X, daily volume > $Y, age > Z days) |
| New data source | May reuse some infrastructure but must define new features appropriate for the target market |
| New hypothesis | Pre-registered, falsifiable, with a theoretical basis for why the new market should behave differently |
| No-go check | Confirm the hypothesis is not a re-skin of memecoin long-only selection |
| New experiment entry | Added to EXPERIMENT_INDEX.md before collection starts |

**What this does NOT permit:** Applying the same feature set to a slightly different token filter and calling it a new program. The market structure must be fundamentally different (e.g., tokens with real order books, not AMM-only memecoins).

---

## What Is Not an Option

The following actions are explicitly prohibited under the current no-go registry and decision tree:

| Prohibited Action | Reason |
|-------------------|--------|
| Re-running the same 42 features with parameter tweaks | NG-006 |
| Launching a live observer from the current feature space | Final recommendation: STOP |
| Adding a 6th horizon (+1d) and re-running | Same feature space, same no-go |
| Filtering to a subset of memecoins and re-running | Same features, same market structure |
| Running a "v3" with minor column additions from the same source tables | NG-005 and NG-006 cover this |

---

## Decision Required

The operator must choose A, B, or C. No implementation, collection, or observer work may begin until the choice is made and documented.
## Option C: New Program — Wallet / Deployer / Early-Buyer Data

Start a brand-new research program built around a fundamentally different data source: wallet-level transaction flow, deployer behavior, insider accumulation patterns, or social-graph signals. The core hypothesis shifts from "what is the token doing?" (price, volume, microstructure) to "who is buying or deploying, and what does their history predict?"

**What this requires before any collection begins:**

| Requirement | Detail |
|-------------|--------|
| New data source | On-chain wallet clustering, deployer history, or similar — not derived from universe_snapshot or microstructure_log |
| New hypothesis | Pre-registered, falsifiable, with a theoretical basis for why wallet/deployer behavior should predict returns |
| No-go check | Confirm the hypothesis is not covered by NG-001 through NG-006 |
| New experiment entry | Added to EXPERIMENT_INDEX.md before collection starts |
| New collection script | Separate from feature_tape_v2.py |

**What this does NOT permit:** Re-running the same 42 features from Feature Acquisition v2 with a wallet filter applied. The no-go registry (NG-006) explicitly prohibits re-testing features derived from universe_snapshot or microstructure_log.

---

