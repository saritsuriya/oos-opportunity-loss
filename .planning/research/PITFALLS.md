# Pitfalls Research

## Pitfall 1: Building UI Before Freezing Data Contracts

- Warning signs:
  - upload screens are designed before schemas are defined
  - duplicate handling is “figure it out later”
- Prevention:
  - define canonical dataset schemas first
  - define business keys for duplicate detection
- Phase:
  - ingestion and data-model phase

## Pitfall 2: Treating Batch Calculation As Synchronous Request Work

- Warning signs:
  - HTTP request triggers full calculation inline
  - large runs block user sessions
- Prevention:
  - run calculations asynchronously via workers
  - persist run status and logs
- Phase:
  - calculation engine integration

## Pitfall 3: Reusing Repo-Relative Filesystem Paths In Production

- Warning signs:
  - code still expects `data/...csv` under the app repo
  - exports overwrite each other by month path
- Prevention:
  - replace local paths with dataset IDs and storage object keys
  - make each run immutable
- Phase:
  - backend foundation

## Pitfall 4: Weak Duplicate Detection For Sales History

- Warning signs:
  - duplicate checks rely on filename only
  - duplicate checks use whole-row equality only
- Prevention:
  - define upload identity and row-level business keys
  - keep ingestion audit records
- Phase:
  - sales ingestion

## Pitfall 5: Poor Explainability Of Business Rules

- Warning signs:
  - users do not understand why loss is zero
  - users cannot see which baseline window was used
- Prevention:
  - expose logic assumptions in run QA and row detail
  - save baseline source, warning flags, and lineage
- Phase:
  - workflow UI and results UI

## Pitfall 6: Letting Optional Dashboards Delay Core Workflow

- Warning signs:
  - design discussions focus on charts before upload/run reliability
- Prevention:
  - prioritize operational workflow first
  - keep dashboards optional in v1
- Phase:
  - product scoping and roadmap control

## Pitfall 7: No Regression Harness Around Frozen V5 Logic

- Warning signs:
  - calculation behavior changes after refactor without known reason
- Prevention:
  - build fixture-based regression tests before or during engine extraction
- Phase:
  - engine extraction

## Pitfall 8: Storing Unneeded Sensitive Raw Data

- Warning signs:
  - full order exports with unnecessary customer fields are retained indefinitely
- Prevention:
  - define a retention and minimization policy at ingest
  - normalize only required fields where possible
- Phase:
  - ingestion foundation

## Overall Recommendation

The highest-risk mistake would be to “just put a web form in front of the script.”
This project should be designed as a dataset-management and calculation-run system, not as a prettier wrapper around local files.

## Confidence

- Pitfalls identified: High
- Phase mapping: Medium-High
