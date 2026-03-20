"""Session-local orchestration helpers for the frozen V5 run step."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable, Mapping, MutableMapping

try:
    from streamlit_app.services.channel_state import get_selected_channel
    from streamlit_app.services.run_execution import (
        build_run_request,
        execute_frozen_v5_run,
        suggest_evaluation_month,
    )
    from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY
except ModuleNotFoundError:
    from services.channel_state import get_selected_channel
    from services.run_execution import (
        build_run_request,
        execute_frozen_v5_run,
        suggest_evaluation_month,
    )
    from services.upload_staging import UPLOAD_REGISTRY_KEY

RUN_WORKFLOW_STATE_KEY = "run_workflow_state"
UPLOAD_STEP_READINESS_KEY = "upload_step_readiness"

RUN_STATUS_IDLE = "idle"
RUN_STATUS_RUNNING = "running"
RUN_STATUS_SUCCEEDED = "succeeded"
RUN_STATUS_FAILED = "failed"


def ensure_run_workflow_state(
    state: MutableMapping[str, Any],
) -> dict[str, object]:
    existing = state.get(RUN_WORKFLOW_STATE_KEY)
    payload = _default_run_workflow_state()
    if isinstance(existing, Mapping):
        payload.update(
            {
                key: _copy_session_value(value)
                for key, value in existing.items()
                if key in payload
            }
        )
    payload["selected_period"] = _format_period(
        payload.get("selected_eval_year"), payload.get("selected_eval_month")
    )
    payload["inputs_changed_since_last_run"] = bool(
        payload.get("last_run_input_signature")
        and payload.get("current_input_signature")
        and payload.get("last_run_input_signature") != payload.get("current_input_signature")
    )
    state[RUN_WORKFLOW_STATE_KEY] = payload
    _sync_active_run_status(state, payload)
    return payload


def sync_run_workflow_state(
    state: MutableMapping[str, Any],
) -> dict[str, object]:
    payload = ensure_run_workflow_state(state)
    registry = state.get(UPLOAD_REGISTRY_KEY)
    payload["current_input_signature"] = _build_registry_signature(registry)
    payload["selected_channel_key"] = get_selected_channel(state)

    suggestion = _resolve_month_suggestion(registry, payload["selected_channel_key"])
    payload["suggested_eval_year"] = suggestion["eval_year"]
    payload["suggested_eval_month"] = suggestion["eval_month"]
    payload["suggested_label"] = suggestion["label"]
    payload["suggestion_confident"] = suggestion["is_confident"]
    payload["suggestion_reason"] = suggestion["reason"]
    payload["month_hints"] = list(suggestion["month_hints"])

    if (
        payload.get("selected_eval_year") is None
        or payload.get("selected_eval_month") is None
    ) and suggestion["eval_year"] and suggestion["eval_month"]:
        payload["selected_eval_year"] = suggestion["eval_year"]
        payload["selected_eval_month"] = suggestion["eval_month"]

    payload["selected_period"] = _format_period(
        payload.get("selected_eval_year"), payload.get("selected_eval_month")
    )
    payload["blocking_messages"] = _compute_blocking_messages(state, payload)
    payload["can_run"] = not payload["blocking_messages"]
    payload["inputs_changed_since_last_run"] = bool(
        payload.get("last_run_input_signature")
        and payload.get("current_input_signature")
        and payload.get("last_run_input_signature") != payload.get("current_input_signature")
    )
    state[RUN_WORKFLOW_STATE_KEY] = payload
    _sync_active_run_status(state, payload)
    return payload


def set_selected_evaluation_month(
    state: MutableMapping[str, Any],
    *,
    eval_year: int,
    eval_month: int,
) -> dict[str, object]:
    if eval_month < 1 or eval_month > 12:
        msg = f"eval_month must be between 1 and 12, got {eval_month!r}"
        raise ValueError(msg)
    payload = ensure_run_workflow_state(state)
    payload["selected_eval_year"] = int(eval_year)
    payload["selected_eval_month"] = int(eval_month)
    state[RUN_WORKFLOW_STATE_KEY] = payload
    return sync_run_workflow_state(state)


def run_frozen_v5_for_session(
    state: MutableMapping[str, Any],
    *,
    build_request_fn: Callable[..., Any] = build_run_request,
    execute_run_fn: Callable[[Any], Any] = execute_frozen_v5_run,
) -> dict[str, object]:
    payload = sync_run_workflow_state(state)
    if not payload["can_run"]:
        return payload

    payload["status"] = RUN_STATUS_RUNNING
    payload["status_label"] = _status_label(RUN_STATUS_RUNNING)
    payload["last_started_at"] = _timestamp_now()
    payload["result"] = None
    payload["error"] = None
    state[RUN_WORKFLOW_STATE_KEY] = payload
    _sync_active_run_status(state, payload)

    try:
        request = build_request_fn(
            workspace_root=str(state["workspace_root"]),
            staged_upload_registry=state[UPLOAD_REGISTRY_KEY],
            channel_key=get_selected_channel(state),
            eval_year=int(payload["selected_eval_year"]),
            eval_month=int(payload["selected_eval_month"]),
        )
        result = execute_run_fn(request)
    except Exception as exc:
        return _finish_failed_run(
            state,
            error_type=type(exc).__name__,
            error_message=str(exc),
            result_payload=None,
        )

    result_payload = result.as_dict()
    if bool(result.ok):
        return _finish_successful_run(state, result_payload=result_payload)

    return _finish_failed_run(
        state,
        error_type=str(result.error_type or "RunFailed"),
        error_message=str(result.error_message or "Frozen V5 run failed."),
        result_payload=result_payload,
    )


def _finish_successful_run(
    state: MutableMapping[str, Any],
    *,
    result_payload: Mapping[str, object],
) -> dict[str, object]:
    payload = ensure_run_workflow_state(state)
    payload["status"] = RUN_STATUS_SUCCEEDED
    payload["status_label"] = _status_label(RUN_STATUS_SUCCEEDED)
    payload["last_finished_at"] = _timestamp_now()
    payload["last_run_period"] = payload.get("selected_period")
    payload["last_run_input_signature"] = payload.get("current_input_signature")
    payload["inputs_changed_since_last_run"] = False
    payload["result"] = dict(result_payload)
    payload["error"] = None
    payload["run_attempt_count"] = int(payload.get("run_attempt_count", 0)) + 1
    state[RUN_WORKFLOW_STATE_KEY] = payload
    _sync_active_run_status(state, payload)
    return payload


def _finish_failed_run(
    state: MutableMapping[str, Any],
    *,
    error_type: str,
    error_message: str,
    result_payload: Mapping[str, object] | None,
) -> dict[str, object]:
    payload = ensure_run_workflow_state(state)
    payload["status"] = RUN_STATUS_FAILED
    payload["status_label"] = _status_label(RUN_STATUS_FAILED)
    payload["last_finished_at"] = _timestamp_now()
    payload["last_run_period"] = payload.get("selected_period")
    payload["last_run_input_signature"] = payload.get("current_input_signature")
    payload["inputs_changed_since_last_run"] = False
    payload["result"] = dict(result_payload) if isinstance(result_payload, Mapping) else None
    payload["error"] = {
        "type": error_type,
        "message": error_message,
    }
    payload["run_attempt_count"] = int(payload.get("run_attempt_count", 0)) + 1
    state[RUN_WORKFLOW_STATE_KEY] = payload
    _sync_active_run_status(state, payload)
    return payload


def _default_run_workflow_state() -> dict[str, object]:
    return {
        "status": RUN_STATUS_IDLE,
        "status_label": _status_label(RUN_STATUS_IDLE),
        "selected_eval_year": None,
        "selected_eval_month": None,
        "selected_period": None,
        "selected_channel_key": None,
        "suggested_eval_year": None,
        "suggested_eval_month": None,
        "suggested_label": None,
        "suggestion_confident": False,
        "suggestion_reason": "Upload a stock file to suggest the evaluation month.",
        "month_hints": [],
        "can_run": False,
        "blocking_messages": [],
        "current_input_signature": None,
        "last_run_input_signature": None,
        "inputs_changed_since_last_run": False,
        "last_started_at": None,
        "last_finished_at": None,
        "last_run_period": None,
        "run_attempt_count": 0,
        "result": None,
        "error": None,
    }


def _compute_blocking_messages(
    state: Mapping[str, Any],
    payload: Mapping[str, object],
) -> list[str]:
    messages: list[str] = []
    if not state.get("workspace_root"):
        messages.append("Session workspace is not ready yet.")

    readiness = state.get(UPLOAD_STEP_READINESS_KEY)
    if not isinstance(readiness, Mapping):
        messages.append("Visit Upload Inputs first so the staged files can be validated.")
    elif not bool(readiness.get("is_ready")):
        blocking_messages = readiness.get("blocking_messages")
        if isinstance(blocking_messages, list) and blocking_messages:
            messages.extend(str(message) for message in blocking_messages)
        else:
            messages.append(
                "Upload all required inputs and resolve blocking validation issues before running V5."
            )

    year = payload.get("selected_eval_year")
    month = payload.get("selected_eval_month")
    if year is None or month is None:
        messages.append("Choose the evaluation month before running V5.")
    elif int(month) < 1 or int(month) > 12:
        messages.append("Evaluation month must be between 1 and 12.")

    return messages


def _resolve_month_suggestion(
    registry: object,
    channel_key: object,
) -> dict[str, object]:
    if not isinstance(registry, Mapping):
        return {
            "eval_year": None,
            "eval_month": None,
            "label": None,
            "is_confident": False,
            "month_hints": [],
            "reason": "Upload a stock file to suggest the evaluation month.",
        }

    try:
        suggestion = suggest_evaluation_month(
            registry,
            channel_key=str(channel_key or ""),
        )
    except Exception as exc:
        return {
            "eval_year": None,
            "eval_month": None,
            "label": None,
            "is_confident": False,
            "month_hints": [],
            "reason": f"Could not inspect the staged stock file yet: {exc}",
        }
    return suggestion.as_dict()


def _build_registry_signature(registry: object) -> str | None:
    if not isinstance(registry, Mapping):
        return None
    parts: list[str] = []
    for slot_key in ("sales", "stock", "sku_live"):
        slot_payload = registry.get(slot_key)
        if not isinstance(slot_payload, Mapping):
            continue
        current_file = slot_payload.get("current_file")
        if not isinstance(current_file, Mapping):
            continue
        parts.append(
            ":".join(
                [
                    slot_key,
                    str(current_file.get("source_name", "")),
                    str(current_file.get("staged_path", "")),
                    str(current_file.get("size_bytes", "")),
                ]
            )
        )
    return "|".join(parts) or None


def _format_period(eval_year: object, eval_month: object) -> str | None:
    if eval_year is None or eval_month is None:
        return None
    return f"{int(eval_year)}-{int(eval_month):02d}"


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _status_label(status: str) -> str:
    return {
        RUN_STATUS_IDLE: "Idle",
        RUN_STATUS_RUNNING: "Running",
        RUN_STATUS_SUCCEEDED: "Succeeded",
        RUN_STATUS_FAILED: "Failed",
    }.get(status, "Idle")


def _sync_active_run_status(
    state: MutableMapping[str, Any],
    payload: Mapping[str, object],
) -> None:
    state["active_run_status"] = str(payload.get("status_label", "Idle"))


def _copy_session_value(value: object) -> object:
    if isinstance(value, list):
        return list(value)
    if isinstance(value, dict):
        return dict(value)
    return value
