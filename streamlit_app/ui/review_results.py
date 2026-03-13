"""Phase 4 review workspace for completed frozen V5 runs."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd
import streamlit as st

try:
    from streamlit_app.services.results_workspace import load_results_workspace
    from streamlit_app.services.run_workflow import sync_run_workflow_state
except ModuleNotFoundError:
    from services.results_workspace import load_results_workspace
    from services.run_workflow import sync_run_workflow_state

UPLOAD_VALIDATION_RESULTS_KEY = "upload_validation_results"


def render_review_results_step() -> None:
    run_state = sync_run_workflow_state(st.session_state)
    load_result = load_results_workspace(run_state)

    if not load_result.ok or load_result.payload is None:
        _render_results_error(load_result.error_type, load_result.error_message)
        return

    payload = load_result.payload
    upload_warnings = _collect_upload_warnings(st.session_state)

    st.subheader("Run Overview")
    _render_trust_banner(payload.overview, upload_warnings)
    _render_overview_metrics(payload.overview)

    overview_tab, site_tab, sku_tab, detail_tab, qa_tab, export_tab = st.tabs(
        [
            "Overview",
            "By Site",
            "By SKU",
            "Detail",
            "QA And Trust",
            "Export",
        ]
    )

    with overview_tab:
        _render_overview_tab(payload, upload_warnings)

    with site_tab:
        st.subheader("Summary by Site")
        st.dataframe(
            _arrow_safe_frame(payload.summary_site),
            width="stretch",
            hide_index=True,
        )

    with sku_tab:
        st.subheader("Summary by SKU")
        st.dataframe(
            _arrow_safe_frame(payload.summary_sku),
            width="stretch",
            hide_index=True,
        )

    with detail_tab:
        st.subheader("Detail Review")
        st.caption(
            "Key explainability fields remain visible in this browser view: "
            "baseline source, baseline window, recorded days, OOS days, and actual quantity."
        )
        st.dataframe(
            _arrow_safe_frame(_ordered_detail_frame(payload.detail)),
            width="stretch",
            hide_index=True,
            height=420,
        )

    with qa_tab:
        _render_qa_tab(payload, upload_warnings)

    with export_tab:
        _render_export_tab(payload)


def _render_trust_banner(
    overview: Mapping[str, object],
    upload_warnings: list[str],
) -> None:
    unmapped_site_count = int(overview.get("unmapped_site_count") or 0)
    is_current = bool(overview.get("is_current"))

    reasons: list[str] = []
    if upload_warnings:
        reasons.append(f"{len(upload_warnings)} upload warning(s)")
    if unmapped_site_count > 0:
        reasons.append(f"{unmapped_site_count} unmapped site row(s)")
    if not is_current:
        reasons.append("staged inputs changed after the last successful run")

    if reasons:
        st.warning(
            "Review QA and trust details before exporting. "
            + "Current signals: "
            + ", ".join(reasons)
            + "."
        )
    else:
        st.success("No high-visibility QA or trust issues were detected for this completed run.")


def _render_overview_metrics(overview: Mapping[str, object]) -> None:
    metric_row_one = st.columns(4)
    metric_row_one[0].metric("Period", str(overview.get("period") or "-"))
    metric_row_one[1].metric(
        "Lost Value Net",
        f"{float(overview.get('lost_value_net_raw') or 0.0):,.2f}",
    )
    metric_row_one[2].metric("Detail Rows", int(overview.get("detail_row_count") or 0))
    metric_row_one[3].metric(
        "Unmapped Site Rows",
        int(overview.get("unmapped_site_count") or 0),
    )

    metric_row_two = st.columns(4)
    metric_row_two[0].metric(
        "Total Lost Qty Raw",
        f"{float(overview.get('total_lost_qty_raw') or 0.0):,.2f}",
    )
    metric_row_two[1].metric(
        "Total Lost Value Gross",
        f"{float(overview.get('total_lost_value_gross_raw') or 0.0):,.2f}",
    )
    metric_row_two[2].metric("QA Rows", int(overview.get("qa_summary_row_count") or 0))
    metric_row_two[3].metric(
        "Current Run",
        "Yes" if bool(overview.get("is_current")) else "No",
    )


def _render_overview_tab(payload, upload_warnings: list[str]) -> None:
    st.subheader("Summary Total")
    st.dataframe(
        _arrow_safe_frame(payload.summary_total),
        width="stretch",
        hide_index=True,
    )

    site_col, sku_col = st.columns(2)
    with site_col:
        st.subheader("Top Sites")
        st.dataframe(
            _arrow_safe_frame(payload.summary_site.head(5)),
            width="stretch",
            hide_index=True,
        )
    with sku_col:
        st.subheader("Top SKUs")
        st.dataframe(
            _arrow_safe_frame(payload.summary_sku.head(5)),
            width="stretch",
            hide_index=True,
        )

    if upload_warnings:
        st.caption("Upload warnings carried into review:")
        for warning in upload_warnings:
            st.markdown(f"- {warning}")


def _render_qa_tab(payload, upload_warnings: list[str]) -> None:
    st.subheader("QA Summary")
    st.dataframe(
        _arrow_safe_frame(payload.qa_summary),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Unmapped Site Codes")
    if len(payload.unmapped_site.index) == 0:
        st.success("No unmapped site codes were detected in the completed run.")
    else:
        st.dataframe(
            _arrow_safe_frame(payload.unmapped_site),
            width="stretch",
            hide_index=True,
        )

    if upload_warnings:
        st.subheader("Upload Warnings")
        for warning in upload_warnings:
            st.markdown(f"- {warning}")

    st.subheader("Definitions")
    st.dataframe(
        _arrow_safe_frame(payload.definitions),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Calculation Example")
    st.dataframe(
        _arrow_safe_frame(payload.calculation_example),
        width="stretch",
        hide_index=True,
    )


def _render_export_tab(payload) -> None:
    st.subheader("Export Files")
    if not payload.is_current:
        st.warning(
            "The staged inputs changed after the last successful run. "
            "Run V5 again before exporting these files."
        )

    workbook_artifact = payload.export_manifest[0]
    st.markdown(f"**{workbook_artifact.label}**")
    st.caption(workbook_artifact.path.name)
    st.download_button(
        label="Download Excel Workbook",
        data=workbook_artifact.path.read_bytes(),
        file_name=workbook_artifact.path.name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="download_workbook",
        disabled=not payload.is_current,
    )

    st.subheader("CSV Exports")
    for artifact in payload.export_manifest[1:]:
        label_col, action_col = st.columns([3, 2])
        with label_col:
            st.markdown(f"**{artifact.label}**")
            st.caption(artifact.path.name)
        with action_col:
            st.download_button(
                label=f"Download {artifact.label}",
                data=artifact.path.read_bytes(),
                file_name=artifact.path.name,
                mime="text/csv",
                key=f"download_{artifact.key}",
                disabled=not payload.is_current,
            )


def _ordered_detail_frame(detail: pd.DataFrame) -> pd.DataFrame:
    preferred_columns = [
        "sku",
        "virtual_site",
        "product_name",
        "loss_net",
        "loss_gross",
        "lost_qty_raw",
        "baseline_source",
        "baseline_window_start",
        "baseline_window_end",
        "recorded_days",
        "oos_days_jan",
        "actual_qty_jan",
    ]
    ordered = [column for column in preferred_columns if column in detail.columns]
    remaining = [column for column in detail.columns if column not in ordered]
    return detail.loc[:, [*ordered, *remaining]]


def _collect_upload_warnings(state: Mapping[str, Any]) -> list[str]:
    validation_results = state.get(UPLOAD_VALIDATION_RESULTS_KEY, {})
    if not isinstance(validation_results, Mapping):
        return []

    warnings: list[str] = []
    for result in validation_results.values():
        if not isinstance(result, Mapping):
            continue
        for issue in result.get("warnings", []):
            if isinstance(issue, Mapping) and issue.get("message"):
                warnings.append(str(issue["message"]))
    return warnings


def _arrow_safe_frame(frame: pd.DataFrame) -> pd.DataFrame:
    safe_frame = frame.copy()
    for column in safe_frame.columns:
        if safe_frame[column].dtype != "object":
            continue
        non_null = safe_frame[column].dropna()
        if non_null.empty:
            continue
        types = {type(value) for value in non_null}
        if len(types) > 1:
            safe_frame[column] = safe_frame[column].astype(str)
    return safe_frame


def _render_results_error(error_type: str | None, error_message: str | None) -> None:
    if error_type == "MissingResultsArtifact":
        st.error(error_message or "One or more generated result files are missing.")
        st.info(
            "The completed run artifacts are no longer available in this session workspace. "
            "Go back to `Run Frozen V5` and rerun before reviewing or exporting."
        )
        return

    if error_type == "InvalidResultsWorkspaceState":
        st.error(error_message or "A completed successful run is required before review.")
        st.info(
            "Return to `Run Frozen V5`, complete a successful run for the current staged inputs, "
            "then come back to review the results."
        )
        return

    st.error(
        error_message
        or "The current session does not have a completed run ready for review."
    )
    st.info(
        "Return to `Run Frozen V5`, complete a successful run for the current staged inputs, "
        "then come back to review the results."
    )
