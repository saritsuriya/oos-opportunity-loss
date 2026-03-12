---
phase: 2
slug: run-input-workflow
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + Streamlit AppTest |
| **Config file** | `pytest.ini` |
| **Quick run command** | `pytest -q` |
| **Full suite command** | `pytest -q` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest -q`
- **After every plan wave:** Run `pytest -q`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 02-01 | 1 | DATA-01, DATA-02, DATA-03 | unit | `pytest -q tests/test_input_staging.py -k session` | ✅ | ⬜ pending |
| 02-01-02 | 02-01 | 1 | DATA-01, DATA-02, DATA-03 | unit | `pytest -q tests/test_input_staging.py -k replace` | ✅ | ⬜ pending |
| 02-01-03 | 02-01 | 1 | DATA-01, DATA-02, DATA-03 | unit | `pytest -q tests/test_input_staging.py` | ✅ | ⬜ pending |
| 02-02-01 | 02-02 | 2 | DATA-05 | unit | `pytest -q tests/test_input_validation.py -k critical` | ✅ | ⬜ pending |
| 02-02-02 | 02-02 | 2 | DATA-05 | unit | `pytest -q tests/test_input_validation.py -k warnings` | ✅ | ⬜ pending |
| 02-02-03 | 02-02 | 2 | DATA-05 | unit | `pytest -q tests/test_input_validation.py` | ✅ | ⬜ pending |
| 02-03-01 | 02-03 | 3 | DATA-01, DATA-02, DATA-03 | ui-smoke | `pytest -q tests/test_upload_step_ui.py -k layout` | ✅ | ⬜ pending |
| 02-03-02 | 02-03 | 3 | DATA-04 | ui-smoke | `pytest -q tests/test_upload_step_ui.py -k site_map` | ✅ | ⬜ pending |
| 02-03-03 | 02-03 | 3 | DATA-01, DATA-02, DATA-03, DATA-04, DATA-05 | ui-smoke | `pytest -q tests/test_upload_step_ui.py` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. `pytest.ini`, Streamlit AppTest support, and the Phase 1 shell baseline already exist, so Phase 2 can create its staging, validation, and UI tests inside the implementation plans without a separate bootstrap plan.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Operator readability of upload summaries and warning copy | DATA-05 | final usefulness of phrasing is subjective | Open the upload step in the browser, upload representative files, and confirm the warnings and summaries are clear to an operator |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
