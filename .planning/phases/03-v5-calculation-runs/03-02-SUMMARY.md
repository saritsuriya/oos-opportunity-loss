---
phase: 03-v5-calculation-runs
plan: 02
subsystem: backend
tags: [streamlit, session-state, orchestration, rerun, pytest]
requires:
  - phase: 03-01
    provides: Structured frozen V5 run request, month suggestion helpers, and direct module execution
provides:
  - Session-backed run orchestration payload with idle, running, succeeded, and failed states
  - Selected-month state, pre-run gating, structured failure capture, and rerun support inside one browser session
  - Input-signature tracking so later phases can detect stale successful runs after uploads change
affects: [03-v5-calculation-runs, 04-results-workspace]
tech-stack:
  added: [streamlit_app/services/run_workflow.py]
  patterns: [session-backed orchestration state, upload-readiness gating reuse, rerun-safe staged-input signatures]
key-files:
  created: [streamlit_app/services/run_workflow.py, tests/test_run_workflow.py]
  modified: [streamlit_app/runtime/session_state.py]
key-decisions:
  - Keep one structured run payload in session state instead of scattering status and selection fields across widget keys.
  - Reuse the Phase 2 upload-readiness contract as the run precondition instead of duplicating validation logic in Phase 3.
  - Track the last successful input signature so the wizard can block stale review navigation after staged files change.
patterns-established:
  - The run step, later result-review phases, and wizard navigation all read the same session-local run payload.
  - Rerun uses the current staged files in place, even when the slot path stays constant and only file metadata changes.
requirements-completed: [RUN-01, RUN-02, RUN-03]
duration: 8 min
completed: 2026-03-13
---

# Phase 3 Plan 02: Run Workflow Summary

**Session-local orchestration layer for selected-month state, execution gating, structured failures, and same-session reruns**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T11:00:00+07:00
- **Completed:** 2026-03-13T11:08:00+07:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added a reusable run-workflow service that turns the raw frozen V5 execution seam into a session-safe orchestration contract.
- Extended session bootstrap so every browser session owns one structured run payload with selected month, suggestion, preconditions, result payload, and failure details.
- Locked rerun behavior, month override, status transitions, and structured error capture behind focused unit coverage.

## Wave Commit

- **Wave 2 implementation:** `14c0cfc` `feat(03-02): add session-local run workflow`

## Files Created/Modified

- `streamlit_app/services/run_workflow.py` - Session-local orchestration helpers for run readiness, month selection, execution, rerun, and failure handling.
- `streamlit_app/runtime/session_state.py` - Seeds the shared run workflow payload during app bootstrap.
- `tests/test_run_workflow.py` - Covers suggestion sync, blocking preconditions, month override, rerun semantics, and failure capture.

## Decisions Made

- Preserved the frozen V5 defaults by limiting browser-side orchestration to selected month and staged-input state.
- Treated changed staged-file metadata as a stale-run signal so review/export remains blocked until the operator reruns.
- Stored structured failure details instead of raw tracebacks so the run step can explain what failed without exposing internals.

## Deviations from Plan

None. The session contract, rerun handling, and test coverage matched the planned scope.

## Issues Encountered

- A first rerun assertion incorrectly expected a different staged file path. The actual design intentionally replaces files in place, so the test was corrected to verify updated current-file metadata instead.

## User Setup Required

None.

## Next Phase Readiness

Plan `03-03` can now render a real run step and reuse the same session payload for month selection, explicit run initiation, same-step outcomes, and rerun guidance.

## Self-Check: PASSED

- Verified `./.venv/bin/pytest -q tests/test_run_workflow.py` passes.
- Verified commit `14c0cfc` exists in git history.
