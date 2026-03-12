"""Streamlit entrypoint for the OOS opportunity-loss workspace."""

import streamlit as st

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
