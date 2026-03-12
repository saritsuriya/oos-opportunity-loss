---
phase: 02-run-input-workflow
plan: 01
subsystem: infra
tags: [streamlit, uploads, session-state, staging, pytest]
requires:
  - phase: 01-02
    provides: Per-session workspace roots with dedicated `workspace_input_dir` and `workspace_output_dir`
  - phase: 01-03
    provides: Deployable Streamlit shell with runtime verification in place
provides:
  - Session-scoped upload slot registry for sales, stock, and SKU/live inputs
  - Deterministic per-slot staging paths under `workspace_input_dir`
  - Replace-in-place upload metadata for later validation and UI layers
affects: [02-run-input-workflow, 03-v5-calculation-runs]
tech-stack:
  added: []
  patterns: [session-local upload registry, extension-aware current-file staging]
key-files:
  created: [streamlit_app/services/upload_staging.py, tests/test_input_staging.py]
  modified: [streamlit_app/runtime/session_state.py]
key-decisions:
  - Keep one slot directory per required upload inside `workspace_input_dir` so the wizard and later validators use the same run-local source of truth.
  - Preserve the uploaded file suffix in canonical `current{suffix}` staging paths so downstream loaders retain format hints without storing upload history.
patterns-established:
  - Upload staging writes only inside the active session `workspace_input_dir`.
  - Session state stores slot metadata as `source_name`, `size_bytes`, and `staged_path` instead of keeping raw Streamlit upload objects.
requirements-completed: [DATA-01, DATA-02, DATA-03]
duration: 6 min
completed: 2026-03-12
---

# Phase 2 Plan 01: Session Upload Staging Summary

**Run-scoped upload slot registry with deterministic per-slot staging paths and replace-in-place metadata for sales, stock, and SKU/live files**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-12T09:13:40Z
- **Completed:** 2026-03-12T09:20:03Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments

- Added a reusable upload staging service that defines the three required slots and maps each one into a canonical session-local directory under `workspace_input_dir`.
- Wired session bootstrap to expose the staged-input registry immediately so the upload step and later phases share the same slot contract.
- Locked the staging behavior down with focused tests for session scoping, deterministic paths, replacement semantics, and path-safety guardrails.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create upload slot contracts and canonical session staging paths** - `4012139` (feat)
2. **Task 2: Implement replace-in-place upload staging and metadata extraction** - `4e09ff2` (feat)
3. **Task 3: Harden the staging contract with focused unit coverage** - `f183030` (test)

## Files Created/Modified

- `streamlit_app/services/upload_staging.py` - Slot definitions, deterministic staging paths, registry helpers, and replace-in-place staging writes.
- `streamlit_app/runtime/session_state.py` - Session bootstrap wiring for the shared staged-input registry.
- `tests/test_input_staging.py` - Focused contract coverage for session scoping, replacement behavior, deterministic paths, and workspace safety.

## Decisions Made

- Chose slot-specific subdirectories (`sales`, `stock`, `sku-live`) under `workspace_input_dir` so the filesystem contract stays predictable and later UI/validation code can target stable locations.
- Stored compact upload metadata in session state instead of keeping raw upload handles, which keeps reruns deterministic and avoids tying later layers to Streamlit widget internals.
- Kept canonical filenames as `current{suffix}` to support same-slot replacement while preserving enough format context for downstream parsing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created a temporary virtual environment for test execution**
- **Found during:** Task 1
- **Issue:** The shell did not have `pytest` available, and the system Python rejected direct dependency installation because the environment is externally managed.
- **Fix:** Created `/tmp/oos-plan-0201-venv`, installed `requirements.txt`, and used that interpreter for all plan verification commands.
- **Files modified:** None (environment-only fix)
- **Verification:** `/tmp/oos-plan-0201-venv/bin/python -m pytest -q tests/test_input_staging.py -k session`
- **Committed in:** Not committed (environment-only fix)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope creep. The environment fix was required to execute the plan’s verification commands in the current shell.

## Issues Encountered

None beyond the temporary verification-environment setup that was fixed inline.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

Plan `02-02` can now validate staged upload files against the frozen V5 input contract without inventing a second storage shape.
The upload UI in Plan `02-03` can read a stable session registry for current-file status, metadata summaries, and replace-in-place behavior.

## Self-Check: PASSED

- Verified `.planning/phases/02-run-input-workflow/02-01-SUMMARY.md` exists on disk.
- Verified task commits `4012139`, `4e09ff2`, and `f183030` exist in git history.
