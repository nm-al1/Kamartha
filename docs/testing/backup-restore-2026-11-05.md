# Backup and isolated restore verification

## Scope

`ops/backup.py` backs up the Kamartha PostgreSQL schema, Alembic revision table,
and every object listed in the private Supabase bucket, including unreferenced
objects. It does not use Supabase Auth, Data API, Realtime, or Edge Functions.

This is an operator-run backup tool and restore drill, not an automated schedule
or a production disaster-recovery approval. No source business data is changed.
The source `backup_runs` table is not updated; the completed manifest is the
external record of this read-only backup.

## Consistency and failure handling

- Use a maintenance window. Backup holds SHARE locks on the 22 application
  tables and Alembic revision table. Reads continue; application database writes
  wait until backup finishes. The lock acquisition timeout is 10 seconds.
- Both `pg_dump` archives use one exported REPEATABLE READ snapshot.
- The Storage listing traverses folders and paginates. Each key maps to a local
  SHA-256 filename, so remote keys cannot escape the object directory.
- Every STAGED or LINKED attachment must exist in the downloaded object set,
  with the database's expected byte size and SHA-256. Otherwise backup fails.
- Storage and PostgreSQL do not share a distributed snapshot. The application's
  unique, immutable upload keys make referenced-file verification possible.
  Do not manually overwrite or delete bucket objects during backup. Unreferenced
  objects uploaded after listing may require the next backup.
- Manifest publication happens last. A directory without `manifest.json` is an
  incomplete run, not a usable backup. Existing directories are never overwritten.
- Checksums detect accidental corruption. They do not authenticate an archive
  against someone who can replace both files and manifest.
- Table fingerprints include counts and every row, sorted under the C collation
  with UTC timestamps and ISO dates. Restore compares these fingerprints and
  the migration revision, not just whether `pg_restore` returned success.

## Privacy and restore limits

Backups contain manager password hashes, session material, and potentially
personal/financial records. They are plaintext PostgreSQL archives and object
bytes, not encrypted backups. The tool restricts a newly created backup directory
to the current Windows account with inheritable ACLs (Unix: mode 0700). Use an
encrypted disk and an independently protected off-machine copy. Neither disk
encryption nor off-machine replication was verified or configured here.

No URL, service key, or database password is written into the manifest or printed
by the command. PostgreSQL receives credentials through child-process environment
variables, not command-line arguments. `backups/` is already gitignored.

Restore accepts only a loopback database whose name ends with `_test`, and refuses
existing Kamartha schemas or migration tables. It never drops or truncates a
target. Restore only trusted local archives: a PostgreSQL archive contains SQL.
The recommended runner creates and deletes its own temporary cluster.

The dump deliberately omits owner and ACL grants for portability. This drill does
not restore global roles, passwords, global default privileges, Supabase platform
schemas, bucket settings, or service configuration. Before any future production
restore, explicitly recreate and verify role permissions, function defaults, and
private bucket policy. No production restore command is provided.

Storage bytes are recovered and checksum-verified on disk. Uploading them into a
replacement private Storage bucket, preserving MIME types and policy, remains a
separate recovery step. No remote Storage restore was performed in this batch.

## Usage

Run from the repository root with backend dependencies installed and PostgreSQL
17 tools available. Supply `--pg-bin` or `PG_BIN` if the binaries live elsewhere.
Create uses the Supabase fields in `backend/.env` regardless of active app profile.

```powershell
backend\.venv\Scripts\python.exe ops\backup.py create --directory backups\supabase-YYYYMMDD-HHMM
backend\.venv\Scripts\python.exe ops\backup.py verify --directory backups\supabase-YYYYMMDD-HHMM
backend\.venv\Scripts\python.exe ops\test_postgres.py --restore-backup backups\supabase-YYYYMMDD-HHMM
```

The last command restores into its newly created local cluster, verifies the
database row fingerprints and local object files, then stops and removes only
that temporary cluster. Existing local databases and Supabase are untouched.

## Evidence, 2026-11-05

1. New tests first referenced the missing backup module and failed to import.
2. Checksum, hashed object paths, guarded restore destinations, and recursive
   paginated Storage listing tests passed after implementation.
3. An integration test created two disposable real PostgreSQL databases. It
   migrated and populated a source with a synthetic manager and STAGED attachment,
   backed up the source, restored into the empty target, and checked the rows and
   recovered attachment bytes. A synthetic unreferenced object was also recovered.
   Storage transport was an in-memory test double, not a live provider restore.
4. The same test confirmed rejection of a reused restore target, detection of a
   corrupted local object, and failure without a completion manifest when source
   metadata and Storage bytes differ.
5. HTTPS/credential/path validation tests initially failed for three unsafe
   Storage origins. Validation was added; final suite results are recorded below.
6. Live Supabase backup command:

   ```powershell
   backend\.venv\Scripts\python.exe ops\backup.py create --directory backups\supabase-2026-11-05-audit
   ```

   Result: PASS, revision `0007_audit_permissions`, 22 tables, 0 Storage objects.
   No business records were inserted, updated, or removed.
7. Live-backup restore command:

   ```powershell
   backend\.venv\Scripts\python.exe ops\test_postgres.py --restore-backup backups\supabase-2026-11-05-audit
   ```

   Result: PASS. All 22 table fingerprints and the Alembic revision matched in
   an isolated local PostgreSQL cluster. The live bucket was empty, so this is
   not proof of a populated live Storage restore.
8. `icacls.exe backups\supabase-2026-11-05-audit` confirmed only the current
   Windows account's explicit inheritable full-control grant on the directory.
9. Final verification:

   ```powershell
   backend\.venv\Scripts\python.exe ops\test_postgres.py
   backend\.venv\Scripts\python.exe ops\backup.py verify --directory backups\supabase-2026-11-05-audit
   ```

   Result: **170 passed, 38 subtests passed, 1 warning**, in 60.12 seconds.
   The warning is the existing Starlette/httpx TestClient deprecation. Backup
   checksum verification also passed. Integration and concurrency tests used the
   disposable cluster, not existing demo databases or Supabase.

## Inline review

Checked that database credentials do not enter subprocess arguments, raw
PostgreSQL errors are not echoed, backup files are private, Storage paths are
hashed, SQL table identifiers are quoted, remote restore targets are refused,
existing targets are not cleared, and completion manifests are not published
after a failed attachment check. No reviewer subagents were spawned.

No dependency was added. No commit or push was made. No coverage percentage is
claimed. Remaining release blockers include owner-password rotation, provider
service configuration, manager credential reconciliation, retention cleanup,
off-machine backup, and a populated remote Storage recovery drill.

## Self-evaluation

This batch proves PostgreSQL recovery and local object recovery, not complete
production disaster recovery.

| Axis | Score | Evidence and improvement |
| --- | --- | --- |
| Accuracy | 4/5 | 170 tests and live snapshot restore passed; populated live Storage recovery is not verified. |
| Completeness | 3/5 | Backup and isolated restore are delivered; the broader approved audit still has release blockers listed above. |
| Clarity | 4/5 | Commands and recovery limits are explicit; a shorter operator checklist would improve incident use. |
| Actionability | 4/5 | Create, verify, and disposable restore commands run; encrypted off-machine replication is still an operator responsibility. |
| Conciseness | 4/5 | One backup module reuses the disposable PostgreSQL runner; some documentation repeats safety limits intentionally. |

Overall: 3.8/5. Highest-impact next steps: reconcile manager credentials without
exposing them, run a populated private Storage recovery drill, and configure an
encrypted off-machine copy. Closing those gaps requires further work; they are
not implied by passing this batch's tests. The user should reasonably agree with
this partial-completion assessment because every unverified boundary is named.
