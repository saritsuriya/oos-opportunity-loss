from __future__ import annotations

import json
import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.temp_workspace import ensure_session_workspace


def test_create_session_workspace_builds_isolated_paths(tmp_path: Path) -> None:
    alpha = ensure_session_workspace("ALPHA-SESSION", base_dir=tmp_path)
    beta = ensure_session_workspace("BETA-SESSION", base_dir=tmp_path)

    assert alpha.root != beta.root
    assert alpha.input_dir.parent == alpha.root
    assert alpha.output_dir.parent == alpha.root
    assert alpha.input_dir.name == "inputs"
    assert alpha.output_dir.name == "outputs"
    assert alpha.metadata_path.exists()
    assert beta.metadata_path.exists()


def test_create_session_workspace_is_deterministic_for_same_session(tmp_path: Path) -> None:
    first = ensure_session_workspace("Repeatable.Session", base_dir=tmp_path)
    second = ensure_session_workspace("Repeatable.Session", base_dir=tmp_path)

    metadata = json.loads(second.metadata_path.read_text(encoding="utf-8"))

    assert first.root == second.root
    assert first.input_dir == second.input_dir
    assert first.output_dir == second.output_dir
    assert metadata["created_at"]
    assert metadata["last_accessed_at"]


def test_create_bootstrap_session_state_exposes_workspace_paths(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("OOS_WORKSPACE_BASE_DIR", str(tmp_path))

    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()

    workspace_root = Path(app.session_state["workspace_root"])
    input_dir = Path(app.session_state["workspace_input_dir"])
    output_dir = Path(app.session_state["workspace_output_dir"])

    assert len(app.exception) == 0
    assert workspace_root.exists()
    assert workspace_root.parent == tmp_path
    assert input_dir.parent == workspace_root
    assert output_dir.parent == workspace_root
