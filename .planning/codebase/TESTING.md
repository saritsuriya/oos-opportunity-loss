# Testing

## Summary

There is no automated test suite in this repository.
Confidence is currently built through script execution, output inspection, and targeted debug scripts.

## Current Verification Approach

### Manual Run Validation

- Run versioned entrypoints directly:
  - `python3 v2_opportunity_loss/main.py`
  - `python3 v4_daily_oos_opportunity/main.py`
  - `python3 v5_daily_oos_opportunity/main.py`
- Review terminal totals, generated Excel files, and exported CSVs

### QA Output Tables

- V4 and V5 generate QA summary CSVs/workbook sheets
- These expose:
  - row counts
  - excluded SKU counts
  - unmapped site counts
  - total lost values
  - baseline-source distribution in V5

### Ad Hoc Analysis Scripts

- Root-level helpers:
  - `debug_logic.py`
  - `debug_stock.py`
  - `debug_values.py`
  - `analyze_data.py`
  - `analyze_stock.py`
  - `analyze_locations.py`
  - `analyze_remarks.py`

## Missing Test Coverage

- No unit tests for loaders
- No unit tests for baseline logic
- No fixture-based regression tests for known calculations
- No contract tests for input file schemas
- No snapshot tests for output report structure

## Productization Implications

Before turning this into a web product, testing should be added at multiple levels:

- unit tests for:
  - file normalization
  - site mapping
  - baseline selection
  - OOS day calculation
- regression tests using frozen input fixtures and expected totals
- ingestion contract tests for required columns and data types
- integration tests for calculation runs
- frontend end-to-end tests once UX/UI exists

## Recommended First Regression Coverage

- V5 calculation on a small frozen sample dataset
- one scenario using `recent_6m`
- one scenario using `fallback_prev_6m`
- one scenario with `actual_qty_jan > 0` forcing loss to zero
- one scenario with unmapped site codes
