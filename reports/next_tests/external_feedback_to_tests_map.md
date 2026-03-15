# External Feedback → Next Tests Conversion Map

**Program:** external_feedback_to_tests_map
**Date:** 2026-03-15
**Author:** Manus AI
**Status:** COMPLETE

---

## What Has Already Been Closed

Seven lines have been formally closed as NO-GO. Any new test that is materially equivalent to one of these is disqualified by definition.

| Closed Line | Core Failure Mode | Why It Closed |
|-------------|------------------|---------------|
| Momentum / Reversion | Predictive directional edge on public data | No durable edge; overfitting risk |
| Feature Acquisition v2 | Predictive feature-family sweep | Same frame as Momentum; no structural basis |
| Large-Cap Swing Stage A | Directional swing on large-cap Solana tokens | No edge after friction |
| Who Family Pilot v1 | Wallet-graph / on-chain behavioral prediction | Data access and signal decay |
| Drift Perps Stage A | Directional perps edge on Drift | No edge after funding costs |
| Meteora LP Stage A → Stage B | LP timing / threshold optimization | Falsified in Stage B; IL and fee income insufficient |
| Solana Yield Surface Stage A | Yield optimization as a standalone edge search | Yield surface is narrow, well-arbitraged, inflation-funded |

The common thread across all seven closures is the same: **public-data predictive selection cannot find a durable directional edge on Solana.** Any new test that is a variant of this question — even dressed in new clothing — will fail for the same reasons.

---

## External Feedback Themes

### Gemini Themes

Gemini's feedback centered on three structural observations. First, "toxic flow" — the set of conditions previously identified as bad-long states — may be more useful as a negative or inverse signal than as a long signal. The logic is that if a state reliably predicts poor long outcomes, it may predict good short outcomes, subject to the practical constraints of shorting on Solana (funding rates, borrow availability, listing bias). Second, structural extraction is more defensible than directional guessing: if a mechanism reliably extracts value from a structural feature of the market (e.g., MEV, liquidation cascades), it does not depend on predicting price direction. Third, Gemini proposed instruction-level extraction as a candidate — capturing value from the mechanics of transaction ordering rather than from price prediction.

**Reliability assessment:** Gemini's structural extraction framing is sound and consistent with the closed-line analysis. The toxic-flow inversion idea is testable and genuinely different from prior work. The instruction-level / MEV extraction idea is real but requires infrastructure that likely exceeds the user's current constraints. Weight: medium-high on the first two, low on the third.

### Grok Themes

Grok's feedback focused on private-solo capital paths: running a validator or custom LST, stablecoin basis and delta-neutral carry, staking and yield optimization, and DePIN or node-farm style ideas. The Solana Yield Surface Stage A already falsified yield optimization as a standalone edge. Validator and custom LST require substantial capital and infrastructure. DePIN and node-farm ideas are outside the defined scope. The only Grok theme that survives initial screening is stablecoin basis and delta-neutral carry, which has a testable structural question: can a human-scale operator capture positive median carry after real frictions?

**Reliability assessment:** Most Grok suggestions are either already closed (yield optimization) or outside constraints (validator, DePIN). The basis/carry idea is worth testing but must be scoped tightly. Weight: low overall, medium on basis/carry only.

### Claude Themes

Claude's feedback was the most structurally rigorous. The core observation — that method-specific failure may matter more than Solana-specific failure — reframes the entire closed-line history. The failures were not failures of Solana as a venue; they were failures of the predictive method applied to Solana. Structural and actuarial approaches are more justified because they do not depend on predicting price direction. Claude's three surviving candidates were: (1) an actuarial / casino-math book test, asking whether the empirical payoff distribution supports positive-EV mechanical sizing; (2) a basis / funding carry feasibility test; and (3) a liquidation hunting feasibility test. Claude explicitly flagged active LP rescue and wallet relaunch as low-trust ideas.

**Reliability assessment:** Claude's framing is the most useful of the three. The actuarial book test is genuinely novel relative to all closed lines. The basis/carry and liquidation hunting tests are testable and structurally different. Weight: high.

---

## Synthesis: What the Three Sources Agree On

Despite different framings, the three external sources converge on a small set of structural themes:

**Theme 1 — Inversion / negative screening:** Gemini's toxic-flow inversion and Claude's implicit endorsement of non-predictive negative screens both point toward using existing signal work as a filter rather than a predictor. The question becomes: "what does this state rule out?" rather than "what does this state predict?"

**Theme 2 — Actuarial / distribution-based:** Claude's casino-math book test is the clearest articulation of this. Instead of predicting which tokens will go up, ask whether the empirical distribution of outcomes — across a large, non-selected universe — supports a mechanical positive-EV book. This is how insurance companies and casinos make money: not by predicting individual outcomes but by knowing the distribution.

**Theme 3 — Structural carry / basis:** Both Grok and Claude identified basis and delta-neutral carry as worth testing. The Solana Yield Surface Stage A showed that yield optimization on SOL-denominated instruments is not compelling, but a tightly scoped test of stablecoin basis structures — where the question is about carry after real frictions, not about yield optimization — is a different question.

**Theme 4 — Liquidation / forced-close extraction:** Claude raised this explicitly. The question is whether liquidation events are observable and capturable at human scale, or whether they are already fully captured by bots operating at microsecond latency.

---

## What the Sources Disagree On (or Are Unreliable About)

Gemini's instruction-level / MEV extraction idea requires infrastructure (co-location, Jito bundle submission, sub-second execution) that the user does not have and has explicitly stated they do not want to build. This idea is disqualified by the constraint filter, not by the logic.

Grok's validator and DePIN ideas are capital-intensive and outside scope. They are not tests; they are business pivots. Disqualified.

The "wallet relaunch" and "active LP rescue" ideas (Claude's low-trust category) are correctly flagged as low-trust. They are variants of closed lines dressed in new language.

---

## Candidate Test Construction

The following section identifies six candidate tests that are materially different from all closed lines, drawn from the synthesized themes above. The four mandatory candidates from the brief are included and scored. Two additional candidates are evaluated.

All six candidates are scored in the companion CSV file and in the Top 3 document.
