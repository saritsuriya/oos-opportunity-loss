from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.temp_workspace import ensure_session_workspace
from streamlit_app.services.upload_staging import (
    UPLOAD_REGISTRY_KEY,
    build_staged_upload_path,
    ensure_upload_registry,
    stage_uploaded_file,
)


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


def test_replace_upload_staging_overwrites_existing_slot_file(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("replace-sales-session", base_dir=tmp_path)
    registry = ensure_upload_registry({"workspace_input_dir": str(workspace.input_dir)})

    first = stage_uploaded_file(
        FakeUpload("march-sales.xlsx", b"first-version"),
        slot_key="sales",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    second = stage_uploaded_file(
        FakeUpload("march-sales.tsv", b"second-version"),
        slot_key="sales",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )

    staged_files = tuple(sorted((workspace.input_dir / "sales").glob("current*")))

    assert Path(str(first["staged_path"])).name == "current.xlsx"
    assert staged_files == (Path(str(second["staged_path"])),)
    assert staged_files[0].read_bytes() == b"second-version"
    assert second["source_name"] == "march-sales.tsv"
    assert second["size_bytes"] == len(b"second-version")


def test_replace_upload_staging_refreshes_registry_metadata(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("replace-stock-session", base_dir=tmp_path)
    registry = ensure_upload_registry({"workspace_input_dir": str(workspace.input_dir)})

    stage_uploaded_file(
        FakeUpload("stock.csv", b"sku,qty\n1,2\n"),
        slot_key="stock",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    refreshed = stage_uploaded_file(
        FakeUpload("stock-refresh.csv", b"sku,qty\n1,5\n"),
        slot_key="stock",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )

    assert registry["stock"]["current_file"] == refreshed
    assert refreshed["source_name"] == "stock-refresh.csv"
    assert Path(str(refreshed["staged_path"])).read_bytes() == b"sku,qty\n1,5\n"


def test_staging_paths_are_deterministic_for_all_slots(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("deterministic-slots", base_dir=tmp_path)
    slot_cases = {
        "sales": ("monthly-sales.xlsm", workspace.input_dir / "sales" / "current.xlsm"),
        "stock": ("stock.csv", workspace.input_dir / "stock" / "current.csv"),
        "sku_live": ("sku-live.csv", workspace.input_dir / "sku-live" / "current.csv"),
    }

    for slot_key, (source_name, expected_path) in slot_cases.items():
        first = build_staged_upload_path(workspace.input_dir, slot_key, source_name)
        second = build_staged_upload_path(workspace.input_dir, slot_key, source_name)

        assert first == second
        assert first == expected_path


def test_stage_uploaded_file_keeps_all_slots_inside_session_input_dir(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("session-guardrails", base_dir=tmp_path)
    registry = ensure_upload_registry({"workspace_input_dir": str(workspace.input_dir)})

    staged_sales = stage_uploaded_file(
        FakeUpload("../../escape.xls", b"sales"),
        slot_key="sales",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    staged_stock = stage_uploaded_file(
        FakeUpload("../stock.csv", b"stock"),
        slot_key="stock",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )
    staged_sku = stage_uploaded_file(
        FakeUpload("nested/path/sku.csv", b"sku"),
        slot_key="sku_live",
        workspace_input_dir=workspace.input_dir,
        registry=registry,
    )

    for metadata in (staged_sales, staged_stock, staged_sku):
        staged_path = Path(str(metadata["staged_path"]))
        assert staged_path.exists()
        assert staged_path.is_relative_to(workspace.input_dir)
        assert staged_path.parent.parent == workspace.input_dir


class FakeUpload:
    def __init__(self, name: str, payload: bytes) -> None:
        self.name = name
        self._payload = payload

    def getbuffer(self) -> memoryview:
        return memoryview(self._payload)
