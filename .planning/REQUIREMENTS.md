# Requirements: OOS Opportunity Loss Web Workspace

**Defined:** 2026-03-11
**Core Value:** Make monthly opportunity-loss calculation reliable, explainable, and operationally easy without changing the current V5 business logic.

## v1 Requirements

### Access

- [ ] **AUTH-01**: Internal user can sign in to the workspace with an authorized account
- [ ] **AUTH-02**: Unauthenticated users cannot access dataset, run, or export pages

### Dataset Management

- [ ] **DATA-01**: User can upload a sales-performance file through the web UI
- [ ] **DATA-02**: User can upload a stock snapshot file for a selected calculation month
- [ ] **DATA-03**: User can upload a SKU universe / live-product file for a run
- [ ] **DATA-04**: User can upload or manage a site-mapping file used by the calculation
- [ ] **DATA-05**: System validates required columns, file type, and parse errors before accepting a dataset

### Sales History

- [ ] **HIST-01**: System persists accepted sales history across months instead of requiring full-history re-upload
- [ ] **HIST-02**: User can append only the new month’s sales data to the existing persisted history
- [ ] **HIST-03**: System detects duplicate sales uploads before they are ingested
- [ ] **HIST-04**: User can see what sales periods are already stored in history

### Calculation Runs

- [ ] **RUN-01**: User can create a calculation run for a selected month using explicit dataset versions
- [ ] **RUN-02**: System executes the frozen V5 logic asynchronously and shows run status
- [ ] **RUN-03**: Each run stores dataset lineage, timestamps, and outcome status

### Results And QA

- [ ] **RES-01**: User can review summary total, summary by site, summary by SKU, and detail results in the web UI
- [ ] **RES-02**: User can see QA warnings, validation issues, and data-coverage signals before trusting a run
- [ ] **RES-03**: User can see key explainability fields such as baseline source and baseline window
- [ ] **RES-04**: User can export result files in `.xlsx`
- [ ] **RES-05**: User can export result files in `.csv`

## v2 Requirements

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
| External client-facing access | v1 is an internal ops workspace |
| Rewriting or redefining V5 business logic | current logic is frozen and should be operationalized first |
| Real-time live data sync | managed uploads are the chosen v1 operating model |
| Approval-heavy workflow | useful later but not required to solve the immediate workflow pain |
| Dashboard-first BI experience | secondary to upload, run, QA, and export reliability |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| DATA-04 | Phase 2 | Pending |
| DATA-05 | Phase 2 | Pending |
| HIST-01 | Phase 3 | Pending |
| HIST-02 | Phase 3 | Pending |
| HIST-03 | Phase 3 | Pending |
| HIST-04 | Phase 3 | Pending |
| RUN-01 | Phase 4 | Pending |
| RUN-02 | Phase 4 | Pending |
| RUN-03 | Phase 4 | Pending |
| RES-01 | Phase 5 | Pending |
| RES-02 | Phase 5 | Pending |
| RES-03 | Phase 5 | Pending |
| RES-04 | Phase 5 | Pending |
| RES-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-11*
*Last updated: 2026-03-11 after initial definition*
