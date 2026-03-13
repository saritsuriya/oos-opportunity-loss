"""Guided wizard shell for the Streamlit operator workspace."""

from __future__ import annotations

import streamlit as st

try:
    from streamlit_app.runtime.session_state import (
        advance_step,
        current_step_index,
        get_wizard_steps,
        rewind_step,
        set_current_step,
    )
    from streamlit_app.services.run_workflow import RUN_STATUS_SUCCEEDED, RUN_WORKFLOW_STATE_KEY
    from streamlit_app.services.v5_boundary import get_boundary_overview
    from streamlit_app.ui.run_v5 import render_run_v5_step
    from streamlit_app.ui.upload_inputs import UPLOAD_STEP_READINESS_KEY, render_upload_inputs_step
except ModuleNotFoundError:
    from runtime.session_state import (
        advance_step,
        current_step_index,
        get_wizard_steps,
        rewind_step,
        set_current_step,
    )
    from services.run_workflow import RUN_STATUS_SUCCEEDED, RUN_WORKFLOW_STATE_KEY
    from services.v5_boundary import get_boundary_overview
    from ui.run_v5 import render_run_v5_step
    from ui.upload_inputs import UPLOAD_STEP_READINESS_KEY, render_upload_inputs_step


def _render_shell_summary(step_index: int, total_steps: int) -> None:
    session_col, step_col, mode_col, mapping_col = st.columns(4)
    session_col.metric("Session", st.session_state["session_id"])
    step_col.metric("Wizard Step", f"{step_index + 1}/{total_steps}")
    mode_col.metric("Workspace", st.session_state["workspace_mode"])
    mapping_col.metric("Site Mapping", "Bundled")


def _render_step_map(step_index: int) -> None:
    st.subheader("Operator Flow")
    columns = st.columns(len(get_wizard_steps()))
    for index, (column, step) in enumerate(zip(columns, get_wizard_steps(), strict=False)):
        if index < step_index:
            status = "Ready"
        elif index == step_index:
            status = "Current"
        else:
            status = "Placeholder"
        with column:
            st.markdown(f"**{index + 1}. {step.label}**")
            st.caption(_display_phase_hint(step.slug, step.phase_hint))
            st.write(status)
            st.write(_display_step_summary(step.slug, step.summary))


def _render_boundary_summary() -> None:
    overview = get_boundary_overview()
    st.subheader("MVP Boundary")
    st.markdown(
        "\n".join(
            [
                f"- Pipeline: {overview.pipeline_name}",
                f"- Integration mode: {overview.integration_mode}",
                f"- Bundled site mapping: `{overview.site_mapping_path}`",
                "- Uploaded inputs and generated outputs remain scoped to the active session workspace.",
                "- Persistence, duplicate detection, and stronger auth remain deferred beyond this phase.",
            ]
        )
    )
    st.caption("Frozen V5 modules reserved behind the boundary:")
    for module in overview.modules:
        st.write(f"{module.import_path} - {module.responsibility}")


def _render_current_step() -> None:
    step = get_wizard_steps()[current_step_index()]
    st.subheader(f"Current Step: {step.label}")

    if step.slug == "foundation":
        st.success("The Phase 1 workspace shell is live and session state is initialized.")
        st.markdown(
            "\n".join(
                [
                    "- The app starts in a guided browser workflow instead of a blank utility page.",
                    "- Session bootstrap creates a run-scoped shell for future temporary file handling.",
                    "- Later phases will attach uploads, V5 execution, QA review, and exports to this same shell.",
                ]
            )
        )
        st.info(
            "This foundation intentionally stops before file upload, calculation execution, "
            "or storage behavior so the V5 flow can be integrated without creating a second path."
        )
    elif step.slug == "upload-inputs":
        render_upload_inputs_step()
    elif step.slug == "run-v5":
        render_run_v5_step()
    else:
        st.warning("Placeholder for Phase 4 QA review and export.")
        st.markdown(
            "\n".join(
                [
                    "- Result summaries and explainability checks will render here.",
                    "- Download actions will expose workbook and CSV outputs from the active session.",
                    "- The flow remains stateless until persistence enhancements arrive in a later phase.",
                ]
            )
        )


def _render_navigation() -> None:
    previous_col, spacer_col, next_col = st.columns([1, 2, 1])
    step = get_wizard_steps()[current_step_index()]
    readiness = st.session_state.get(UPLOAD_STEP_READINESS_KEY, {})
    run_state = st.session_state.get(RUN_WORKFLOW_STATE_KEY, {})
    run_step_ready = (
        isinstance(run_state, dict)
        and run_state.get("status") == RUN_STATUS_SUCCEEDED
        and not bool(run_state.get("inputs_changed_since_last_run"))
    )
    next_disabled = step.slug == "upload-inputs" and not bool(readiness.get("is_ready"))
    if step.slug == "run-v5" and not run_step_ready:
        next_disabled = True
    with previous_col:
        if st.button("Previous step", disabled=current_step_index() == 0):
            rewind_step()
            st.rerun()
    with next_col:
        last_step = current_step_index() == len(get_wizard_steps()) - 1
        label = "Restart wizard" if last_step else "Next step"
        if st.button(label, disabled=next_disabled and not last_step):
            if last_step:
                set_current_step(0)
            else:
                advance_step()
            st.rerun()
    if next_disabled:
        if step.slug == "upload-inputs":
            st.caption("Upload all three required inputs and resolve blocking errors to continue.")
        elif step.slug == "run-v5":
            st.caption("Complete a successful Run V5 with the current staged inputs to continue.")


def _display_phase_hint(step_slug: str, default_hint: str) -> str:
    if step_slug == "upload-inputs":
        return "Phase 2 live now"
    if step_slug == "run-v5":
        return "Phase 3 live now"
    return default_hint


def _display_step_summary(step_slug: str, default_summary: str) -> str:
    if step_slug == "upload-inputs":
        return "Stage and validate the three required run-scoped input files from one screen."
    if step_slug == "run-v5":
        return "Select the evaluation month, run frozen V5, and stay on this step for the outcome."
    return default_summary


def render_wizard_shell() -> None:
    step_index = current_step_index()
    total_steps = len(get_wizard_steps())

    st.title("OOS Opportunity Loss Workspace")
    st.caption(
        "Stateless Streamlit foundation for operating the frozen V5 opportunity-loss "
        "workflow from an internal browser session."
    )

    _render_shell_summary(step_index, total_steps)
    st.divider()
    _render_step_map(step_index)
    st.divider()
    _render_boundary_summary()
    st.divider()
    _render_current_step()
    st.divider()
    _render_navigation()
