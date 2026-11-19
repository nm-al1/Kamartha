# Stage A — auth and initial plumbing

## Implemented

- Flutter login, first-account setup, password change and logout.
- Bootstrap checks `/auth/me`; a protected session screen shows the real manager
  and application mode. This is not the initialization workflow or dashboard.
- Dio browser adapter sends cookies with credentials. CSRF tokens and form
  secrets stay in memory, not localStorage. Origin is supplied by the browser.
- Responsive scrollable auth forms, password visibility, validation, busy/error
  states and manual recovery guidance.
- Inter variable font and SIL OFL are bundled under `frontend/assets/fonts/`.
  Font source links are recorded there; no font API is called at runtime.
- Backend CSRF recovers from expired/forged cookies, reports first-setup
  availability, and `/auth/me` reports the current mode.
- Clock injection through the app factory, pagination parameters, a mode check
  intended for use after the business lock, idempotency helpers and a Storage
  protocol with process-local fake implementation.

## Actual checks

- `python -m pytest -q`, with isolated `kamartha_test` PostgreSQL connection:
  **40 passed**, 38 subtests passed. No integration skip. One existing Starlette
  TestClient/httpx deprecation warning remains.
- PostgreSQL integration checks include setup/login, CSRF, logout, invalid-cookie
  recovery, password change, mode response and idempotency replay/conflict.
- `flutter test`: **1 widget test passed**, using a fake auth repository to
  check required-field validation and availability of first-account setup.
- `flutter analyze`: **No issues found**.
- `flutter build web`: successful after isolating browser-only adapter imports.

The first widget run failed on a browser-only import in VM tests. A conditional
adapter import fixed it. The added invalid-cookie integration scenario initially
failed due to a hostless test cookie coexisting with the real cookie; setting the
cookie domain/path correctly made the scenario pass.

## Try locally

Terminal 1, from `backend/` with its existing private `.env`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Terminal 2, from `frontend/`:

```powershell
flutter run -d web-server --web-hostname localhost --web-port 8080
```

Open **http://localhost:8080** (not 127.0.0.1, because the configured Origin is
localhost). With no manager, select first-account setup, enter the private setup
code and create an account. Then login, reload to check the session, change the
password, login again and logout. Setup writes the first real development
manager; automated tests use isolated fixtures instead and roll them back.

## Remaining verification and boundaries

- The full browser interaction against the running API has not been automated
  or visually inspected. A passing build/widget test is not browser E2E proof.
- Multi-connection setup races, throttle/idle boundaries and revocation races
  still need dedicated integration coverage.
- Idempotency helpers have sequential database replay/conflict coverage, not
  concurrency or lost-response coverage. Future business writers must call
  `lock_business()` before checking mode/idempotency and commit once.
- Fake Storage is process-local and not durable. No upload endpoint or real
  Supabase adapter is provided at this stage. The protocol defines the future
  adapter boundary; real Storage testing remains mandatory before handoff.
- Stage B data initialization and operational navigation are not implemented.
- No formal BB/WB family or traceability row is marked fully verified by this
  report. These checks are partial supporting evidence only.
