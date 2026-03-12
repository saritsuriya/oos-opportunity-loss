# OOS Opportunity Loss Web Workspace

## What This Is

An internal web application for the operations team to run the OOS opportunity-loss calculation using the frozen V5 business logic. The first delivery is intentionally lean: users upload the required files for a run, execute the calculation from the browser, review QA, and export results without introducing persistent business-data storage yet.

## Core Value

Make monthly opportunity-loss calculation easier to operate from the browser without changing the current V5 business logic.

## Requirements

### Validated

- ✓ Calculate opportunity loss from local sales, stock, product, and site-mapping files using versioned Python pipelines — existing
- ✓ Export detailed Excel and CSV outputs with summaries and QA sheets — existing
- ✓ Use V5 as the current daily-stock model with rolling baseline and fallback window logic — existing

### Active

- [ ] Internal ops users can upload the required run files through a web UI instead of running local scripts
- [ ] Users can run the frozen V5 logic from the browser for a selected month using run-scoped inputs
- [ ] Users can review QA warnings and key explainability fields before trusting the result
- [ ] Users can export result files in `.xlsx` and `.csv`
- [ ] The app uses temporary run files only for the active job and does not yet persist business history across months
- [ ] Site mapping is bundled as a system configuration in the MVP and is not uploaded by users per run

### Deferred

- [ ] Persist sales history so future months only need delta uploads
- [ ] Detect duplicate monthly sales uploads before they are appended to stored history
- [ ] Store dataset lineage and reusable dataset versions across runs
- [ ] Add admin-managed site-mapping maintenance outside the code bundle
- [ ] Add dashboards and month-over-month reporting views

### Out of Scope

- External client or partner access — v1 is an internal ops tool first
- Direct ERP/API synchronization — start with managed file uploads and leave system integrations for later
- Redefining the V5 business logic — the current logic is intentionally frozen for this phase
- Full approval/governance workflow — useful later, but not the first release priority

## Context

The existing repository is a brownfield analytics codebase with multiple script generations. `v5_daily_oos_opportunity/` is the current source of truth for business logic, but it still operates as a local CLI pipeline over CSV/XLSX files and local output folders. Although longer-term workflow value will come from persistent history and duplicate-safe monthly ingestion, the immediate goal is to prove a simpler browser-based runner that preserves V5 output quality without committing to storage architecture too early.

## Constraints

- **Business Logic**: Preserve the current V5 formula and assumptions — the team wants the web app to operationalize the current model, not change it
- **Users**: Internal operations team only for this phase — optimize for expert internal workflow rather than public-product polish
- **Data Flow**: This phase is stateless — required files are uploaded per run, processed temporarily, and then discarded after completion/expiry
- **Output**: Excel export is mandatory — users still need `.xlsx` as a business deliverable
- **Architecture**: Brownfield extraction from scripts — calculation logic should be extracted from the current Python pipeline instead of rewritten blindly

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use V5 as the canonical calculation model | Current team has frozen the logic and wants the product built on top of it | Accepted |
| Build a stateless MVP first | Reduces implementation risk and avoids premature storage architecture decisions | Accepted |
| Defer sales-history persistence and duplicate detection | Valuable later, but not required to prove the browser workflow | Accepted |
| Keep sales, stock, and SKU files explicit per run in phase 1 | Makes the first release easier to reason about and easier to operate safely | Accepted |
| Bundle site mapping as MVP system config | Site mapping is small and stable enough to avoid adding upload/admin scope in the first release | Accepted |
| Prioritize run workflow over dashboards in v1 | The first pain to solve is upload, calculate, QA, and export reliability | Accepted |

---
*Last updated: 2026-03-11 after stateless MVP scope decision*
