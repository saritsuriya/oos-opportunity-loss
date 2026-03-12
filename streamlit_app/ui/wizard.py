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
    from streamlit_app.services.v5_boundary import get_boundary_overview
except ModuleNotFoundError:
    from runtime.session_state import (
        advance_step,
        current_step_index,
        get_wizard_steps,
        rewind_step,
        set_current_step,
    )
    from services.v5_boundary import get_boundary_overview


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
            st.caption(step.phase_hint)
            st.write(status)
            st.write(step.summary)


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
        st.warning("Placeholder for Phase 2 input staging.")
        st.markdown(
            "\n".join(
                [
                    "- Sales, stock, and SKU upload widgets will land here next.",
                    "- Uploaded files will be copied into a per-session temporary workspace.",
                    "- The bundled site-mapping configuration will be shown read-only in this step.",
                ]
            )
        )
    elif step.slug == "run-v5":
        st.warning("Placeholder for Phase 3 V5 run orchestration.")
        st.markdown(
            "\n".join(
                [
                    "- This step will call the reusable V5 boundary instead of the CLI entrypoint.",
                    "- Operators will be able to run the frozen logic for a selected month.",
                    "- Run status and failure feedback will stay visible in the session shell.",
                ]
            )
        )
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
    with previous_col:
        if st.button("Previous step", disabled=current_step_index() == 0):
            rewind_step()
            st.rerun()
    with next_col:
        last_step = current_step_index() == len(get_wizard_steps()) - 1
        label = "Restart wizard" if last_step else "Next step"
        if st.button(label):
            if last_step:
                set_current_step(0)
            else:
                advance_step()
            st.rerun()


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
