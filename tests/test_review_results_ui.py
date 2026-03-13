from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.run_workflow import RUN_WORKFLOW_STATE_KEY
from tests.test_results_workspace import _build_completed_run_state


def test_review_results_overview_renders_totals_and_trust_signal(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_completed_run(app, tmp_path)

    assert len(app.exception) == 0
    assert any(node.value == "Run Overview" for node in app.subheader)
    assert any(metric.label == "Lost Value Net" for metric in app.metric)
    assert any(
        "Review QA and trust details before exporting." in node.value for node in app.warning
    )
    assert any(node.value == "Summary Total" for node in app.subheader)
    assert any(node.value == "Top Sites" for node in app.subheader)
    assert any(node.value == "Top SKUs" for node in app.subheader)


def test_review_results_detail_tab_surfaces_explainability_fields(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_completed_run(app, tmp_path)

    assert len(app.exception) == 0
    assert any(node.value == "Detail Review" for node in app.subheader)
    assert any(
        "baseline source, baseline window, recorded days, OOS days, and actual quantity"
        in node.value
        for node in app.caption
    )
    assert len(app.dataframe) >= 4
    detail_frames = [
        list(node.value.columns)
        for node in app.dataframe
        if "baseline_source" in list(node.value.columns)
    ]
    assert detail_frames
    assert "recorded_days" in detail_frames[0]
    assert "oos_days_jan" in detail_frames[0]
    assert "actual_qty_jan" in detail_frames[0]


def test_review_results_qa_tab_shows_definitions_and_calculation_example(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_completed_run(app, tmp_path)

    assert len(app.exception) == 0
    assert any(node.value == "QA Summary" for node in app.subheader)
    assert any(node.value == "Unmapped Site Codes" for node in app.subheader)
    assert any(node.value == "Definitions" for node in app.subheader)
    assert any(node.value == "Calculation Example" for node in app.subheader)
    assert any(
        "Detected data from multiple months in the uploaded file." in node.value
        for node in app.markdown
    )


def _seed_completed_run(app: AppTest, tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path)
    app.session_state[RUN_WORKFLOW_STATE_KEY] = run_state
    app.session_state["upload_validation_results"] = {
        "sales": {
            "warnings": [
                {
                    "message": "Detected data from multiple months in the uploaded file.",
                }
            ]
        }
    }
    app.session_state["current_step_index"] = 3
    app.run()
