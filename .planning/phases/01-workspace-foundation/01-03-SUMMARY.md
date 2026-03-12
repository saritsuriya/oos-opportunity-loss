---
phase: 01-workspace-foundation
plan: 03
subsystem: infra
tags: [streamlit, windows, powershell, pytest, deployment]
requires:
  - phase: 01-01
    provides: Bootable Streamlit app entrypoint and frozen-V5 shell boundary
  - phase: 01-02
    provides: Session temp workspace and reusable stale-cleanup helpers
provides:
  - Internal-hosting Streamlit runtime configuration for the Windows baseline
  - Windows startup and cleanup scripts that target the real app and cleanup artifacts
  - Phase 1 deployment runbook with explicit manual host setup steps
affects: [02-run-input-workflow, 03-v5-calculation-runs, 04-results-workspace]
tech-stack:
  added: []
  patterns: [Windows script wrappers around Streamlit CLI, scheduled reuse of shared cleanup helpers]
key-files:
  created:
    [
      .streamlit/config.toml,
      scripts/run_streamlit.ps1,
      scripts/cleanup_temp_workspace.py,
      scripts/cleanup_temp_workspace.ps1,
      docs/phase-01-deployment.md,
      tests/test_deploy_config.py,
    ]
  modified: [tests/test_deploy_config.py]
key-decisions:
  - Keep the startup script foreground-oriented so Windows service or scheduled-task wrappers can own the process without another launcher.
  - Reuse the Phase 1 runtime cleanup helpers through a thin CLI wrapper instead of duplicating stale-workspace logic in a separate deployment script.
  - Leave the final public host name and port as operator-supplied startup parameters instead of baking environment-specific values into repo config.
patterns-established:
  - Internal-host deployment relies on repo-root `.streamlit/config.toml` plus a PowerShell wrapper that passes the browser-facing host and port.
  - Scheduled cleanup runs the same Python cleanup path the app runtime uses for stale session workspaces.
requirements-completed: [OPS-01]
duration: 10 min
completed: 2026-03-12
---

# Phase 1 Plan 03: Workspace Foundation Summary

**Windows-hosted Streamlit deployment baseline with explicit runtime config, startup and cleanup scripts, and an operator runbook**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-12T05:05:13Z
- **Completed:** 2026-03-12T05:15:13Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Added explicit Streamlit hosting defaults for the internal Windows baseline, including headless runtime, network binding, and upload/message sizing.
- Wrapped the app startup path and stale-workspace cleanup path in Windows-facing PowerShell scripts that target real repo artifacts.
- Documented the Phase 1 deployment workflow and locked it down with deploy-focused smoke coverage.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Streamlit runtime configuration for internal hosting** - `ce30dba` (feat)
2. **Task 2: Create startup and cleanup scripts for the Windows deployment path** - `a284fbb` (feat)
3. **Task 3: Write the operator deployment runbook** - `b0b0d0f` (docs)

## Files Created/Modified

- `.streamlit/config.toml` - Internal-hosting Streamlit defaults for headless runtime, port binding, and upload sizing.
- `scripts/run_streamlit.ps1` - Foreground startup wrapper for the real Streamlit entrypoint and browser-facing host parameters.
- `scripts/cleanup_temp_workspace.py` - Python CLI that reuses shared stale-workspace cleanup behavior from Plan `01-02`.
- `scripts/cleanup_temp_workspace.ps1` - Windows Scheduled Task wrapper for the Python cleanup entrypoint.
- `docs/phase-01-deployment.md` - Phase 1 Windows deployment runbook with host preparation, URL shape, cleanup schedule, and manual setup steps.
- `tests/test_deploy_config.py` - Deployment smoke checks for config, script targets, cleanup behavior, and runbook coverage.

## Decisions Made

- Kept `server.address = "0.0.0.0"` in the repo baseline and pushed the chosen browser-visible host name into `scripts/run_streamlit.ps1` so the same build can move between internal hosts without editing config.
- Left the deployment baseline stateless and internal-only, with no new auth or persistence expansion beyond the Phase 1 boundary.
- Defaulted scheduled cleanup to `24` hours so abandoned session workspaces are pruned nightly without tightening the active-session contract from Plan `01-02`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added repo-root import bootstrapping to the deploy smoke test**
- **Found during:** Task 2
- **Issue:** `pytest -q tests/test_deploy_config.py -k scripts` failed during collection because `streamlit_app` was not importable from the new test module.
- **Fix:** Inserted the repo root into `sys.path` before importing `streamlit_app.runtime.temp_workspace`.
- **Files modified:** `tests/test_deploy_config.py`
- **Verification:** `./.venv/bin/pytest -q tests/test_deploy_config.py -k scripts`
- **Committed in:** `a284fbb`

**2. [Rule 1 - Bug] Normalized Windows path literals in the PowerShell wrappers**
- **Found during:** Task 2
- **Issue:** The initial wrapper scripts used doubled backslashes inside literal path segments, which made the deployment smoke assertion fail and was noisier than a native Windows command path.
- **Fix:** Rewrote the PowerShell literals to use standard Windows separators for `.streamlit`, `.venv`, and `scripts` paths.
- **Files modified:** `scripts/run_streamlit.ps1`, `scripts/cleanup_temp_workspace.ps1`
- **Verification:** `./.venv/bin/pytest -q tests/test_deploy_config.py -k scripts`
- **Committed in:** `a284fbb`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** No scope creep. Both fixes were required to keep the new deployment verification executable and the Windows wrappers clean.

## Issues Encountered

None beyond the Task 2 verification issues that were fixed inline.

## User Setup Required

- Choose the final Windows host name, internal DNS alias, and service port.
- Create the Windows service or startup task that runs `scripts/run_streamlit.ps1`.
- Open the required Windows Firewall or internal network rule for the chosen port.
- Create the nightly scheduled task that runs `scripts/cleanup_temp_workspace.ps1`.

## Next Phase Readiness

Phase `02-run-input-workflow` can now build upload staging against a deployable Streamlit host instead of a local-only shell.
The temp-workspace cleanup contract is preserved end-to-end, and the site-mapping baseline remains bundled and documented without widening Phase 1 into persistence or authentication work.

## Self-Check: PASSED

- Verified `.planning/phases/01-workspace-foundation/01-03-SUMMARY.md` exists on disk.
- Verified task commits `ce30dba`, `a284fbb`, and `b0b0d0f` exist in git history.
