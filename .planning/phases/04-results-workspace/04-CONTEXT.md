# Phase 4: Results Workspace - Context

**Gathered:** 2026-03-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 4 delivers the browser workspace for reviewing and exporting the results of a completed frozen V5 run. It covers how summary outputs, row-level detail, QA signals, explainability fields, and download actions are presented inside the existing wizard. It does not add persistent run history, run-to-run comparison, approval workflow, or new calculation logic.

</domain>

<decisions>
## Implementation Decisions

### Results layout
- Keep the existing wizard and make `Review And Export` an overview-first results step rather than a new free-form dashboard.
- The results workspace should use tabs inside one page rather than a long scroll or side-navigation layout.
- The first view should be a compact overview that leads into deeper result tabs for summary tables, detail, QA, and exports.
- The top overview area should emphasize headline totals plus a visible QA/trust signal before users drill into deeper tabs.

### Detail browsing
- Phase 4 should include a browsable on-screen detail table rather than forcing operators into export-only review.
- The detail experience should stay lightweight and fit the stateless MVP; the goal is practical browser review, not a full analyst workbench.
- The browser detail view should surface key explainability columns directly in the main table instead of hiding them behind export-only workflows.

### QA and trust posture
- QA should be strong but non-blocking: show a visible warning banner when QA issues or coverage risks exist, but do not require an explicit acknowledgment gate in this phase.
- The overview should show upload warnings, key QA summary signals, and unmapped-site counts before users drill into deeper QA content.
- Definitions and the calculation example should be available inside a QA-oriented tab rather than always visible in the overview.

### Explainability defaults
- The browser detail experience should expose key explainability fields by default, including baseline source, baseline window, recorded days, OOS days, and actual quantity.
- Explainability should help operators understand why a row has loss, not just what the loss number is.
- Phase 4 should not add advanced model-tuning controls or alternative formulas; it should explain the frozen V5 behavior already implemented.

### Export flow
- Downloads should live in a dedicated export tab within the results workspace, not as the primary focus of the overview area.
- The export tab should present one prominent workbook download plus separate CSV downloads for the generated artifacts.
- Each download action should show the filename and artifact type, but the export tab should stay lightweight rather than becoming a metadata-heavy file manager.

### Claude's Discretion
- Exact tab labels, ordering, and visual density inside the results workspace
- Exact wording and severity styling for QA banners and summary cards
- Which result tabs use metrics, tables, or expanders as long as the locked layout and trust posture stay intact
- Whether small ranking snippets appear in the overview, so long as headline totals plus QA remain the primary first-screen focus

</decisions>

<specifics>
## Specific Ideas

- The browser result flow should feel like a controlled continuation of Phase 3, not a separate BI tool.
- "Overview first" means the user should land on totals and trust signals before seeing deeper site/SKU/detail tables.
- "Browsable table" means operators can inspect row-level results on screen before exporting, but the UI should stay lean enough for internal monthly operations work.
- Definitions and the worked calculation example are still valuable in the browser, but they belong in a trust-oriented area rather than occupying the first screen.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `streamlit_app/ui/wizard.py`: already owns the `review-results` step location and the navigation gate from the `run-v5` step.
- `streamlit_app/services/run_workflow.py`: already stores the completed-run payload, current-period selection, stale-input detection, and structured status that Phase 4 can read instead of rebuilding result state.
- `streamlit_app/services/run_execution.py`: already returns structured artifact paths, detail row counts, QA row counts, and total lost value for a completed run.
- `streamlit_app/ui/run_v5.py`: already shows the successful-run summary and can hand off users into `Review And Export` after a valid run with current staged inputs.
- `v5_daily_oos_opportunity/reporter_v5.py`: already generates the workbook sheets and CSV outputs that Phase 4 should surface: `Summary Total`, `Summary by Site`, `Summary by SKU`, `Detail SKU Site`, `QA Summary`, `QA Unmapped SiteCode`, `Definitions`, and `Calculation Example`.

### Established Patterns
- The app remains a step-by-step Streamlit wizard, not a persistent multi-page analytics suite.
- Results are session-local and tied to the active run; Phase 4 should not assume history, storage, or cross-run comparison.
- Site mapping remains bundled system config and is already reflected inside the generated outputs.
- Phase 3 already blocks review navigation when staged inputs changed after the last successful run, so Phase 4 can trust that review/export represents the current run artifacts.

### Integration Points
- The `review-results` branch in `streamlit_app/ui/wizard.py` is still a placeholder and should become the entry point for the Phase 4 UI.
- Phase 4 should read the last successful run payload from session state and the artifact paths under `workspace_output_dir`.
- The results workspace will need to load generated CSV outputs and possibly workbook metadata from the active session workspace without rerunning V5.
- Export actions should hand off the existing generated files rather than regenerating outputs through a second calculation path.

### Current Result Constraints
- `ReporterV5` writes separate CSV files for detail, summary-by-site, summary-by-SKU, summary-total, and QA summary, plus a workbook containing those outputs and supporting sheets.
- `V5RunResult` currently records detail row count, QA row count, unmapped site count, total lost value net, workbook path, and CSV artifact paths, but not the actual table contents.
- The `QA Unmapped SiteCode`, `Definitions`, and `Calculation Example` sheets exist only in the workbook today, so Phase 4 must decide whether to derive browser views from workbook reads or add a lightweight service seam around those artifacts during implementation.

</code_context>

<deferred>
## Deferred Ideas

- Comparing one run against another or browsing historical runs
- Saved filters, reusable result views, or dashboard-style trend analysis
- Approval / acknowledgment workflows before export
- Persistent export archives or shared download history
- Direct Databricks-backed result browsing instead of the stateless session workspace

</deferred>

---
*Phase: 04-results-workspace*
*Context gathered: 2026-03-13*
