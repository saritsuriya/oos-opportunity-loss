"""Streamlit entrypoint for the OOS opportunity-loss workspace."""

import streamlit as st

APP_TITLE = "OOS Opportunity Loss Workspace"


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)
    st.caption("Phase 1 foundation for the frozen V5 operator workflow.")
    st.info(
        "Guided wizard navigation, session bootstrap, and the reusable V5 boundary "
        "will be wired into this entrypoint in the next task."
    )


def main() -> None:
    render_app()


if __name__ == "__main__":
    main()
