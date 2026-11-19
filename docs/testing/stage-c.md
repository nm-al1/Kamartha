# Stage C: operational contracts and occupancy

## Scope

Implements BR-06–BR-17 and the selected AC-06–AC-14/AC-37–AC-40 paths:
contract creation with package snapshots and the first invoice, room/person
overlap rejection, per-person exit, responsible-person changes, replacements,
extension, and continuation.

## Available behavior

- A contract starts on or after the cutover date, uses the package snapshot and
  agreed price, and creates exactly one invoice for the first full period.
- Room overlap, known-open occupancy, person overlap, duplicate residents, wrong
  resident count, capacity mismatch, and responsible-person mismatch are rejected
  in the same transaction.
- Exiting a person updates only that occupancy. If the responsible person leaves,
  a staying successor is required in the same save. The last exit closes the
  administrative contact and cancels only future operational invoices with no
  valid payment; a paid future period blocks the closure.
- A replacement must follow a verified exit, must fit capacity, must not be in
  the future, and must stay inside the contract. It does not change price,
  contract end, invoices, or the current responsible person when that person
  remains.
- Extension checks the expected version, adds whole periods from the original
  anchor, and rejects room overlap.
- Continuation starts at or after the old effective end, moves all still-staying
  people to the new contract as CONTINUED, requires the same people to be
  included, and creates a new first invoice.
- Every write is idempotent and uses the `app_settings` row lock, so room and
  person allocation checks are serialized.

## Actual checks

| Check | Result |
| --- | --- |
| `tests/unit/test_lease_rules.py` | **6 passed**: anchor month clipping, leap year, half-open overlap, staying-occupancy block, exit boundary/unknown exit, replacement rules, derived status |
| `tests/integration/test_stage_c.py` | **5 passed**: creation/first invoice/conflicts, responsible exit and successor, last exit/future cancellation/paid-period block, extension/version, replacement/continuation |
| `tests/integration/test_stage_c_concurrency.py` | **2 passed**: two concurrent contracts for one room create one lease; same-key concurrent creation replays one lease |
| Full backend suite | **105 passed**, 38 subtests, no skips, **83%** coverage after Stage C/D/E/F code was added |
| `flutter analyze` | No issues found |
| `flutter build web --release` | Successful including Wasm dry-run |

The room race test uses a committed throwaway schema in the isolated
`kamartha_test` database, independent connections, and the real application
engine. It proves the current serialization path, not an untested future
allocation endpoint.

## Boundaries

- A read-only browser smoke against an isolated ACTIVE test database reached
  Beranda, Tagihan, Pengeluaran, Laporan and Masa sewa at 1280 px, then 390 px
  without document overflow or uncaught JavaScript errors. It did not create a
  contract from the browser.
- AC-06–AC-14/AC-37–AC-40 are not marked fully verified; only the selected
  scenarios above were executed.
- The old Stage B development database remains in PREPARATION unless the user
  finalizes it. No development business data was seeded, finalized, or deleted.
