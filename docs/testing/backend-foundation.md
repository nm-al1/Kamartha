# Backend foundation: execution evidence

Historical report: the counts and unverified database notes below describe the
original foundation run, not the current application. See `stage-a.md` and
`stage-b.md` for subsequent PostgreSQL execution and current test/coverage results.

This report records partial implementation, not completion of the PRD.
Sources: `../PRD.md`, `../architecture.md`, `../database.md`, `../03-uml/uml.md`.
Git operations were not performed; the user manages Git independently.

## Implemented scope

| Area | Implemented | Verification limit |
| --- | --- | --- |
| Billing rules | Anchored 1/6/12-month calendar, H−3, balance and derived status | Pure unit tests; no database materialization yet |
| Payment rules | Methods, dates, positive allocations, same lease, duplicates and exact total | No persistence or concurrency guarantee yet |
| API foundation | Health, errors, request IDs, private production documentation | Liveness only, not database readiness |
| Authentication | Setup, login, opaque sessions, CSRF, counters, logout, password change | Boundary tests pass; successful DB flows remain unverified |
| Schema | Six Alembic revisions, 22 tables, keys/checks/guards | SQL generation and revision chain tested offline only |
| Runtime permissions | Separate operator-reviewed SQL script | Not applied to any server |

## RED/GREEN evidence

- Foundation tests initially failed collection because `app.core.clock` did not exist.
  After implementation, foundation tests passed.
- Migration tests initially failed because Alembic configuration did not exist.
  After implementation, six-revision history and generated SQL assertions passed.
- Authentication boundary tests ran and failed seven cases with HTTP 404 before
  routes existed. After implementation, those cases passed with the expected
  401/403/422/503 responses.

## Commands executed

From `backend/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=app --cov-report=term-missing
.\.venv\Scripts\python.exe -m pip check
```

Actual result: **32 passed, 3 skipped, 38 subtests passed**. Combined branch/statement
coverage reported **62%** for `app`. Billing and payment pure-rule modules each
reported 100%; that does not imply AC-01–AC-50 passed end to end.
The overall 80% coverage target has not been reached.
`pip check`: `No broken requirements found.`

Three PostgreSQL integration tests were skipped because `TEST_DATABASE_URL` was
not configured. PostgreSQL/Docker executables were not found on PATH during the
environment check. No schema was migrated and no external database was modified.

One non-failing warning concerns Starlette's deprecated httpx TestClient adapter.
The current adapter ran the boundary tests successfully; its future replacement
has not been evaluated.

## Pending

- Execute migrations and success-path authentication tests on isolated PostgreSQL.
- Implement and test business services/endpoints for room/resident CRUD,
  initialization/finalization, leases/occupancies, billing synchronization,
  payments/cancellation, expenses/audit, dashboard, reports and WA previews.
- Implement Storage upload/validation/staging/streaming/cleanup.
- Verify concurrency with separate real database connections, runtime privileges,
  anonymous Data API rejection, backup/restore and PostgreSQL guard behavior.
- Complete formal black-box/white-box evidence and traceability for all 50 AC.

This backend must not be deployed for real tenant or financial data yet.
