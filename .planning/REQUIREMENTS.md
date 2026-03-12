# Requirements: OOS Opportunity Loss Web Workspace

**Defined:** 2026-03-11
**Core Value:** Make monthly opportunity-loss calculation easier to operate from the browser without changing the current V5 business logic.

## v1 Requirements

### Workspace Access And Runtime

- [ ] **OPS-01**: Internal operator can access the workspace from the approved environment
- [ ] **OPS-02**: System stores uploaded files and generated outputs only temporarily for the active run and cleans them up automatically

### Run Input Management

- [ ] **DATA-01**: User can upload a sales-performance file through the web UI for a run
- [ ] **DATA-02**: User can upload a stock snapshot file for a selected calculation month
- [ ] **DATA-03**: User can upload a SKU universe / live-product file for a run
- [ ] **DATA-04**: System applies a bundled site-mapping configuration for the calculation in MVP
- [ ] **DATA-05**: System validates required columns, file type, and parse errors before accepting uploaded run inputs

### Calculation Runs

- [ ] **RUN-01**: User can create a calculation run for a selected month using the files uploaded in that run
- [ ] **RUN-02**: System executes the frozen V5 logic and shows clear success/failure status
- [ ] **RUN-03**: User can rerun by uploading the required files again without relying on stored business history

### Results And QA

- [ ] **RES-01**: User can review summary total, summary by site, summary by SKU, and detail results in the web UI
- [ ] **RES-02**: User can see QA warnings, validation issues, and data-coverage signals before trusting a run
- [ ] **RES-03**: User can see key explainability fields such as baseline source and baseline window
- [ ] **RES-04**: User can export result files in `.xlsx`
- [ ] **RES-05**: User can export result files in `.csv`

## v2 Requirements

### History And Persistence

- **HIST-01**: System persists accepted sales history across months instead of requiring re-upload for every run
- **HIST-02**: User can append only the new month’s sales data to the existing stored history
- **HIST-03**: System detects duplicate sales uploads before they are committed
- **HIST-04**: User can see what sales periods are already stored in history
- **HIST-05**: System stores reusable dataset lineage and version history across runs

### Configuration Management

- **CFG-01**: Admin can update site-mapping configuration without editing bundled app files

### Reporting And Comparison

- **RPT-01**: User can compare one calculation run against another
- **RPT-02**: User can view month-over-month trend dashboards
- **RPT-03**: User can filter and save result views for recurring review

### Workflow And Governance

- **FLOW-01**: User can submit runs for review or approval before publishing
- **FLOW-02**: Managers can approve or reject a calculation run

### Integrations

- **SYNC-01**: System can ingest data directly from upstream operational systems instead of manual upload

## Out of Scope

| Feature | Reason |
|---------|--------|
| Persistent business-data storage in the first release | intentionally deferred until the stateless workflow proves value |
| Rewriting or redefining V5 business logic | current logic is frozen and should be operationalized first |
| Real-time live data sync | managed uploads are the chosen initial operating model |
| Approval-heavy workflow | useful later but not required to solve the immediate workflow pain |
| Dashboard-first BI experience | secondary to upload, run, QA, and export reliability |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| OPS-01 | Phase 1 | Pending |
| OPS-02 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| DATA-05 | Phase 2 | Pending |
| RUN-01 | Phase 3 | Pending |
| RUN-02 | Phase 3 | Pending |
| RUN-03 | Phase 3 | Pending |
| RES-01 | Phase 4 | Pending |
| RES-02 | Phase 4 | Pending |
| RES-03 | Phase 4 | Pending |
| RES-04 | Phase 4 | Pending |
| RES-05 | Phase 4 | Pending |
| HIST-01 | Phase 5 | Deferred |
| HIST-02 | Phase 5 | Deferred |
| HIST-03 | Phase 5 | Deferred |
| HIST-04 | Phase 5 | Deferred |
| HIST-05 | Phase 5 | Deferred |
| CFG-01 | Phase 5 | Deferred |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-11 after stateless MVP scope decision*
