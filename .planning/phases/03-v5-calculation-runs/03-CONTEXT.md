# Phase 3: V5 Calculation Runs - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 3 delivers the browser-side execution flow for the frozen V5 calculation using the run-scoped files already staged in the active session. It covers month selection for the run, explicit run initiation, session-local execution status, success or failure feedback, and rerun behavior within the same session. It does not yet deliver full result browsing, QA review surfaces, or download/export UX beyond preparing the run artifacts for Phase 4.

</domain>

<decisions>
## Implementation Decisions

### Run month selection
- The run step should suggest the evaluation month from the uploaded stock file when it can be derived confidently.
- The operator must still be able to override the suggested month and year before running.
- Phase 3 should not fully hide the month selector, and it should not force a separate manual-only month-picking flow if a sensible suggestion is available.

### Run initiation
- The frozen V5 run should start only when the operator clicks an explicit `Run V5` action in the run step.
- Entering the run step should not auto-start execution.
- Phase 3 should not add a second confirmation dialog before running unless planning uncovers a strong reason within scope.

### Rerun behavior
- Within the same session, the operator can rerun using the current staged files without uploading them again.
- If the operator wants different inputs, they should go back to the upload step and replace the staged files there, then return to rerun.
- Phase 3 should not force a full re-upload for every rerun in the same session.

### Run outcome feedback
- After the run finishes, keep the operator on the run step and show a clear success or failure summary there.
- Do not auto-advance to `Review And Export` on success.
- The run step should make the next action obvious: proceed to review when successful, or adjust inputs / rerun when unsuccessful.

### Frozen V5 configuration posture
- Keep the browser run aligned to the frozen V5 defaults rather than exposing advanced model tuning in this phase.
- The operator-facing run controls should stay focused on the evaluation month and the already-staged inputs.
- Phase 3 should not add browser controls for baseline window tuning, site-mapping replacement, or optional extra order-file variants unless those are already required by the existing staged-input workflow.

### Claude's Discretion
- Exact wording and layout of the run summary, failure messaging, and rerun call-to-action
- Whether the run step shows a compact input recap above the run button or alongside the status area
- How progress is phrased during execution, as long as the operator can tell the run is active and whether it succeeded or failed
- Exact form of the suggested-month explanation when the stock file implies a calculation period

</decisions>

<specifics>
## Specific Ideas

- The run step should feel like a controlled handoff from upload validation into calculation, not like a new mini-app with many settings.
- Suggesting the run month from the stock snapshot is desirable because the stock file is the strongest signal for the calculation period, but the operator still wants the ability to correct it.
- "Stay with summary" means the operator should see what happened immediately on the run step, then choose when to move into the next step.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `streamlit_app/ui/upload_inputs.py`: already computes `UPLOAD_STEP_READINESS_KEY` and keeps the staged upload registry plus validation results in session state, which Phase 3 can use as the pre-run gate.
- `streamlit_app/services/upload_staging.py`: already gives deterministic session-local file paths for the three required inputs, so Phase 3 can build the V5 run from filesystem paths instead of raw widget objects.
- `streamlit_app/services/input_validation.py`: already mirrors the frozen V5 input contract and can be reused to confirm staged inputs remain valid before execution.
- `streamlit_app/services/v5_boundary.py`: already exposes `load_frozen_v5_symbols()` and `build_run_blueprint(...)`, which are the natural seam for calling the frozen V5 loader, analyzer, and reporter without going through the CLI entrypoint.
- `streamlit_app/runtime/session_state.py` and `streamlit_app/runtime/temp_workspace.py`: already provide session workspace paths for staging inputs and writing run outputs.
- `v5_daily_oos_opportunity/main.py`: shows the existing CLI shape for `InputPaths`, `ModelConfig`, output naming, and the current V5 defaults for baseline windows.

### Established Patterns
- The app remains a step-by-step Streamlit wizard with navigation gated by shared session state, not a free-form dashboard.
- Uploaded files are staged to the session workspace first, then reused from stable filesystem paths.
- Site mapping remains bundled system config and is already surfaced from the V5 boundary as read-only context.
- Phase 2 already separated blocking validation from warnings, so Phase 3 should inherit that run-readiness posture rather than inventing a second validation mode.

### Integration Points
- The `run-v5` wizard step in `streamlit_app/ui/wizard.py` is still a placeholder and should become the entry point for the Phase 3 run UI.
- The staged files in `workspace_input_dir` should feed into `InputPaths` through `build_run_blueprint(...)` or a nearby boundary helper rather than reconstructing path logic in the UI.
- Run outputs should be written into the active session `workspace_output_dir` so Phase 4 can pick them up for review and export.
- Phase 3 needs a session-visible run status payload that the wizard can read for active/running/success/failure states and for rerun behavior.

### Current V5 Run Constraints
- `v5_daily_oos_opportunity/main.py` currently expects `orders`, `daily_stock`, `site_map`, `product`, `eval_year`, `eval_month`, and optional `output`.
- The frozen V5 CLI also has `--baseline-months`, `--fallback-months`, and `--orders-actual`, but the current browser upload workflow does not expose those as staged inputs or operator controls.
- The reporter already generates the workbook plus CSV artifacts into an output folder, which Phase 3 can treat as the completion condition for a successful run.

</code_context>

<deferred>
## Deferred Ideas

- Advanced browser controls for baseline windows, optional extra order files, or alternate run modes
- Auto-starting the calculation when the operator enters the run step
- Auto-advancing directly into the review/export step after success
- Cancellation, background queues, or persistent run history

</deferred>

---
*Phase: 03-v5-calculation-runs*
*Context gathered: 2026-03-12*
