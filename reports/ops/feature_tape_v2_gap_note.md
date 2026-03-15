# Feature Tape v2 — Collection Gap Note

**Created:** 2026-03-13T19:15Z
**Revised:** 2026-03-13T19:30Z — exact per-horizon exclusion counts from DB
**Gap type:** Upstream snapshot writer stall (not a collector failure)

---

## 1. Exact Gap Window

| Event | Timestamp (UTC) | Epoch |
|-------|-----------------|-------|
| Last successful snapshot written | 2026-03-13T06:26:00Z | 1773383160 |
| Supervisor SIGTERM (systemd daemon-reexec) | 2026-03-13T06:27:20Z | 1773383240 |
| et_universe_scanner.py terminated | 2026-03-13T06:27:20Z | 1773383240 |
| preflight_unified.py stub created | 2026-03-13T18:43:06Z | 1773427386 |
| solana-trader.service restarted | 2026-03-13T18:43:06Z | 1773427386 |
| First new snapshot after recovery | 2026-03-13T18:43:00Z | 1773427380 |
| First recovered collector fire | 2026-03-13T18:45:00Z | 1773427500 |

**Gap window (exclusive start, inclusive end):** `(2026-03-13T06:27:00Z, 2026-03-13T18:43:00Z]`
**Gap duration:** approximately 12 hours 16 minutes

---

## 2. Fire Counts

| Category | Count | Details |
|----------|-------|---------|
| Successful fires before gap | 36 | Fires 1–36, 2026-03-12T21:45:00Z → 2026-03-13T06:15:00Z |
| Fires during gap window | 1 | Fire dc1485fe at 2026-03-13T06:30:00Z — used stale 06:26Z snapshot |
| Missed fires (no snapshot) | 48 | 2026-03-13T06:45:00Z → 2026-03-13T18:30:00Z |
| Successful fires after recovery | continuing | Fire 37 at 18:45Z (41 rows), fire 38 at 19:00Z (41 rows), … |

**Total rows in dataset at time of this note:** 1,788

---

## 3. Borderline Fire: dc1485fe (2026-03-13T06:30:00Z)

The collector fired at 06:30Z, three minutes after the scanner was terminated. It wrote 47
rows using the stale 06:26Z snapshot. Although the snapshot was only 4 minutes old at fire
time — within normal tolerance — the scanner was already dead and no new microstructure
sweeps had occurred since 06:26Z. This fire is therefore flagged
**`borderline_all_horizons = 1`** and is **excluded from the primary analysis at all label
horizons**. It may be included in a sensitivity appendix if needed, but must never appear
in the primary sweep denominator.

---

## 4. Exact Per-Horizon Exclusion Logic

The exclusion rule for each row and each horizon `h` is:

```
gap_affected_h = 1
  IF (fire_time_epoch + h_seconds) > 1773383220   -- 2026-03-13T06:27:00Z (exclusive)
 AND (fire_time_epoch + h_seconds) <= 1773427380  -- 2026-03-13T18:43:00Z (inclusive)
```

This is evaluated using `fire_time_epoch` (a REAL column in `feature_tape_v2`) to avoid
timezone-suffix parsing issues with SQLite's `datetime()` function. The equivalent SQL
template for any horizon is:

```sql
-- Example: +5m exclusion flag
SELECT id,
       CASE
         WHEN (fire_time_epoch + 300) > 1773383220
          AND (fire_time_epoch + 300) <= 1773427380
         THEN 1 ELSE 0
       END AS gap_affected_5m
FROM feature_tape_v2;
```

---

## 5. Exact Excluded Row Counts by Horizon

All counts are queried directly from the live database (`feature_tape_v2`) as of
2026-03-13T19:20Z. The borderline fire (dc1485fe, 06:30Z) is included in these counts
because its forward windows fall within the gap at every horizon.

| Horizon | Offset (s) | Excluded Rows | Excluded Fires | Affected Fire Times (UTC) |
|---------|-----------|---------------|----------------|---------------------------|
| +5m     | 300       | **47**        | 1              | 06:30 |
| +15m    | 900       | **94**        | 2              | 06:15, 06:30 |
| +30m    | 1,800     | **140**       | 3              | 06:00, 06:15, 06:30 |
| +1h     | 3,600     | **227**       | 5              | 05:30, 05:45, 06:00, 06:15, 06:30 |
| +4h     | 14,400    | **763**       | 17             | 02:30 through 06:30 inclusive |

### Detailed Fire Breakdown

**+5m (47 rows, 1 fire)**

| Fire Time | Rows |
|-----------|------|
| 2026-03-13T06:30:00Z | 47 |

**+15m (94 rows, 2 fires)**

| Fire Time | Rows |
|-----------|------|
| 2026-03-13T06:15:00Z | 47 |
| 2026-03-13T06:30:00Z | 47 |

**+30m (140 rows, 3 fires)**

| Fire Time | Rows |
|-----------|------|
| 2026-03-13T06:00:00Z | 46 |
| 2026-03-13T06:15:00Z | 47 |
| 2026-03-13T06:30:00Z | 47 |

**+1h (227 rows, 5 fires)**

| Fire Time | Rows |
|-----------|------|
| 2026-03-13T05:30:00Z | 41 |
| 2026-03-13T05:45:00Z | 46 |
| 2026-03-13T06:00:00Z | 46 |
| 2026-03-13T06:15:00Z | 47 |
| 2026-03-13T06:30:00Z | 47 |

**+4h (763 rows, 17 fires)**

| Fire Time | Rows |
|-----------|------|
| 2026-03-13T02:30:00Z | 39 |
| 2026-03-13T02:45:00Z | 44 |
| 2026-03-13T03:00:00Z | 44 |
| 2026-03-13T03:15:00Z | 45 |
| 2026-03-13T03:30:00Z | 45 |
| 2026-03-13T03:45:00Z | 46 |
| 2026-03-13T04:00:00Z | 46 |
| 2026-03-13T04:15:00Z | 47 |
| 2026-03-13T04:30:00Z | 47 |
| 2026-03-13T04:45:00Z | 46 |
| 2026-03-13T05:00:00Z | 46 |
| 2026-03-13T05:15:00Z | 41 |
| 2026-03-13T05:30:00Z | 41 |
| 2026-03-13T05:45:00Z | 46 |
| 2026-03-13T06:00:00Z | 46 |
| 2026-03-13T06:15:00Z | 47 |
| 2026-03-13T06:30:00Z | 47 |

---

## 6. Final Sweep Denominator Guidance

For each label horizon, the primary sweep denominator is:

```
denominator_h = total_rows - gap_affected_h_rows
```

Using the exact counts above (as of 1,788 total rows at note time; recompute at 96-fire
completion):

| Horizon | Total Rows | Excluded | Primary Denominator |
|---------|-----------|----------|---------------------|
| +5m     | 1,788     | 47       | 1,741               |
| +15m    | 1,788     | 94       | 1,694               |
| +30m    | 1,788     | 140      | 1,648               |
| +1h     | 1,788     | 227      | 1,561               |
| +4h     | 1,788     | 763      | 1,025               |

These denominators will be recomputed from the final dataset at 96-fire completion.
The `derive_labels.py` script marks gap-affected rows via the `missing_disk_gap` column.
The final sweep scripts (`feature_sweep.py`, `run_feature_tape_v2_final_sweeps.sh`) must
filter on `missing_disk_gap = 0` (or the per-horizon equivalent) before computing label
coverage and model-ready row counts.

---

## 7. Final Sweep Script Confirmation

The horizon-specific exclusion flags will be applied as follows in the final sweep:

```sql
-- Primary analysis filter (per horizon h):
WHERE gap_affected_{h} = 0
  AND borderline_all_horizons = 0
```

The `borderline_all_horizons` flag applies to all 47 rows from fire dc1485fe (06:30Z) and
excludes them from the primary denominator at every horizon. These rows are retained in the
table for completeness and may be included in a sensitivity appendix.

No changes to `derive_labels.py`, `feature_sweep.py`, or any sweep script are made at this
time. This note serves as the authoritative reference for the final sweep operator.

---

## 8. Root Cause Summary

The gap was caused by a `systemctl daemon-reexec` triggered by `apt-daily-upgrade.service`
at 2026-03-13T06:27:19Z. The underlying vulnerability was that `preflight_unified.py` was
absent from disk (never committed to git), causing `solana-trader.service` to fail its
`ExecStartPre` on every restart attempt for ~12 hours. See
`reports/ops/preflight_unified_followup.md` for the full follow-up plan.
