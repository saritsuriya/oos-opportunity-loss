"""Session bootstrap helpers for the Streamlit operator workflow."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from uuid import uuid4

import streamlit as st


@dataclass(frozen=True)
class WizardStep:
    slug: str
    label: str
    phase_hint: str
    summary: str


_WIZARD_STEPS: tuple[WizardStep, ...] = (
    WizardStep(
        slug="foundation",
        label="Foundation",
        phase_hint="Phase 1 live now",
        summary="Boot the browser workspace, session shell, and the stateless MVP rules.",
    ),
    WizardStep(
        slug="upload-inputs",
        label="Upload Inputs",
        phase_hint="Reserved for Phase 2",
        summary="Stage sales, stock, and SKU files into a per-session workspace without persistence.",
    ),
    WizardStep(
        slug="run-v5",
        label="Run Frozen V5",
        phase_hint="Reserved for Phase 3",
        summary="Call the frozen V5 loader, analyzer, and reporter path from the browser runtime.",
    ),
    WizardStep(
        slug="review-results",
        label="Review And Export",
        phase_hint="Reserved for Phase 4",
        summary="Surface QA outcomes and downloadable workbook and CSV artifacts.",
    ),
)


def get_wizard_steps() -> tuple[WizardStep, ...]:
    return _WIZARD_STEPS


def bootstrap_session_state() -> dict[str, object]:
    defaults: dict[str, object] = {
        "session_bootstrapped": True,
        "session_id": uuid4().hex[:8].upper(),
        "session_started_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "current_step_index": 0,
        "workspace_mode": "Stateless MVP",
        "workspace_scope": "Per-session temporary files only",
        "site_mapping_mode": "Bundled system configuration",
        "active_run_status": "Not started",
        "wizard_steps": [asdict(step) for step in get_wizard_steps()],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    return {key: st.session_state[key] for key in defaults}


def current_step_index() -> int:
    index = int(st.session_state.get("current_step_index", 0))
    max_index = len(get_wizard_steps()) - 1
    if index < 0:
        index = 0
    if index > max_index:
        index = max_index
    st.session_state["current_step_index"] = index
    return index


def set_current_step(index: int) -> int:
    bounded = min(max(index, 0), len(get_wizard_steps()) - 1)
    st.session_state["current_step_index"] = bounded
    return bounded


def advance_step() -> int:
    return set_current_step(current_step_index() + 1)


def rewind_step() -> int:
    return set_current_step(current_step_index() - 1)
