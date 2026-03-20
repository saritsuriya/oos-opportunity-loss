"""Single-page operator shell for the Streamlit workspace."""

from __future__ import annotations

import streamlit as st

try:
    from streamlit_app.services.channel_state import get_selected_channel_label
    from streamlit_app.services.run_workflow import RUN_WORKFLOW_STATE_KEY
    from streamlit_app.services.v5_boundary import get_boundary_overview
    from streamlit_app.ui.review_results import render_review_results_step
    from streamlit_app.ui.run_v5 import render_run_v5_step
    from streamlit_app.ui.upload_inputs import UPLOAD_STEP_READINESS_KEY, render_upload_inputs_step
except ModuleNotFoundError:
    from services.channel_state import get_selected_channel_label
    from services.run_workflow import RUN_WORKFLOW_STATE_KEY
    from services.v5_boundary import get_boundary_overview
    from ui.review_results import render_review_results_step
    from ui.run_v5 import render_run_v5_step
    from ui.upload_inputs import UPLOAD_STEP_READINESS_KEY, render_upload_inputs_step


def _render_shell_summary() -> None:
    readiness = st.session_state.get(UPLOAD_STEP_READINESS_KEY, {})
    run_state = st.session_state.get(RUN_WORKFLOW_STATE_KEY, {})
    channel_label = get_selected_channel_label(st.session_state)

    session_col, upload_col, run_col, mapping_col = st.columns(4)
    session_col.metric("Session", st.session_state["session_id"])
    upload_col.metric(
        "Uploads Ready",
        f"{int(readiness.get('ready_slots', 0))}/{int(readiness.get('total_slots', 3))}",
    )
    run_col.metric("Channel", channel_label)
    mapping_col.metric("Run Status", str(run_state.get("status_label", "Idle")))


def _render_workflow_overview() -> None:
    st.subheader("Workflow")
    step_one, step_two, step_three = st.columns(3)
    with step_one:
        st.markdown("**1. Upload Inputs**")
        st.caption("Stage and validate sales, stock, and SKU/live files.")
    with step_two:
        st.markdown("**2. Run Frozen V5**")
        st.caption("Select the evaluation month and run the frozen calculation.")
    with step_three:
        st.markdown("**3. Review And Export**")
        st.caption("Inspect QA and download the generated workbook and CSV files.")


def _render_boundary_summary() -> None:
    overview = get_boundary_overview(st.session_state.get("selected_channel_key", "th"))
    with st.expander("System Context", expanded=False):
        st.markdown(
            "\n".join(
                [
                    f"- Pipeline: {overview.pipeline_name}",
                    f"- Integration mode: {overview.integration_mode}",
                    f"- Site mapping source: `{overview.site_mapping_path}`",
                    "- Uploaded inputs and generated outputs remain scoped to the active session workspace.",
                    "- Persistence, duplicate detection, and stronger auth remain deferred beyond this phase.",
                ]
            )
        )
        st.caption("Frozen V5 modules reserved behind the boundary:")
        for module in overview.modules:
            st.write(f"{module.import_path} - {module.responsibility}")


def render_wizard_shell() -> None:
    st.title("OOS Opportunity Loss Workspace")
    st.caption(
        "Single-page Streamlit workspace for operating the frozen V5 opportunity-loss "
        "workflow from an internal browser session."
    )

    _render_shell_summary()
    st.divider()
    _render_workflow_overview()
    st.divider()
    _render_boundary_summary()
    st.divider()

    st.subheader("Upload Inputs")
    render_upload_inputs_step()
    st.divider()

    st.subheader("Run Frozen V5")
    render_run_v5_step()
    st.divider()

    st.subheader("Review And Export")
    render_review_results_step()
