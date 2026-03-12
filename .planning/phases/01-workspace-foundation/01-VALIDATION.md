---
phase: 1
slug: workspace-foundation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + Streamlit AppTest |
| **Config file** | `pytest.ini` or `none — Wave 0 installs` |
| **Quick run command** | `pytest -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01-01 | 1 | OPS-01 | build | `python3 -m compileall streamlit_app` | ✅ | ⬜ pending |
| 01-01-02 | 01-01 | 1 | OPS-01 | build | `python3 -m compileall streamlit_app` | ✅ | ⬜ pending |
| 01-01-03 | 01-01 | 1 | OPS-01 | smoke | `pytest -q tests/test_app_smoke.py` | ✅ | ⬜ pending |
| 01-02-01 | 01-02 | 2 | OPS-02 | unit | `pytest -q tests/test_temp_workspace.py -k create` | ✅ | ⬜ pending |
| 01-02-02 | 01-02 | 2 | OPS-02 | unit | `pytest -q tests/test_temp_workspace.py -k cleanup` | ✅ | ⬜ pending |
| 01-02-03 | 01-02 | 2 | OPS-02 | unit | `pytest -q tests/test_temp_workspace.py` | ✅ | ⬜ pending |
| 01-03-01 | 01-03 | 3 | OPS-01 | smoke | `pytest -q tests/test_deploy_config.py -k config` | ✅ | ⬜ pending |
| 01-03-02 | 01-03 | 3 | OPS-01 | smoke | `pytest -q tests/test_deploy_config.py -k scripts` | ✅ | ⬜ pending |
| 01-03-03 | 01-03 | 3 | OPS-01 | smoke | `pytest -q tests/test_deploy_config.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Automated verification is created inside the implementation tasks, so no separate Wave 0 bootstrap plan is required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Internal browser access from a team machine | OPS-01 | depends on local network and host environment | Start the app on the Windows server, open the internal URL from another team machine, verify the shell loads |
| Nightly cleanup wiring on target host | OPS-02 | scheduler integration is host-specific | Leave temp artifacts in the workspace root, run the configured cleanup task, verify old session folders are removed |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
