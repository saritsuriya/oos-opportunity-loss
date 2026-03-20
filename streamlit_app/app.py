"""Streamlit entrypoint for the OOS opportunity-loss workspace."""

from pathlib import Path
import sys

import streamlit as st


def _ensure_repo_root_on_syspath() -> None:
    repo_root = str(Path(__file__).resolve().parents[1])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


_ensure_repo_root_on_syspath()

try:
    from streamlit_app.runtime.session_state import bootstrap_session_state
    from streamlit_app.ui.wizard import render_wizard_shell
except ModuleNotFoundError:
    from runtime.session_state import bootstrap_session_state
    from ui.wizard import render_wizard_shell

APP_TITLE = "OOS Opportunity Loss Workspace"


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
    bootstrap_session_state()
    render_wizard_shell()


def main() -> None:
    render_app()


if __name__ == "__main__":
    main()
