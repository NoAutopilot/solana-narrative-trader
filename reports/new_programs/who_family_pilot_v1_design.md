# Who Family Pilot v1 — Design Document

**Program:** who_family_pilot_v1
**Date:** 2026-03-15
**Status:** Pilot (bounded feasibility study)

---

## 1. Research Question

Does "who launched / who bought early" contain more signal than the price-and-feature families that already failed (momentum/reversion, feature acquisition v2, large-cap swing)?

Specifically, this pilot tests three sub-hypotheses against a small adversarial sample:

1. **Deployer Recidivism:** Do stronger-performing tokens cluster around repeat deployers or related deployer wallets?
2. **Early-Buyer Overlap:** Do the first 10–20 buyers of stronger tokens overlap more than those of weaker tokens, beyond random expectation?
3. **Smart-Money Concentration:** Do stronger tokens show materially different early buyer concentration than weaker tokens?

## 2. Sample Definition

The sample is drawn from the frozen 96-fire feature_tape_v2 artifact (`feature_tape_v2_frozen_96fires_20260314T150050Z.db`), which provides a point-in-time universe of Solana tokens observed between 2026-03-12T21:45Z and 2026-03-14T09:30Z.

**Labeling rule:** Per-token average forward +1h return across all eligible observations with at least 5 labeled rows. This horizon was chosen because it has the highest label coverage (95.6%) in the frozen dataset and avoids the +4h gap-exclusion penalty.

**Group assignment:** Tokens are ranked by average +1h return and split into a "stronger" group (top performers with positive avg return and N >= 15 where possible) and a "weaker" group (bottom performers with negative avg return and N >= 15 where possible). Ten tokens per group, all pumpfun-origin for comparability.

| Group | Tokens | Avg +1h Return Range | Min Observations |
|-------|--------|---------------------|-----------------|
| Stronger | 10 | +4.0% to +73.0% | 7–60 per token |
| Weaker | 10 | -0.8% to -31.9% | 1–91 per token |

## 3. Wallet Fields Used

For each sampled token, the pilot gathers:

- **Mint authority** via Solana `getAccountInfo` RPC (jsonParsed encoding) — intended as a deployer proxy
- **First 50 transaction signatures** via `getSignaturesForAddress` RPC, sorted by slot ascending
- **Parsed transaction details** via Helius Enhanced Transactions API — extracting token transfer recipients as early buyers
- **First 10 and first 20 unique buyer wallets** from the parsed transactions

## 4. Point-in-Time Concerns

The sample definition uses forward returns computed from the frozen artifact, which means the stronger/weaker labels are determined ex-post. This is acceptable for a feasibility pilot (we are asking "is there any signal at all?") but would need to be restructured for any production system.

The wallet data (deployer, early buyers) is inherently point-in-time — it reflects the actual on-chain state at token creation and cannot be subject to lookahead bias.

## 5. Kill Criteria

The pilot produces a **NO-GO** verdict if any of the following hold:

1. Deployer identification is blocked for the majority of sampled tokens
2. Early-buyer overlap in the stronger group is not statistically distinguishable from the null (shuffled grouping baseline)
3. Concentration metrics show no meaningful difference between stronger and weaker groups
4. The data required for a full program is not realistically obtainable with current resources

The pilot produces a **GO** verdict only if there is clear, non-trivial, statistically supported evidence that wallet-based features differentiate stronger from weaker tokens, and the data pipeline is feasible.

## 6. Methodology

**Deployer recidivism:** Count unique deployer wallets across both groups. Identify any deployer appearing in multiple tokens. Compare deployer reuse rates between groups.

**Early-buyer overlap:** For each group (stronger, weaker), compute pairwise Jaccard similarity of the first-10 and first-20 buyer sets. Compare within-group overlap between stronger and weaker groups. Also compute cross-group overlap as a reference.

**Concentration:** For each token's first 20 buyers, compute top-1 share, top-3 share, and HHI (Herfindahl-Hirschman Index) of token amounts received.

**Null comparison:** Permutation test with 1,000 random shuffles of group assignment. Compare actual stronger-group overlap against the null distribution. Report z-score and empirical p-value.
