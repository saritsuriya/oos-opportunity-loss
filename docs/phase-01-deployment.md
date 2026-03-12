# Phase 01 Windows Deployment Baseline

This runbook covers the Phase 1 internal deployment baseline only: one Windows-hosted Streamlit app, temporary per-session workspaces, bundled site mapping, and no new persistence or authentication layers.

## Deployment Scope

- Host a single internal Streamlit instance on a Windows server or Windows VM that the operations team can reach through a normal browser URL.
- Keep the MVP stateless. Uploaded inputs and generated outputs live only in the managed temp workspace and are cleaned up after use or by the scheduled cleanup job.
- Keep the bundled V5 site mapping file in the repo. Phase 1 does not add a user upload or admin management path for that file.

## Required Artifacts

- `.streamlit/config.toml` - internal-hosting server defaults for Streamlit
- `scripts/run_streamlit.ps1` - foreground startup command for the app service or startup task
- `scripts/cleanup_temp_workspace.py` - Python cleanup entrypoint that reuses the app runtime cleanup logic
- `scripts/cleanup_temp_workspace.ps1` - Windows Scheduled Task wrapper for stale-workspace cleanup

## Host Preparation

1. Copy the repo to a local path on the Windows host, for example `C:\apps\oos-opportunity-lost`.
2. Install Python 3.13 or newer and make sure either `python` is on `PATH` or you know the full path to `python.exe`.
3. Create the virtual environment and install dependencies:

```powershell
cd C:\apps\oos-opportunity-lost
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

4. Smoke-check the deployment artifacts before wiring the host service:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_deploy_config.py
```

## Choose The Internal URL

Pick the Windows host name or internal DNS record that operators will use, plus the final port. The baseline config defaults to `0.0.0.0:8501`, so the expected internal URL shape is:

`http://<public-hostname>:8501/`

If your team uses a different internal port, pass it through the startup script and open the matching Windows Firewall rule.

## Start The App

Run the generated startup script from PowerShell. It starts the real Streamlit entrypoint from Plan `01-01`, keeps the process in the foreground for a Windows service wrapper, and sets the browser-facing host and port shown in Streamlit.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_streamlit.ps1 `
  -ProjectRoot C:\apps\oos-opportunity-lost `
  -PublicHostName oos-op-loss.internal `
  -Port 8501
```

Expected result:

- Streamlit binds on `0.0.0.0`
- Operators browse to `http://oos-op-loss.internal:8501/`
- The startup path uses `streamlit_app/app.py` and `.streamlit/config.toml` from this repo

For a persistent host process, wrap `scripts/run_streamlit.ps1` in the Windows service or startup-task mechanism your infrastructure team prefers. The generated script is the command you should point that service to.

## Bundled Site Mapping Behavior

Phase 1 keeps site mapping as a system-owned file inside the repo:

`v5_daily_oos_opportunity\data\Site mapping.csv`

Operators do not upload this file in the browser. If the business needs a mapping change, update the bundled file in source control and redeploy the repo copy.

## Scheduled Cleanup

Plan `01-02` introduced the runtime cleanup helpers for `session-*` temp workspaces. Phase `01-03` wraps that same logic in Windows-friendly scripts so the host can prune abandoned sessions nightly without adding persistent storage.

Recommended scheduled task command:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cleanup_temp_workspace.ps1 `
  -ProjectRoot C:\apps\oos-opportunity-lost `
  -MaxAgeHours 24
```

Recommended schedule:

- Run once per night after normal operator hours
- Keep `MaxAgeHours` at `24` unless the team intentionally wants a shorter cleanup window
- Point the scheduled task at the same repo copy and Python environment as the app startup task

## Manual Setup Still Required

- Choose the final Windows host name, internal DNS alias, and port.
- Create the Windows service or startup task that runs `scripts/run_streamlit.ps1`.
- Open the required Windows Firewall or internal network rule for the chosen port.
- Create the nightly cleanup scheduled task that runs `scripts/cleanup_temp_workspace.ps1`.

## Out Of Scope For Phase 1

- No login or expanded authentication
- No persistent business-data storage or run-history retention
- No production SSL termination inside Streamlit itself; if HTTPS is needed, terminate it with the host's internal reverse proxy or load balancer later
