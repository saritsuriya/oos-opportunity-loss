# Research Summary

Note: this document captures the recommended end-state architecture from research. On 2026-03-11, project scope was intentionally reduced for execution so the current delivery plan starts with a stateless/no-storage MVP first, with persistence deferred to a later phase.

## Stack

Recommended stack:

- Next.js App Router frontend
- FastAPI API layer
- PostgreSQL as system of record
- Celery + Redis for async jobs
- S3-compatible file storage for raw uploads and generated exports

This fits the project because the current engine is already Python, while the future product needs strong browser workflow support, persistent datasets, and background execution.

## Table Stakes

Core v1 features should be:

- managed uploads
- persistent sales history with monthly append flow
- duplicate detection
- run-scoped stock and SKU uploads
- calculation run management
- QA and explainability
- `.xlsx` and `.csv` export

## Watch Out For

Highest-risk mistakes:

- building the UI before dataset contracts are defined
- running long calculations inside HTTP requests
- keeping repo-relative filesystem assumptions
- weak duplicate protection for sales history
- poor explainability of zero-loss and baseline-window behavior

## Product Direction

This should be built as an **internal operational workspace** first, not as a dashboard-first product and not as an external SaaS product.
The system boundary is:

- ingest datasets
- persist normalized history
- run frozen V5 logic asynchronously
- review QA and outputs
- export results

## Recommendation For Roadmap

Roadmap should start with:

1. product scaffold and data model
2. upload and validation flows
3. extraction of the V5 engine into backend services
4. run workflow and export UX
5. optional dashboards and comparison views
