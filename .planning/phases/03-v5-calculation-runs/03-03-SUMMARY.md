---
phase: 03-v5-calculation-runs
plan: 03
subsystem: ui
tags: [streamlit, wizard, run-step, app-test, rerun]
requires:
  - phase: 03-02
    provides: Session-local run workflow payload with statuses, selected month, rerun semantics, and stale-input detection
provides:
  - Dedicated `run-v5` step with suggested month, override controls, and explicit execution
  - Same-step success/failure feedback plus rerun guidance
  - Wizard gating that only allows review/export after a successful run for the current staged inputs
affects: [03-v5-calculation-runs, 04-results-workspace]
tech-stack:
  added: [streamlit_app/ui/run_v5.py]
  patterns: [wizard-step module extraction, outcome-on-same-step UX, AppTest service stubbing]
key-files:
  created: [streamlit_app/ui/run_v5.py, tests/test_run_step_ui.py]
  modified: [streamlit_app/ui/wizard.py]
key-decisions:
  - Keep the run step lean: suggested month, month override, explicit `Run V5`, and immediate outcome messaging only.
  - Keep operators on the run step after completion instead of auto-advancing into review/export.
  - Disable forward navigation when staged inputs changed after the last successful run so stale outputs cannot be reviewed accidentally.
patterns-established:
  - Browser-level tests patch the run service at the UI seam so run-step behavior is covered without invoking the full frozen V5 pipeline.
  - The wizard shell reads the shared run payload to control both run-step rendering and forward navigation.
requirements-completed: [RUN-01, RUN-02, RUN-03]
duration: 7 min
completed: 2026-03-13
---

# Phase 3 Plan 03: Run Step UI Summary

**Real run-step UI for suggested-month review, explicit frozen V5 execution, same-step outcomes, and stale-input-aware navigation**

## Performance

- **Duration:** 7 min
- **Started:** 2026-03-13T11:08:00+07:00
- **Completed:** 2026-03-13T11:15:00+07:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Replaced the Phase 1 placeholder with a dedicated run-step UI that shows staged-input context, suggested evaluation month, and explicit run controls.
- Kept success and failure feedback on the same step with clear next actions for rerun or review/export.
- Wired the wizard navigation to the shared run payload so operators cannot continue to review stale or incomplete results.

## Wave Commit

- **Wave 3 implementation:** `c1e7eb0` `feat(03-03): build run-step UI`

## Files Created/Modified

- `streamlit_app/ui/run_v5.py` - Renders the run-step controls, suggestion guidance, outcome state, and rerun messaging.
- `streamlit_app/ui/wizard.py` - Routes the `run-v5` step to the new UI module and gates forward navigation on a fresh successful run.
- `tests/test_run_step_ui.py` - Covers month suggestion visibility, explicit execution, success/failure outcomes, and rerun behavior through Streamlit AppTest.

## Decisions Made

- Used a clear `Run V5` action instead of auto-running when the operator lands on the step.
- Surfaced workbook readiness and next-step guidance immediately after success so the operator never has to guess what happened.
- Warned when staged inputs changed after a successful run and forced rerun before review/export.

## Deviations from Plan

None. The UI stayed within the agreed scope and deferred full result browsing to Phase 4.

## Issues Encountered

None.

## User Setup Required

None.

## Next Phase Readiness

Phase 4 now receives a trustworthy completed-run state and artifact handoff from the wizard instead of a placeholder run step.

## Self-Check: PASSED

- Verified `./.venv/bin/pytest -q tests/test_run_step_ui.py` passes.
- Verified commit `c1e7eb0` exists in git history.
