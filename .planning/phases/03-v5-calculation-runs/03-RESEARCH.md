# Phase 3: V5 Calculation Runs - Research

**Date:** 2026-03-12  
**Status:** Ready for planning

## Objective

Research how to implement the frozen V5 run flow inside the existing Streamlit wizard while preserving the stateless MVP boundary, the bundled site-mapping rule, and the operator decisions captured in Phase 3 context.

## Codebase Findings

### Existing browser/runtime seam to reuse
- `streamlit_app/ui/upload_inputs.py` already leaves a trustworthy pre-run contract in session state: staged upload metadata, validation results, and `UPLOAD_STEP_READINESS_KEY`.
- `streamlit_app/runtime/session_state.py` already persists session-local state across Streamlit reruns and exposes `workspace_input_dir` plus `workspace_output_dir`.
- `streamlit_app/runtime/temp_workspace.py` already gives deterministic per-session filesystem roots, which is the correct place to write the workbook and CSV artifacts created by a run.
- `streamlit_app/services/v5_boundary.py` already exposes the frozen V5 modules via `load_frozen_v5_symbols()` and already has `build_run_blueprint(...)` as the natural place to centralize run paths.

### Existing V5 execution contract
- `v5_daily_oos_opportunity/main.py` shows the current browser-equivalent run contract clearly: `InputPaths`, `DataLoaderV5`, `DailyOOSOpportunityV5`, `ModelConfig`, and `ReporterV5`.
- The CLI builds one evaluation month at a time and uses `eval_year` + `eval_month` plus staged file paths; this matches the Phase 3 scope well.
- The frozen V5 path already writes one workbook and a fixed set of CSVs through `ReporterV5.generate(...)`; Phase 3 should treat that output set as the completion signal for a successful run.
- The current CLI exposes extra controls such as `orders_actual`, `baseline_months`, and `fallback_months`, but the browser scope deliberately does not surface those yet.

### Output artifact shape
- `ReporterV5.generate(...)` writes:
  - workbook: `OOS_Opportunity_Lost_<period>_V5.xlsx`
  - detail CSV
  - summary by site CSV
  - summary by SKU CSV
  - summary total CSV
  - QA summary CSV
- This means Phase 3 can produce a structured artifact manifest without inventing new filenames or new output formats.

## Streamlit Research

### Session and rerun model
- `st.session_state` is the correct place for run-month selection, active run status, last successful run payload, and failure details because Streamlit reruns the script on interaction but preserves per-session state.
- The explicit run-button decision fits Streamlit’s normal interaction model well: operator clicks once, the run service executes, and the resulting state is written back into session state for the next rerun to display.

### Run feedback primitives
- `st.spinner` is the lightest primitive for a synchronous in-request run and gives immediate operator feedback that work is active.
- `st.status` can support a richer status block if planning decides the run step benefits from a persistent progress/result container instead of only success/error banners.
- Because the MVP is single-user and stateless, Phase 3 does not need background queues or persistent job tracking to satisfy the current scope.

### App testing posture
- Streamlit AppTest can continue to verify the run step at the browser-shell level, including month suggestion display, explicit run initiation, success/failure rendering, and readiness-gated navigation.
- Service-level execution should still be covered with plain pytest unit tests so the run path stays fast to verify without relying only on AppTest.

## Recommended Phase Shape

### Plan 03-01: reusable V5 run service
- Extend the existing V5 boundary with helpers that translate staged session inputs into a concrete V5 run request.
- Add a reusable run service that calls the frozen V5 modules directly instead of shelling out to the CLI.
- Return a structured result that includes selected month, output workbook path, generated CSV paths, and summary metadata the UI can reuse later.

### Plan 03-02: session-local orchestration and status
- Add a session-state contract for idle/running/succeeded/failed run states plus the selected or suggested month.
- Wrap the raw run service with orchestration that captures exceptions, preserves rerun semantics, and keeps the run step deterministic across reruns.
- Keep reruns inside the same session by reusing the staged files unless the operator replaces them in Phase 2.

### Plan 03-03: real run-step UI
- Replace the `run-v5` placeholder in the wizard shell with a dedicated UI module.
- Show the suggested month with override controls, a compact recap of staged inputs, an explicit `Run V5` action, and a success/failure summary that stays on the same step.
- Surface the generated artifact set only as a readiness/handoff summary for Phase 4, not as the full review/export UX yet.

## Risks and Guardrails

### Scope risks
- Recreating the CLI in the browser with many advanced flags would overrun the frozen-V5 posture decided in context.
- Jumping straight into review tables or download controls would blur the Phase 3 / Phase 4 boundary.
- Adding asynchronous job infrastructure now would overbuild the MVP relative to the current single-run session workflow.

### Implementation guardrails
- Call the frozen Python modules directly; do not add a subprocess wrapper around `main.py`.
- Keep all generated artifacts inside the active session `workspace_output_dir`.
- Preserve the current V5 default model behavior: same data loader expectations, same analyzer defaults, same reporter outputs.
- Treat the upload-step readiness contract as the run precondition instead of inventing a second validation path.

## Validation Architecture

Phase 3 should use a three-layer test strategy:

- **Unit tests for the extracted run service**: verify suggested month inference from staged stock data, output path construction, successful V5 execution against representative staged files, and structured failure capture.
- **Unit tests for orchestration/session contracts**: verify idle/running/succeeded/failed transitions, rerun behavior with unchanged staged files, and handling of operator month overrides.
- **Streamlit AppTest coverage for the run step**: verify suggested month display, explicit `Run V5` initiation, success/failure summaries that stay on the run step, and gating/handoff behavior toward the next wizard step.

Suggested fast feedback commands for planning:

- `pytest -q tests/test_run_execution.py`
- `pytest -q tests/test_run_workflow.py`
- `pytest -q tests/test_run_step_ui.py`
- `pytest -q`

## Planning Implications

- One plan should create the reusable run-service seam behind the existing V5 boundary.
- One plan should capture run orchestration, session status, and rerun behavior without touching Phase 4 review scope.
- One plan should wire the `run-v5` step into the wizard shell and expose only the run-step success/failure summary and artifact handoff needed for downstream review/export.

## Sources

- Streamlit `st.session_state`: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Streamlit `st.spinner`: https://docs.streamlit.io/develop/api-reference/status/st.spinner
- Streamlit `st.status`: https://docs.streamlit.io/develop/api-reference/status/st.status
- Streamlit App Testing: https://docs.streamlit.io/develop/concepts/app-testing/get-started
