from __future__ import annotations

import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.temp_workspace import ensure_session_workspace
from streamlit_app.services.run_workflow import (
    RUN_STATUS_FAILED,
    RUN_STATUS_SUCCEEDED,
    RUN_WORKFLOW_STATE_KEY,
    ensure_run_workflow_state,
    run_frozen_v5_for_session,
    set_selected_evaluation_month,
    sync_run_workflow_state,
)
from streamlit_app.services.upload_staging import (
    UPLOAD_REGISTRY_KEY,
    create_upload_registry,
    stage_uploaded_file,
)

UPLOAD_STEP_READINESS_KEY = "upload_step_readiness"


def test_run_workflow_status_sync_uses_stock_month_suggestion(tmp_path: Path) -> None:
    state = _build_session_state(
        tmp_path,
        stock_dates=("2026-03-01", "2026-03-15", "2026-03-31"),
    )

    payload = sync_run_workflow_state(state)

    assert payload["status"] == "idle"
    assert payload["status_label"] == "Idle"
    assert payload["selected_eval_year"] == 2026
    assert payload["selected_eval_month"] == 3
    assert payload["selected_period"] == "2026-03"
    assert payload["suggested_label"] == "March 2026"
    assert payload["suggestion_confident"] is True
    assert payload["month_hints"] == ["2026-03"]
    assert payload["can_run"] is True
    assert payload["blocking_messages"] == []
    assert payload["current_input_signature"]
    assert state["active_run_status"] == "Idle"


def test_run_workflow_status_blocks_without_upload_readiness(tmp_path: Path) -> None:
    state = _build_session_state(
        tmp_path,
        stock_dates=("2026-03-01", "2026-03-15"),
        include_readiness=False,
    )

    payload = sync_run_workflow_state(state)

    assert payload["status"] == "idle"
    assert payload["can_run"] is False
    assert "Visit Upload Inputs first" in payload["blocking_messages"][0]


def test_run_workflow_status_allows_month_override(tmp_path: Path) -> None:
    state = _build_session_state(
        tmp_path,
        stock_dates=("2026-03-01", "2026-03-15"),
    )

    ensure_run_workflow_state(state)
    payload = set_selected_evaluation_month(state, eval_year=2026, eval_month=4)

    assert payload["selected_eval_year"] == 2026
    assert payload["selected_eval_month"] == 4
    assert payload["selected_period"] == "2026-04"
    assert payload["suggested_label"] == "March 2026"
    assert payload["can_run"] is True


def test_run_workflow_rerun_reuses_current_staged_files(tmp_path: Path) -> None:
    state = _build_session_state(
        tmp_path,
        stock_dates=("2026-03-01", "2026-03-15"),
    )
    calls: list[dict[str, object]] = []

    def fake_build_request(*, workspace_root, staged_upload_registry, eval_year, eval_month, **_) -> dict[str, object]:
        current_sales = staged_upload_registry["sales"]["current_file"]
        calls.append(
            {
                "sales_name": current_sales["source_name"],
                "sales_path": current_sales["staged_path"],
                "workspace_root": workspace_root,
                "period": f"{eval_year}-{eval_month:02d}",
            }
        )
        return {"period": f"{eval_year}-{eval_month:02d}", "sales_name": current_sales["source_name"]}

    def fake_execute_run(request: dict[str, object]) -> _FakeRunResult:
        return _FakeRunResult.success(request)

    first_payload = run_frozen_v5_for_session(
        state,
        build_request_fn=fake_build_request,
        execute_run_fn=fake_execute_run,
    )
    _replace_sales_upload(state, payload=_sales_bytes("replacement.tsv"))
    second_payload = run_frozen_v5_for_session(
        state,
        build_request_fn=fake_build_request,
        execute_run_fn=fake_execute_run,
    )

    assert first_payload["status"] == RUN_STATUS_SUCCEEDED
    assert second_payload["status"] == RUN_STATUS_SUCCEEDED
    assert len(calls) == 2
    assert calls[0]["sales_name"] == "sales.tsv"
    assert calls[1]["sales_name"] == "replacement.tsv"
    assert calls[0]["sales_path"] == calls[1]["sales_path"]
    assert second_payload["last_run_input_signature"] == second_payload["current_input_signature"]
    assert second_payload["run_attempt_count"] == 2
    assert second_payload["inputs_changed_since_last_run"] is False


def test_run_workflow_failure_captures_structured_error(tmp_path: Path) -> None:
    state = _build_session_state(
        tmp_path,
        stock_dates=("2026-03-01", "2026-03-15"),
    )

    def fake_build_request(*, workspace_root, staged_upload_registry, eval_year, eval_month, **_) -> dict[str, object]:
        return {"period": f"{eval_year}-{eval_month:02d}"}

    def fake_execute_run(request: dict[str, object]) -> _FakeRunResult:
        return _FakeRunResult.failure(
            request,
            error_type="RuntimeError",
            error_message="analysis failed",
        )

    payload = run_frozen_v5_for_session(
        state,
        build_request_fn=fake_build_request,
        execute_run_fn=fake_execute_run,
    )

    assert payload["status"] == RUN_STATUS_FAILED
    assert payload["status_label"] == "Failed"
    assert payload["error"] == {
        "type": "RuntimeError",
        "message": "analysis failed",
    }
    assert payload["result"]["status"] == "failed"
    assert payload["run_attempt_count"] == 1
    assert state["active_run_status"] == "Failed"
    assert state[RUN_WORKFLOW_STATE_KEY]["last_run_period"] == "2026-03"


@dataclass(frozen=True)
class _FakeRunResult:
    ok: bool
    status: str
    payload: dict[str, object]
    error_type: str | None = None
    error_message: str | None = None

    @classmethod
    def success(cls, request: dict[str, object]) -> "_FakeRunResult":
        return cls(
            ok=True,
            status="success",
            payload={
                "ok": True,
                "status": "success",
                "period": request["period"],
                "request": dict(request),
                "artifacts": {"workbook": f"/tmp/{request['period']}.xlsx"},
                "detail_row_count": 12,
                "qa_summary_row_count": 3,
                "unmapped_site_count": 0,
                "lost_value_net_raw": 99.5,
            },
        )

    @classmethod
    def failure(
        cls,
        request: dict[str, object],
        *,
        error_type: str,
        error_message: str,
    ) -> "_FakeRunResult":
        return cls(
            ok=False,
            status="failed",
            error_type=error_type,
            error_message=error_message,
            payload={
                "ok": False,
                "status": "failed",
                "period": request["period"],
                "request": dict(request),
                "artifacts": {"workbook": f"/tmp/{request['period']}.xlsx"},
                "detail_row_count": 0,
                "qa_summary_row_count": 0,
                "unmapped_site_count": 0,
                "lost_value_net_raw": 0.0,
                "error_type": error_type,
                "error_message": error_message,
            },
        )

    def as_dict(self) -> dict[str, object]:
        return dict(self.payload)


class _FakeUpload:
    def __init__(self, name: str, payload: bytes) -> None:
        self.name = name
        self._payload = payload

    def getbuffer(self) -> memoryview:
        return memoryview(self._payload)


def _build_session_state(
    tmp_path: Path,
    *,
    stock_dates: tuple[str, ...],
    include_readiness: bool = True,
) -> dict[str, object]:
    workspace = ensure_session_workspace("phase-03-run-workflow", base_dir=tmp_path)
    registry = create_upload_registry(workspace.input_dir)

    stage_uploaded_file(
        _FakeUpload("sales.tsv", _sales_bytes("sales.tsv")),
        slot_key="sales",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        _FakeUpload("stock.csv", _stock_bytes(stock_dates)),
        slot_key="stock",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        _FakeUpload("sku-live.csv", _sku_bytes()),
        slot_key="sku_live",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )

    state: dict[str, object] = {
        "workspace_root": str(workspace.root),
        "workspace_input_dir": str(workspace.input_dir),
        "workspace_output_dir": str(workspace.output_dir),
        UPLOAD_REGISTRY_KEY: registry,
    }
    if include_readiness:
        state[UPLOAD_STEP_READINESS_KEY] = {
            "is_ready": True,
            "ready_slots": 3,
            "total_slots": 3,
            "warning_count": 0,
            "blocking_messages": [],
        }
    return state


def _replace_sales_upload(state: dict[str, object], *, payload: bytes) -> None:
    registry = state[UPLOAD_REGISTRY_KEY]
    stage_uploaded_file(
        _FakeUpload("replacement.tsv", payload),
        slot_key="sales",
        workspace_input_dir=state["workspace_input_dir"],
        registry=registry,
    )
    sync_run_workflow_state(state)


def _sales_bytes(name: str) -> bytes:
    buffer = BytesIO()
    pd.DataFrame(
        [
            {
                "Purchase Date": "2026-03-05",
                "Sku": "SKU-1",
                "stock": "BKK",
                "Quantity": 1,
                "Gross": 100,
                "Net": 90,
                "Product Name": name,
            }
        ]
    ).to_csv(buffer, sep="\t", index=False, encoding="utf-16")
    return buffer.getvalue()


def _stock_bytes(stock_dates: tuple[str, ...]) -> bytes:
    return pd.DataFrame(
        {
            "posting_date": list(stock_dates),
            "site_code": ["26GA"] * len(stock_dates),
            "article_code": ["SKU-1"] * len(stock_dates),
            "stock_balance": [5] * len(stock_dates),
        }
    ).to_csv(index=False).encode("utf-8")


def _sku_bytes() -> bytes:
    return pd.DataFrame([{"skuNo": "SKU-1"}]).to_csv(index=False).encode("utf-8")
