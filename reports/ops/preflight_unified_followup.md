# preflight_unified.py — Follow-Up Note

**Created:** 2026-03-13T19:15Z
**Context:** Emergency recovery during feature_tape_v2 collection run

---

## 1. What Happened

`preflight_unified.py` was referenced in the `ExecStartPre` directive of
`/etc/systemd/system/solana-trader.service` but was absent from disk. The file was never
committed to git (not present in any commit in the repository history). When `systemd`
restarted `solana-trader.service` following a `daemon-reexec` at 2026-03-13T06:27Z, the
`ExecStartPre` step failed with `FileNotFoundError`, preventing `supervisor.py` from
starting and keeping `et_universe_scanner.py` (the `universe_snapshot` writer) down for
approximately 12 hours.

---

## 2. Current State of the Stub

An emergency stub was created at `2026-03-13T18:43Z` to unblock collection. The stub:

- Exits 0 unconditionally (allows `solana-trader.service` to start)
- Writes a `preflight_ping` record to the live DB with `result="stub_pass"`
- Is **not committed** to git (currently an untracked file in the working directory)
- Does **not** perform any real health checks

**Git status as of 2026-03-13T19:15Z:**

```
On branch master
Untracked files:
    preflight_unified.py   ← stub, not committed
```

The stub must remain in place and must **not** be removed or replaced during the current
collection run, as doing so would risk restarting `solana-trader.service` and interrupting
`et_universe_scanner.py`.

---

## 3. Where the Real Preflight Should Live

| Item | Value |
|------|-------|
| File path | `/root/solana_trader/preflight_unified.py` |
| Called by | `solana-trader.service` → `ExecStartPre=/usr/bin/python3 /root/solana_trader/preflight_unified.py trader` |
| Called with arg | `trader` |
| Expected exit code | `0` on pass, non-zero on fail |
| DB side-effect | Should write a row to `preflight_ping (service, result, ts)` |
| Backup reference | `preflight_ping` table exists in backup DB at `/root/solana_trader/backups/sqlite/solana_trader/20260311T090044Z.db` with rows dated 2026-03-09 and 2026-03-10, confirming the original script was functional at that time |

---

## 4. What Needs to Happen After the Run

The following actions are deferred until after the feature_tape_v2 collection run completes
(i.e., after the 96-fire threshold is reached and labels are derived):

**Step 1 — Reconstruct the real preflight script.** Based on the `canary_unified.py`
specification (§A Scanner canary criteria), a proper `preflight_unified.py trader` should
verify at minimum: (a) `universe_snapshot` has a row within the last 5 minutes, (b)
`et_universe_scanner.py` is running, (c) the DB is writable. Exit non-zero on any failure.

**Step 2 — Commit the real script to git.** The stub (or replacement) must be tracked:
```bash
cd /root/solana_trader
git add preflight_unified.py
git commit -m "fix: add tracked preflight_unified.py (was missing from repo)"
git push
```

**Step 3 — Verify the service unit still references the correct path.** The unit file at
`/etc/systemd/system/solana-trader.service` references
`/root/solana_trader/preflight_unified.py` — this is correct and should not be changed.

**Step 4 — Test the full restart cycle.** After replacing the stub:
```bash
python3 /root/solana_trader/preflight_unified.py trader
# Expect: exit 0, preflight_ping row written
systemctl restart solana-trader.service
systemctl status solana-trader.service  # Expect: active (running)
```

---

## 5. Risk Assessment

The current stub is low-risk for the duration of the collection run. It does not suppress
any real errors — it simply skips health checks that the original script would have
performed. The `solana-trader.service` is running correctly with the stub in place.

The primary risk is that if `solana-trader.service` is restarted for any reason (e.g.,
another `daemon-reexec`), the stub will pass `ExecStartPre` even if the system is in a
degraded state. This is acceptable during the collection window but should be resolved
before any production use.
