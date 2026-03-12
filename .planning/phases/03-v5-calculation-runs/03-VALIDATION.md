---
phase: 3
slug: v5-calculation-runs
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + Streamlit AppTest |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~25 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 25 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 03-01 | 1 | RUN-01 | unit | `pytest -q tests/test_run_execution.py -k month` | ✅ | ⬜ pending |
| 03-01-02 | 03-01 | 1 | RUN-01, RUN-02 | unit | `pytest -q tests/test_run_execution.py -k execute` | ✅ | ⬜ pending |
| 03-01-03 | 03-01 | 1 | RUN-01, RUN-02 | unit | `pytest -q tests/test_run_execution.py` | ✅ | ⬜ pending |
| 03-02-01 | 03-02 | 2 | RUN-01, RUN-02 | unit | `pytest -q tests/test_run_workflow.py -k status` | ✅ | ⬜ pending |
| 03-02-02 | 03-02 | 2 | RUN-03 | unit | `pytest -q tests/test_run_workflow.py -k rerun` | ✅ | ⬜ pending |
| 03-02-03 | 03-02 | 2 | RUN-01, RUN-02, RUN-03 | unit | `pytest -q tests/test_run_workflow.py` | ✅ | ⬜ pending |
| 03-03-01 | 03-03 | 3 | RUN-01 | ui-smoke | `pytest -q tests/test_run_step_ui.py -k month` | ✅ | ⬜ pending |
| 03-03-02 | 03-03 | 3 | RUN-02 | ui-smoke | `pytest -q tests/test_run_step_ui.py -k outcome` | ✅ | ⬜ pending |
| 03-03-03 | 03-03 | 3 | RUN-01, RUN-02, RUN-03 | ui-smoke | `pytest -q tests/test_run_step_ui.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. `pytest.ini`, Streamlit AppTest support, the session workspace runtime, and the Phase 2 staged-input workflow already exist, so Phase 3 can add execution, orchestration, and run-step tests inside the implementation plans without a separate bootstrap plan.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator clarity of run success/failure summary and next-step guidance | RUN-02 | final readability and trust are subjective | Open the run step in the browser, execute both a successful and failing run scenario, and confirm the operator can clearly tell what happened and what to do next |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 25s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
