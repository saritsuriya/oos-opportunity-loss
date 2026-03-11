# Structure

## Top-Level Layout

- Legacy scripts at repo root:
  - `main.py`
  - `data_loader.py`
  - `analyzer.py`
  - `reporter.py`
  - `analyze_*.py`
  - `debug_*.py`
- Historical/generated artifacts:
  - `OOS_Opportunity_Lost_Report.xlsx`
  - `OOS_Opportunity_Lost_Report_stock_detail.csv`
  - `debug_stock_cleaned.xlsx`
- Raw sources:
  - `sources/`
- Versioned calculation implementations:
  - `v2_opportunity_loss/`
  - `v4_daily_oos_opportunity/`
  - `v5_daily_oos_opportunity/`

## Active Working Area

`v5_daily_oos_opportunity/` is the current logical source of truth for future productization.

### `v5_daily_oos_opportunity/`

- `main.py`
  - CLI entrypoint
  - path resolution
  - model execution
- `data_loader_v5.py`
  - file loading
  - schema validation
  - normalization
- `analyzer_v5.py`
  - business logic
  - baseline and OOS calculations
- `reporter_v5.py`
  - workbook/CSV generation
- `README.md`
  - plain-language logic summary
- `data/`
  - symlink to `../v4_daily_oos_opportunity/data`
- `output/`
  - generated period folders and reports

## Historical Version Folders

### `v2_opportunity_loss/`

- earlier configurable model
- different baseline philosophy
- own `data/` and `output/`

### `v4_daily_oos_opportunity/`

- immediate predecessor to V5
- same broad pipeline
- full-year 2025 baseline

## Naming Patterns

- Version folders carry business meaning:
  - `v2_opportunity_loss`
  - `v4_daily_oos_opportunity`
  - `v5_daily_oos_opportunity`
- Loaders/analyzers/reporters are version-specific
- Output workbooks are period-scoped and version-tagged

## Structural Observations

- This is a brownfield analytics repo, not a web monorepo
- There is no frontend source tree yet
- There is no backend service folder yet
- There is no tests folder
- There is no shared domain module reused across versions

## Recommended Future Structure

For the web product, split responsibilities into explicit areas:

- `apps/web/` or equivalent for UX/UI
- `apps/api/` or service backend
- `packages/calculation-engine/` for V5 logic extracted from scripts
- `packages/data-contracts/` for file schemas and validation
- persistent storage for uploaded datasets and run metadata
