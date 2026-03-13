from __future__ import annotations

from io import BytesIO
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.run_workflow import (
    RUN_STATUS_FAILED,
    RUN_STATUS_SUCCEEDED,
    RUN_WORKFLOW_STATE_KEY,
    sync_run_workflow_state,
)
from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY, stage_uploaded_file
from streamlit_app.ui import run_v5 as run_v5_ui
from streamlit_app.ui.upload_inputs import UPLOAD_STEP_READINESS_KEY


def test_run_step_month_controls_show_suggestion_and_explicit_run_action(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_run_ready_state(app, stock_dates=("2026-03-01", "2026-03-15", "2026-03-31"))

    assert len(app.exception) == 0
    assert any(input_widget.label == "Evaluation year" for input_widget in app.number_input)
    assert any(input_widget.label == "Evaluation month" for input_widget in app.selectbox)
    assert any(button.label == "Run V5" for button in app.button)
    assert any(
        "Suggested evaluation month: March 2026." in node.value for node in app.info
    )
    assert app.session_state[RUN_WORKFLOW_STATE_KEY]["selected_period"] == "2026-03"


def test_run_step_outcome_success_stays_on_step_and_enables_review(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(run_v5_ui, "run_frozen_v5_for_session", _fake_successful_run)

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_run_ready_state(app, stock_dates=("2026-03-01", "2026-03-15"))

    _click_button(app, "Run V5")

    assert len(app.exception) == 0
    assert app.session_state["active_run_status"] == "Succeeded"
    assert any("completed successfully" in node.value for node in app.success)
    assert any("Review and export the generated workbook and CSV outputs below" in node.value for node in app.info)
    assert any(node.value == "Review And Export" for node in app.subheader)


def test_run_step_outcome_failure_shows_rerun_guidance(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))
    monkeypatch.setattr(run_v5_ui, "run_frozen_v5_for_session", _fake_failed_run)

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_run_ready_state(app, stock_dates=("2026-03-01", "2026-03-15"))

    _click_button(app, "Run V5")

    assert len(app.exception) == 0
    assert app.session_state[RUN_WORKFLOW_STATE_KEY]["status"] == RUN_STATUS_FAILED
    assert any("Frozen V5 failed" in node.value for node in app.error)
    assert any("analysis failed" in node.value for node in app.markdown)
    assert any("rerun with the current staged files" in node.value for node in app.info)


def test_run_step_rerun_uses_current_staged_files(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))
    calls: list[str] = []

    def fake_run(state) -> dict[str, object]:
        current_sales = state[UPLOAD_REGISTRY_KEY]["sales"]["current_file"]["source_name"]
        calls.append(str(current_sales))
        return _mark_run_success(state)

    monkeypatch.setattr(run_v5_ui, "run_frozen_v5_for_session", fake_run)

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_run_ready_state(app, stock_dates=("2026-03-01", "2026-03-15"))

    _click_button(app, "Run V5")
    _replace_sales_upload(app, payload=_sales_bytes("replacement.tsv"))

    assert any("staged inputs changed" in node.value.lower() for node in app.warning)

    _click_button(app, "Run V5")

    assert len(app.exception) == 0
    assert calls == ["sales.tsv", "replacement.tsv"]
    assert app.session_state[RUN_WORKFLOW_STATE_KEY]["status"] == RUN_STATUS_SUCCEEDED


class _FakeUpload:
    def __init__(self, name: str, payload: bytes) -> None:
        self.name = name
        self._payload = payload

    def getbuffer(self) -> memoryview:
        return memoryview(self._payload)


def _seed_run_ready_state(app: AppTest, *, stock_dates: tuple[str, ...]) -> None:
    registry = {
        slot_key: dict(slot_state)
        for slot_key, slot_state in app.session_state[UPLOAD_REGISTRY_KEY].items()
    }
    workspace_input_dir = Path(app.session_state["workspace_input_dir"])

    stage_uploaded_file(
        _FakeUpload("sales.tsv", _sales_bytes("sales.tsv")),
        slot_key="sales",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        _FakeUpload("stock.csv", _stock_bytes(stock_dates)),
        slot_key="stock",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        _FakeUpload("sku-live.csv", _sku_bytes()),
        slot_key="sku_live",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )

    app.session_state[UPLOAD_REGISTRY_KEY] = registry
    app.session_state[UPLOAD_STEP_READINESS_KEY] = {
        "is_ready": True,
        "ready_slots": 3,
        "total_slots": 3,
        "warning_count": 0,
        "blocking_messages": [],
    }
    app.session_state["current_step_index"] = 2
    app.run()


def _replace_sales_upload(app: AppTest, *, payload: bytes) -> None:
    registry = app.session_state[UPLOAD_REGISTRY_KEY]
    workspace_input_dir = Path(app.session_state["workspace_input_dir"])
    stage_uploaded_file(
        _FakeUpload("replacement.tsv", payload),
        slot_key="sales",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )
    app.session_state[UPLOAD_REGISTRY_KEY] = registry
    app.run()


def _click_button(app: AppTest, label: str) -> None:
    _button_by_label(app, label).click().run()


def _button_by_label(app: AppTest, label: str):
    for button in app.button:
        if button.label == label:
            return button
    raise AssertionError(f"Button not found: {label}")


def _fake_successful_run(state) -> dict[str, object]:
    return _mark_run_success(state)


def _fake_failed_run(state) -> dict[str, object]:
    payload = sync_run_workflow_state(state)
    payload.update(
        {
            "status": RUN_STATUS_FAILED,
            "status_label": "Failed",
            "last_finished_at": "2026-03-13T11:30:00+00:00",
            "last_run_period": payload["selected_period"],
            "last_run_input_signature": payload["current_input_signature"],
            "inputs_changed_since_last_run": False,
            "run_attempt_count": int(payload.get("run_attempt_count", 0)) + 1,
            "result": {
                "status": "failed",
                "period": payload["selected_period"],
                "artifacts": {"workbook": "/tmp/failure.xlsx"},
                "error_type": "RuntimeError",
                "error_message": "analysis failed",
            },
            "error": {
                "type": "RuntimeError",
                "message": "analysis failed",
            },
        }
    )
    state[RUN_WORKFLOW_STATE_KEY] = payload
    state["active_run_status"] = "Failed"
    return payload


def _mark_run_success(state) -> dict[str, object]:
    payload = sync_run_workflow_state(state)
    payload.update(
        {
            "status": RUN_STATUS_SUCCEEDED,
            "status_label": "Succeeded",
            "last_finished_at": "2026-03-13T11:30:00+00:00",
            "last_run_period": payload["selected_period"],
            "last_run_input_signature": payload["current_input_signature"],
            "inputs_changed_since_last_run": False,
            "run_attempt_count": int(payload.get("run_attempt_count", 0)) + 1,
            "result": {
                "status": "success",
                "period": payload["selected_period"],
                "detail_row_count": 12,
                "qa_summary_row_count": 3,
                "lost_value_net_raw": 99.5,
                "artifacts": {"workbook": "/tmp/success.xlsx"},
            },
            "error": None,
        }
    )
    state[RUN_WORKFLOW_STATE_KEY] = payload
    state["active_run_status"] = "Succeeded"
    return payload


def _sales_bytes(label: str) -> bytes:
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
                "Product Name": label,
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
