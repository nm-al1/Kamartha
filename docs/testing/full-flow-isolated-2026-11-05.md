# Isolated business flow and live private Storage, 2026-11-05

## Outcome

Manager access to the primary Supabase database now verifies against the private
credential file. No password reset or credential-file change was performed.
The previously reported credential mismatch is resolved as of this check.

The user chose an isolated test environment instead of finalizing the primary
database. The complete business API flow passed with disposable real PostgreSQL
and a uniquely named private Supabase Storage bucket. The primary database
remains PREPARATION with no business data. Both temporary resources were removed.

## Primary authentication verification

- A read-only PostgreSQL check confirmed the account exists, username/password
  match `backend/.env.manager.local`, and the manager is active.
- In-process FastAPI TestClient, using the Supabase profile, returned health 200,
  CSRF 200, setup_available=false, login 200, me 200, logout 200, and me 401 after
  logout. No browser deployment or public HTTPS route is implied.
- Login/logout created normal auth bookkeeping, but no business records.
- No credential values were printed, saved to this report, or changed.

## Reproducible isolated flow

Run from the project root:

```powershell
backend\.venv\Scripts\python.exe ops\test_postgres.py --flow-smoke
```

The existing runner creates its own password-protected loopback PostgreSQL
cluster and empty `kamartha_isolated_test` database. `ops/full_flow_smoke.py`
migrates that database and refuses a remote or non-test database target. Test
Settings explicitly clear profile-specific environment overrides, preventing
accidental inheritance of the primary Supabase database URL.

Only the Storage URL and service key are read from `backend/.env`. A new
`kamartha-flow-test-<uuid>` bucket is created private with a 2 MB size limit and
JPG/PNG/PDF allowlist. The application uses its real SupabaseStorage adapter, not
FakeStorage, for this opt-in live run. The primary bucket is never emptied or
written by this flow. The temporary bucket is emptied and deleted in `finally`;
the runner stops and removes only its own temporary PostgreSQL cluster.

The isolated database uses its own random setup code, manager password, and CSRF
secret. It does not reuse the primary manager account. Date inputs derive from
the current Asia/Makassar business date, with cutover at the first day of that
month. There is no fixed clock earlier than the database-created manager date.

## Checked scenario

| Step | Verified result |
| --- | --- |
| Setup and login | Fresh isolated manager, PREPARATION mode, CSRF and session accepted. |
| Master data | Two dummy rooms, two dummy residents, existing 1-person monthly package. |
| Opening data | Previous-month contract and current-period opening invoice Rp500,000, opening paid Rp200,000. |
| Reconciliation | Can finalize; receivable exactly Rp300,000. |
| Finalization | Mode ACTIVE; same idempotency key returns the same result; new preparation writes are rejected. |
| Operational contract | Second room/resident, Rp700,000 monthly invoice; overlapping repeat contract rejected. |
| Billing sync | No duplicate invoice created. |
| Storage upload | Two valid synthetic PNGs uploaded and downloaded with identical bytes while STAGED. |
| Partial payment | Rp400,000 payment reduces remaining to Rp300,000; replay returns the same payment ID; changed payload with the same key rejected. |
| Cancellation | Cancelling the partial payment restores remaining to Rp700,000. |
| Overpayment | Rp800,000 against the Rp700,000 invoice rejected. |
| Full payment | Rp700,000 payment links the first attachment; invoice becomes PAID with zero remaining. |
| Attachment reuse | Attempt to attach the payment receipt to an expense is rejected and rolled back. |
| Expense audit | Expense Rp90,000 corrected to Rp100,000, second attachment linked, version 2 and one audit; stale version rejected. |
| Linked download | Both linked attachment downloads match uploaded PNG bytes. |
| Cash report | Income Rp700,000; expense Rp100,000; difference Rp600,000. Opening paid and the cancelled payment do not inflate income. |
| Dashboard | Two occupied rooms; opening receivable remains Rp300,000. |
| WhatsApp preview | Payment preview returns a wa.me link. No message is sent. |
| Logout | me and attachment download both return 401 after logout. |
| Bucket privacy | Anonymous public-object request does not return 200; bucket metadata confirms public=false. |
| Cleanup | Exactly two objects before cleanup; this run's temporary bucket emptied and deleted. |

Live command result:

```text
Isolated business flow: PASS; real PostgreSQL + private Supabase Storage.
Cash: income=700000; expense=100000; net=600000; receivables=300000.
Temporary bucket emptied and deleted: kamartha-flow-test-ad2a1ea7c5914e5a83b9dc417d2b74f2
```

## Primary-data invariants checked afterward

A separate read-only check confirmed primary Supabase mode PREPARATION and zero
rows in rooms, residents, leases, invoices, payments, expenses, and attachments.
The primary Storage bucket remains empty. The bucket-list API confirmed this
run's temporary bucket no longer exists.

## Automated regression evidence

The new integration scenario was written first and failed because the smoke
module did not yet exist. The first implemented run then reproduced a test-clock
mismatch: a newly created manager had a real database password_changed_at later
than the fixed March clock, so me returned 401 after login. The harness now uses
the actual clock and relative calendar dates; the application was not changed.

The scenario also runs in the normal integration suite against real PostgreSQL
with the local in-memory Storage adapter. Live Storage access happens only with
the explicit `--flow-smoke` option. Unit regressions verify that inherited
profile variables cannot replace the test target, and a remote database is
rejected before the live flow starts.

```powershell
backend\.venv\Scripts\python.exe ops\test_postgres.py
```

Result: **173 passed, 38 subtests passed, 1 warning**, in 56.49 seconds. Warning:
the existing Starlette/httpx TestClient deprecation. No coverage percentage is
claimed. No business application source, schema migration, or credentials were
changed by this batch. No commit or push was made.

## Boundaries and next step

This verifies API behavior in-process, not Flutter browser interactions or a
public deployment. The isolated application runs on the temporary database's
owner connection; full business flow under the restricted production runtime
role is not separately claimed by this run. Production runtime DB/Storage
connectivity was verified in the earlier Supabase smoke.

Live object upload/download is not a populated disaster-recovery restore drill.
Owner password rotation, provider service disablement, retention cleanup,
encrypted off-machine backups, and public HTTPS remain separate open work.

The next UI step is to inspect the final FigCraft source, map its screens to
existing Flutter routes, and integrate layouts without changing API contracts or
business rules. The primary database should remain untouched during UI testing.

## Inline review and self-evaluation

Reviewed target validation, explicit Settings isolation, UUID bucket ownership,
credential output suppression, and cleanup boundaries. Cleanup never targets
the primary bucket; a bucket-creation conflict does not authorize deleting it.
No subagents were spawned.

| Axis | Score | Evidence or remaining gap |
| --- | --- | --- |
| Accuracy | 4/5 | 173 tests plus a live private Storage flow passed; no browser or production-runtime parity claim. |
| Completeness | 4/5 | Login and isolated business flow delivered; FigCraft integration is the next phase. |
| Clarity | 4/5 | Commands, amounts, target ownership and unchanged primary state are explicit; UI mapping is not yet documented. |
| Actionability | 4/5 | One command repeats the isolated live flow; provider Storage credentials and PostgreSQL tools remain prerequisites. |
| Conciseness | 4/5 | One shared scenario supports offline regression and opt-in live validation; this report preserves detailed evidence separately from chat. |

Overall: 4.0/5. Next improvements: integrate and test the final UI, add a
restricted-runtime full-flow variant, and independently verify populated Storage
recovery. The user should reasonably agree with this assessment because verified
API outcomes and unverified deployment/UI boundaries are separated.
