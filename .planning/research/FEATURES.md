# Features Research

## Table Stakes

### Access

- Internal login / controlled access
- User-visible run ownership and timestamps

### Dataset Management

- Upload sales history files
- Append monthly sales deltas to persisted history
- Upload stock snapshot for a selected calculation month
- Upload SKU universe / live product file
- Upload or manage site mapping
- Duplicate detection before accepting a sales upload
- Validation errors with row-level feedback

### Calculation Workflow

- Create a calculation run for a selected month
- Show run status: validating, queued, running, completed, failed
- Lock the run to explicit dataset versions
- Persist outputs per run

### Results

- Summary by total / site / SKU
- Detail-level result review
- Export `.xlsx`
- Export `.csv`

### QA / Explainability

- Show which files were used
- Show warnings and unmapped/invalid data
- Explain key logic assumptions
- Explain baseline source and window selection

## Differentiators

- Compare one run against another
- Show month-over-month opportunity trend
- Explain why a row has zero loss
- Highlight rows hidden from calculation because of status/site coverage
- Provide downloadable templates with schema guidance
- Surface “data health” scores before execution

## Anti-Features For V1

- External customer multi-tenancy
- Real-time ERP/API integrations
- Approval/governance workflow with multi-stage signoff
- Rebuilding the V5 formula
- Dashboard-heavy BI layer before the operational workflow is stable

## Feature Dependencies

- Result pages depend on persisted runs
- Persisted runs depend on normalized datasets
- Duplicate detection depends on a clear upload/dataset model
- Explainability depends on saving baseline source, warnings, and input lineage

## Recommended v1 Bias

The project should prioritize:

1. upload and validation
2. duplicate-safe monthly append flow
3. run management
4. QA visibility
5. export reliability

Dashboards should be present only as a light optional layer in v1.

## Confidence

- Table stakes: High
- Differentiators: Medium-High
- Anti-features: High
