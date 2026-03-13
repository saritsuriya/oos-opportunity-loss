"""Run-step UI for selecting the evaluation month and executing frozen V5."""

from __future__ import annotations

import calendar
from pathlib import Path
from typing import Mapping

import streamlit as st

try:
    from streamlit_app.services.run_workflow import (
        RUN_STATUS_FAILED,
        RUN_STATUS_RUNNING,
        RUN_STATUS_SUCCEEDED,
        run_frozen_v5_for_session,
        set_selected_evaluation_month,
        sync_run_workflow_state,
    )
    from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY
except ModuleNotFoundError:
    from services.run_workflow import (
        RUN_STATUS_FAILED,
        RUN_STATUS_RUNNING,
        RUN_STATUS_SUCCEEDED,
        run_frozen_v5_for_session,
        set_selected_evaluation_month,
        sync_run_workflow_state,
    )
    from services.upload_staging import UPLOAD_REGISTRY_KEY


def render_run_v5_step() -> None:
    run_state = sync_run_workflow_state(st.session_state)
    upload_readiness = st.session_state.get("upload_step_readiness", {})
    uploads_ready = bool(upload_readiness.get("is_ready")) if isinstance(upload_readiness, Mapping) else False

    _render_run_metrics(run_state)
    _render_staged_input_recap()
    if uploads_ready:
        run_state = _render_month_controls(run_state)
        _render_suggestion_guidance(run_state)
    else:
        st.caption("Upload and validate all required inputs above to unlock month selection.")
    _render_preconditions(run_state)

    run_button_disabled = not bool(run_state["can_run"]) or run_state["status"] == RUN_STATUS_RUNNING
    if st.button("Run V5", type="primary", disabled=run_button_disabled):
        selected_period = run_state.get("selected_period") or "the selected month"
        with st.spinner(f"Running frozen V5 for {selected_period}..."):
            run_state = run_frozen_v5_for_session(st.session_state)

    _render_run_outcome(run_state)


def _render_run_metrics(run_state: Mapping[str, object]) -> None:
    status_col, period_col, attempts_col = st.columns(3)
    status_col.metric("Run Status", str(run_state["status_label"]))
    period_col.metric("Selected Period", str(run_state.get("selected_period") or "Not selected"))
    attempts_col.metric("Run Attempts", int(run_state.get("run_attempt_count", 0)))


def _render_staged_input_recap() -> None:
    registry = st.session_state.get(UPLOAD_REGISTRY_KEY, {})
    with st.container(border=True):
        st.subheader("Current Staged Inputs")
        for slot_key, label in (
            ("sales", "Sales"),
            ("stock", "Stock"),
            ("sku_live", "SKU / Live"),
        ):
            slot_state = registry.get(slot_key, {})
            current_file = slot_state.get("current_file") if isinstance(slot_state, Mapping) else None
            if not isinstance(current_file, Mapping):
                st.markdown(f"- **{label}:** not staged yet")
                continue
            st.markdown(
                f"- **{label}:** {current_file['source_name']} "
                f"(`{Path(str(current_file['staged_path'])).name}`)"
            )


def _render_month_controls(run_state: Mapping[str, object]) -> dict[str, object]:
    selected_year = int(run_state.get("selected_eval_year") or _fallback_year(run_state))
    selected_month = int(run_state.get("selected_eval_month") or 1)

    year_col, month_col = st.columns(2)
    with year_col:
        year_value = int(
            st.number_input(
                "Evaluation year",
                min_value=2020,
                max_value=2100,
                value=selected_year,
                step=1,
            )
        )
    with month_col:
        month_value = int(
            st.selectbox(
                "Evaluation month",
                options=tuple(range(1, 13)),
                index=max(selected_month - 1, 0),
                format_func=lambda month: calendar.month_name[int(month)],
            )
        )

    if (
        year_value != run_state.get("selected_eval_year")
        or month_value != run_state.get("selected_eval_month")
    ):
        return set_selected_evaluation_month(
            st.session_state,
            eval_year=year_value,
            eval_month=month_value,
        )
    return dict(run_state)


def _render_suggestion_guidance(run_state: Mapping[str, object]) -> None:
    suggested_label = run_state.get("suggested_label")
    suggestion_reason = str(run_state.get("suggestion_reason") or "")
    month_hints = [str(value) for value in run_state.get("month_hints", [])]

    if suggested_label and bool(run_state.get("suggestion_confident")):
        st.info(f"Suggested evaluation month: {suggested_label}. {suggestion_reason}")
    elif month_hints:
        st.warning(
            "The staged stock file spans multiple months. "
            "Choose the evaluation month manually."
        )
        st.caption("Detected stock months: " + ", ".join(month_hints))
    else:
        st.caption(suggestion_reason)

    selected_period = run_state.get("selected_period")
    if selected_period:
        st.caption(f"Selected period for this run: {selected_period}")


def _render_preconditions(run_state: Mapping[str, object]) -> None:
    blocking_messages = [str(message) for message in run_state.get("blocking_messages", [])]
    if blocking_messages:
        st.error(
            "Resolve these items before running V5:\n"
            + "\n".join(f"- {message}" for message in blocking_messages)
        )
    elif run_state["status"] != RUN_STATUS_RUNNING:
        st.success("The staged inputs are ready. Run V5 when you are ready to calculate.")


def _render_run_outcome(run_state: Mapping[str, object]) -> None:
    if bool(run_state.get("inputs_changed_since_last_run")):
        st.warning(
            "One or more staged inputs changed after the last run. "
            "Run V5 again before moving to review and export."
        )

    status = str(run_state.get("status"))
    if status == RUN_STATUS_SUCCEEDED:
        result = run_state.get("result") or {}
        if not isinstance(result, Mapping):
            result = {}
        st.success(
            f"Frozen V5 completed successfully for {run_state.get('last_run_period') or run_state.get('selected_period')}."
        )
        detail_col, qa_col, loss_col = st.columns(3)
        detail_col.metric("Detail Rows", int(result.get("detail_row_count", 0)))
        qa_col.metric("QA Rows", int(result.get("qa_summary_row_count", 0)))
        loss_col.metric(
            "Lost Value Net",
            f"{float(result.get('lost_value_net_raw', 0.0)):,.2f}",
        )
        workbook_path = _extract_artifact_path(result, "workbook")
        if workbook_path:
            st.caption(f"Workbook ready: {workbook_path}")
        st.info("Review and export the generated workbook and CSV outputs below when you are ready.")
        return

    if status == RUN_STATUS_FAILED:
        error = run_state.get("error") or {}
        if not isinstance(error, Mapping):
            error = {}
        st.error(
            f"Frozen V5 failed for {run_state.get('last_run_period') or run_state.get('selected_period')}."
        )
        st.markdown(
            "\n".join(
                [
                    f"**Error type:** {error.get('type', 'Unknown')}",
                    f"**Error message:** {error.get('message', 'No error message available.')}",
                ]
            )
        )
        st.info(
            "You can rerun with the current staged files, or go back to Upload Inputs to replace them first."
        )
        return

    if status == RUN_STATUS_RUNNING:
        st.info("Frozen V5 is currently running for the selected month.")
        return

    st.info("Review the selected month and click Run V5 when you are ready.")


def _extract_artifact_path(result: Mapping[str, object], artifact_key: str) -> str | None:
    artifacts = result.get("artifacts")
    if not isinstance(artifacts, Mapping):
        return None
    value = artifacts.get(artifact_key)
    if not value:
        return None
    return str(value)


def _fallback_year(run_state: Mapping[str, object]) -> int:
    suggested_year = run_state.get("suggested_eval_year")
    if suggested_year is not None:
        return int(suggested_year)
    last_run_period = run_state.get("last_run_period")
    if isinstance(last_run_period, str) and "-" in last_run_period:
        year_text, _ = last_run_period.split("-", maxsplit=1)
        return int(year_text)
    return 2026
