# Phase 1: Workspace Foundation - Context

**Gathered:** 2026-03-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 1 delivers the internal app foundation for the stateless MVP: a browser-accessible workspace, the initial operator shell, and temporary runtime primitives for uploaded files and generated exports. It does not yet deliver persistent data storage, monthly history management, or the full calculation workflow itself.

</domain>

<decisions>
## Implementation Decisions

### Operator access
- Host the MVP on the Windows server and let the team open it through a normal internal browser URL.
- Do not require login for Phase 1 while the app remains an internal-only tool on the internal network.
- Do not optimize for VPN-only access or server-local-only usage in this phase.

### App foundation and shell
- Use Streamlit as the Phase 1 framework for the MVP foundation.
- The default operator experience should be a guided step-by-step wizard, not a sidebar-heavy workspace or a bare utility page.
- Favor low-friction delivery and team familiarity over a more flexible but heavier custom web stack in this phase.

### Temporary runtime handling
- Use per-session temporary working folders/files for uploaded run inputs and generated exports.
- Add a nightly cleanup job as a safety net for abandoned sessions or missed cleanup paths.
- Keep the MVP stateless: do not retain business datasets beyond the active session in Phase 1.

### Claude's Discretion
- Exact wizard step labels and layout details
- Visual styling and density within the Streamlit shell
- Read-only presentation of bundled site-mapping configuration in the app shell
- Exact Windows process/service wrapper and cleanup scheduler implementation

</decisions>

<specifics>
## Specific Ideas

- The team has used tools "something like Streamlit before", so familiarity and ease of deployment matter.
- Operators should "access normally", which is interpreted as opening a standard internal browser URL rather than using RDP or a special VPN-only flow.
- Shell design was delegated to Claude, with a step-by-step wizard chosen as the default direction.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `v5_daily_oos_opportunity/data_loader_v5.py` `DataLoaderV5`: already validates and normalizes orders, daily stock, product, and site-mapping inputs.
- `v5_daily_oos_opportunity/analyzer_v5.py` `DailyOOSOpportunityV5`: current source-of-truth calculation engine for V5 business logic.
- `v5_daily_oos_opportunity/reporter_v5.py` `ReporterV5`: already writes the required `.xlsx` workbook plus summary/detail CSV outputs.
- `v5_daily_oos_opportunity/data_loader_v5.py` `InputPaths` and `v5_daily_oos_opportunity/analyzer_v5.py` `ModelConfig`: usable boundary objects for passing staged file paths and run configuration into the existing pipeline.

### Established Patterns
- The live calculation code is Python-only and organized as `main -> data loader -> analyzer -> reporter`.
- The current runtime is file-path-driven and batch-oriented; the web foundation will need to stage temp files and call the existing modules rather than rely on in-memory-only inputs.
- There is no existing frontend app, backend service, dependency manifest, or packaged Python module yet; Phase 1 will establish the first user-facing runtime layer.

### Integration Points
- The Streamlit shell should stage uploaded files into temporary paths, then feed those paths into the current V5 loader/analyzer/reporter flow.
- Generated workbook and CSV outputs should be produced through `ReporterV5.generate(...)` and surfaced back through the app as downloads.
- Bundled site mapping should continue to flow through `DataLoaderV5.load_site_mapping()` so the MVP stays aligned with existing V5 behavior.

</code_context>

<deferred>
## Deferred Ideas

- Persistent sales-history storage and duplicate-safe monthly append flow
- Admin-managed site-mapping maintenance outside bundled app files
- Individual user accounts or stronger authentication
- Dashboarding, run comparison, and broader reporting UX

</deferred>

---
*Phase: 01-workspace-foundation*
*Context gathered: 2026-03-12*
