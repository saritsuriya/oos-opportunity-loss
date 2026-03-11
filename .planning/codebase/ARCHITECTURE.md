# Architecture

## Summary

The repository follows a batch analytics architecture.
Each version is organized as a pipeline:

`main` -> `data loader` -> `analyzer` -> `reporter`

The current target logic is `v5_daily_oos_opportunity/`.

## Version Evolution

### Legacy Root Flow

- Files:
  - `main.py`
  - `data_loader.py`
  - `analyzer.py`
  - `reporter.py`
- Model style:
  - monthly stock snapshot interpretation
  - airport/site aggregation
  - hardcoded input files under `sources/`

### V2

- Folder: `v2_opportunity_loss/`
- Focus:
  - more explainable site-level expected demand model
  - configurable CLI arguments
  - workbook plus CSV exports

### V4

- Folder: `v4_daily_oos_opportunity/`
- Focus:
  - daily stock availability model
  - full SKU x virtual site universe
  - 2025 full-year baseline

### V5

- Folder: `v5_daily_oos_opportunity/`
- Focus:
  - same daily OOS mechanics as V4
  - rolling 6-month baseline before evaluation month
  - fallback previous 6 months when recent window is zero
  - QA fields that expose baseline source and window bounds

## Current V5 Data Flow

1. `v5_daily_oos_opportunity/main.py` resolves file paths and CLI options
2. `v5_daily_oos_opportunity/data_loader_v5.py` loads and normalizes:
   - orders
   - daily stock
   - site mapping
   - product universe
3. `v5_daily_oos_opportunity/analyzer_v5.py`:
   - filters the SKU universe
   - maps physical sites to `virtual_site`
   - aggregates daily stock by `posting_date + sku + virtual_site`
   - builds a full SKU x virtual-site evaluation universe
   - calculates OOS days
   - calculates rolling baseline demand
   - calculates expected qty, gap, and opportunity loss
4. `v5_daily_oos_opportunity/reporter_v5.py` writes:
   - Excel workbook
   - detail and summary CSVs
   - QA summary
   - definitions and calculation example

## Architectural Characteristics

- Batch-only, no request/response runtime
- File-path-driven, not database-driven
- Heavy reliance on pandas joins and grouped aggregations
- Logic and reporting are tightly coupled per version folder
- Outputs are materialized files, not queryable records

## Best Backend Shape for the Web App

- Preserve the core separation:
  - ingestion layer
  - normalized storage
  - calculation service using V5 logic
  - reporting/query layer
- Convert each current input file into a managed dataset:
  - sales history table
  - stock snapshot table
  - SKU universe table
  - site mapping table
- Run V5 as a job tied to a calculation run record instead of a local script execution
