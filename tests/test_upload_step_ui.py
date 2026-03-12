from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_upload_step_layout_renders_three_required_cards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    app.session_state["current_step_index"] = 1
    app.run()

    assert len(app.exception) == 0
    assert [node.value for node in app.subheader[-3:]] == ["Sales", "Stock", "SKU / Live"]

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
