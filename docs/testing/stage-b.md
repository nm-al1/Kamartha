# Stage B: rooms, residents and opening data

## Scope and sources

Implemented from `PRD.md` BR-14/16/18/34–39, `architecture.md` sections 5/7,
`database.md`, `03-uml/uml.md`, `design.md` INIT-01/ROOM-01/02/RES-01/02,
and the AC-26/27/28 families in `test-plan.md` and `traceability.md`.
This is implementation evidence, not blanket acceptance of every BB/WB variant.
The user manages Git; no commit or Git reset was performed.

## Available behavior

- Authenticated room and resident lists, literal search, pagination, detail,
  creation and editing. Room numbers and resident identities retain database
  uniqueness constraints. Money uses integer rupiah and the existing BIGINT schema.
- Room support cannot be reduced below existing contracts. Reference prices do
  not populate or overwrite contract prices. Availability remains separate from
  the derived occupancy status.
- Resident detail exposes occupancy history; room detail exposes saved contracts.
- Login redirects preparation sessions to `/initialization`; active sessions go
  to `/home`. The latter is a stage-boundary page, not the stage E dashboard.
- Opening settings select the recording cutover date before draft creation.
- Opening forms reuse rooms/residents/packages, save incomplete drafts without
  inventing values, and support one/two initial occupants, later replacement
  rows, responsible resident, known/unknown historical exit, and invoice rows.
- Reconciliation revalidates drafts and shows resolved names, rooms, contract
  ranges, original invoice values, pre-cutover paid amounts and receivables.
- Paid current periods are required. Duplicate/off-calendar periods, invalid
  balances, invalid dates, capacity violations and cross-record overlaps reject
  finalization. Unknown historical exit conservatively reserves that person's
  interval through the original lease end; no fictional exit date is generated.
- Finalization requires two explicit confirmations and a current reconciliation
  hash. Under the `app_settings` row lock, one transaction materializes opening
  leases, occupancies, responsible history, invoices and an immutable finalization
  snapshot, switches mode to ACTIVE, and stores the successful idempotency result.
- No historical cash receipts are manufactured. Opening paid amounts remain on
  invoices. Finalized draft and cutover edits are rejected by the API.
- Opening settings/draft updates and room/resident writes use UUID idempotency
  keys; draft creation also retains its unique `client_record_key`. Flutter keeps
  finalization payload/key for an uncertain-result retry. Reloading the status
  reads the authoritative mode before allowing a new review.

## Actual checks

### Audit-002 fixes: stable CSRF and UI/accessibility

- An authenticated session now keeps one server-derived CSRF token.
  `GET /auth/csrf` no longer rotates it. The token is
  `HMAC-SHA256(ip_hash_secret, "kamartha-csrf:" + raw session token)`; only its
  hash is stored. Login returns the same derived token, and logging out or
  revoking the session invalidates it. Pre-authentication login/setup CSRF still
  rotates through the separate preauth session.
- A new independent-connection regression creates two residents concurrently
  with one session CSRF token: both return **201**, and repeated
  `GET /auth/csrf` returns that same token. Before the fix the audit reproduced
  one **201** and one **403 `CSRF_REJECTED`** because each client refresh replaced
  the other request's token.
- The concurrency module now has **4 tests** (finalization, same-key replay,
  same-key draft creation, same-token concurrent writes). It passed **4 passed**
  in three consecutive runs (7.1–7.8 s each).
- Flutter clears the previous bootstrap error when “Muat ulang” succeeds. A new
  widget test reproduces the old stale-error state, then requires the error to
  disappear and the form to return.
- The opening form now validates dates as real `YYYY-MM-DD` values and money as
  non-negative/positive integer rupiah before saving an incomplete draft. Errors
  appear beside the field, the first invalid field receives focus, and server
  `error.fields` are mapped to the matching input. The `Exception(...)` wrapper
  and literal `Exception:` prefix are gone. Widget tests cover invalid money and
  a server field error.
- Authentication AppBar uses `#B9380B` (white text measured **5.78:1**, AA) instead
  of `#F45A24` (**3.32:1**). Body/input text is **16 px**, metadata **14 px**, titles
  **24 px**. Input radius is **12**, card groups **16**, primary buttons **24**.
- Rupiah display now uses Indonesian thousands separators (`Rp500.000`,
  `Rp1.500.000`) in room rows, contracts, opening recap, finalization dialog and
  the opening-form remaining amount. A unit test covers grouping, zero, negative
  and missing values.
- The rail and bottom navigation show the current location. Verified visually at
  1280 and 360 widths; the release build has no document overflow at
  360/390/430/1280.

| Check | Result |
| --- | --- |
| `python -m pytest -q --cov=app --cov-report=term` with real isolated PostgreSQL | **87 passed**, 38 subtests passed, no skips; **90%** combined coverage |
| Four concurrency tests, three consecutive runs | **4 passed** each run |
| `flutter test --coverage` | **15 passed**; LCOV **829/999 lines, 83.0%** |
| `flutter analyze` | **No issues found** |
| `flutter build web --release` | Successful, including Wasm dry-run |
| `ops/browser_stage_b_smoke.py` against the new release build | Login, preparation, four responsive widths, room/resident form open+cancel, logout and zero uncaught JavaScript errors passed |

Manual accessibility checks (complete keyboard traversal, screen-reader/axe,
text zoom and a visual-regression baseline) and the full mutating browser journey
remain **not executed**. The CSRF fix is covered for concurrent writes, not for
every future endpoint; new write endpoints must keep using `require_manager`.

### Audit fixes: contact closure and draft creation replay

- Opening finalization now closes administrative responsible history when its
  selected occupant is EXITED. The last history row remains available for debt
  follow-up; a STAYING responsible person retains an open history row.
  Closure uses database administrative time, not a fabricated historical exit date.
- Draft creation stores an immutable success response/hash under
  `initialization.create` and `client_record_key` in the business transaction.
  Replaying the original creation after an edit returns the original response
  without overwriting the latest draft. Reading the draft returns its current
  version. Same key with different creation payload remains a 409 conflict.
  Replay also works after finalization without reopening preparation mode.
- RED: the three new PostgreSQL regression cases all failed before the fix.
  GREEN: the full backend suite produced **83 passed, 38 subtests passed**, no
  skips, with one existing TestClient deprecation warning.
- Old development records are not rewritten. A draft created before this fix
  has no immutable original creation response; fallback can only register the
  unchanged currently stored payload. It cannot reconstruct an older payload
  after an earlier edit. Previously finalized contact history is not backfilled.
- Flutter was unchanged; browser, coverage and concurrent-connection checks
  were not rerun for these backend-only changes.

### Earlier audit fixes: initial residents and room status

- Initial residents must be distinct even when their entered/exited dates form
  empty intervals. Distinct-resident validation no longer depends on overlap.
- The room list/detail query labels a current contract OCCUPIED only when a
  STAYING occupancy has actually entered. Exited occupants do not imply physical
  occupancy. Contract rows remain intact; this label does not authorize a new
  overlapping lease or bypass future allocation checks.
- Before the fix, the six targeted regression cases produced **2 failed, 4 passed**:
  duplicate initial resident and all-exited/current-contract status reproduced.
- After the fix, `python -m pytest -q` with isolated PostgreSQL produced
  **80 passed, 38 subtests passed**, no skips, one existing deprecation warning.
  List and detail status tests cover current/exited, current/staying,
  ended/staying and ended/exited cases. No development business data was modified.
- Coverage percentages below refer to the earlier coverage run, not a fresh
  measurement after this fix. Flutter was unchanged; browser tests and
  multi-connection race tests were not rerun for that backend-only patch.

### Concurrency evidence: finalization and draft creation

- `backend/tests/integration/test_stage_b_concurrency.py` commits a throwaway
  schema in the isolated `_test` database, drives the real application engine
  through independent connections, then drops the schema. It does not reuse the
  rolled-back single-connection fixture.
- Two finalizations with different keys: exactly one 200 and one 409
  `MODE_REJECTED`; one finalization, lease, occupancy, invoice and responsible
  history; no payments; settings mode ACTIVE.
- Two finalizations with the same key: both 200 with identical data; one
  finalization and one lease.
- Two draft creations with the same key: both 201 with the same record; one
  record and one idempotency row.
- At that time the three tests passed in three consecutive runs (3 passed each,
  about 6 s per run). The full suite then produced **86 passed, 38 subtests
  passed**, no skips; coverage remained **90%**. The later Audit-002 section adds
  the fourth concurrency test and the current **87 passed / 4 passed × 3 runs**
  result.
- This proves the `app_settings` row lock serializes these Stage B paths. It does
  not prove room-allocation concurrency: allocation endpoints begin in Stage C.

One existing Starlette TestClient/httpx deprecation warning remains. Flutter also
reports five newer package versions outside current constraints; no upgrade was
performed merely to silence this notice.

### Test specification

| Guarantee exercised | Actual test |
| --- | --- |
| Original end-of-month anchor; current paid period required; invalid balances, dates, occupancy and periods rejected | `backend/tests/unit/test_initialization.py` |
| Required identities trim correctly; no NIK-only assumption | `backend/tests/unit/test_residents.py` |
| Setup/auth regression plus resident creation/edit/search and duplicate identity | `backend/tests/integration/test_postgres_foundation.py` |
| Opening finalization and same-key replay create exactly one lease/invoice | `backend/tests/integration/test_stage_b.py::test_opening_finalize_and_safe_replay` |
| Missing fields and stale drafts cannot finalize or overwrite | `test_incomplete_draft_and_stale_versions` |
| Cross-record room/person conflict blocks finalization | `test_cross_record_conflict` |
| Room CRUD, literal underscore search, pagination validation, write replay/conflict | `test_room_crud_search_and_idempotency` |
| Stale cutover version, future dates and a changed reconciliation are rejected | `test_settings_dates_and_reconciliation_change` |
| Failure after materialization rolls back leases/occupancies/invoices/finalization and leaves preparation mode | `test_materialization_failure_rolls_back_all_rows` |
| Two people, one verified exited with unknown date, share one invoice and one receivable | `test_two_people_with_one_exited_unknown_date` |
| Business reads need a session; writes reject incorrect CSRF | `test_business_endpoints_require_session_and_csrf` |
| A changed finalization payload cannot reuse a successful key | `test_finalization_rejects_changed_key_payload` |
| Concurrent finalization, same-key replay and draft creation use independent connections and materialize once | `backend/tests/integration/test_stage_b_concurrency.py` |
| Incomplete draft save, room form at 360/390/430/1280 widths | `frontend/test/stage_b_test.dart` |
| Preparation date/draft/edit/review/finalize navigation, retry, password-change navigation and serialization | `frontend/test/initialization_flow_test.dart` (fake repositories) |

### RED/GREEN evidence

- The new opening unit-test target was executed before implementation and failed
  to import the missing initialization rules/schema module. Those tests now pass.
- The opening Flutter test was executed before its widget existed and failed
  compilation. That same incomplete-draft test now passes.
- PostgreSQL tests caught a real psycopg parameter inference conflict when room
  number was used both as VARCHAR and `lower(text)`. An explicit VARCHAR cast
  fixed creation/update; the database tests were rerun successfully.
- An initial fake-clock fixture predated the manager password timestamp and
  correctly received 401. The fixture now gives its test manager a consistent
  historical password timestamp. Production authentication checks were not weakened.
- Widget scrolling initially targeted multiple scrollables and then tapped an
  off-screen button. Tests now select the form's scrollable and reveal the whole
  button before tapping. No missed-tap warning was suppressed.

### Browser evidence and limits

The smoke test uses only the explicitly created local dummy admin. It logs in
and out, opens then cancels master forms, and does not save business records or
finalize the user's development database. It captures preparation at widths
360, 390, 430 and 1280. The latest Audit-002 screenshots remain in
`%LOCALAPPDATA%/Temp/opencode/kamartha-stage-b-audit002/` (earlier run:
`kamartha-stage-b/`), not in tracked source.

The temporary static server used port 8082. Playwright intercepted static URLs
under `http://localhost:8080` and fulfilled them from this release server, so the
real API still saw the configured Origin. Chrome's LocalNetworkAccessChecks
feature was disabled only for that isolated automation browser because synthetic
static responses otherwise triggered loopback permission denial. CORS and API
CSRF checks were not disabled. An expected anonymous `/auth/me` 401 is not a
JavaScript crash. No uncaught JavaScript errors were observed.

Recorded clicks: login -> preparation; Kamar -> create form -> Escape cancellation;
Penghuni -> create form -> Escape cancellation; session menu -> logout -> login.
The full mutating browser journey is **not** claimed as verified. Its widget
navigation tests use fake repositories; actual business transactions are tested
separately against PostgreSQL. There is no visual-regression baseline, axe audit,
complete keyboard traversal, or text-zoom result, so these are not marked passed.

## Try with the existing dummy admin

1. Keep the backend running on 8000 with `--reload`.
2. Hot restart Flutter with uppercase `R`, or restart its command with
   `--web-hostname localhost --web-port 8080`. Open `http://localhost:8080`.
3. Login with the existing local dummy credentials. No second registration is needed.
4. Add rooms and residents through their menus.
5. Save a cutover date, add an opening file, and enter its contract/occupancies
   and period rows. Use YYYY-MM-DD dates and plain integer rupiah.
6. Save a draft; return to see validation and reconciliation. Edit until complete.
7. For a demo, compare the complete recap, check both confirmations, then finalize.

**Finalization locks this database's opening balances and cutover. There is no
reset button. Do not finalize an empty database just to bypass preparation if
you still intend to add opening dummy records.** No business data was seeded,
deleted or finalized by this implementation run.

## Remaining boundaries

- Finalization, same-key replay and draft creation now have independent-connection
  race coverage. Room-allocation races cannot be executed until Stage C provides
  the allocation endpoint; the Stage B lock test is not allocation proof.
- Complete BB families, CFG/basis-path artifacts and partner reconciliation
  acceptance remain formal follow-up work, not automatically passed by coverage.
- Operational contract creation is recorded in `stage-c.md`; receipts,
  allocations, expenses, synchronization, reports, dashboard and files are
  recorded in `stage-d-e-f.md`. Real Supabase Storage and restore remain
  unverified until credentials and an isolated restore drill exist.
- The post-build UI audit is recorded in `../../anti-slop/audit-001-2026-10-31.md`;
  the follow-up functional/accessibility pass is in
  `../../anti-slop/audit-002-2026-10-31.md`. Its eight UI/CSRF findings were
  approved by the user, applied, and verified above. Manual keyboard,
  screen-reader/axe, text-zoom and visual-baseline checks remain open.

## Self-evaluation

| Axis | Score | Evidence / improvement |
| --- | --- | --- |
| Accuracy | 4/5 | PostgreSQL assertions, 90% coverage, build pass and repeated independent-connection finalization races; room allocation remains Stage C. |
| Completeness | 4/5 | Stage B routes and UI exist; full mutating browser E2E and formal AC variants remain unverified. |
| Clarity | 4/5 | Try steps and irreversible finalization warning are explicit; date entry still relies on YYYY-MM-DD text. |
| Actionability | 4/5 | Existing admin can open forms immediately; Flutter needs a hot restart to pick up new routes. |
| Conciseness | 4/5 | User-facing summary is short; this evidence report is intentionally longer for coursework traceability. |

Overall: **4.0/5**. Highest-value follow-ups: isolated mutating browser E2E,
manual keyboard/screen-reader/text-zoom checks, and Stage C room allocation
races. These gaps are disclosed so the user can distinguish a working
demonstration from completed formal acceptance.
