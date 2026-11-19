# Stage D–F: billing, cash, dashboard, messages and files

## Scope

Implements the remaining operational surface described by the PRD and
architecture:

- `POST /billing/synchronize`, invoice list/detail and future-invoice cancellation
- payments with exact allocations, replay and reasoned cancellation
- expenses with versioned correction/cancellation audits
- dashboard, reminders and cash reports
- authenticated WhatsApp preview without send claims
- private attachment upload, content access and payment/expense linking
- a Supabase Storage adapter selected only when credentials exist

## Behavior summary

- Billing creates at most one invoice per lease-period, only from the cutover
  date and no earlier than H−3. Repeated synchronization is a no-op.
- Invoice status is derived from active/cancelled state, valid allocations,
  opening balance and business date. Payment cancellation restores the balance;
  the receipt itself remains as a historical row.
- Payment allocations must belong to one lease, be positive, not exceed the
  current remaining balance and sum exactly to the receipt. The service rereads
  balances under the business lock.
- Expenses reject dates before cutover or in the future. Correction requires the
  current version and a reason; before/after snapshots are audited. Cancellation
  keeps the row and excludes it from cash reports.
- The dashboard synchronizes billing before reading. It reports room occupancy
  states separately from people and contract counts, and returns invoice/end-of-
  lease reminders.
- Cash reports reject ranges before cutover, reversed ranges and future ends.
  Income uses valid payment receipt dates; expenses use valid expense dates.
- WhatsApp preview returns recipient, normalized number, message and a `wa.me`
  URL. It never marks a message sent and never changes money.
- Attachments accept JPG/PNG/PDF up to 2 MB after signature/structure checks.
  Staged files are owner-only; linked files are readable by the authenticated
  manager. Payment has at most one proof; expense proofs remain historical after
  correction.

## Actual checks

| Check | Result |
| --- | --- |
| `tests/integration/test_stage_d.py` | **5 passed**: billing synchronization/cancellation, payment replay/overpay/cancel, expense audit/report, dashboard/reminders/WA, attachment validation/link |
| Full backend suite | **105 passed**, 38 subtests, no skips, **83%** coverage |
| `flutter test` | **18 passed** (3 new operations-page tests) |
| Flutter LCOV | **989/2222 lines, 44.5%**; new operational UI is broader than the automated widget coverage |
| `flutter analyze` | No issues found |
| `flutter build web --release` | Successful including Wasm dry-run |
| Read-only browser smoke against an isolated ACTIVE test database | Login, Beranda, Tagihan, Pengeluaran, Laporan and Masa sewa at 1280 px; 390 px no document overflow; no uncaught JavaScript errors |

## Boundaries and unverified items

- Supabase Storage credentials are absent. `SupabaseStorage` is implemented but
  has **not** been exercised against a real project; the running app still uses
  process-local `FakeStorage`. Files are not durable across restarts.
- Flutter now has an optional file picker on payment and expense forms. The
  picker and multipart upload path were compiled and analyzer-checked, but the
  browser upload itself was not included in the recorded smoke test.
- No mutating browser E2E journey has been recorded for contracts, payments,
  expenses, reports or attachments.
- The dashboard/billing synchronization is currently called by the UI before the
  dashboard read; it is not a background job.
- No backup/restore, UAT, axe/screen-reader, keyboard traversal, text zoom or
  visual regression result is claimed.
- Formal `test-plan.md` results and AC-level traceability remain incomplete; this
  report is implementation evidence, not stage acceptance by itself.
