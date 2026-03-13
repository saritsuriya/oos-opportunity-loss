---
phase: 4
slug: results-workspace
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-13
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + Streamlit AppTest |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | RES-01 | unit | `pytest -q tests/test_results_workspace.py -k artifact` | ✅ | ⬜ pending |
| 04-01-02 | 01 | 1 | RES-02, RES-03 | unit | `pytest -q tests/test_results_workspace.py -k workbook` | ✅ | ⬜ pending |
| 04-01-03 | 01 | 1 | RES-01, RES-02, RES-03 | unit | `pytest -q tests/test_results_workspace.py` | ✅ | ⬜ pending |
| 04-02-01 | 02 | 2 | RES-01 | ui-smoke | `pytest -q tests/test_review_results_ui.py -k overview` | ✅ | ⬜ pending |
| 04-02-02 | 02 | 2 | RES-01, RES-03 | ui-smoke | `pytest -q tests/test_review_results_ui.py -k detail` | ✅ | ⬜ pending |
| 04-02-03 | 02 | 2 | RES-02, RES-03 | ui-smoke | `pytest -q tests/test_review_results_ui.py -k qa` | ✅ | ⬜ pending |
| 04-03-01 | 03 | 3 | RES-04, RES-05 | ui-smoke | `pytest -q tests/test_review_results_ui.py -k export` | ✅ | ⬜ pending |
| 04-03-02 | 03 | 3 | RES-02 | ui-smoke | `pytest -q tests/test_review_results_ui.py -k missing` | ✅ | ⬜ pending |
| 04-03-03 | 03 | 3 | RES-04, RES-05 | ui-smoke | `pytest -q tests/test_review_results_ui.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. `pytest`, Streamlit AppTest, session-state bootstrap, run orchestration, and the Phase 3 completed-run payload already exist, so Phase 4 can add result-loading and review/export tests directly inside the implementation plans without a bootstrap wave.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QA/trust messaging feels clear and proportionate in the browser | RES-02, RES-03 | readability and operator trust remain subjective | Open the review step after a successful run, inspect the overview, QA banner, and trust tab, and confirm an operator can quickly tell whether the run is trustworthy and where to drill in next |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
