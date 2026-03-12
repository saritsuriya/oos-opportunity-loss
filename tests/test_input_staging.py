from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.temp_workspace import ensure_session_workspace
from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY, ensure_upload_registry


def test_session_upload_registry_uses_active_workspace_input_dir(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("phase-2-session", base_dir=tmp_path)
    state = {"workspace_input_dir": str(workspace.input_dir)}

    registry = ensure_upload_registry(state)

    assert set(registry) == {"sales", "stock", "sku_live"}
    for slot_state in registry.values():
        slot_dir = Path(str(slot_state["slot_dir"]))
        assert slot_dir.parent == workspace.input_dir
        assert slot_dir.is_relative_to(workspace.input_dir)
        assert slot_state["current_file"] is None


def test_session_upload_registry_bootstrap_exposes_slot_state(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()

    registry = app.session_state[UPLOAD_REGISTRY_KEY]
    workspace_input_dir = Path(app.session_state["workspace_input_dir"])

    assert len(app.exception) == 0
    assert set(registry) == {"sales", "stock", "sku_live"}
    for slot_key, slot_state in registry.items():
        slot_dir = Path(str(slot_state["slot_dir"]))
        assert slot_state["slot_key"] == slot_key
        assert slot_dir.is_relative_to(workspace_input_dir)
        assert slot_state["current_file"] is None
