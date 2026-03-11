# Roadmap: OOS Opportunity Loss Web Workspace

## Overview

This roadmap now starts with a stateless MVP. The first goal is not to solve long-term data management; it is to replace the current local script workflow with a browser-based upload, calculate, QA, and export flow using the frozen V5 logic. Persistent storage, append-only sales history, and duplicate-safe monthly ingestion are intentionally deferred until the lean workflow proves useful.

## Phases

- [ ] **Phase 1: Workspace Foundation** - Create the internal web app shell and temporary run workspace
- [ ] **Phase 2: Run Input Workflow** - Build per-run file upload and validation for required inputs
- [ ] **Phase 3: V5 Calculation Runs** - Extract and run the frozen V5 logic from uploaded files
- [ ] **Phase 4: Results Workspace** - Deliver QA review and export workflow in the web UI
- [ ] **Phase 5: Persistence Enhancements** - Add stored history, duplicate protection, and reusable dataset management after MVP

## Phase Details

### Phase 1: Workspace Foundation
**Goal**: The project has a working internal web app foundation with temporary run storage and no persistent business-data layer.
**Depends on**: Nothing (first phase)
**Requirements**: OPS-01, OPS-02
**Success Criteria** (what must be TRUE):
  1. Internal users can open the workspace from the approved environment
  2. The app can create and clean up temporary working folders/files for uploaded run inputs and outputs
  3. The app scaffold supports UI and calculation backend responsibilities in one lean deployable system
**Plans**: 3 plans

Plans:
- [ ] 01-01: Scaffold the web app shell and define the V5 integration boundary
- [ ] 01-02: Implement temporary run workspace handling and cleanup behavior
- [ ] 01-03: Configure lean internal deployment for the chosen host environment

### Phase 2: Run Input Workflow
**Goal**: Users can upload the required run-scoped datasets through the browser with validation feedback.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05
**Success Criteria** (what must be TRUE):
  1. User can upload each required file type from the web UI for a run
  2. Invalid files are rejected with clear validation feedback
  3. Valid files are staged only for the active run and do not require persistent history
**Plans**: 3 plans

Plans:
- [ ] 02-01: Build upload endpoints and temporary file models for run inputs
- [ ] 02-02: Implement schema validation and ingestion warnings
- [ ] 02-03: Build upload UI for sales, stock, SKU, and site-mapping files

### Phase 3: V5 Calculation Runs
**Goal**: The frozen V5 logic runs from uploaded files inside the web workflow and returns a completed run result.
**Depends on**: Phase 2
**Requirements**: RUN-01, RUN-02, RUN-03
**Success Criteria** (what must be TRUE):
  1. User can create a run for a selected month from the web app
  2. Backend executes the V5 logic and returns success or failure clearly
  3. User can rerun by uploading the required files again without relying on stored business history
**Plans**: 3 plans

Plans:
- [ ] 03-01: Extract V5 calculation engine from script form into reusable backend code
- [ ] 03-02: Implement run orchestration, error handling, and session-visible status
- [ ] 03-03: Generate temporary result artifacts for downstream review and export

### Phase 4: Results Workspace
**Goal**: Users can trust, review, and export run results from a browser workflow.
**Depends on**: Phase 3
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05
**Success Criteria** (what must be TRUE):
  1. User can view summaries and detail results for a completed run
  2. User can review QA signals and explainability fields before export
  3. User can download `.xlsx` and `.csv` outputs from the app
**Plans**: 3 plans

Plans:
- [ ] 04-01: Build run results pages and summary/detail views
- [ ] 04-02: Build QA and explainability surfaces for trust and troubleshooting
- [ ] 04-03: Implement export generation and download workflow

### Phase 5: Persistence Enhancements
**Goal**: The product evolves beyond the stateless MVP by adding stored history and duplicate-safe monthly ingestion.
**Depends on**: Phase 4
**Requirements**: HIST-01, HIST-02, HIST-03, HIST-04, HIST-05
**Success Criteria** (what must be TRUE):
  1. Sales history persists across months instead of being re-uploaded every run
  2. Duplicate monthly sales uploads are detected before commit
  3. Users can see stored history coverage and reusable dataset lineage
**Plans**: 3 plans

Plans:
- [ ] 05-01: Define persistent data model and business keys for stored history
- [ ] 05-02: Implement append-only ingest and duplicate-detection logic
- [ ] 05-03: Build stored-history and dataset-management UI

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Workspace Foundation | 0/3 | Not started | - |
| 2. Run Input Workflow | 0/3 | Not started | - |
| 3. V5 Calculation Runs | 0/3 | Not started | - |
| 4. Results Workspace | 0/3 | Not started | - |
| 5. Persistence Enhancements | 0/3 | Deferred | - |
