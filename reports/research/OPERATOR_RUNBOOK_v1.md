# Operator Runbook v1 — Solana Narrative Trader

**Date:** 2026-03-13
**Applies to:** Feature Acquisition v2 phase

---

## A. What to Do at the 10-Fire Health Checkpoint

**When:** ~2 hours after collector service start (fire 10 in `feature_tape_v2_fire_log`).

**Step 1.** SSH into VPS and run the health query:

```bash
sqlite3 /root/solana_trader/data/solana_trader.db << 'SQL'
SELECT COUNT(DISTINCT fire_id) as fires,
       COUNT(*) as total_rows,
       SUM(CASE WHEN eligible=1 THEN 1 ELSE 0 END) as eligible_rows,
       SUM(CASE WHEN lane IS NULL THEN 1 ELSE 0 END) as null_lanes,
       SUM(CASE WHEN buys_m5 IS NOT NULL THEN 1 ELSE 0 END) as micro_rows,
       SUM(CASE WHEN jup_vs_cpamm_diff_pct IS NOT NULL THEN 1 ELSE 0 END) as quote_rows
FROM feature_tape_v2;
SQL
```

**Step 2.** Apply pass criteria:

| Check | Pass Threshold | Action if Fail |
|-------|---------------|----------------|
| `null_lanes` | = 0 | PATCH + RESTART (see Section F) |
| `fires` | = 10 | Wait; collector may be slow |
| `eligible_rows / total_rows` | > 30% | Investigate scanner gate logic |
| `micro_rows / eligible_rows` | > 50% | Expected; Orca/Meteora have no micro |
| `quote_rows / eligible_rows` | > 80% | Investigate Jupiter quote failures |

**Step 3.** If all checks pass, take no action. The collector continues uninterrupted.

**Step 4.** Ratify the collection scope decision (already ratified): full-universe collection, eligible-only analysis.

---

## B. What to Do at 96-Fire Completion

**When:** ~24 hours after collector service start.

**Step 1.** Verify fire count:

```bash
sqlite3 /root/solana_trader/data/solana_trader.db \
  "SELECT COUNT(DISTINCT fire_id) FROM feature_tape_v2_fire_log;"
```

**Step 2.** If autopilot is running, it will detect completion automatically. Check autopilot log:

```bash
tail -50 /var/log/ft_v2_autopilot.log
```

**Step 3.** If autopilot is NOT running (was not launched), launch it now:

```bash
cd /root/solana_trader && git pull origin master
nohup bash ops/feature_tape_v2_autopilot.sh > /var/log/ft_v2_autopilot.log 2>&1 &
```

**Step 4.** Do NOT stop the collector. The autopilot is read-only and runs alongside the live collector.

---

## C. What to Do When Label Maturity Is Reached

**When:** ~28 hours after collector service start (last fire epoch + 4h + 2m buffer).

**Step 1.** The autopilot handles this automatically. It will:
1. Detect label maturity for all 5 horizons (+5m, +15m, +30m, +1h, +4h)
2. Write `reports/synthesis/feature_tape_v2_label_maturity.md`
3. Freeze the dataset
4. Run the final sweep

**Step 2.** If running manually, execute in order:

```bash
# Freeze dataset
bash ops/feature_tape_v2_freeze_dataset.sh

# Run final sweeps
bash ops/run_feature_tape_v2_final_sweeps.sh
```

**Step 3.** Do NOT collect additional fires after the freeze. The frozen artifact is the canonical dataset for all analysis.

---

## D. How to Read the Final Recommendation

**File:** `reports/synthesis/feature_family_sweep_v2_final_recommendation.md`

The report contains:

1. **Verdict** — one of: `PROCEED`, `PIVOT`, `STOP`
2. **Best candidate** — feature name, family, horizon, gross/net median, holdout result
3. **Red-team battery result** — PASS / FRAGILE / FAIL with module breakdown
4. **Benchmark comparison** — vs v1 best, vs baseline
5. **No-go registry check** — any matches
6. **Recommended next action** — explicit one-sentence instruction

**Reading rules:**
- Read the verdict first. If FAIL or STOP, do not read further before deciding.
- If PROCEED, verify the red-team battery result is PASS (not FRAGILE).
- If FRAGILE, treat as PROCEED only with explicit human sign-off on the fragile modules.
- The `+1d` horizon is excluded from the primary decision. It is informational only.

---

## E. What NOT to Touch During Collection

The following are **frozen** until the final recommendation is produced:

| Item | Why |
|------|-----|
| `feature_tape_v2.py` | Any change invalidates the dataset |
| `feature_tape_v2` table schema | Schema changes require DROP + restart |
| Label derivation semantics | Changing labels mid-collection creates lookahead |
| `universe_snapshot` schema | Source table changes corrupt joins |
| `microstructure_log` schema | Source table changes corrupt joins |
| No-go registry | Removals are never allowed; additions only after sweep |
| Benchmark suite v1 | Changing benchmarks mid-sweep is p-hacking |
| Any live observer | No observer is approved |
| Any dashboard | No dashboard changes |

---

## F. What to Do If Health Fails

**Scenario 1: null_lanes > 0**

```bash
# Stop collector
systemctl stop solana-feature-tape-v2.service

# Pull latest patch
cd /root/solana_trader && git pull origin master

# Drop tables (will be recreated)
sqlite3 /root/solana_trader/data/solana_trader.db \
  "DROP TABLE IF EXISTS feature_tape_v2; DROP TABLE IF EXISTS feature_tape_v2_fire_log;"

# Restart
systemctl start solana-feature-tape-v2.service
```

**Scenario 2: Collector has stopped (service crash)**

```bash
systemctl status solana-feature-tape-v2.service
journalctl -u solana-feature-tape-v2.service -n 50
systemctl restart solana-feature-tape-v2.service
```

**Scenario 3: DB corruption**

```bash
sqlite3 /root/solana_trader/data/solana_trader.db "PRAGMA integrity_check;"
```

If corruption is confirmed, restore from the most recent off-box backup (if available) or restart collection from scratch.

**Scenario 4: Collector running but writing zero rows**

```bash
sqlite3 /root/solana_trader/data/solana_trader.db \
  "SELECT fire_utc, rows_written FROM feature_tape_v2_fire_log ORDER BY fire_utc DESC LIMIT 5;"
```

If `rows_written = 0` for 3+ consecutive fires, check scanner is running and `universe_snapshot` is being populated.

---

## G. What to Do If No Candidate Passes

If the final recommendation verdict is `STOP` or `PIVOT`:

**STOP path:**
1. Stop the collector: `systemctl stop solana-feature-tape-v2.service`
2. Archive the frozen dataset to off-box storage (when credentials available)
3. Write a closure memo to `reports/synthesis/feature_tape_v2_closure_memo.md`
4. Do not launch any observer
5. Convene a program review: Is Feature Acquisition v3 viable? Is a product pivot warranted?

**PIVOT path:**
1. Keep the collector running (data is still useful)
2. Execute Stage B of the large-cap swing study:
   ```bash
   python3 scripts/dynamic_universe_builder.py --db-path artifacts/feature_tape_v2_frozen_*.db ...
   python3 scripts/ohlcv_loader.py --universe-db artifacts/largecap_universe.db ...
   python3 scripts/stageA_data_qc.py --universe-db artifacts/largecap_universe.db ...
   ```
3. Do not launch any observer until the swing study completes its own gate sequence

---

## H. What to Do If One Candidate Passes

If the final recommendation verdict is `PROCEED`:

**Step 1.** Verify the red-team battery result is PASS (not FRAGILE).

**Step 2.** Run the contract tests against the frozen DB:

```bash
python3 tests/feature_tape_v2_contract_test.py \
    --db-path artifacts/feature_tape_v2_frozen_*.db
```

All 10 tests must pass.

**Step 3.** Generate the provenance manifest:

```bash
python3 scripts/generate_manifest.py \
    --run-type final_sweep \
    --db-path artifacts/feature_tape_v2_frozen_*.db \
    --script-path scripts/final_sweep_v2.py \
    --output-dir reports/sweeps/
```

**Step 4.** Design the live observer. The observer must:
- Use only the features that passed the battery
- Use the same eligible-only filter (`WHERE eligible = 1`)
- Use the same label horizon that passed
- Have a pre-registered kill switch (stop loss at portfolio level)
- Start with minimum position size

**Step 5.** Do NOT launch the observer until the design has been reviewed and the manifest is committed to GitHub.
