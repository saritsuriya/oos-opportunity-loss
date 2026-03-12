from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.v5_boundary import get_boundary_overview, load_frozen_v5_symbols


def test_v5_boundary_exposes_frozen_pipeline_symbols() -> None:
    overview = get_boundary_overview()

    assert overview.pipeline_name == "Frozen V5 daily OOS opportunity pipeline"
    assert overview.site_mapping_path.endswith("Site mapping.csv")

    symbols = load_frozen_v5_symbols()

    assert set(symbols) == {
        "InputPaths",
        "DataLoaderV5",
        "ModelConfig",
        "DailyOOSOpportunityV5",
        "ReporterV5",
    }


def test_streamlit_app_entrypoint_renders_guided_shell() -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()

    assert len(app.exception) == 0
    assert app.title[0].value == "OOS Opportunity Loss Workspace"
    assert app.session_state["session_bootstrapped"] is True
    assert app.session_state["current_step_index"] == 0
    assert any(subheader.value == "MVP Boundary" for subheader in app.subheader)
