# Feature Tape v2 — Analysis Views

**Date:** 2026-03-12
**Author:** Manus AI
**Status:** RATIFIED — cold-path documentation

---

## Purpose

This document defines the two analysis views (primary and secondary) that all future sweep scripts, reports, and notebooks must use when querying `feature_tape_v2`. Every report must explicitly state which view is used in its header.

---

## View Definitions

### Primary View: Eligible-Only

```sql
CREATE VIEW IF NOT EXISTS v2_primary AS
SELECT * FROM feature_tape_v2
WHERE eligible = 1;
```

| Property | Value |
|----------|-------|
| Filter | `eligible = 1` |
| Use | Feature sweeps, model discovery, promotion gate evaluation, holdout evaluation |
| Denominator label | `n_eligible` |
| Report header | `View: PRIMARY (eligible-only)` |

This is the **default** view for all analysis. Any report that does not explicitly state its view is assumed to use the primary view.

### Secondary View: Full-Universe

```sql
CREATE VIEW IF NOT EXISTS v2_secondary AS
SELECT * FROM feature_tape_v2;
```

| Property | Value |
|----------|-------|
| Filter | None (all rows) |
| Use | Coverage monitoring, lane distribution, data quality audits, missingness analysis |
| Denominator label | `n_total` |
| Report header | `View: SECONDARY (full-universe audit)` |

This view is used only for audit purposes. Results from this view must never be used for promotion decisions, model training, or holdout evaluation.

---

## Report Header Standard

Every future report or sweep output must include the following header block:

```
════════════════════════════════════════════════════
Report: {report_name}
Date:   {date}
View:   PRIMARY (eligible-only) | SECONDARY (full-universe audit)
Fires:  {first_fire_id} → {last_fire_id} ({n_fires} fires)
Rows:   {n_rows} ({n_eligible} eligible, {n_ineligible} ineligible)
════════════════════════════════════════════════════
```

If a report shows both views, it must clearly separate them with section headers:

```
## Primary View (eligible-only)
...

## Secondary View (full-universe audit)
...
```

---

## Coverage Reporting Standard

All coverage reports must show both views side by side:

```
Coverage — Fire {fire_id}
  Full universe:    {n_total} rows
    micro:          {n_micro}/{n_total} ({pct_micro_total}%)
    quote:          {n_quote}/{n_total} ({pct_quote_total}%)
  Eligible only:    {n_eligible} rows
    micro:          {n_micro_elig}/{n_eligible} ({pct_micro_elig}%)
    quote:          {n_quote_elig}/{n_eligible} ({pct_quote_elig}%)
```

The eligible-only micro coverage is the metric used for promotion gate G8 (`coverage >= 70%`).

---

## Feature Scope Rules

Different feature families have different expected availability by view:

| Feature Family | Primary (eligible-only) | Secondary (full-universe) |
|---------------|------------------------|--------------------------|
| Identity columns | Always available | Always available |
| Classification columns | Always available | Always available |
| Fundamentals (snapshot-native) | Always available | Always available |
| Family A: Order-flow (micro-native) | Available for ~70-80% of eligible rows (Raydium/PumpSwap only) | Available for ~60-75% of all rows |
| Family A: Order-flow (snapshot fallback) | Always available | Always available |
| Family B: Route/quote quality | Available for ~95-100% of eligible rows | **Expected NULL for ineligible rows** |
| Family C: Liquidity (micro-native) | Available for ~70-80% of eligible rows | Available for ~60-75% of all rows |
| Family C: Market-state aggregates | Always available (fire-level) | Always available (fire-level) |

**Key rule:** When computing coverage for Family B (quote/route) features, the denominator must be `n_eligible`, not `n_total`. Ineligible rows are expected to have NULL quote features by design.

---

## SQL Snippets for Common Operations

### Sweep query (primary view)

```sql
SELECT *
FROM feature_tape_v2
WHERE eligible = 1
  AND fire_time_epoch BETWEEN :start_epoch AND :end_epoch
ORDER BY fire_time_epoch, candidate_mint;
```

### Coverage query (dual view)

```sql
SELECT
  COUNT(*)                                                    AS n_total,
  SUM(CASE WHEN eligible = 1 THEN 1 ELSE 0 END)             AS n_eligible,
  SUM(CASE WHEN eligible = 0 THEN 1 ELSE 0 END)             AS n_ineligible,
  -- Micro coverage
  SUM(CASE WHEN order_flow_source = 'microstructure_log' THEN 1 ELSE 0 END) AS n_micro_total,
  SUM(CASE WHEN eligible = 1 AND order_flow_source = 'microstructure_log' THEN 1 ELSE 0 END) AS n_micro_eligible,
  -- Quote coverage (eligible-only denominator)
  SUM(CASE WHEN eligible = 1 AND jup_vs_cpamm_diff_pct IS NOT NULL THEN 1 ELSE 0 END) AS n_quote_eligible
FROM feature_tape_v2
WHERE fire_id = :fire_id;
```

### Lane distribution (secondary view)

```sql
SELECT lane, eligible, COUNT(*) AS n
FROM feature_tape_v2
WHERE fire_id = :fire_id
GROUP BY lane, eligible
ORDER BY n DESC;
```

---

## Enforcement

All sweep and report scripts in this repository must:

1. Accept a `--view` argument with values `primary` (default) or `secondary`.
2. Apply the corresponding `WHERE eligible = 1` filter for primary view.
3. Include the report header block defined above.
4. Log the view used to the provenance manifest (see `provenance_manifest_spec.md`).

Scripts that do not comply with this standard must not be used for promotion decisions.
