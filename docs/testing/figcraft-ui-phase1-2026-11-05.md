# FigCraft to Flutter, first implementation batch

## Verification update, 2026-11-11

### FigCraft matching, first comparison batch

Latest: **171 tests passed**, analyzer clean, release build successful, five-
viewport synthetic Chrome smoke passed. Room filters now use three equal columns
and a full-width confirmation row at normal scale. Large text stacks controls.
Navbar hover stays transparent over the white capsule; keyboard focus retains
its existing chip color. No palette or API changes were made.

Reviewed equivalent-size reference/current image pairs for Login, Kamar, Tagihan
and Menu. Remaining differences and scope are in
`anti-slop/audit-012-2026-11-11.md`. Login input details and spacing, invoice filter
widths, and Menu icon/wrapping differences remain. These comparisons do not prove
all-screen or pixel-perfect fidelity. Static sample data is not copied into UI.

### Dialog stress matrix and keyboard follow-up

Latest results: **169 tests passed**, analyzer clean, release build successful,
and intercepted Chrome smoke passed five viewports. Colors remain unchanged.

Added 56 regressions: 25 lease dialog cases at text 200%, four portrait sizes
and 800x360 landscape with keyboard inset 160; 20 content-page layout cases at
800x360 and 1280x900; navbar and login keyboard flows; four master-form stress
cases; five list loading/error/retry/empty-state cases. The dialog matrix types
into fields, checks Batal remains above the keyboard and closes via Escape
without writing. Existing save/error/retry and controller disposal checks pass.

Initial dialog cases reproduced bottom overflow and an extension input-border
paint assertion. All five dialogs now use scrollable title/content and 16 px
insets. A browser-only full-flow Escape failure required a dialog-local callback;
all five actions use the existing route helper. The browser runner now opens
extension, types periods and verifies Escape dismisses it at each viewport.
Diagnostic isolated browser checks passed before that callback, so do not claim
the underlying framework/focus discrepancy was fully diagnosed.

Master forms (room and resident) also reproduced horizontal/bottom overflow.
They now use scrollable dialogs, 16 px insets, and an expanded room-capacity
dropdown. Their small portrait and landscape keyboard tests pass without writes.
List-state tests load the real Inter font and verify delayed loading, a synthetic
503 message, clicking retry, cleared errors, and empty content for rooms,
residents, leases, invoices and expenses at 320 px/text 200%.

Desktop tests initially scrolled the sidebar instead of report content; corrected
the test selector, not report runtime. Details and limits are in
`anti-slop/audit-011-2026-11-11.md`. This is a scoped improvement, not completion of
all visual comparisons, data-state coverage, keyboard/focus checks or device
screen readers. Global AA contrast remains unresolved per the user's decision.

### Login brand centering and retained palette

The user explicitly rejected global palette changes and requested centering the
login logo/name/tagline shown in their screenshot. Original color tokens remain
unchanged. Existing AA contrast failures remain unresolved, not waived as a pass.

The header Stack now passes its full parent width to its non-positioned content
using StackFit.passthrough. Previously the branding Padding could shrink to the
text width and sit at the left. No logo, typography, form, or API behavior changed.
Three centering regressions cover 320, 390, and 1280 px with reduced text scale
(0.8) to expose shrink-wrapping; the desktop regression failed before the fix.
Existing login 200% text and keyboard validation coverage also passes.

Verification: 113 Flutter tests passed, analyzer clean, release web build passed,
and intercepted Chrome smoke passed five viewports. Visual inspection of refreshed
login-390.png confirms centered branding. No real backend writes occurred.
Scoped checks: layout centering PASS; build/browser smoke PASS; palette unchanged.
The full accessibility delivery gate remains blocked by known contrast and
unverified device screen readers. This is not a complete UI/UX sign-off.

### Lease action retry keys

Latest: **110 tests passed**, analyzer clean, release build successful, Chrome
synthetic smoke passed five viewports after restarting the static server. The
initial smoke attempt failed with connection refused because port 8081 was down;
no application defect was inferred from that failure.

A regression first proved extension retries generated different Idempotency-Key
values for the same request. Detail actions now share a page-local pending-key map
indexed by JSON method/path/payload. Failures retain the key; confirmed response
success removes it. Continuation now goes through that same write helper and
still navigates to the returned lease ID. API paths/payloads/business rules are
unchanged. Same failed payload retains a key across all five action retry tests.

A fake server additionally stores a result then loses its first response. The
identical extension retry returns that stored result without a second fake commit;
a later intentional extension gets a new key. Different failed input also gets a
different key. This is frontend regression evidence, not a live PostgreSQL replay
drill or proof every business action is exactly-once.

Limits: keys live only while this detail page exists. Browser reload/navigation,
changing inputs after an ambiguous outcome, or changed authoritative version can
produce a new request; reconcile current server state before doing that. No durable
retry journal was added. New-contract creation/payment retry comparison remains
separate follow-up work. No primary Supabase or real backend writes occurred.

### Lease save/error/retry test coverage

Latest suite: **109 tests passed**, analyzer clean. This batch changes tests and
documentation only; application source and release web output are unchanged.
Build/browser smoke were not rerun because there is no runtime change.

Ten additional widget tests cover successful and rejected/retried writes for
extend, exit, responsible change, replacement, and continuation. API fixtures
record POST path and payload; success verifies detail reload or navigation to the
returned continuation ID. Exit selects a real fixture successor. Assertions cover
extension version/periods, responsible occupancy ID, replacement predecessor and
resident IDs, continuation package/residents/responsible/date/price/periods.

Rejected writes use a Dio 409 response with the standard error envelope and
synthetic request ID. Each action shows the server message, remains usable,
and submits another request when reopened and confirmed. This verifies manual
reopening/re-entry, not automatic recovery of rejected dialog inputs or stable
idempotency keys after an ambiguous network timeout. Fixtures do not establish
that business-invalid inputs are accepted by the actual backend.

All writes are in-memory test calls. No real backend or primary Supabase requests
occurred. Remaining: ambiguous-outcome retry/idempotency review, large-text and
keyboard-inset tests for every action dialog, global contrast, and screen readers.

### Remaining lease dialog lifecycle follow-up

Latest results: **99 tests passed**, analyzer clean, release build successful.
Chrome synthetic smoke now passes all five viewports, including opening/closing
the new-contract form; screenshots `lease-create-*.png` are refreshed.

Exit, responsible-change, replacement, and continuation dialogs now use a local
DialogRoute helper that awaits route.completed after the result. Their controllers
and notifiers are disposed only after the closing transition removes the dialog.
This preserves their existing form state, payload values, and API endpoints.
Extension retains its previously fixed field-owned controller.

Four focused-input/cancel widget regressions cover these action dialogs and
assert no writes. Testing also exposed 5.1 px right overflow in replacement;
action dropdowns now expand within available width. These are standard-size
dialog tests, not a full 200%/keyboard-inset matrix for every action dialog.

Browser login issue: separate diagnostic runs at 320 and 360 px showed the login
textbox without page errors. The smoke runner now allows three seconds after
semantic activation before its login assertion. The subsequent full run passes;
startup is timing-sensitive and this is a bounded runner stabilization, not a
proven root-cause fix or zero-flake claim. No real contract writes or primary
Supabase changes occurred; backend was not restarted for this synthetic run.

### Contract creation and extension regression follow-up

Current widget verification: **95 tests passed**, analyzer clean, release web
build succeeded. New contract form follows LEASE-03 frame 2160: room/package,
dates/price, occupants/responsible person. Header has a 104 px toolbar and wrapping
text capped at 1.3 scaling, consistent with the shared shell. Long date/price
labels and errors wrap. Existing contract review/save validation and payloads are
unchanged; no new dependency was added.

`lease_forms_test.dart` first reproduced TextEditingController used after disposal
when editing the extension period and cancelling. Extension now uses a field-owned
controller with initialValue/onChanged; cancelling no longer disposes a controller
still used by the closing route. Regression verifies no write and no exceptions.
Four new contract tests validate at 320/360/390/430 px with 200% text and no writes.

Browser verification for this batch is **blocked**, not passed: static assets
serve HTTP 200, but the runner timed out waiting for initial login semantics.
The first attempt also waited for networkidle; bootstrap now waits for load and
the existing semantic/login checks. The latest form screenshots were not proven
fresh. Earlier successful browser results below remain historical.

Remaining action dialogs (exit, responsible change, replacement, continuation)
still use their original local controller/notifier lifetimes and need focused
typing/cancel regressions before claiming all action dialogs safe. No real
contract or Supabase business write was performed. Backend remains stopped after
the harness restart; only the static frontend was restarted for synthetic QA.

### Lease list/detail and resident history follow-up

Current verification: **90 Flutter tests passed**, analyzer clean, release web
build successful, extended Chrome synthetic smoke passed all five viewports with
zero page errors. Backend/API/business rules and primary Supabase data unchanged.

Authoritative FigCraft frames LEASE-01 (745) and LEASE-02 (784) were read directly
from document.json. Lease list now groups records, uses compact Indonesian date
ranges, and reports loaded count honestly when pagination remains. Opening detail
uses push so back preserves the list. Contract facts use Paket/Kontrak/Harga per
periode tables. Occupancy cards allow names, role/state, and dates to wrap without
fixed ListTile heights; invoice details use the same fact-table structure.
Operational action callbacks and their existing availability guards are retained.

Resident detail now shows a grouped occupancy history with contract dates, explicit
unknown exit dates, empty-history messaging, and Lihat kontrak for actual lease IDs.
No responsible flag, filename, resident assignment, or other absent API field is
invented. Historical exited occupants are not presented as current occupants.

Tests add a non-mutating extension dialog open/cancel journey, unknown resident
exit-date coverage, and scrolling list/detail/resident views at 320/360/390/430 px
and 200% text. Browser journeys exercise Menu to resident detail, Lihat kontrak,
contextual back through resident/list/Menu; Menu to lease list/detail and back.
Screenshots: `leases-*.png`, `lease-detail-*.png`, `resident-detail-*.png` under the
existing scratch evidence folder.

Remaining: contract creation/action forms still need their own fidelity and
interaction batch; global contrast, exhaustive keyboard and real screen-reader
verification remain open. No real extend/exit/replace/continue request was sent.

### Initialization follow-up

Current totals: **76 Flutter tests passed**, analyzer clean, release web build
successful, extended Chrome synthetic smoke passed all five viewports with zero
page errors. No real initialization settings, drafts, or finalization requests
were written to the primary Supabase database.

Read the authoritative FigCraft ZIP directly: INIT-01 frame 842, responsive
content nodes 2037–2075. Implementation retains its four-stage preparation flow:
cutover date, resident/contract records, reconciliation, and explicit finalization.
Records now share a grouped surface with dividers/chevrons. Reconciliation counts
have their own fact card. Section headings and spacing establish hierarchy;
finalization has a visible warning about locked cutover and opening balances.
No displayed record/count is copied from design sample data.

Draft editor uses a 104 px wrapping header, SafeArea, resize-to-keyboard scaffold,
and a 640 px content cap. Contract, occupancy, and invoice sections are distinct.
Long field labels can wrap; inline errors allow three lines. Draft serialization,
optional unknown exit dates, version/idempotency handling, reconciliation hash,
and two-checkbox finalization guard were not changed.

Existing widget business journeys still cover draft create/edit/review/finalize,
errors/retry, invalid money focus, and field errors. New tests add preparation
overview scrolling at 320/360/390/430 px and 200% text, plus a long-label draft at
320x568/200%. The large-text overview fixture has no records; populated large-text
record groups and real devices are not separately verified.

Browser smoke switches only its in-memory fixture mode to PREPARATION, opens
`/initialization`, opens Tambah berkas, and returns without saving/finalizing.
Screenshots: `initialization-*.png`, `opening-form-*.png` in the existing scratch
folder. Initial extended run exceeded ten minutes because hash-only navigation
called the 90-second semantics-placeholder wait after semantics were enabled.
Those three hash-navigation waits now use a one-second bound; the unchanged app
passes the full runner. Initial app bootstrap retains the original long wait.

Remaining UI work: lease list/detail/forms and resident detail/history fidelity.
Global contrast and physical screen-reader verification remain open.

### Payment form and cash report follow-up

Latest verification supersedes the totals below: **71 Flutter tests passed**,
analyzer clean, release web build successful, Chrome synthetic smoke passed all
five viewports with zero page errors. Backend application code, API contracts,
credentials, and primary Supabase data were not changed.

Payment form now shows API-backed room/resident/period/remaining context before
receipt inputs. The review action stays in a safe-area footer; button height can
grow with text rather than clipping at 48 px. Expanded method dropdown fixes the
69 px right overflow reproduced at 320x568 with 200% text. Header scaling is
capped consistently with the existing shell. Form/review lists have distinct
keys so review starts at the top rather than inheriting the input scroll offset.
Keyboard focus is dismissed on review. Upload completion gates review/back/input
while upload is active. Explicit confirmation remains required before save.

Cash report adopts the shared subtitle, grouped summary, Indonesian date labels,
and grouped receipt/expense rows. Small or enlarged-text layouts stack amounts.
Cancelled rows retain a visible Batal label; summary uses authoritative API
totals rather than summing rows that also include cancelled records. Both empty
sections have messages. Date inputs remain explicit YYYY-MM-DD controls; a date
range picker is not implemented. Resident names are not invented for this API.

Browser evidence: Menu to report, Tampilkan loads synthetic totals, back returns
to Menu; payment input accepts amount then opens review. New screenshots are
`payment-form-*.png` and `reports-*.png` in the existing scratch evidence folder.
Widget stress covers payment form/review with 200% text and keyboard inset,
including reachable confirmation; report results scroll at 320/360/390/430 px
and 200% text. Real uploads, real payment POSTs, physical screen readers, and full
keyboard traversal were not exercised. Existing brand contrast findings remain.

Next unfinished UI work: initialization, lease screens, and resident detail.

Latest follow-up: **65 tests passed**, analyzer clean, release build and five-size
Chrome synthetic smoke passed. Expense detail action text now uses contrast-tested
dark warning/danger tokens. Detail navigation has a separately named button
semantic beside the action menu. Expense create/correction form is full-screen,
scrollable, safe-area aware, and tested with 200% text plus a keyboard inset.
Form screenshots: `scratch/figcraft-phase1-2026-11-05/expense-form-*.png`.
See `anti-slop/audit-005-2026-11-11.md` for approved fixes and remaining limits.

The expense detail route now displays API-backed amount, category, date,
description, attachment presence, cancellation status, and audit reasons.
It does not invent attachment filenames or manager names absent from the API.
List rows open detail; correction and cancellation retain existing endpoints.
Deep links fall back to the expense list.

Regression testing exposed a cancellation dialog lifecycle bug: its reason
controller was disposed while the closing dialog still used it. Both list and
detail now let TextField own its controller and capture only the reason value.

Verification results:

- `flutter analyze`: no issues.
- `flutter test --reporter expanded`: **63 tests passed**.
- Release web build with the existing localhost API define: passed.
- Chrome synthetic smoke: passed at 320/360/390/430/1280 px, zero page errors.
- Detail correction opens and closes without writing; cancellation dialog opens
  and closes without writing; detail returns to list, then Menu.
- Widget cancellation verifies POST path, expected version, reason, reload,
  closed action disabling, and audit history.
- Detail scroll layout passes 320/360/390/430 px with 200% text.

Browser screenshots remain in `scratch/figcraft-phase1-2026-11-05/`, including
`expense-detail-320.png` through `expense-detail-1280.png`. They are regenerated
evidence, not a separately versioned screenshot archive.
The previous temporary Playwright installation was incomplete after restart;
the runner now works with PYTHONPATH set to
`C:\Users\nmal1\AppData\Local\Temp\opencode\browser-qa-20261111`.
No application dependency or backend database was changed.

Visual acceptance remains pending the existing contrast decision. This update
does not claim full keyboard, screen-reader, coverage, or production validation.
Next UI batch: payment/expense forms, reports, and initialization fidelity.
Historical results below describe the earlier batch, not the current totals.

## Delivered scope

The first UI batch adopts the latest responsive FigCraft document without
changing API contracts, backend rules, credentials, or primary business data.
This is a reviewable implementation batch, not completion of all 28 screens.

| Area | Change |
| --- | --- |
| Theme | Central Accomodio tokens, existing bundled Inter font, 16 px body, 14 px metadata, tokenized input/card/button shapes. |
| Desktop density | Explicit standard visual density prevents Windows web from shrinking the 48 px minimum button style. |
| Mobile shell | Four-tab floating white capsule, 64 px minimum content height, 13 px labels, custom vector icons, 16 px margins and dynamic SafeArea. |
| Accessibility layout | Text scaling is not disabled; navbar and page titles can grow; keyboard reduces body space and hides the primary navbar. |
| Contextual navigation | Detail pages use back history when available; expense screen can return to Menu. Deep-link fallback is contextual rather than always Home. |
| Home | Orange greeting from the manager API, authoritative occupancy/KPI data, room search, reminder tabs, real navigation shortcuts, preparation guard, loading/error/empty handling. |
| Menu | New /menu route groups residents, leases, expenses, reports, password and session links; preparation hides operational links. |
| Login | Gradient brand region and white form panel; setup/password/session logic preserved; focused fields request scroll visibility. |
| Lists | Shared wrapping record cards for room/resident, invoice and expense lists; invoice summary remains API-authoritative. |

The design file was read directly from the `document.json` entry in
`design/kamartha-design-responsive.figcraft`. Its inspected frame IDs included
401 Login, 421 Home, 468 Rooms, 543 Invoices, 647 Expenses, and 711 Menu.
The local FigCraft MCP endpoint on port 47800 was unavailable. Existing PNGs
under `design/responsive/verified/` supplied rendered visual references.
No FigCraft file or historical design was modified.

## Deliberate boundaries

This batch does not add missing backend room/resident joins, composite invoice
filters, or expense total APIs. Room search says number search because that is
what the existing API implements. No sample names, counts or money from the
design are hardcoded into app screens. Full detail/payment/review/report layouts
remain follow-up work; their functional code is preserved and receives the shared
theme, not a claim of completed visual integration.

## TDD evidence

- `figcraft_shell_test.dart` first failed to compile because the new theme and
  capsule modules did not exist. After implementation, tests exercise tokens,
  all four navbar destinations at 320/360/390/430 px and 100%/200% text, plus
  contextual detail back navigation.
- The detail back test initially failed because router-delegate URI described
  the original route during an imperative push. The shell now uses the route's
  `GoRouterState` rather than treating detail as a primary screen.
- Home tests first failed against the old plain summary because the new greeting
  and occupancy composition were absent. They now verify real fixture counts,
  reminder data, and preservation of the no-sync rule in PREPARATION.
- Menu tests first failed because the new page was absent. They now verify mode
  gating and a real resident-management route. Mobile tests set the test view's
  physical size and pixel ratio, not only renderer surface constraints.
- Login's new-brand test failed before adding the brand/form layout. Existing
  setup, login, password-change, reload and logout widget journeys remain green.
- A Windows-platform density test failed with adaptive density (-2, -2). Setting
  `VisualDensity.standard` made the same test pass.
- `figcraft_layout_test.dart` exercises primary lists/Menu at 320/360/390/430 px
  and 200% text, including scrolling. Its login case uses a synthetic keyboard
  inset and reaches/validates the submit button. This is not a real-device test.

## Commands and final results

From `frontend/`:

```powershell
flutter test --reporter expanded
flutter analyze
flutter build web --release --dart-define=API_URL=http://localhost:8001/api/v1
```

Results: **54 tests passed**, analyzer **no issues**, release web build succeeded.
No coverage percentage is claimed. The existing backend suite was not rerun
because backend application source was not changed in this UI batch.

## Browser smoke

`ops/browser_figcraft_smoke.py` uses installed Chrome through Playwright. Every
API request is intercepted with synthetic QA data inside the browser context.
It does not log into the real manager account or write to the real backend.

The operator environment already had Playwright installed in the approved temp
QA directory; no frontend runtime dependency was added.

From the project root in this environment:

```powershell
$env:PYTHONPATH='C:\Users\nmal1\AppData\Local\Temp\opencode\browser-qa-python'
backend\.venv\Scripts\python.exe ops\browser_figcraft_smoke.py
```

All five viewports passed: 320x568, 360x800, 390x844, 430x932 and 1280x900.
Each viewport exercised:

1. Login using synthetic-only credentials.
2. Home, Rooms, Invoices and Menu primary navigation.
3. Menu to Expenses, then contextual back to Menu.
4. Scroll to account/session, then logout back to Login.

Page-error count: zero at each viewport. Browser console/resource audit, Core
Web Vitals, automated pixel-diff, exhaustive keyboard navigation, axe, and real
Android/iPhone screen readers were not measured and are not claimed to pass.
Screenshots are taken after short UI-transition settling, not browser zoom.

Outputs: `scratch/figcraft-phase1-2026-11-05/results.json` and 30 PNG screenshots.
Some screenshots were visually inspected; see the audit for the exact subset.
No baseline-equivalence or full WCAG approval is claimed.

## Running preview and open work

At verification, static frontend `http://localhost:8081` and API health
`http://localhost:8001/api/v1/health` both returned HTTP 200. The real API process
uses the process-only Supabase development override for localhost cookies. The
file default remains local. Background preview processes may stop when the
harness restarts; the URLs are local preview addresses, not public deployment.

The user selected antislop AFTER implementation. Follow-up findings are in
`anti-slop/audit-004-2026-11-05.md`. The main unresolved accessibility finding is
normal-text contrast in the requested palette; the Home search's merged semantic
label also needs review. No after-audit palette change was made without approval.

Next: resolve those findings, then continue screen-specific FigCraft integration
for room details, invoice/payment/review, expenses forms and cash reports. Keep
future UI/business-flow tests in an isolated environment, not the primary DB.

## Review and self-evaluation

Reviewed shared navigation selection, contextual back, preparation visibility,
bound API-derived values, input reflow and preservation of request/idempotency
logic inline. No reviewer subagents were spawned. No commits or pushes were made.

| Axis | Score | Evidence and gap |
| --- | --- | --- |
| Accuracy | 4/5 | 54 tests, clean analyzer, release build and five browser viewports pass; no full backend/browser integration claim. |
| Completeness | 3/5 | Shared shell and primary screens are delivered, but all 28 screens and two accessibility findings remain open. |
| Clarity | 4/5 | Source design, commands, screenshots and limits are recorded; a screen-by-screen progress matrix would help the next phase. |
| Actionability | 4/5 | Local preview and repeatable smoke script work; full visual sign-off requires user decisions in audit 004. |
| Conciseness | 4/5 | Theme, navbar and record cards are reused; detailed evidence stays in docs rather than chat. |

Overall: 3.8/5. Highest-impact improvements: resolve contrast and semantics, then
finish the screen-specific layouts. Completing those needs another implementation
phase; passing tests does not close those gaps. This partial-completion assessment
should match the user's review because outstanding work is explicit.
