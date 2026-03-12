---
phase: 02-run-input-workflow
plan: 02
subsystem: data
tags: [streamlit, pandas, validation, uploads, pytest]
requires:
  - phase: 02-01
    provides: Session-scoped staged upload metadata with canonical per-slot paths
provides:
  - Slot-aware validation for staged sales, stock, and SKU/live files
  - Blocking errors for unsupported formats, unreadable files, and missing required columns
  - Non-blocking warnings plus compact row and month summaries for the upload UI
affects: [02-run-input-workflow, 03-v5-calculation-runs]
tech-stack:
  added: []
  patterns: [slot-aware validation contract, compact upload summary metadata]
key-files:
  created: [streamlit_app/services/input_validation.py, tests/test_input_validation.py]
  modified: []
key-decisions:
  - Reuse the staged upload metadata contract from Plan 02-01 so validation stays independent from Streamlit widget internals.
  - Keep empty or near-empty datasets and mixed-month date hints as warnings instead of blockers so operators can still inspect and decide in the upload step.
  - Limit Phase 2 summaries to row counts and date/month hints rather than preview tables or business-logic QA.
patterns-established:
  - Validation returns separate blocking errors and non-blocking warnings with one compact summary payload.
  - Required-column checks mirror the frozen V5 loader expectations for each upload slot.
requirements-completed: [DATA-05]
duration: 3 min
completed: 2026-03-12
---

# Phase 2 Plan 02: Validation Service Summary

**Slot-aware staged-input validation with V5-backed schema checks, warning classification, and compact upload summaries for sales, stock, and SKU/live files**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-12T09:31:32Z
- **Completed:** 2026-03-12T09:34:30Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Added a reusable validation service that accepts staged slot metadata and blocks unsupported formats, unreadable files, and missing required columns.
- Extended the validator with non-blocking warning rules for empty, near-empty, and mixed-month uploads plus compact summary metadata for row counts and date hints.
- Locked the contract down with focused tests covering all three slots, supported formats, blocking-vs-warning behavior, and UI-facing serialization.

## Task Commits

Each task was committed atomically:

1. **Task 1: Encode critical validation rules from the frozen V5 input contract** - `b2f31df` (feat)
2. **Task 2: Add non-blocking warnings and compact upload summaries** - `1ab9880` (feat)
3. **Task 3: Lock the validation contract with focused unit coverage** - `61c35e8` (test)

## Files Created/Modified

- `streamlit_app/services/input_validation.py` - Slot-aware staged-file validation, warning classification, and summary extraction.
- `tests/test_input_validation.py` - Fast unit coverage for critical errors, warnings, supported formats, and UI-facing summary serialization.

## Decisions Made

- Reused the upload-staging metadata shape from Plan `02-01` so the later upload UI can validate already-staged files without duplicating adapter code.
- Treated empty, near-empty, and mixed-month signals as warnings because the Phase 2 decision boundary only blocks schema and readability failures.
- Kept summaries intentionally compact with row counts and date/month hints so this phase does not drift into data-preview or business-QA behavior.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan `02-03` can now reuse one validation service for sales, stock, and SKU/live upload cards instead of repeating slot-specific schema logic in the UI.
Phase `03` can also trust a stable pre-run contract for blocking errors, non-blocking warnings, and compact upload metadata.

## Self-Check: PASSED

- Verified `.planning/phases/02-run-input-workflow/02-02-SUMMARY.md` exists on disk.
- Verified task commits `b2f31df`, `1ab9880`, and `61c35e8` exist in git history.
