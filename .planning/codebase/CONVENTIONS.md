# Conventions

## General Style

- Code style is practical and script-oriented rather than framework-driven
- Functions and classes are organized by responsibility:
  - loader
  - analyzer
  - reporter
- Business logic is concentrated in analyzer modules

## Naming Conventions

- Version-specific files use suffixes:
  - `data_loader_v2.py`
  - `analyzer_v4.py`
  - `reporter_v5.py`
- Config objects use `ModelConfig`
- input path containers use `InputPaths`
- output metrics are descriptive, for example:
  - `lost_value_gross_raw`
  - `lost_value_net_raw`
  - `actual_qty_jan`
  - `baseline_source`

## Data Normalization Conventions

- SKU identifiers are normalized to strings and stripped of:
  - quotes
  - Excel formula wrappers
  - trailing `.0`
  - extra whitespace
- Site names are lowercased canonical labels such as:
  - `wh-bkk`
  - `bkk-out`
  - `dmk-out`
- Product SKUs beginning with `p`/`P` are excluded from evaluation

## Error Handling

- File existence is validated explicitly
- Missing required columns raise `ValueError`
- Invalid parse rows are typically dropped after coercion
- Logging is done with `print`, not structured logging

## Reporting Conventions

- Excel workbook plus CSV sidecar exports
- Summary sheets are always derived from the `detail` dataframe
- QA information is surfaced as data tables, not assertions

## Operational Conventions

- Newer flows are documented in README files inside version folders
- The repo preserves old versions instead of replacing them
- Logic comparisons are done by generating separate versioned outputs

## Implications for Productization

- These conventions are good for analyst-owned scripts
- For a web app, implicit conventions need to become explicit contracts:
  - upload schemas
  - run status states
  - dataset versioning rules
  - audit fields
  - user-facing error messages
