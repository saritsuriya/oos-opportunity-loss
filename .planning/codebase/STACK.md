# Stack

## Summary

This repository is a local, script-driven analytics tool for OOS opportunity-loss calculation.
The current production logic lives in `v5_daily_oos_opportunity/` and is implemented entirely in Python with pandas-centric data processing.

## Languages and Runtime

- Primary language: Python
- Runtime assumption: `python3`
- Execution mode: command-line scripts, no server process
- Repository style: ad hoc analytics repo, not a packaged Python project

## Core Libraries

- `pandas` for CSV/XLSX loading, joins, grouping, and Excel export
- `numpy` for vectorized calculations in analyzers
- `openpyxl` via `pd.ExcelWriter(..., engine="openpyxl")` for workbook output
- Python stdlib modules:
  - `argparse`
  - `calendar`
  - `os`
  - `pathlib`
  - `re`
  - `dataclasses`
  - `typing`

## Dependency Management

- No `requirements.txt`, `pyproject.toml`, or `package.json` found
- Environment is implied rather than declared
- Dependency setup is currently tribal knowledge

## Active Entrypoints

- Legacy root flow: `main.py`
- V2 flow: `v2_opportunity_loss/main.py`
- V4 flow: `v4_daily_oos_opportunity/main.py`
- Current active logic: `v5_daily_oos_opportunity/main.py`

## Data and File Formats

- Orders:
  - UTF-16 tab-delimited text in `OrderDetail*.csv`
  - Excel fallback supported in newer loaders
- Daily stock:
  - CSV files such as `Earth - Daily Stock by Location Jan 2026.csv`
- Product universe:
  - CSV file such as `product-2026-03-02-10-07.csv`
- Site mapping:
  - CSV file `Site mapping.csv`
- Outputs:
  - Excel workbooks in `output/`
  - CSV extracts for detail and summaries

## Configuration Style

- Config is passed through CLI arguments in `v2_opportunity_loss/main.py`, `v4_daily_oos_opportunity/main.py`, and `v5_daily_oos_opportunity/main.py`
- Defaults are assembled from local file paths, not environment variables
- There is no persistent app config layer or secrets management

## Implications for Web Product Work

- The current stack is suitable as a calculation engine, not as a user-facing application
- A web product will need:
  - persistent storage for uploaded history and monthly deltas
  - an ingestion layer for validating file schemas
  - a backend job or service layer for running the V5 calculation
  - a frontend for upload, run history, QA visibility, and result review
