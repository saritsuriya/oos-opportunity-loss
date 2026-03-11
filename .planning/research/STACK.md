# Stack Research

## Recommendation

Use a split web stack:

- **Frontend**: Next.js App Router + TypeScript
- **API**: FastAPI
- **Database**: PostgreSQL
- **Async jobs**: Celery worker with Redis as broker/result backend
- **File storage**: S3-compatible object storage for raw uploads and generated exports

## Why This Fits This Project

- The current calculation engine is already Python, so a Python API/worker layer avoids unnecessary translation risk
- The product needs a strong internal web UI, and Next.js App Router is a current mainstream React choice for structured full-stack web applications
- The system needs persistent datasets, run history, uniqueness constraints, and queryable result metadata; PostgreSQL fits that better than filesystem storage
- The calculation should run asynchronously, not in browser request time, because current V5 runs are batch-style and produce large outputs
- Raw source files and exported reports should live outside the database as durable file objects, while metadata lives in PostgreSQL

## Frontend

### Recommended

- Next.js App Router
- TypeScript
- React Server Components where useful for data-heavy pages
- A data-table library for result exploration
- Schema-driven forms and client validation

### Why

- Next.js App Router is the current first-class routing model in official docs
- Route Handlers are available inside the `app` directory when frontend-side endpoints are useful, but this project should still keep the calculation API as a dedicated backend service
- App Router suits internal workflow tools with mixed server-rendered pages, forms, and authenticated dashboards

## Backend API

### Recommended

- FastAPI for internal APIs
- `UploadFile` for multipart file ingestion
- Thin request layer that hands work to async jobs rather than running calculations inline

### Why

- FastAPI already matches the current Python/pandas ecosystem
- Official docs support `UploadFile` and combined file/form request patterns
- FastAPI `BackgroundTasks` exist, but for this project they should be reserved for small follow-up work, not the main calculation engine

## Jobs

### Recommended

- Celery worker processes
- Redis broker

### Why

- Calculation runs should be async, persisted, retriable, and observable
- Celery is mature and current
- Redis is an established broker choice for task queues

## Database

### Recommended

- PostgreSQL as the primary system of record

### Why

- Need transaction history persistence
- Need uniqueness constraints for duplicate protection
- Need indexes for efficient lookups by period, dataset type, and run
- Need versioning for monthly sales history, stock snapshots, SKU universes, and run artifacts

## File Storage

### Recommended

- S3-compatible blob storage

### Store There

- raw uploaded files
- normalized export files
- generated `.xlsx` reports
- CSV sidecars

## What Not To Use First

- Do **not** build v1 as a browser-only app that parses all files client-side
- Do **not** wrap the current CLI directly behind synchronous HTTP endpoints
- Do **not** use filesystem-only storage for production history and exports
- Do **not** rewrite the V5 math into JavaScript for v1

## Confidence

- Frontend: High
- FastAPI backend: High
- PostgreSQL persistence: High
- Celery + Redis jobs: Medium-High
- S3-compatible storage: High

## Sources

- Next.js App Router: https://nextjs.org/docs/app
- Next.js Route Handlers: https://nextjs.org/docs/15/app/getting-started/route-handlers-and-middleware
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- FastAPI forms + files: https://fastapi.tiangolo.com/tutorial/request-forms-and-files/
- FastAPI background tasks: https://fastapi.tiangolo.com/tutorial/background-tasks/
- Celery user guide: https://docs.celeryq.dev/en/stable/userguide/
- PostgreSQL indexes: https://www.postgresql.org/docs/current/indexes.html
- PostgreSQL partial indexes: https://www.postgresql.org/docs/16/indexes-partial.html
