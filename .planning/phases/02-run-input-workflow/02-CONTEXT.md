# Phase 2: Run Input Workflow - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 2 delivers the browser workflow for collecting the run-scoped input files needed by the frozen V5 model. It covers upload interactions, validation feedback, bundled site-mapping visibility, and temporary staging into the active session workspace. It does not yet execute V5, persist business history, or show result outputs.

</domain>

<decisions>
## Implementation Decisions

### Upload step structure
- Keep the Phase 1 guided wizard shell and implement Phase 2 inside the existing `Upload Inputs` step.
- Show the three required inputs on one screen as separate upload cards for sales, stock, and SKU/live files.
- Each upload card should show its own current status so operators can complete the input set in one place rather than through nested substeps.

### Validation behavior
- Block progress only on critical validation failures such as unreadable files, missing required columns, and unsupported file types.
- Non-critical findings should be shown as visible warnings without blocking the operator from moving forward.
- Uploaded files should be validated as soon as they are provided rather than waiting for a final "submit all" step.

### Re-upload and staging rules
- If the user uploads a replacement file for the same slot in the same session, keep only the latest file for that slot.
- Phase 2 should continue to stage files only inside the per-session temporary workspace created in Phase 1.
- The upload step should not introduce persistence, version history, or multi-file selection for the same slot in this phase.

### Input format posture
- Match the practical input formats that the frozen V5 pipeline already accepts instead of forcing a new export format now.
- Phase 2 should preserve compatibility with the current sales-file behavior and the existing CSV-based stock and product inputs.
- Validation should explain the accepted format expectations in operator-facing terms rather than exposing raw parser assumptions.

### Bundled site-mapping visibility
- Site mapping remains system-owned bundled configuration and is not uploaded by the user.
- The upload step should show a read-only summary that bundled site mapping is active, along with a concise summary of the mapped sites / virtual sites.
- The site-mapping summary is informational only in this phase; editing or replacing it stays out of scope.

### Upload confirmation detail
- After a valid upload, show a useful operator summary rather than just a success badge.
- The summary should include file name, file size, detected row count, and key date/month hints where those are available.
- The upload step should stop short of a full data preview table unless the planner finds a lightweight reason to add one within scope.

### Claude's Discretion
- Exact card layout, copywriting, spacing, and status styling inside the upload step
- Exact wording for critical errors versus warnings
- How much of the file summary is shown inline versus behind expanders
- Whether validation runs automatically on upload or via an explicit "validate" action inside each card, as long as the behavior still feels immediate

</decisions>

<specifics>
## Specific Ideas

- The operator should be able to complete all three uploads from one screen, not bounce through a second wizard inside the upload step.
- "Useful summary" means a quick sanity check after upload, not a full analyst-style data browser.
- The accepted-format posture should follow the current V5 pipeline so the web workflow does not force business users to change their existing exports before the calculation flow is working end to end.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `streamlit_app/ui/wizard.py`: already contains the Phase 2 placeholder location inside the wizard shell and should become the entry point for the upload UI.
- `streamlit_app/runtime/session_state.py`: already tracks the current wizard step and stores session workspace paths that Phase 2 can reuse for run-scoped staging.
- `streamlit_app/runtime/temp_workspace.py`: provides deterministic session workspace roots with dedicated `inputs/` and `outputs/` directories.
- `streamlit_app/services/v5_boundary.py`: exposes the bundled site-mapping path and the frozen V5 module boundary that later phases will call after uploads are staged.
- `streamlit_app/runtime/cleanup.py` and `scripts/cleanup_temp_workspace.py`: already define the stateless cleanup contract that Phase 2 must preserve.

### Established Patterns
- The app shell is a step-by-step wizard in Streamlit, not a multi-page dashboard or sidebar-first workspace.
- Uploaded artifacts must stay within the active session workspace; Phase 1 explicitly avoided any persistent business-data layer.
- Site mapping is already presented as bundled system configuration in the foundation shell and should stay read-only in Phase 2.

### Integration Points
- New upload components should write staged files into `workspace_input_dir` from session state.
- Validation results should prepare clean, run-scoped input metadata that Phase 3 can use to decide whether the frozen V5 run is ready.
- The upload step should surface bundled site-mapping status from `get_boundary_overview()` rather than inventing a second source of truth.

### Current V5 Input Constraints
- `v5_daily_oos_opportunity/data_loader_v5.py` expects sales/orders with `Purchase Date`, `Sku`, `stock`, `Quantity`, `Gross`, `Net`, and `Product Name`.
- The current sales loader supports Excel formats (`.xlsx`, `.xlsm`, `.xls`) and the UTF-16 tab-separated export format.
- The daily stock loader expects CSV input with `posting_date`, `site_code`, `article_code`, and `stock_balance`.
- The product/SKU loader expects CSV input with at least `skuNo`, with optional `productName` and `status`.
- Site mapping stays bundled and expects `Virtual Location`, `Site`, and `Active`, but Phase 2 does not expose site-mapping upload.

</code_context>

<deferred>
## Deferred Ideas

- Pulling sales, stock, or SKU/live directly from Databricks instead of user upload
- Persistent upload history, duplicate detection, or reusable stored datasets
- Site-mapping download, editing, or admin management UI
- Rich table previews or analyst-style data exploration inside the upload step

</deferred>

---
*Phase: 02-run-input-workflow*
*Context gathered: 2026-03-12*
