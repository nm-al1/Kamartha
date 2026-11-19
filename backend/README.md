# Kamartha backend

Status: foundation in progress, not a complete implementation of KF-01–KF-12.
Follow `../docs/PRD.md`, `architecture.md`, `database.md` and `03-uml/uml.md`.
The Flutter design is not required to implement backend business rules.

## Available

- FastAPI application factory, `/api/v1/health`, error envelopes and request IDs.
- WITA business clock, Argon2id passwords and opaque-token hashing.
- Authentication routes: setup, login, me, CSRF, logout and change-password.
- Database-backed sessions, prelogin CSRF and username/IP login counters.
- Six Alembic revisions defining 22 private-schema tables and integrity controls.
- Pure billing/calendar/balance/payment-allocation validation.

Authentication success paths and migrations still require PostgreSQL integration tests.
Business CRUD, lease/initialization workflows, payment persistence, reports,
messaging and Storage endpoints are not implemented yet. Empty module directories
do not mean those features exist.

## Local setup (PowerShell)

Run from `backend/`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.lock
Copy-Item .env.example .env
```

Fill `.env` locally, never in chat, screenshots or committed files. Satu berkas
memuat dua blok bertag; `APP_PROFILE` memilih blok yang aktif.

- `APP_PROFILE`: `local` atau `supabase`.
- `LOCAL_DATABASE_URL`: PostgreSQL runtime role lokal, `postgresql+psycopg://...`.
- `LOCAL_MIGRATION_DATABASE_URL`: koneksi owner migrasi lokal.
- `LOCAL_IP_HASH_SECRET`: secret acak minimal 32 karakter.
- `LOCAL_SETUP_CODE_HASH`: hash Argon2id kode setup; kode aslinya di
  `LOCAL_SETUP_CODE` untuk demo lokal.
- `SUPABASE_*`: blok online, termasuk dua URL database dan service key.
- `APP_ORIGIN`/profil origin: exact frontend origin, HTTPS in production.
- Use `?sslmode=require` (or verified TLS) for remote database connections.
- Production requires `APP_PROFILE=supabase`, `SUPABASE_URL` and
  `SUPABASE_SERVICE_KEY`; startup fails when any is missing. `APP_PROFILE=local`
  uses process-local `FakeStorage`, whose files are lost on restart.

Generate secrets without echoing passwords in command history:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
.\.venv\Scripts\python.exe -c "from getpass import getpass; from app.core.security import hash_password; print(hash_password(getpass('Setup code (15-128 characters): ')))"
```

Run migrations through the local launcher, which resolves the `LOCAL_*` tags:

```powershell
..\backend\.venv\Scripts\python.exe ..\ops\local_demo.py --help
```

A manual `alembic upgrade head` needs `MIGRATION_DATABASE_URL` set in the
environment first; `.env` stores the tagged `LOCAL_MIGRATION_DATABASE_URL`.

Then an operator reviews/runs `../ops/grant_runtime.sql` as owner and sets the
runtime-role password securely. Keep schema `kamartha` out of Supabase exposed
schemas. No runtime account, hosting project or bucket is created automatically.

### Supabase profile

Local development stays on the `LOCAL_*` tags with PostgreSQL lokal and
`FakeStorage`. The `SUPABASE_*` tags are provisioned explicitly; switch with
`APP_PROFILE=supabase` when the project is ready:

```powershell
..\backend\.venv\Scripts\python.exe ..\ops\supabase_setup.py
..\backend\.venv\Scripts\python.exe ..\ops\supabase_smoke.py
```

`supabase_setup.py` creates the runtime role, runs Alembic, applies
`ops/grant_runtime.sql`, checks least privilege, and creates the private bucket.
It aborts if schema `kamartha` already exists unless `--allow-existing` is given.
The runtime login goes through the session pooler (port `5432`) with username
`kamartha_runtime.<PROJECT-REF>`; Supabase Auth, Data API, Realtime and Edge
Functions are not used. See `../docs/testing/demo-supabase-2026-11-05.md`.

Create the first manager once, after the smoke test:

```powershell
..\backend\.venv\Scripts\python.exe ..\ops\supabase_auth_smoke.py --dry-run
..\backend\.venv\Scripts\python.exe ..\ops\supabase_auth_smoke.py
```

An interactive terminal prompts for username and password. A non-interactive
run generates a password into `backend/.env.manager.local` (gitignored) without
printing it. `/auth/setup` closes automatically after the first manager.


```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

`/api/v1/health` is a liveness check only; HTTP 200 does not prove database readiness.
Development exposes `/docs`; production disables public documentation.
Development cookies are HTTP-compatible; production cookies require HTTPS.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit -q --cov=app --cov-report=term-missing
```

Offline Alembic tests check revision order and generated SQL only. They do not
prove PostgreSQL accepts that SQL or that concurrency rules work.

For integration, use a separate PostgreSQL database without schema `kamartha`:

```powershell
$env:TEST_DATABASE_URL = 'postgresql+psycopg://...'
$env:CONFIRM_ISOLATED_TEST_DATABASE = 'yes'
.\.venv\Scripts\python.exe -m pytest tests/integration -q
```

Do not use production credentials. Tests refuse an existing `kamartha` schema.
Fixtures create the schema inside an outer transaction and roll it back.
Without `TEST_DATABASE_URL`, integration tests are skipped, not passed.
Separate-connection concurrency and backup/restore remain pending. The Supabase
Storage adapter was verified live on 2026-11-05 (private bucket round trip).

## Platform

Dependencies were resolved on Windows with Python 3.14.6. Architecture recommends
Python 3.12 as a candidate; that version and Linux deployment have not been tested.
The pinned lockfile is a version lock, not a cryptographic package-hash lock.
