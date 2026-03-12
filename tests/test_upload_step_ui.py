from __future__ import annotations

from io import BytesIO
import sys
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY, stage_uploaded_file
from streamlit_app.services.v5_boundary import get_bundled_site_mapping_status
from streamlit_app.ui.upload_inputs import UPLOAD_STEP_READINESS_KEY


def test_upload_step_layout_renders_three_required_cards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    app.session_state["current_step_index"] = 1
    app.run()

    assert len(app.exception) == 0
    subheaders = [node.value for node in app.subheader]
    assert "Sales" in subheaders
    assert "Stock" in subheaders
    assert "SKU / Live" in subheaders

    uploaders = app.get("file_uploader")
    assert len(uploaders) == 3
    assert [u.label for u in uploaders] == [
        "Upload Sales file",
        "Upload Stock file",
        "Upload SKU / Live file",
    ]

    assert app.metric[4].label == "Required Uploads Ready"
    assert app.metric[4].value == "0/3"
    assert app.metric[5].label == "Blocking Issues"
    assert app.metric[5].value == "3"
    assert "Sales: upload required." in app.error[0].value
    assert "SKU / Live: upload required." in app.error[0].value
    assert app.button[1].label == "Next step"
    assert app.button[1].disabled is True


def test_upload_step_site_map_panel_shows_bundled_status_and_summaries(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_registry(
        app,
        sales_payload=_sales_bytes_with_multiple_months(),
        stock_payload=_stock_csv_bytes(),
        sku_payload=_sku_csv_bytes(),
    )

    site_map_status = get_bundled_site_mapping_status()

    assert len(app.exception) == 0
    assert any(node.value == "Bundled Site Mapping" for node in app.subheader)
    assert any(node.value == site_map_status.status_label for node in app.success)
    assert any(node.value == site_map_status.path for node in app.caption)
    assert any("Sample virtual sites:" in node.value for node in app.markdown)
    assert any("Row count:** 2" in node.value for node in app.markdown)
    assert any("Date coverage:** 2026-01-05 to 2026-02-03" in node.value for node in app.markdown)
    assert any("Month hints:** 2026-01, 2026-02" in node.value for node in app.markdown)
    assert any("Detected data from multiple months in the uploaded file." == node.value for node in app.warning)
    readiness = app.session_state[UPLOAD_STEP_READINESS_KEY]
    assert readiness["is_ready"] is True
    assert readiness["ready_slots"] == 3
    assert readiness["warning_count"] == 1
    assert app.button[1].disabled is False


def test_upload_step_blocks_progress_for_validation_errors(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_registry(
        app,
        sales_payload=_sales_bytes_single_month(),
        stock_payload=_invalid_stock_csv_bytes(),
        sku_payload=_sku_csv_bytes(),
    )

    readiness = app.session_state[UPLOAD_STEP_READINESS_KEY]

    assert len(app.exception) == 0
    assert readiness["is_ready"] is False
    assert readiness["ready_slots"] == 2
    assert readiness["warning_count"] == 0
    assert any(
        "Missing required columns: article_code, stock_balance" in message
        for message in readiness["blocking_messages"]
    )
    assert any(
        "Resolve these blocking items before continuing:" in node.value for node in app.error
    )
    assert any("Blocking validation issues found:" in node.value for node in app.error)
    assert any(
        "Missing required columns: article_code, stock_balance" in node.value for node in app.markdown
    )
    assert app.metric[4].value == "2/3"
    assert app.metric[5].value == "1"
    assert app.button[1].disabled is True


class FakeUpload:
    def __init__(self, name: str, payload: bytes) -> None:
        self.name = name
        self._payload = payload

    def getbuffer(self) -> memoryview:
        return memoryview(self._payload)


def _sales_bytes_with_multiple_months() -> bytes:
    buffer = BytesIO()
    pd.DataFrame(
        [
            {
                "Purchase Date": "2026-01-05",
                "Sku": "SKU-1",
                "stock": "BKK",
                "Quantity": 1,
                "Gross": 100,
                "Net": 90,
                "Product Name": "Alpha",
            },
            {
                "Purchase Date": "2026-02-03",
                "Sku": "SKU-2",
                "stock": "BKK",
                "Quantity": 2,
                "Gross": 120,
                "Net": 110,
                "Product Name": "Beta",
            },
        ]
    ).to_csv(buffer, sep="\t", index=False, encoding="utf-16")
    return buffer.getvalue()


def _sales_bytes_single_month() -> bytes:
    buffer = BytesIO()
    pd.DataFrame(
        [
            {
                "Purchase Date": "2026-01-05",
                "Sku": "SKU-1",
                "stock": "BKK",
                "Quantity": 1,
                "Gross": 100,
                "Net": 90,
                "Product Name": "Alpha",
            },
            {
                "Purchase Date": "2026-01-08",
                "Sku": "SKU-2",
                "stock": "BKK",
                "Quantity": 3,
                "Gross": 130,
                "Net": 125,
                "Product Name": "Beta",
            },
        ]
    ).to_csv(buffer, sep="\t", index=False, encoding="utf-16")
    return buffer.getvalue()


def _stock_csv_bytes() -> bytes:
    return pd.DataFrame(
        [
            {
                "posting_date": "2026-01-05",
                "site_code": "26GA",
                "article_code": "SKU-1",
                "stock_balance": 5,
            },
            {
                "posting_date": "2026-01-05",
                "site_code": "26FH",
                "article_code": "SKU-2",
                "stock_balance": 3,
            },
        ]
    ).to_csv(index=False).encode("utf-8")


def _invalid_stock_csv_bytes() -> bytes:
    return pd.DataFrame(
        [{"posting_date": "2026-01-05", "site_code": "26GA"}]
    ).to_csv(index=False).encode("utf-8")


def _sku_csv_bytes() -> bytes:
    return pd.DataFrame([{"skuNo": "SKU-1"}, {"skuNo": "SKU-2"}]).to_csv(index=False).encode(
        "utf-8"
    )


def _seed_registry(
    app: AppTest,
    *,
    sales_payload: bytes,
    stock_payload: bytes,
    sku_payload: bytes,
) -> None:
    registry = {
        slot_key: dict(slot_state)
        for slot_key, slot_state in app.session_state[UPLOAD_REGISTRY_KEY].items()
    }
    workspace_input_dir = Path(app.session_state["workspace_input_dir"])

    stage_uploaded_file(
        FakeUpload("sales.txt", sales_payload),
        slot_key="sales",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        FakeUpload("stock.csv", stock_payload),
        slot_key="stock",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )
    stage_uploaded_file(
        FakeUpload("sku-live.csv", sku_payload),
        slot_key="sku_live",
        workspace_input_dir=workspace_input_dir,
        registry=registry,
    )

    app.session_state[UPLOAD_REGISTRY_KEY] = registry
    app.session_state["current_step_index"] = 1
    app.run()
