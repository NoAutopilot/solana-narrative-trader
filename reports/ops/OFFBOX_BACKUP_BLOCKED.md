# OFFBOX BACKUP BLOCKED
_Date: 2026-03-10T15:45Z_

---

## Status: BLOCKED

Off-box backup is **not configured**. The backup system is currently **local-only**.

---

## What Was Checked

| Tool | Status |
|---|---|
| rclone | Not installed |
| aws cli | Not installed |
| s3cmd | Not installed |
| DO Spaces env vars | Not set |
| Backblaze B2 env vars | Not set |
| rclone config files | Not found |

---

## Risk

Without off-box backup, the backup system does **not protect against**:

- VPS provider failure or data centre incident
- Accidental volume deletion
- VPS resize/migration that corrupts the volume (as occurred on 2026-03-09)

The current local backup at `/root/solana_trader/backups/sqlite/` protects against:

- Accidental DB corruption during normal operation
- Operator error (accidental DELETE or DROP)
- Application bugs that corrupt a single DB file

---

## Required Action (Owner)

To complete durability, configure one of the following:

**Option A — DigitalOcean Spaces (recommended for DO VPS)**
1. Create a DO Spaces bucket in the same region as the VPS
2. Generate a Spaces access key pair
3. Install rclone: `apt install rclone`
4. Configure rclone with the DO Spaces endpoint
5. Add `rclone sync /root/solana_trader/backups/sqlite/ spaces:bucket/solana_trader/` to `backup_sqlite.sh`

**Option B — AWS S3**
1. Create an S3 bucket
2. Install aws cli: `apt install awscli`
3. Configure credentials: `aws configure`
4. Add `aws s3 sync /root/solana_trader/backups/sqlite/ s3://bucket/solana_trader/` to `backup_sqlite.sh`

**Option C — Backblaze B2**
1. Create a B2 bucket
2. Install rclone and configure B2 remote
3. Add rclone sync to `backup_sqlite.sh`

---

## Current Durability Level

```
Local hot backup:    ACTIVE   (15-min, 72h retention)
Local hourly:        ACTIVE   (14-day retention)
Local daily:         ACTIVE   (30-day retention)
Off-box copy:        BLOCKED  (not configured)
Restore drill:       ACTIVE   (see restore_test_latest.md)
```

**The system is NOT fully protected until off-box backup is configured.**

---

## No Claim of Full Durability

This file serves as a permanent record that off-box backup was not configured at the time of Phase 1 completion. Do not treat the backup system as complete until this file is replaced with `OFFBOX_BACKUP_ACTIVE.md`.
