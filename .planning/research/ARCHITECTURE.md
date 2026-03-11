# Architecture Research

## Recommended Components

### 1. Web App

- Internal UI for:
  - dataset uploads
  - upload history
  - run creation
  - QA review
  - result exploration
  - export download

### 2. API Service

- Authentication / authorization
- Dataset ingestion endpoints
- Run-management endpoints
- Query endpoints for runs, summaries, and details

### 3. Validation / Ingestion Layer

- File schema validation
- duplicate detection
- normalization into canonical tables
- ingestion warnings and rejection reasons

### 4. Operational Database

- dataset metadata
- normalized sales history
- stock snapshot metadata
- SKU universe versions
- site mapping versions
- run metadata
- warnings, audit logs, and export references

### 5. File Storage

- raw upload files
- generated workbooks and CSV exports

### 6. Calculation Worker

- Runs frozen V5 logic against normalized dataset versions
- Produces run detail/summary outputs
- Emits QA and run logs

## Core Data Boundaries

### Persisted History

- `sales_transactions`
- append-only over time
- duplicate-safe ingest rules required

### Run-Scoped Reference Data

- `stock_snapshot`
- `sku_universe`
- `site_mapping`

Each run should reference explicit versions, not “latest at runtime.”

### Calculation Outputs

- `calculation_run`
- `run_summary_total`
- `run_summary_site`
- `run_summary_sku`
- `run_detail`
- `run_warning`

## Data Flow

1. User uploads a file
2. API stores raw file and creates a dataset ingestion record
3. Validation layer checks schema and duplicates
4. Valid rows are normalized into operational tables
5. User creates a calculation run for a month
6. API enqueues a worker job
7. Worker loads the exact referenced datasets
8. Worker executes V5 calculation logic
9. Worker stores outputs and export artifacts
10. UI renders run status, QA, summaries, detail, and downloads

## Suggested Build Order

### Phase 1

- project scaffold
- auth shell
- database schema
- file storage integration

### Phase 2

- sales-history upload and append pipeline
- duplicate detection
- stock / SKU / site-map ingestion

### Phase 3

- extraction of V5 calculation engine into reusable service code
- async run execution
- persisted run outputs

### Phase 4

- workflow UI: upload, run, QA, result review
- export delivery

### Phase 5

- optional dashboards and run comparison
- operational hardening

## Key Design Principle

Do not make the UI talk directly to raw files and do not make the worker read from repo-relative paths.
Everything should flow through versioned datasets and persisted calculation runs.

## Confidence

- Component boundaries: High
- Data model direction: High
- Build order: High
