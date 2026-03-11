# Integrations

## Summary

The current repository has no external API or SaaS integrations.
Its integrations are file-based: local CSV/XLSX inputs and local Excel/CSV outputs.

## Input Integrations

### Orders History

- Source files:
  - `v5_daily_oos_opportunity/data/OrderDetail.csv`
  - `v5_daily_oos_opportunity/data/OrderDetailTilFeb.csv`
- Loader: `v5_daily_oos_opportunity/data_loader_v5.py`
- Expected fields include:
  - `Purchase Date`
  - `Sku`
  - `stock`
  - `Quantity`
  - `Gross`
  - `Net`
  - `Product Name`

### Daily Stock Snapshot

- Source files:
  - `v5_daily_oos_opportunity/data/Earth - Daily Stock by Location Jan 2026.csv`
  - `v5_daily_oos_opportunity/data/Earth - Daily Stock by Location Feb 2026.csv`
- Loader: `v5_daily_oos_opportunity/data_loader_v5.py`
- Expected fields include:
  - `posting_date`
  - `site_code`
  - `article_code`
  - `stock_balance`

### Site Mapping

- Source file: `v5_daily_oos_opportunity/data/Site mapping.csv`
- Purpose: maps physical `Site` values to logical `Virtual Location`
- Only rows with `Active == X` are used

### Product Universe

- Source file: `v5_daily_oos_opportunity/data/product-2026-03-02-10-07.csv`
- Purpose: defines the SKU universe to evaluate
- Current rule: live SKUs are preferred when `status` is available

## Output Integrations

- Main workbook:
  - `v5_daily_oos_opportunity/output/<period>/OOS_Opportunity_Lost_<period>_V5.xlsx`
- Sidecar CSVs:
  - detail
  - summary by site
  - summary by SKU
  - summary total
  - QA summary

## Non-Integrations

- No database
- No authentication provider
- No cloud object storage
- No webhook processing
- No scheduler/orchestrator
- No third-party analytics or monitoring

## Web Product Implications

- The future app should treat file ingestion as a first-class system boundary
- The “sales performance” feed is the best candidate for append-only persistence
- The “stock snapshot for calculate month” remains a period-scoped upload
- The “SKU to check (Live)” feed can be versioned per upload or synchronized into a reference table
