# Command Index v1 — Solana Narrative Trader

**Date:** 2026-03-13
**Format:** Exact commands only. No guessing. Run on VPS unless noted.

---

## Health Check

```bash
# Current fire count and row stats
sqlite3 /root/solana_trader/data/solana_trader.db \
  "SELECT COUNT(DISTINCT fire_id) fires, COUNT(*) rows,
   SUM(CASE WHEN eligible=1 THEN 1 ELSE 0 END) eligible,
   SUM(CASE WHEN lane IS NULL THEN 1 ELSE 0 END) null_lanes,
   SUM(CASE WHEN buys_m5 IS NOT NULL THEN 1 ELSE 0 END) micro
   FROM feature_tape_v2;"

# Last 5 fires
sqlite3 /root/solana_trader/data/solana_trader.db \
  "SELECT fire_utc, rows_written, duration_s FROM feature_tape_v2_fire_log ORDER BY fire_utc DESC LIMIT 5;"

# Collector service status
systemctl status solana-feature-tape-v2.service

# Collector live logs
journalctl -u solana-feature-tape-v2.service -f

# Autopilot log
tail -f /var/log/ft_v2_autopilot.log
```

---

## Deploy / Pull Latest Code

```bash
# Pull latest from GitHub (run on VPS)
cd /root/solana_trader && git pull origin master

# Verify syntax after pull
python3 -m py_compile /root/solana_trader/feature_tape_v2.py && echo "SYNTAX OK"
```

---

## Dry-Run Final Sweep

```bash
# Dry run — validates sample sizes, no output files written
python3 scripts/final_sweep_v2.py --dry-run \
    --db-path /root/solana_trader/data/solana_trader.db
```

---

## Autopilot Launch

```bash
# Pull latest first
cd /root/solana_trader && git pull origin master

# Launch autopilot (background, logs to file)
nohup bash ops/feature_tape_v2_autopilot.sh \
    > /var/log/ft_v2_autopilot.log 2>&1 &

# Confirm PID
echo "Autopilot PID: $(pgrep -f feature_tape_v2_autopilot)"
```

---

## Manifest Generation

```bash
# Generate manifest for a sweep run
python3 scripts/generate_manifest.py \
    --run-type final_sweep \
    --db-path /root/solana_trader/data/solana_trader.db \
    --script-path scripts/final_sweep_v2.py \
    --output-dir reports/sweeps/

# Generate manifest for frozen artifact
python3 scripts/generate_manifest.py \
    --run-type freeze \
    --db-path artifacts/feature_tape_v2_frozen_$(date +%Y%m%d)_*.db \
    --script-path ops/feature_tape_v2_freeze_dataset.sh \
    --output-dir reports/synthesis/
```

---

## Reading Current Status

```bash
# Current state doc (from repo, run on sandbox)
cat reports/research/CURRENT_STATE.md

# Status packet (generated, run on VPS or sandbox)
python3 scripts/build_status_packet.py \
    --db-path /root/solana_trader/data/solana_trader.db

# Final recommendation (after autopilot completes)
cat reports/synthesis/feature_family_sweep_v2_final_recommendation.md
```

---

## Contract Tests

```bash
# Run against live DB
python3 tests/feature_tape_v2_contract_test.py \
    --db-path /root/solana_trader/data/solana_trader.db

# Run against frozen artifact
python3 tests/feature_tape_v2_contract_test.py \
    --db-path artifacts/feature_tape_v2_frozen_*.db

# Dry run (list tests only)
python3 tests/feature_tape_v2_contract_test.py --dry-run
```

---

## Red-Team Battery

```bash
# Run battery for a specific candidate
python3 scripts/red_team_validation_battery.py \
    --sweep-csv reports/sweeps/feature_family_sweep_v2_ranked_summary.csv \
    --holdout-csv reports/sweeps/feature_family_sweep_v2_holdout.csv \
    --candidate "buy_sell_ratio_m5" \
    --horizon "+15m" \
    --output-dir reports/red_team/
```

---

## Dataset Freeze (Manual)

```bash
# Freeze dataset manually (autopilot does this automatically)
bash ops/feature_tape_v2_freeze_dataset.sh
```

---

## Backup / Restore Proof

```bash
# BLOCKED — no off-box credentials configured
# When credentials are available:
# aws s3 cp artifacts/feature_tape_v2_frozen_*.db s3://bucket/solana-trader/
# aws s3 cp s3://bucket/solana-trader/feature_tape_v2_frozen_*.db artifacts/restore_test.db
# sqlite3 artifacts/restore_test.db "PRAGMA integrity_check;"
```

---

## Off-Box Sync

```bash
# BLOCKED — no credentials present
# Required: AWS CLI configured with S3 bucket, or rclone with B2/GCS config
# When unblocked, add sync command here
```

---

## Collector Restart (After Health Failure)

```bash
# Stop collector
systemctl stop solana-feature-tape-v2.service

# Drop tables (schema will be recreated)
sqlite3 /root/solana_trader/data/solana_trader.db \
  "DROP TABLE IF EXISTS feature_tape_v2; DROP TABLE IF EXISTS feature_tape_v2_fire_log;"

# Pull latest patch
cd /root/solana_trader && git pull origin master

# Restart
systemctl start solana-feature-tape-v2.service
systemctl status solana-feature-tape-v2.service
```

---

## External Review Packet

```bash
# Generate all formats (markdown, yaml, json)
python3 scripts/build_external_review_packet.py \
    --output-dir reports/external_review/

# Markdown only
python3 scripts/build_external_review_packet.py \
    --format markdown \
    --output-dir reports/external_review/
```

---

## GitHub Sync (From Sandbox)

```bash
# Push all changes
cd /home/ubuntu/solana-narrative-trader && \
git add -A && \
git commit -m "message" && \
git push origin master
```
