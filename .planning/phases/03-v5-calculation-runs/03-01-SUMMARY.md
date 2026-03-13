---
phase: 03-v5-calculation-runs
plan: 01
subsystem: backend
tags: [streamlit, v5, execution, outputs, pytest]
requires:
  - phase: 02-03
    provides: Trusted staged upload registry, validation results, and readiness gating from the wizard shell
provides:
  - Structured frozen V5 run request built from staged session inputs and the selected evaluation month
  - Direct Python execution path for the frozen V5 modules without the CLI entrypoint
  - Structured run result with generated workbook and CSV artifact paths under the active session workspace
affects: [03-v5-calculation-runs, 04-results-workspace]
tech-stack:
  added: [streamlit_app/services/run_execution.py]
  patterns: [direct module execution, typed run request/result contract, output-workspace artifact manifest]
key-files:
  created: [streamlit_app/services/run_execution.py, tests/test_run_execution.py]
  modified: [streamlit_app/services/v5_boundary.py]
key-decisions:
  - Keep the browser run path inside Python module boundaries instead of invoking the CLI script as a subprocess.
  - Treat the workbook plus fixed CSV set as the canonical artifact manifest for a successful Phase 3 run.
patterns-established:
  - The V5 run request is derived from the staged session files, bundled site mapping, and selected evaluation month.
  - The run service returns a structured success/failure payload that later orchestration and UI layers can reuse.
requirements-completed: [RUN-01, RUN-02]
duration: 3 min
completed: 2026-03-13
---

# Phase 3 Plan 01: Frozen V5 Run Service Summary

**Reusable frozen V5 execution seam with suggested-month helpers, direct module invocation, and structured artifact metadata for the session workspace**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-13T10:56:55+07:00
- **Completed:** 2026-03-13T10:59:23+07:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Extended the V5 boundary with typed run-request and artifact contracts that map the staged session files plus the selected month into a concrete frozen V5 execution request.
- Added a reusable `run_execution` service that infers a suggested month from the staged stock file, executes the frozen V5 Python modules directly, and records the workbook plus CSV outputs into the active session workspace.
- Locked the run-service contract down with focused unit tests for month suggestion, request construction, successful execution, and structured success payload serialization.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build the run-request contract and suggested-month helpers** - `f641b9a` (feat)
2. **Task 2: Execute the frozen V5 modules directly and return a structured run result** - `1e5b890` (feat)
3. **Task 3: Harden the run-service contract with focused unit coverage** - `8a08fb1` (test)

## Files Created/Modified

- `streamlit_app/services/v5_boundary.py` - Adds typed run request and artifact helpers aligned to the frozen V5 output naming contract.
- `streamlit_app/services/run_execution.py` - Resolves staged session inputs, suggests an evaluation month from stock data, executes the frozen V5 modules directly, and returns structured run results.
- `tests/test_run_execution.py` - Covers month suggestion, request construction, successful execution, artifact generation, and serialized payload shape.

## Decisions Made

- Reused the staged upload registry from Phase 2 instead of introducing a second run-input adapter for the browser flow.
- Kept execution purely in-process against the frozen Python modules so the app can reason about errors and artifacts without a subprocess boundary.
- Treated the workbook and fixed CSV set from `ReporterV5` as the success condition and handoff contract for later phases.

## Deviations from Plan

None. The direct execution seam, artifact contract, and test coverage all matched the planned scope.

## Issues Encountered

None.

## User Setup Required

None. The service uses the staged files and bundled site mapping already available inside the active session workspace.

## Next Phase Readiness

Plan `03-02` can now orchestrate run-state transitions and rerun behavior around one structured execution service instead of rebuilding V5 invocation logic.
The later run-step UI can read a stable success/failure payload plus artifact manifest from the browser runtime.

## Self-Check: PASSED

- Verified `./.venv/bin/pytest -q tests/test_run_execution.py` passes.
- Verified task commits `f641b9a`, `1e5b890`, and `8a08fb1` exist in git history.
