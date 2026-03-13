"""Upload-step UI for staging and validating run-scoped input files."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping

import streamlit as st

try:
    from streamlit_app.services.input_validation import validate_staged_input
    from streamlit_app.services.upload_staging import (
        UPLOAD_REGISTRY_KEY,
        ensure_upload_registry,
        get_upload_slots,
        stage_uploaded_file,
    )
    from streamlit_app.services.v5_boundary import get_bundled_site_mapping_status
except ModuleNotFoundError:
    from services.input_validation import validate_staged_input
    from services.upload_staging import (
        UPLOAD_REGISTRY_KEY,
        ensure_upload_registry,
        get_upload_slots,
        stage_uploaded_file,
    )
    from services.v5_boundary import get_bundled_site_mapping_status

UPLOAD_VALIDATION_RESULTS_KEY = "upload_validation_results"
UPLOAD_UPLOAD_SIGNATURES_KEY = "upload_widget_signatures"
UPLOAD_STEP_READINESS_KEY = "upload_step_readiness"

_SLOT_DESCRIPTIONS = {
    "sales": "Monthly sales export used as the orders input for the frozen V5 run.",
    "stock": "Daily stock CSV with posting date, site code, article code, and stock balance.",
    "sku_live": "Current SKU/live CSV that defines the active product universe for the run.",
}


def render_upload_inputs_step() -> None:
    """Render the Phase 2 upload experience inside the existing wizard shell."""

    registry = _ensure_registry()
    validation_results = st.session_state.setdefault(UPLOAD_VALIDATION_RESULTS_KEY, {})

    _sync_existing_validations(registry, validation_results)
    readiness_placeholder = st.empty()

    columns = st.columns(len(get_upload_slots()))
    for column, slot in zip(columns, get_upload_slots(), strict=False):
        with column:
            with st.container(border=True):
                _render_slot_card(slot.key, registry[slot.key], validation_results)

    _sync_existing_validations(registry, validation_results)
    readiness = _compute_readiness(registry, validation_results)
    with readiness_placeholder.container():
        _render_readiness_banner(readiness)

    st.divider()
    _render_site_mapping_panel()
    st.session_state[UPLOAD_STEP_READINESS_KEY] = readiness


def _ensure_registry() -> dict[str, dict[str, object]]:
    registry = st.session_state.get(UPLOAD_REGISTRY_KEY)
    if isinstance(registry, Mapping):
        return registry  # type: ignore[return-value]
    return ensure_upload_registry(st.session_state)


def _sync_existing_validations(
    registry: Mapping[str, Mapping[str, object]],
    validation_results: dict[str, dict[str, object]],
) -> None:
    for slot in get_upload_slots():
        current_file = registry[slot.key].get("current_file")
        if not isinstance(current_file, Mapping):
            validation_results.pop(slot.key, None)
            continue
        if _validation_matches_current_file(current_file, validation_results.get(slot.key)):
            continue
        validation_results[slot.key] = validate_staged_input(current_file).as_dict()


def _validation_matches_current_file(
    current_file: Mapping[str, object],
    validation_result: Mapping[str, object] | None,
) -> bool:
    if not isinstance(validation_result, Mapping):
        return False
    return (
        validation_result.get("slot_key") == current_file.get("slot_key")
        and validation_result.get("source_name") == current_file.get("source_name")
        and validation_result.get("staged_path") == current_file.get("staged_path")
    )


def _render_readiness_banner(readiness: Mapping[str, object]) -> None:
    total_slots = int(readiness["total_slots"])
    ready_slots = int(readiness["ready_slots"])
    blocking_count = len(readiness["blocking_messages"])
    warning_count = int(readiness["warning_count"])

    ready_col, blocker_col, warning_col = st.columns(3)
    ready_col.metric("Required Uploads Ready", f"{ready_slots}/{total_slots}")
    blocker_col.metric("Blocking Issues", blocking_count)
    warning_col.metric("Warnings", warning_count)

    if readiness["is_ready"]:
        st.success("All required uploads are staged and ready for the Phase 3 run step.")
    else:
        blocker_lines = "\n".join(f"- {message}" for message in readiness["blocking_messages"])
        st.error(f"Resolve these blocking items before continuing:\n{blocker_lines}")


def _render_slot_card(
    slot_key: str,
    slot_state: Mapping[str, object],
    validation_results: dict[str, dict[str, object]],
) -> None:
    slot_label = str(slot_state["label"])
    accepted_extensions = tuple(str(extension) for extension in slot_state["accepted_extensions"])

    st.subheader(slot_label)
    st.caption(_SLOT_DESCRIPTIONS[slot_key])
    st.caption(f"Accepted formats: {_format_extensions(accepted_extensions)}")

    uploaded_file = st.file_uploader(
        f"Upload {slot_label} file",
        type=[extension.removeprefix(".") for extension in accepted_extensions],
        key=f"upload_{slot_key}_widget",
    )
    if uploaded_file is not None:
        _process_uploaded_file(slot_key, uploaded_file, validation_results)

    current_file = slot_state.get("current_file")
    if not isinstance(current_file, Mapping):
        st.info("Awaiting upload for this required input.")
        return

    validation_result = validation_results.get(slot_key)
    _render_current_file_state(current_file, validation_result)


def _process_uploaded_file(
    slot_key: str,
    uploaded_file: Any,
    validation_results: dict[str, dict[str, object]],
) -> None:
    upload_signatures = st.session_state.setdefault(UPLOAD_UPLOAD_SIGNATURES_KEY, {})
    signature = _build_upload_signature(uploaded_file)
    if upload_signatures.get(slot_key) == signature:
        return

    registry = _ensure_registry()
    staged_file = stage_uploaded_file(
        uploaded_file,
        slot_key=slot_key,
        workspace_input_dir=str(st.session_state["workspace_input_dir"]),
        registry=registry,
    )
    validation_results[slot_key] = validate_staged_input(staged_file).as_dict()
    upload_signatures[slot_key] = signature


def _build_upload_signature(uploaded_file: Any) -> str:
    payload = bytes(uploaded_file.getbuffer()) if hasattr(uploaded_file, "getbuffer") else bytes(uploaded_file.read())
    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    digest = hashlib.sha256(payload).hexdigest()
    return f"{getattr(uploaded_file, 'name', '')}:{digest}"


def _render_current_file_state(
    current_file: Mapping[str, object],
    validation_result: Mapping[str, object] | None,
) -> None:
    st.markdown(
        "\n".join(
            [
                f"**Current file:** {current_file['source_name']}",
                f"**Staged size:** {_format_file_size(int(current_file['size_bytes']))}",
            ]
        )
    )

    if not isinstance(validation_result, Mapping):
        st.warning("Validation has not finished yet for this file.")
        return

    errors = tuple(validation_result.get("errors", ()))
    warnings = tuple(validation_result.get("warnings", ()))
    _render_validation_summary(validation_result)
    if errors:
        st.error("Blocking validation issues found:")
        for issue in errors:
            st.markdown(f"- {issue['message']}")
    elif warnings:
        st.success("File staged successfully. Review the warnings below before continuing.")
        for issue in warnings:
            st.warning(issue["message"])
    else:
        st.success("File staged successfully and passed Phase 2 validation.")


def _render_validation_summary(validation_result: Mapping[str, object]) -> None:
    summary = validation_result.get("summary")
    if not isinstance(summary, Mapping):
        return

    lines: list[str] = []
    row_count = summary.get("row_count")
    if row_count is not None:
        lines.append(f"**Row count:** {row_count}")
    date_field = summary.get("date_field")
    if date_field:
        lines.append(f"**Date field:** {date_field}")
    min_date = summary.get("min_date")
    max_date = summary.get("max_date")
    if min_date and max_date:
        lines.append(f"**Date coverage:** {min_date} to {max_date}")
    month_hints = tuple(summary.get("month_hints", ()))
    if month_hints:
        lines.append(f"**Month hints:** {', '.join(str(month) for month in month_hints)}")

    if lines:
        st.markdown("\n".join(lines))


def _compute_readiness(
    registry: Mapping[str, Mapping[str, object]],
    validation_results: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    ready_slots = 0
    warning_count = 0
    blocking_messages: list[str] = []

    for slot in get_upload_slots():
        slot_state = registry[slot.key]
        current_file = slot_state.get("current_file")
        if not isinstance(current_file, Mapping):
            blocking_messages.append(f"{slot.label}: upload required.")
            continue

        validation_result = validation_results.get(slot.key)
        if not isinstance(validation_result, Mapping):
            blocking_messages.append(f"{slot.label}: validation pending.")
            continue

        errors = tuple(validation_result.get("errors", ()))
        warnings = tuple(validation_result.get("warnings", ()))
        warning_count += len(warnings)
        if errors:
            blocking_messages.extend(f"{slot.label}: {issue['message']}" for issue in errors)
            continue
        ready_slots += 1

    return {
        "is_ready": ready_slots == len(get_upload_slots()) and not blocking_messages,
        "ready_slots": ready_slots,
        "total_slots": len(get_upload_slots()),
        "warning_count": warning_count,
        "blocking_messages": blocking_messages,
    }


def _format_extensions(extensions: tuple[str, ...]) -> str:
    return ", ".join(extension.upper().removeprefix(".") for extension in extensions)


def _format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.1f} MB"


def _render_site_mapping_panel() -> None:
    status = get_bundled_site_mapping_status()

    with st.container(border=True):
        st.subheader("Bundled Site Mapping")
        if status.is_ready:
            st.success(status.status_label)
        else:
            st.error(status.status_label)

        path_col, row_col, virtual_col, site_col = st.columns(4)
        path_col.metric("Mapping Source", "Bundled")
        row_col.metric("Rows", status.active_mapping_rows if status.is_ready else status.total_rows)
        virtual_col.metric("Virtual Sites", status.virtual_site_count)
        site_col.metric("Mapped Sites", status.site_count)

        st.caption(status.path)
        for line in status.details:
            st.markdown(f"- {line}")
        if status.sample_virtual_sites:
            st.markdown(
                "**Sample virtual sites:** " + ", ".join(status.sample_virtual_sites)
            )
