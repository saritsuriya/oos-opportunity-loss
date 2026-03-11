# Concerns

## Main Risks in the Current Repo

### 1. File-Based Operations Are Fragile

- The system depends on exact column names in manually supplied CSV/XLSX files
- There is no formal schema registry or migration layer
- Monthly operational success depends on users preparing the files correctly

### 2. Logic Is Locked Inside Scripts

- The current V5 logic is embedded in `v5_daily_oos_opportunity/analyzer_v5.py`
- There is no reusable package or service boundary
- Turning this into a web app will require extraction, not just wrapping the script

### 3. No Persistent Data Model Yet

- The user explicitly wants monthly sales history to be appended rather than re-uploaded in full
- The current repo has no storage model for:
  - raw uploads
  - normalized transaction history
  - snapshot history
  - run history
  - auditability

### 4. UX Risk Around Data Trust

- Opportunity-loss numbers are sensitive and can shift materially when baseline logic changes
- Users will need strong explainability:
  - what files were used
  - what month was evaluated
  - which baseline window was selected
  - why a SKU has loss or no loss

### 5. Jan-Specific Field Names Persist

- Some output fields still contain `_jan` naming even though evaluation month is configurable
- This can confuse business users in a multi-month web UI

### 6. No Auth or Multi-User Model

- The current tool assumes a single local operator
- A web app will need role and access decisions:
  - who can upload
  - who can rerun
  - who can approve or publish results

### 7. No Automated Regression Protection

- Logic changes currently rely on manual comparison
- This is dangerous once the app becomes business-facing

## Product Risks to Design Around

- Duplicate uploads of monthly sales files
- Partial or late monthly sales append flows
- Stock snapshot uploaded for the wrong month
- SKU universe drift between runs
- Reproducibility of historical runs after source data changes

## Highest-Leverage Design Recommendation

Make the web product run on persisted datasets and explicit calculation runs:

- persist sales history incrementally
- persist stock snapshots by period
- persist SKU universe versions
- persist calculation inputs and outputs by run

That design directly addresses the user’s main operational pain point: not wanting to upload the entire sales history every month again.
