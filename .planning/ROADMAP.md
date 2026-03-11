# Roadmap: OOS Opportunity Loss Web Workspace

## Overview

This roadmap turns the existing V5 script pipeline into an internal web workspace without changing the frozen business logic. The sequence is deliberate: establish product and data foundations first, then solve upload and persistent-history workflow, then operationalize the V5 engine as a managed run service, and only after that build the results UX and optional reporting enhancements.

## Phases

- [ ] **Phase 1: Platform Foundation** - Create the internal web app skeleton, access control, and storage backbone
- [ ] **Phase 2: Dataset Ingestion** - Build managed uploads and validation for run-scoped datasets
- [ ] **Phase 3: Sales History Persistence** - Create append-only sales history with duplicate-safe monthly ingestion
- [ ] **Phase 4: V5 Calculation Runs** - Extract and run the frozen V5 logic as an async backend job
- [ ] **Phase 5: Results Workspace** - Deliver QA review, result exploration, and export workflow in the web UI

## Phase Details

### Phase 1: Platform Foundation
**Goal**: The project has a working internal web/app backend foundation with authenticated access and persistent storage primitives.
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02
**Success Criteria** (what must be TRUE):
  1. Internal users can access the workspace only after authentication
  2. The system has a persistent database and file storage layer ready for datasets and exports
  3. The app scaffold supports separate UI, API, and worker responsibilities
**Plans**: 3 plans

Plans:
- [ ] 01-01: Scaffold frontend, backend, and shared project structure
- [ ] 01-02: Implement authentication and protected internal routes
- [ ] 01-03: Provision database schema baseline and file storage integration

### Phase 2: Dataset Ingestion
**Goal**: Users can upload stock, SKU, and site-map datasets through the browser with schema validation and visible ingestion feedback.
**Depends on**: Phase 1
**Requirements**: DATA-01, DATA-02, DATA-03, DATA-04, DATA-05
**Success Criteria** (what must be TRUE):
  1. User can upload each required dataset type from the web UI
  2. Invalid files are rejected with clear validation feedback
  3. Accepted datasets are stored as versioned records with raw-file lineage
**Plans**: 3 plans

Plans:
- [ ] 02-01: Build dataset models and ingestion endpoints
- [ ] 02-02: Implement schema validation and ingestion warnings
- [ ] 02-03: Build upload and dataset-history UI for run-scoped inputs

### Phase 3: Sales History Persistence
**Goal**: Sales history becomes a persistent append-only dataset with duplicate-safe monthly updates.
**Depends on**: Phase 2
**Requirements**: HIST-01, HIST-02, HIST-03, HIST-04
**Success Criteria** (what must be TRUE):
  1. User can append only a new month of sales data to stored history
  2. Duplicate sales uploads are detected before commit
  3. User can see what history periods are already stored
**Plans**: 3 plans

Plans:
- [ ] 03-01: Define normalized sales-history schema and business keys
- [ ] 03-02: Implement append-only ingest and duplicate-detection logic
- [ ] 03-03: Build sales-history management UI and period visibility

### Phase 4: V5 Calculation Runs
**Goal**: The frozen V5 logic runs asynchronously as a managed backend job using explicit dataset versions.
**Depends on**: Phase 3
**Requirements**: RUN-01, RUN-02, RUN-03
**Success Criteria** (what must be TRUE):
  1. User can create a run for a selected month from the web app
  2. Backend worker executes the V5 logic asynchronously and tracks status
  3. Each run preserves its input lineage, timestamps, and stored outputs
**Plans**: 3 plans

Plans:
- [ ] 04-01: Extract V5 calculation engine from script form into reusable backend code
- [ ] 04-02: Implement async run orchestration and job tracking
- [ ] 04-03: Persist run outputs, warnings, and export artifacts

### Phase 5: Results Workspace
**Goal**: Users can trust, review, and export run results from a browser workflow.
**Depends on**: Phase 4
**Requirements**: RES-01, RES-02, RES-03, RES-04, RES-05
**Success Criteria** (what must be TRUE):
  1. User can view summaries and detail results for a completed run
  2. User can review QA signals and explainability fields before export
  3. User can download `.xlsx` and `.csv` outputs from the app
**Plans**: 3 plans

Plans:
- [ ] 05-01: Build run results pages and summary/detail views
- [ ] 05-02: Build QA and explainability surfaces for trust and troubleshooting
- [ ] 05-03: Implement export generation and download workflow

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Platform Foundation | 0/3 | Not started | - |
| 2. Dataset Ingestion | 0/3 | Not started | - |
| 3. Sales History Persistence | 0/3 | Not started | - |
| 4. V5 Calculation Runs | 0/3 | Not started | - |
| 5. Results Workspace | 0/3 | Not started | - |
