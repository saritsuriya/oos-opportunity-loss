# OOS Opportunity Loss Web Workspace

## What This Is

An internal web application for the operations team to run the OOS opportunity-loss calculation using the frozen V5 business logic. It replaces the current script-and-files workflow with a managed upload, append, validate, calculate, QA, and export experience so users can operate the process from the browser without re-uploading full history every month.

## Core Value

Make monthly opportunity-loss calculation reliable, explainable, and operationally easy without changing the current V5 business logic.

## Requirements

### Validated

- ✓ Calculate opportunity loss from local sales, stock, product, and site-mapping files using versioned Python pipelines — existing
- ✓ Export detailed Excel and CSV outputs with summaries and QA sheets — existing
- ✓ Use V5 as the current daily-stock model with rolling baseline and fallback window logic — existing

### Active

- [ ] Internal ops users can upload source files through a web UI instead of running local scripts
- [ ] Sales history is stored persistently so future months only need delta uploads, not full-history re-uploads
- [ ] The system detects duplicate monthly sales uploads before they corrupt the persisted history
- [ ] Users can upload the calculate-month stock snapshot and the SKU universe / live-product file for each run
- [ ] Users can run the frozen V5 logic as a managed calculation job with visible run status
- [ ] Users can review QA warnings and input coverage before trusting the result
- [ ] Users can export result files in `.xlsx` and `.csv`
- [ ] Optional dashboards can summarize outputs, but the primary v1 focus is the operational run workflow

### Out of Scope

- External client or partner access — v1 is an internal ops tool first
- Direct ERP/API synchronization — start with managed file uploads and leave system integrations for later
- Redefining the V5 business logic — the current logic is intentionally frozen for this phase
- Full approval/governance workflow — useful later, but not the first release priority

## Context

The existing repository is a brownfield analytics codebase with multiple script generations. `v5_daily_oos_opportunity/` is the current source of truth for business logic, but it still operates as a local CLI pipeline over CSV/XLSX files and local output folders. The main operational pain point is that sales-performance history should accumulate across months instead of being uploaded from scratch every period, while stock snapshot and SKU-universe inputs remain run-specific. The future product must preserve trust in the output by making data lineage, validation, and QA visible to users.

## Constraints

- **Business Logic**: Preserve the current V5 formula and assumptions — the team wants the web app to operationalize the current model, not change it
- **Users**: Internal operations team only for v1 — optimize for expert internal workflow rather than public-product polish
- **Data Flow**: Managed uploads with persistent history — monthly sales should be append-only with duplicate protection
- **Output**: Excel export is mandatory — users still need `.xlsx` as a business deliverable
- **Architecture**: Brownfield extraction from scripts — calculation logic should be extracted from the current Python pipeline instead of rewritten blindly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use V5 as the canonical calculation model | Current team has frozen the logic and wants the product built on top of it | — Pending |
| Build internal web workspace first | Main need is operational ease for internal users, not external productization | — Pending |
| Persist sales history and append deltas monthly | Removes repeated full-history uploads and matches the team’s stated operating model | — Pending |
| Keep stock snapshot and SKU universe as run-scoped uploads | These inputs are tied to the calculation month and should remain explicit per run | — Pending |
| Prioritize workflow over dashboards in v1 | The first pain to solve is upload/validate/run/export reliability | — Pending |

---
*Last updated: 2026-03-11 after initialization*
