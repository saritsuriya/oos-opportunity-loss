from __future__ import annotations

import sys
from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.run_workflow import RUN_WORKFLOW_STATE_KEY
from streamlit_app.services.upload_staging import UPLOAD_REGISTRY_KEY
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


def test_review_results_export_tab_shows_workbook_and_csv_downloads(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    _seed_completed_run(app, tmp_path)

    assert len(app.exception) == 0
    assert any(node.value == "Export Files" for node in app.subheader)
    assert any(node.value == "CSV Exports" for node in app.subheader)
    download_labels = [node.label for node in app.get("download_button")]
    assert "Download Excel Workbook" in download_labels
    assert "Download Summary Total CSV" in download_labels
    assert "Download Summary by Site CSV" in download_labels
    assert "Download Detail CSV" in download_labels


def test_review_results_shows_missing_artifact_guidance(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    run_state = _build_completed_run_state(tmp_path)
    Path(run_state["result"]["artifacts"]["workbook"]).unlink()
    _seed_completed_run(app, tmp_path, run_state=run_state)

    assert len(app.exception) == 0
    assert any("artifact 'workbook' was not found" in node.value.lower() for node in app.error)
    assert any("no longer available in this session workspace" in node.value.lower() for node in app.info)


def test_review_results_disables_exports_when_run_is_stale(tmp_path: Path) -> None:
    app = AppTest.from_file(str(ROOT / "streamlit_app" / "app.py"))
    app.run()
    run_state = _build_completed_run_state(tmp_path)
    run_state["last_run_input_signature"] = "old-signature"
    staged_registry = {
        "sales": {
            "current_file": {
                "source_name": "replacement.tsv",
                "staged_path": str(tmp_path / "inputs" / "sales" / "current.tsv"),
                "size_bytes": 10,
            }
        },
        "stock": {
            "current_file": {
                "source_name": "stock.csv",
                "staged_path": str(tmp_path / "inputs" / "stock" / "current.csv"),
                "size_bytes": 10,
            }
        },
        "sku_live": {
            "current_file": {
                "source_name": "sku-live.csv",
                "staged_path": str(tmp_path / "inputs" / "sku-live" / "current.csv"),
                "size_bytes": 10,
            }
        },
    }
    _seed_completed_run(app, tmp_path, run_state=run_state, registry=staged_registry)

    assert len(app.exception) == 0
    assert any(
        "Run V5 again before exporting these files." in node.value for node in app.warning
    )
    assert all(node.disabled is True for node in app.get("download_button"))


def _seed_completed_run(
    app: AppTest,
    tmp_path: Path,
    *,
    run_state: dict[str, object] | None = None,
    registry: dict[str, object] | None = None,
) -> None:
    if run_state is None:
        run_state = _build_completed_run_state(tmp_path)
    app.session_state[RUN_WORKFLOW_STATE_KEY] = run_state
    if registry is None:
        staged_sales_path = tmp_path / "inputs" / "sales" / "current.tsv"
        staged_sales_path.parent.mkdir(parents=True, exist_ok=True)
        staged_sales_path.write_text("placeholder", encoding="utf-8")
        registry = {
            "sales": {
                "current_file": {
                    "source_name": "sales.tsv",
                    "staged_path": str(staged_sales_path),
                    "size_bytes": 10,
                    "slot_key": "sales",
                }
            }
        }
    if registry is not None:
        app.session_state[UPLOAD_REGISTRY_KEY] = registry
    app.session_state["upload_validation_results"] = {
        "sales": {
            "slot_key": "sales",
            "source_name": "sales.tsv",
            "staged_path": str(registry["sales"]["current_file"]["staged_path"]),
            "warnings": [
                {
                    "message": "Detected data from multiple months in the uploaded file.",
                }
            ],
            "summary": {},
        }
    }
    app.session_state["current_step_index"] = 3
    app.run()
