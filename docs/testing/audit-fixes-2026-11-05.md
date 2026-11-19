# Backend audit fixes, 2026-11-05

## Delivered

This is the first repair batch, not closure of the entire audit. No commits or
pushes were made. No business records were added or removed.

| Finding | Change | Evidence |
| --- | --- | --- |
| Supabase storage fallback | Reject incomplete Supabase Storage configuration in every environment. Local FakeStorage remains available offline. | Two regression tests failed before the fix and passed afterward. |
| HTTP production origin | Reject HTTP origins in production after resolving the selected profile. Local development origins remain allowed. | Regression test failed before the fix and passed afterward. |
| Future contract conflict | Treat STAYING as an open-ended interval from the contract start, rather than blocking all dates. Preserve blocking after an unconfirmed lease end. | Earlier adjacent interval regression failed before the fix; regression and existing lease tests now pass. |
| Invoice detail scans every invoice | Filter invoice ID inside both the paid aggregate and invoice selection. Limit detail results to one row. | PostgreSQL integration test captured SQL, failed before the change, and passed afterward. |
| Future functions inherit PUBLIC EXECUTE | Migration `0007_audit_permissions` revokes the migration owner's global default PUBLIC EXECUTE. A schema-level revoke cannot subtract PostgreSQL's global default grant. | Creating a function after migration was publicly executable before the fix; the same PostgreSQL test now confirms execution is denied. |
| Exposed migration metadata grants | Migration `0007` revokes PUBLIC and existing anon/authenticated/service_role grants on `public.alembic_version`. | Applied on local development, local test, and Supabase. Supabase reports zero grants for all three API roles. |
| Blocked integration tests | `ops/test_postgres.py` creates a password-protected temporary PostgreSQL cluster bound to loopback, creates an isolated test database, runs pytest, stops the cluster, and removes its own temporary directory. | Full integration and concurrency suite executed successfully without granting CREATEDB to application roles. |
| Exposed runtime DB password | Generated a new runtime password, changed the Supabase role, verified a fresh connection, and updated `backend/.env`. | Runtime connection and DB/Storage smoke passed. Recovery URL is only in gitignored `backend/.env.runtime-rotation.local`; no password was printed. |

The global function default change applies to future functions created by the
migration owner in all schemas. It does not revoke existing platform-function
grants. New functions needing external execution must receive explicit grants.
Downgrading `0007` intentionally does not reopen anonymous metadata access.

## Test isolation defect found during verification

Alembic's `load_dotenv()` repopulated profile environment variables after the
integration fixture cleared them. The first full run therefore sent some auth
requests to the existing local DB, causing failed-login/preauth bookkeeping.
No business records were changed. The test runner and integration fixture now
set `PYTHON_DOTENV_DISABLED=1`; the fixture also clears all Settings fields.
Subsequent full tests ran solely against the disposable cluster.

## Commands and results

From the project root:

```powershell
backend\.venv\Scripts\python.exe ops\test_postgres.py
```

Result: **159 passed, 38 subtests passed, 1 warning**, in 49.92 seconds.
The warning is Starlette's deprecation notice for its httpx TestClient backend.
Coverage percentage was not measured; no 80% coverage claim is made.

The invoice-detail PostgreSQL reproducer initially failed its SQL-filter
assertion. The future-function privilege reproducer initially observed PUBLIC
EXECUTE. Both pass in the final full run. Initial guard/lease reproducer:
4 failed, 8 passed. No Git RED/GREEN checkpoints exist because this workspace
is not a Git repository.

```powershell
backend\.venv\Scripts\python.exe ops\supabase_smoke.py
```

Result: health, runtime database, Storage put/get, private bucket, and object
deletion all passed after runtime password rotation. The smoke object was
removed; it did not create business records.

Backend and frontend were restarted at `http://localhost:8001` and
`http://localhost:8081`. Backend uses a process-only Supabase development
override. The file default remains `APP_PROFILE=local`.

## Open blockers and remaining scope

1. Rotate the exposed Supabase owner password through the Supabase dashboard.
   Update `SUPABASE_MIGRATION_DATABASE_URL` privately in `backend/.env`; never
   paste the password in chat. Owner rotation has not been performed.
2. Disable unused Supabase services through verified dashboard controls.
   No authenticated management API or dashboard session was available. A public
   gateway 401 proves routing, not the exact service configuration. Data API,
   Auth, Realtime, and Edge Function disablement is not claimed.
3. The manager username matches `backend/.env.manager.local`, but that file's
   password does not verify against the current Supabase password hash.
   Live login returned 401. The password was not reset and the file was not
   overwritten. Update the private file with the current password or explicitly
   authorize account recovery before the business-flow smoke.
4. Database and Storage backup automation plus an independently verified restore
   drill remain unimplemented. Do not use this batch as approval to enter real
   data. Database backup alone does not cover Storage objects.
5. Expired auth/idempotency rows and abandoned staged attachments still lack a
   retention job. Define retention and idempotency replay guarantees before
   deleting rows; no bulk cleanup was performed.
6. Storage bucket readiness checks and broader business-event coverage remain
   open. No indexes were added blindly: expense_audits already has an index
   beginning with expense_id, and current-responsible lookups use the existing
   partial responsible_current index.
7. Dummy-data finalization/payment/Storage flow and UI browser verification have
   not been rerun. Production HTTPS hosting is still deferred.

## Review

Reviewed changed source and tests inline. Confirmed profile validation precedes
Storage selection, invoice IDs remain bound SQL parameters, existing STAYING
overstay behavior remains tested, the migration contains no business-data DML,
and runtime credentials never enter tool output. No subagents were spawned.
