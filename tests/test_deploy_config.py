from __future__ import annotations

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / ".streamlit" / "config.toml"


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
