# Phase 4: Results Workspace - Research

**Date:** 2026-03-13  
**Status:** Complete

## Research Goal

Answer what the planner needs to know to implement a browser-based results workspace for the frozen V5 run artifacts without changing the stateless MVP shape or the frozen business logic.

## What Already Exists

Phase 3 already established the critical seam:

- `streamlit_app/services/run_workflow.py` stores the completed-run payload in session state.
- `streamlit_app/services/run_execution.py` returns the workbook path, CSV artifact paths, row counts, and headline lost-value metric.
- `streamlit_app/ui/run_v5.py` keeps the user on the run step and tells them to continue to review/export after success.
- `v5_daily_oos_opportunity/reporter_v5.py` already generates:
  - `Summary Total`
  - `Summary by Site`
  - `Summary by SKU`
  - `Detail SKU Site`
  - `QA Summary`
  - `QA Unmapped SiteCode`
  - `Definitions`
  - `Calculation Example`
  - matching CSV exports for detail, summary-site, summary-SKU, summary-total, and QA summary

This means Phase 4 does not need a second calculation path. It needs a read-only browser layer over files that already exist in the active session workspace.

## Recommended Implementation Shape

### 1. Add a lightweight result-loading service

Phase 4 should not read artifact files directly inside the UI module. Add a service layer that:

- accepts the completed-run payload from session state
- validates that required artifact paths still exist
- loads result tables from CSV where possible
- loads workbook-only sheets only when needed
- returns a structured browser-facing payload for:
  - overview metrics
  - summary total
  - summary by site
  - summary by SKU
  - detail
  - QA summary
  - unmapped sites
  - definitions
  - calculation example
  - export manifest

This keeps the UI thin and makes Phase 4 testable without rerunning the calculation.

### 2. Prefer CSV-first for browser tables

Use the generated CSV files as the primary browser data source when the artifact exists:

- `*_summary_total.csv`
- `*_summary_site.csv`
- `*_summary_sku.csv`
- `*_detail.csv`
- `*_qa_summary.csv`

This is simpler and cheaper than reading everything from Excel.

Only the following currently require workbook reads or a new service seam:

- `QA Unmapped SiteCode`
- `Definitions`
- `Calculation Example`

The easiest Phase 4 path is:

- keep CSV-backed tables for the main result tabs
- read workbook-only sheets lazily when the QA/trust tab is opened

### 3. Build the results step as one tabbed page

The Phase 4 context already locked the layout:

- overview first
- tabs inside one page
- lightweight detail browsing
- dedicated export tab

The practical tab set is:

- `Overview`
- `By Site`
- `By SKU`
- `Detail`
- `QA And Trust`
- `Export`

Using `st.tabs` is a good fit here. Current Streamlit docs say tab content is computed by default, but tracked tabs can rerun and expose the active tab through `.open`, which allows lazy rendering for heavier content like detail tables or workbook reads. Source: Streamlit `st.tabs` docs, version `1.55.0` [link](https://docs.streamlit.io/develop/api-reference/layout/st.tabs).

Implication for planning:

- results loading should separate cheap overview data from heavier detail/workbook reads
- the UI can render expensive tabs conditionally if tracked tabs are used

### 4. Use `st.dataframe`, not `st.data_editor`

The detail table is for review, not editing.

`st.dataframe` is the right primitive because it provides an interactive table for browsing and supports `column_config`, sizing, selection hooks, and non-edit use. Source: Streamlit `st.dataframe` docs, version `1.55.0` [link](https://docs.streamlit.io/develop/api-reference/data/st.dataframe).

`st.data_editor` is the wrong default here because:

- the phase is read-only
- editable tables introduce accidental workflow ambiguity
- unsupported/mixed dtypes create unnecessary surface area

Source: Streamlit `st.data_editor` docs, version `1.55.0` [link](https://docs.streamlit.io/develop/api-reference/data/st.data_editor).

Implication for planning:

- implement read-only browser tables with `st.dataframe`
- use `column_config` to improve readability for money, ratios, counts, and dates
- avoid editable result views in this phase

### 5. Keep overview metrics separate from deep tables

The run payload already exposes:

- `detail_row_count`
- `qa_summary_row_count`
- `unmapped_site_count`
- `lost_value_net_raw`
- artifact paths

The results workspace can combine those with `summary_total` to produce the overview block without loading every table at first render.

This supports the locked UI direction:

- headline totals
- trust signal
- then drill into tabs

### 6. Treat QA as visible but non-blocking

Phase 4 should surface trust issues strongly without creating a new approval gate.

Browser trust signals should merge:

- upload-step warnings still present in session state
- current run status / stale-input state from `run_workflow`
- `QA Summary` table
- unmapped site rows if any

Recommended trust model:

- top banner in overview
- compact counts in overview
- deeper QA tab with definitions and calculation example

This aligns with the phase context and keeps approval/governance out of scope.

### 7. Use direct file download actions, but keep memory in mind

The export tab can use `st.download_button` with the already-generated workbook and CSV files.

Current Streamlit docs note:

- data passed to `st.download_button` is stored in memory while the user is connected
- keeping payload sizes under a couple hundred MB is recommended
- buttons can be wrapped to avoid unnecessary reruns if needed

Source: Streamlit `st.download_button` docs, version `1.55.0` [link](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button).

Implication for planning:

- use existing generated files rather than building new export payloads in memory
- for this project size, direct file-backed download actions are acceptable
- expose one prominent workbook action and separate CSV actions by artifact name/type

## Open Technical Choices For Planning

These are still planner choices, not user decisions:

### Workbook-only sheet access

Two reasonable options:

1. Read workbook-only sheets directly in a result-loading service using `pandas.read_excel`.
2. Extend the run-result service seam to emit additional CSV or serialized files for unmapped sites, definitions, and calculation example.

Recommendation:

- For Phase 4, read workbook-only sheets in the result-loading service.
- Do not reopen Phase 3 just to add more export artifacts unless implementation finds workbook reads unstable or slow.

Reason:

- lowest scope expansion
- preserves the current reporter contract
- good enough for a stateless internal MVP

### Detail table scale

The detail export can be tens of thousands of rows. The browser detail view should stay useful without becoming a full data grid project.

Recommendation:

- support lightweight browsing in Phase 4
- allow a manageable view with column selection or compact filters only if they stay simple
- push deep analysis to exported files

Do not plan:

- advanced query builders
- saved filters
- editable tables
- cross-tab linked filtering systems

### Data caching

Because results are session-local files and users may switch tabs repeatedly, a small caching layer around artifact reads is worthwhile.

Recommendation:

- cache parsed artifacts by file path and modification time
- invalidate automatically when a new run replaces the files

This keeps repeated tab visits fast without introducing persistence.

## Suggested Service Split

The likely clean split for planning is:

- `results_loader.py`
  - load artifact manifest from run payload
  - validate file existence
  - read CSV-backed result tables
  - read workbook-only trust sheets
  - return typed/structured result view model

- `review_results.py`
  - render overview
  - render tabbed sections
  - render export actions

- targeted tests
  - service tests for artifact loading, missing files, workbook-sheet fallback
  - AppTest coverage for overview, QA banner, tab rendering, and export actions

## Risks To Account For In Planning

### 1. Missing artifact drift

If a run payload says success but files were cleaned up or replaced, the review step must fail clearly.

Plan implication:

- add artifact-existence checks up front
- show operator-friendly error with rerun guidance

### 2. Workbook-only QA content

Definitions and calculation example are not currently exported as separate CSVs.

Plan implication:

- either lazy-read workbook sheets or explicitly defer those parts
- do not accidentally omit them, because Phase 4 context locked them into the browser trust flow

### 3. Overbuilding the detail browser

It is easy to drift into BI-tool behavior.

Plan implication:

- keep browser detail browsing lightweight
- optimize for trust and operational review, not analyst-grade exploration

### 4. Rerun / stale state coupling

Phase 3 already blocks navigation when inputs change after success. Phase 4 must respect that contract instead of independently deciding result freshness.

Plan implication:

- all result loading should begin from the Phase 3 run payload
- do not invent a second “current run” source of truth

## Testing Direction

The repo already uses:

- `pytest`
- `streamlit.testing.v1.AppTest`

That is enough for Phase 4.

Recommended test layers:

- service-level tests for loading summary/detail/QA/export manifests from artifact files
- failure-path tests for missing artifacts or workbook-only sheet problems
- AppTest coverage for:
  - overview-first render
  - visible QA banner
  - detail tab render
  - export tab buttons and labels
  - review step behavior when artifacts are missing or stale

## Validation Architecture

### Test stack

- Continue with `pytest` and `streamlit.testing.v1.AppTest`
- No Wave 0 testing bootstrap is needed; the infrastructure already exists

### Fast feedback expectations

- service tests should stay fast and file-based
- AppTest coverage should be focused on review/export behavior, not full V5 execution
- full suite runtime should remain close to the current baseline

### Required verification coverage

At minimum, planning should cover:

1. artifact-loading service reads summary/detail/QA/export data from a completed run
2. missing or stale artifacts produce clear review-step errors
3. overview shows headline totals and QA/trust signal
4. detail tab shows explainability columns in the browser
5. export tab exposes workbook plus named CSV actions

## Planning Guidance

The cleanest Phase 4 shape is likely three plans:

1. artifact/result loading service
2. overview/detail/QA browser workspace
3. export tab and final review-step polish

This keeps the dependency order natural:

- service seam first
- browser review surfaces second
- export and full review workflow last

## Recommendation Summary

Plan Phase 4 as a read-only browser layer over Phase 3 artifacts.

Key planning principles:

- do not rerun V5 in the review step
- do not invent persistence
- prefer CSV-first reads for browser tables
- lazy-read workbook-only trust sheets
- keep detail browsing useful but intentionally lightweight
- use strong but non-blocking QA/trust surfacing
- expose direct downloads from generated files in a dedicated export tab

---

Research completed for Phase 4 planning on 2026-03-13.
