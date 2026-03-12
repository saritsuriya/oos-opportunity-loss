from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.cleanup import cleanup_session_workspace, cleanup_stale_workspaces
from streamlit_app.runtime.temp_workspace import ensure_session_workspace, sanitize_session_id


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


def test_cleanup_session_workspace_removes_session_tree(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("cleanup-now", base_dir=tmp_path)
    (workspace.output_dir / "artifact.txt").write_text("temporary", encoding="utf-8")

    removed = cleanup_session_workspace("cleanup-now", base_dir=tmp_path)

    assert removed is True
    assert not workspace.root.exists()


def test_cleanup_stale_workspaces_removes_only_expired_roots(tmp_path: Path) -> None:
    stale_workspace = ensure_session_workspace("stale-run", base_dir=tmp_path)
    fresh_workspace = ensure_session_workspace("fresh-run", base_dir=tmp_path)

    stale_timestamp = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc).timestamp()
    fresh_timestamp = datetime(2026, 3, 12, 11, 45, tzinfo=timezone.utc).timestamp()
    _set_tree_mtime(stale_workspace.root, stale_timestamp)
    _set_tree_mtime(fresh_workspace.root, fresh_timestamp)

    removed = cleanup_stale_workspaces(
        timedelta(hours=6),
        base_dir=tmp_path,
        now=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    assert removed == (stale_workspace.root,)
    assert not stale_workspace.root.exists()
    assert fresh_workspace.root.exists()


def test_workspace_contract_separates_inputs_from_outputs(tmp_path: Path) -> None:
    workspace = ensure_session_workspace("contract-run", base_dir=tmp_path)
    staged_input = workspace.input_dir / "orders.csv"
    generated_output = workspace.output_dir / "summary.csv"

    staged_input.write_text("input", encoding="utf-8")
    generated_output.write_text("output", encoding="utf-8")

    assert staged_input.parent != generated_output.parent
    assert staged_input.relative_to(workspace.root).parts[0] == "inputs"
    assert generated_output.relative_to(workspace.root).parts[0] == "outputs"
    assert not staged_input.is_relative_to(workspace.output_dir)
    assert not generated_output.is_relative_to(workspace.input_dir)


def test_workspace_contract_keeps_cleanup_scoped_to_session_directories(tmp_path: Path) -> None:
    stale_workspace = ensure_session_workspace("stale-scope", base_dir=tmp_path)
    manual_folder = tmp_path / "manual-notes"
    manual_folder.mkdir()

    stale_timestamp = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc).timestamp()
    _set_tree_mtime(stale_workspace.root, stale_timestamp)
    os.utime(manual_folder, (stale_timestamp, stale_timestamp))

    removed = cleanup_stale_workspaces(
        timedelta(hours=6),
        base_dir=tmp_path,
        now=datetime(2026, 3, 12, 12, 0, tzinfo=timezone.utc),
    )

    assert removed == (stale_workspace.root,)
    assert manual_folder.exists()


def test_workspace_contract_rejects_blank_session_ids() -> None:
    with pytest.raises(ValueError):
        sanitize_session_id("   ")


def _set_tree_mtime(root: Path, timestamp: float) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        os.utime(path, (timestamp, timestamp))
    os.utime(root, (timestamp, timestamp))
