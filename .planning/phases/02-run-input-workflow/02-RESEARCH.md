# Phase 2: Run Input Workflow - Research

**Date:** 2026-03-12  
**Status:** Ready for planning

## Objective

Research how to implement the Phase 2 upload workflow inside the existing Streamlit wizard while preserving the stateless MVP boundary, the bundled site-mapping rule, and the frozen V5 input constraints.

## Codebase Findings

### Existing foundation to reuse
- `streamlit_app/ui/wizard.py` already reserves a single `upload-inputs` step inside the wizard shell, so Phase 2 should extend the current shell instead of introducing a second navigation model.
- `streamlit_app/runtime/session_state.py` already creates a stable `session_id` plus `workspace_input_dir` and `workspace_output_dir` for the active session.
- `streamlit_app/runtime/temp_workspace.py` already gives deterministic session workspaces, which is the correct place to stage uploaded files and replace them per slot.
- `streamlit_app/services/v5_boundary.py` already knows the bundled site-mapping path and can surface that same source of truth to the upload step.

### Existing V5 input contract
- Sales/orders are the loosest input: `DataLoaderV5.load_orders()` supports Excel (`.xlsx`, `.xlsm`, `.xls`) and the current UTF-16 TSV export format.
- Daily stock is stricter: `load_daily_stock()` expects CSV with `posting_date`, `site_code`, `article_code`, and `stock_balance`.
- Product/SKU live is stricter: `load_product_universe()` expects CSV with `skuNo`, and optionally `productName` plus `status`.
- Site mapping is already bundled and should stay outside the upload path for this phase.

## Streamlit Research

### Upload interaction model
- `st.file_uploader` is the correct widget for per-file uploads, supports file-type filtering, and returns `UploadedFile` objects as file-like objects or bytes. This fits the need to immediately stage files into the session workspace after upload.
- The widget limit is governed by `server.maxUploadSize`; the project already set that to `200` MB in `.streamlit/config.toml`, so Phase 2 can rely on the existing baseline rather than inventing custom size handling first.
- Streamlit forms batch widget submission. Because the user chose immediate per-file validation instead of a final combined submit, the upload cards should favor direct uploaders plus session-state updates over wrapping the whole screen in one `st.form`.

### State and replace behavior
- Streamlit session state is the correct place to track per-slot metadata such as current staged path, upload status, critical errors, warnings, and file summary.
- Because reruns are a normal part of Streamlit interaction, the staging layer should write uploaded bytes to deterministic slot paths in `workspace_input_dir` so "replace current file" stays predictable across reruns.

### Feedback and visibility
- Streamlit already has the primitives needed for the requested UX: `st.success`, `st.warning`, `st.error`, `st.caption`, `st.expander`, and card-like column layouts.
- The "useful summary" decision fits a compact metadata panel rather than a full table preview. That keeps scope aligned with validation and staging instead of drifting into result exploration.

## Recommended Phase Shape

### Upload card responsibilities
- Each input card should own: accepted formats, current staged file, immediate validation status, warnings, and a compact file summary.
- The upload step as a whole should own: overall readiness state for the three required files, bundled site-mapping summary, and the rule that only critical errors block moving forward.

### Validation split
- **Envelope validation:** file presence, supported extension, readable parse, required columns, and basic row-count sanity. These should run in Phase 2.
- **Ingestion warnings:** empty-but-readable rows, date parse gaps, unexpected month/date hints, duplicate-looking keys, or unusual stock/site patterns. These should be visible but not blocking.
- **Business logic validation:** anything requiring actual V5 execution belongs later, not in this phase.

### Staging contract
- Stage each slot into a canonical path under `workspace_input_dir`, for example `orders/current.*`, `daily_stock/current.csv`, and `product/current.csv`.
- Persist a metadata structure in session state that includes the staged path, source filename, byte size, detected row count, and validation status.
- Replacement should overwrite the staged slot and replace its metadata atomically inside the session.

## Risks and Guardrails

### Scope risks
- A rich preview table would quickly turn Phase 2 into an analyst UI rather than an upload workflow.
- Supporting arbitrary file formats beyond the current V5 contract would create parser complexity before the end-to-end runner exists.
- Upload history or multi-version file management would break the stateless MVP boundary and should stay deferred.

### Implementation guardrails
- Keep all staged files inside the existing session workspace. Do not add a second temp root.
- Reuse the V5 loader column expectations as the validation truth so Phase 2 and Phase 3 do not diverge.
- Reuse `get_boundary_overview()` or adjacent boundary helpers for bundled site-mapping presentation rather than reading unrelated files directly in the UI.

## Validation Architecture

Phase 2 should use a mixed test strategy:

- **Unit tests for staging helpers**: verify slot replacement, canonical staging paths, metadata extraction, and cleanup-safe behavior without loading the UI.
- **Unit tests for validation services**: verify supported formats, required-column checks, blocking-versus-warning classification, and summary extraction against small fixture files.
- **Streamlit AppTest coverage for the upload step**: verify the three-card layout, bundled site-mapping summary, readiness state, and surfaced critical/warning messages without requiring the full V5 run flow.

Suggested fast feedback commands for planning:

- `pytest -q tests/test_input_staging.py`
- `pytest -q tests/test_input_validation.py`
- `pytest -q tests/test_upload_step_ui.py`
- `pytest -q`

## Planning Implications

- One plan should establish the reusable upload/staging primitives and session metadata contract.
- One plan should encode validation rules and warnings directly from the frozen V5 input schema.
- One plan should wire the Streamlit upload UI into the existing wizard shell and show bundled site-mapping context plus upload summaries.

## Sources

- Streamlit `st.file_uploader`: https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- Streamlit `st.form`: https://docs.streamlit.io/develop/api-reference/execution-flow/st.form
- Streamlit `st.session_state`: https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- Streamlit `server.maxUploadSize`: https://docs.streamlit.io/develop/api-reference/configuration/config.toml#server
- Streamlit App Testing: https://docs.streamlit.io/develop/concepts/app-testing/get-started
