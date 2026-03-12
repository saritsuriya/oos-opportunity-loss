from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.runtime.temp_workspace import ensure_session_workspace

CONFIG_PATH = ROOT / ".streamlit" / "config.toml"
RUN_SCRIPT_PATH = ROOT / "scripts" / "run_streamlit.ps1"
CLEANUP_SCRIPT_PATH = ROOT / "scripts" / "cleanup_temp_workspace.py"
CLEANUP_WRAPPER_PATH = ROOT / "scripts" / "cleanup_temp_workspace.ps1"
RUNBOOK_PATH = ROOT / "docs" / "phase-01-deployment.md"


def load_streamlit_deploy_config() -> dict[str, object]:
    return tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def test_streamlit_internal_hosting_config_defaults_are_explicit() -> None:
    config = load_streamlit_deploy_config()
    server = config["server"]
    browser = config["browser"]

    assert server["headless"] is True
    assert server["runOnSave"] is False
    assert server["address"] == "0.0.0.0"
    assert server["port"] == 8501
    assert server["enableCORS"] is True
    assert server["enableXsrfProtection"] is True
    assert browser["gatherUsageStats"] is False
    assert browser["serverPort"] == 8501


def test_streamlit_upload_config_matches_phase_1_file_size_posture() -> None:
    config = load_streamlit_deploy_config()
    server = config["server"]

    assert server["maxUploadSize"] == 200
    assert server["maxMessageSize"] == 200
    assert server["maxUploadSize"] >= 42
    assert server["maxMessageSize"] >= server["maxUploadSize"]


def test_cleanup_scripts_prune_stale_session_workspaces(tmp_path: Path) -> None:
    stale_workspace = ensure_session_workspace("stale-scheduled", base_dir=tmp_path)
    fresh_workspace = ensure_session_workspace("fresh-scheduled", base_dir=tmp_path)

    stale_timestamp = datetime(2026, 3, 10, 0, 0, tzinfo=timezone.utc).timestamp()
    fresh_timestamp = datetime(2026, 3, 12, 11, 45, tzinfo=timezone.utc).timestamp()
    _set_tree_mtime(stale_workspace.root, stale_timestamp)
    _set_tree_mtime(fresh_workspace.root, fresh_timestamp)

    result = subprocess.run(
        [
            sys.executable,
            str(CLEANUP_SCRIPT_PATH),
            "--base-dir",
            str(tmp_path),
            "--max-age-hours",
            "6",
            "--now-iso",
            "2026-03-12T12:00:00+00:00",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert f"Removed: {stale_workspace.root}" in result.stdout
    assert not stale_workspace.root.exists()
    assert fresh_workspace.root.exists()


def test_windows_scripts_target_real_project_artifacts() -> None:
    run_script = RUN_SCRIPT_PATH.read_text(encoding="utf-8")
    cleanup_script = CLEANUP_SCRIPT_PATH.read_text(encoding="utf-8")
    cleanup_wrapper = CLEANUP_WRAPPER_PATH.read_text(encoding="utf-8")

    assert ".streamlit\\config.toml" in run_script
    assert "streamlit_app\\app.py" in run_script
    assert "--server.address" in run_script
    assert "--browser.serverAddress" in run_script
    assert "cleanup_stale_workspaces" in cleanup_script
    assert "get_workspace_base_dir" in cleanup_script
    assert "scripts\\cleanup_temp_workspace.py" in cleanup_wrapper
    assert "--max-age-hours" in cleanup_wrapper


def test_runbook_describes_phase_1_windows_deployment_baseline() -> None:
    runbook = RUNBOOK_PATH.read_text(encoding="utf-8")

    assert "scripts/run_streamlit.ps1" in runbook
    assert "scripts/cleanup_temp_workspace.ps1" in runbook
    assert "http://<public-hostname>:8501/" in runbook
    assert "Site mapping.csv" in runbook
    assert "stateless" in runbook
    assert "No login or expanded authentication" in runbook


def _set_tree_mtime(root: Path, timestamp: float) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        os.utime(path, (timestamp, timestamp))
    os.utime(root, (timestamp, timestamp))
