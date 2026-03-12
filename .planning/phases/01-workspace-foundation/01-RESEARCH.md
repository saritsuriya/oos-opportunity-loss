# Phase 1: Workspace Foundation - Research

**Date:** 2026-03-12
**Status:** Complete

## Research Question

What does the planner need to know to implement a lean Phase 1 foundation for a stateless internal MVP using the frozen V5 calculation logic?

## Key Findings

### 1. Streamlit is the best fit for this phase

Why it fits:
- The current repo is Python-only and has no existing frontend or backend application structure.
- The user explicitly wants a lean internal MVP and the team already has familiarity with tools "like Streamlit".
- Streamlit provides the core primitives this phase needs without forcing premature backend architecture:
  - file uploads via `st.file_uploader`
  - session-scoped state via `st.session_state`
  - download delivery via `st.download_button`
  - multipage/navigation support if the app grows later
  - server configuration through `config.toml`

Relevant official docs:
- https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state
- https://docs.streamlit.io/develop/api-reference/widgets/st.download_button
- https://docs.streamlit.io/develop/concepts/multipage-apps/overview
- https://docs.streamlit.io/develop/api-reference/configuration/config.toml#server

### 2. Phase 1 should create a wrapper, not re-architect V5

The existing V5 pipeline is already clean enough to wrap:
- `DataLoaderV5` validates and normalizes inputs
- `DailyOOSOpportunityV5` runs the core logic
- `ReporterV5` materializes workbook and CSV outputs

The current problem is not the model logic. It is the lack of an app runtime around it.

Planning implication:
- Phase 1 should define the app shell and runtime boundary only
- It should not yet implement the full upload + calculate workflow from later phases
- A thin integration seam should be created so later phases can call V5 from app code without going through the CLI entrypoint

### 3. Temporary file staging is required even for a no-storage MVP

The current V5 modules are file-path-driven.
Even if the app is "stateless", uploaded files still need to be staged to temporary filesystem locations so the existing loader/reporter flow can operate safely.

Planning implication:
- create a per-session workspace root under a temp directory
- separate uploaded inputs from generated outputs
- clean up per-session artifacts after the active flow ends
- add a scheduled cleanup pass for abandoned sessions

### 4. Internal browser URL is the right deployment baseline

The user chose:
- normal internal browser URL
- no login in Phase 1
- Windows server hosting

Planning implication:
- deployment should optimize for one internal app instance reachable by the team
- do not spend Phase 1 scope on identity management
- keep deployment assets simple: run command, config file, startup/service wrapper, and operator instructions

### 5. Current data sizes do not block a Streamlit MVP

Observed local input sizes are still reasonable for this phase:
- daily stock CSV around 39-42 MB per month
- orders file around 31 MB
- product file around 6 MB
- site mapping is tiny

Streamlit's default `server.maxUploadSize` is 200 MB per file, so current source files fit comfortably inside default limits.

Planning implication:
- no custom large-file architecture is needed in Phase 1
- upload constraints should still be validated explicitly and surfaced clearly in the UI

### 6. The main Phase 1 risks are operational, not algorithmic

Key risks:
- mixing Phase 1 foundation work with Phase 2 upload workflow or Phase 3 execution logic
- temp file collisions across simultaneous sessions
- leaving deployment instructions implicit because the repo has no dependency manifest today
- introducing a second logic path instead of wrapping V5 consistently

Planner should bias toward:
- a small app skeleton
- one runtime path
- clear temp-workspace utilities
- explicit deployment/config bootstrap

## Planning Guidance

The roadmap already splits Phase 1 into the correct three concerns:

1. `01-01` app shell and V5 integration boundary
2. `01-02` temp workspace and cleanup primitives
3. `01-03` internal deployment baseline on the chosen host environment

Recommended sequencing:
- Wave 1: scaffold the Streamlit app, app state boundary, and reusable runtime utilities
- Wave 2: temp workspace lifecycle and cleanup behavior
- Wave 3: deployment/config hardening and operator runbook

## Validation Architecture

Recommended validation approach for this phase:

- Test framework: `pytest`
- App-level smoke coverage: Streamlit `AppTest`
- Utility-level coverage: direct unit tests for temp workspace helpers and config resolution
- Manual checks remain necessary for internal-network reachability and Windows-host startup behavior

Relevant official docs:
- https://docs.streamlit.io/develop/concepts/app-testing/get-started
- https://fastapi.tiangolo.com/tutorial/request-files/ (useful only if the project later evolves beyond Streamlit; not needed in this phase)

Validation expectations by concern:
- app shell boots without crashing
- session initialization works
- temp workspace is created per session and cleaned when requested
- bundled site mapping is discoverable as app config, not run upload
- deployment config supports internal access on the target host

## Recommendation

Plan Phase 1 as a true foundation phase for a Streamlit-based internal MVP:
- build the shell
- establish temp runtime primitives
- establish deployment/config baseline

Do not pull upload parsing, run orchestration, or persistent storage into this phase.
