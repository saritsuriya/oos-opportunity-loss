from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.results_workspace import (
    InvalidResultsWorkspaceState,
    MissingResultsArtifact,
    ResultsWorkbookReadError,
    load_results_workspace,
)


def test_load_results_workspace_reads_csv_artifacts_and_manifest(tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path)

    result = load_results_workspace(run_state)

    assert result.ok is True
    assert result.payload is not None
    payload = result.payload
    assert payload.period == "2026-03"
    assert payload.is_current is True
    assert payload.overview["detail_row_count"] == 2
    assert payload.overview["unmapped_site_count"] == 1
    assert payload.overview["total_lost_qty_raw"] == 4.0
    assert list(payload.summary_site["virtual_site"]) == ["BKK"]
    assert list(payload.summary_sku["sku"]) == ["SKU-1"]
    assert list(payload.detail["sku"]) == ["SKU-1", "SKU-2"]
    assert len(payload.export_manifest) == 6
    assert payload.export_manifest[0].key == "workbook"
    assert payload.export_manifest[1].key == "summary_total_csv"
    manifest_payload = result.as_dict()["payload"]["export_manifest"]
    assert manifest_payload[0]["filename"] == "OOS_Opportunity_Lost_TH_2026-03_V5.xlsx"


def test_load_results_workspace_reads_workbook_only_trust_sheets(tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path)

    result = load_results_workspace(run_state)

    assert result.ok is True
    assert result.payload is not None
    payload = result.payload
    assert list(payload.unmapped_site["site_code"]) == ["UNMAPPED-1"]
    assert "baseline_source" in set(payload.definitions["field"])
    assert list(payload.calculation_example["item"]) == [
        "Sample row",
        "Step 1 baseline_daily_qty",
    ]


def test_load_results_workspace_fails_when_required_artifact_is_missing(tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path)
    summary_site_csv = Path(
        run_state["result"]["artifacts"]["summary_site_csv"]
    )
    summary_site_csv.unlink()

    result = load_results_workspace(run_state)

    assert result.ok is False
    assert result.payload is None
    assert result.error_type == MissingResultsArtifact.__name__
    assert "summary_site_csv" in str(result.error_message)


def test_load_results_workspace_fails_when_run_is_not_succeeded(tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path)
    run_state["status"] = "failed"

    result = load_results_workspace(run_state)

    assert result.ok is False
    assert result.error_type == InvalidResultsWorkspaceState.__name__
    assert "successful frozen V5 run is required" in str(result.error_message)


def test_load_results_workspace_fails_when_workbook_sheet_is_missing(tmp_path: Path) -> None:
    run_state = _build_completed_run_state(tmp_path, include_calc_example=False)

    result = load_results_workspace(run_state)

    assert result.ok is False
    assert result.error_type == ResultsWorkbookReadError.__name__
    assert "Calculation Example" in str(result.error_message)


def _build_completed_run_state(
    tmp_path: Path,
    *,
    include_calc_example: bool = True,
) -> dict[str, object]:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / "OOS_Opportunity_Lost_TH_2026-03_V5"
    workbook = output_dir / "OOS_Opportunity_Lost_TH_2026-03_V5.xlsx"

    summary_total = pd.DataFrame(
        [
            {"metric": "Total Lost Qty Raw", "value": 4.0},
            {"metric": "Total Lost Value Gross Raw", "value": 180.0},
            {"metric": "Total Lost Value Net Raw", "value": 150.0},
        ]
    )
    summary_site = pd.DataFrame(
        [
            {
                "virtual_site": "BKK",
                "sku_site_rows_eval": 2,
                "avg_oos_ratio": 0.5,
                "lost_qty_raw": 4.0,
                "lost_value_gross_raw": 180.0,
                "lost_value_net_raw": 150.0,
                "loss_gross": 180.0,
                "loss_net": 150.0,
            }
        ]
    )
    summary_sku = pd.DataFrame(
        [
            {
                "sku": "SKU-1",
                "product_name": "Alpha",
                "lost_qty_raw": 4.0,
                "lost_value_gross_raw": 180.0,
                "lost_value_net_raw": 150.0,
                "loss_gross": 180.0,
                "loss_net": 150.0,
                "loss_net_BKK": 150.0,
            }
        ]
    )
    detail = pd.DataFrame(
        [
            {
                "sku": "SKU-1",
                "virtual_site": "BKK",
                "baseline_source": "recent_6m",
                "baseline_window_start": "2025-09-01",
                "baseline_window_end": "2026-02-28",
                "recorded_days": 28,
                "oos_days_jan": 5,
                "actual_qty_jan": 0,
                "lost_qty_raw": 4.0,
                "lost_value_net_raw": 150.0,
            },
            {
                "sku": "SKU-2",
                "virtual_site": "BKK",
                "baseline_source": "no_history",
                "baseline_window_start": "",
                "baseline_window_end": "",
                "recorded_days": 0,
                "oos_days_jan": 0,
                "actual_qty_jan": 0,
                "lost_qty_raw": 0.0,
                "lost_value_net_raw": 0.0,
            },
        ]
    )
    qa_summary = pd.DataFrame(
        [
            {"check": "rows_using_recent_6m", "value": 1},
            {"check": "rows_using_no_history", "value": 1},
        ]
    )
    unmapped = pd.DataFrame([{"site_code": "UNMAPPED-1"}])
    definitions = pd.DataFrame(
        [
            {"field": "baseline_source", "definition": "History window used for the baseline"},
            {"field": "recorded_days", "definition": "Days with stock rows present"},
        ]
    )
    calc_example = pd.DataFrame(
        [
            {"item": "Sample row", "formula": "highest loss_net row in Detail", "value": "SKU-1"},
            {"item": "Step 1 baseline_daily_qty", "formula": "qty / days", "value": 0.5},
        ]
    )

    summary_total.to_csv(f"{base}_summary_total.csv", index=False)
    summary_site.to_csv(f"{base}_summary_site.csv", index=False)
    summary_sku.to_csv(f"{base}_summary_sku.csv", index=False)
    detail.to_csv(f"{base}_detail.csv", index=False)
    qa_summary.to_csv(f"{base}_qa_summary.csv", index=False)

    with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
        summary_total.to_excel(writer, sheet_name="Summary Total", index=False)
        summary_site.to_excel(writer, sheet_name="Summary by Site", index=False)
        summary_sku.to_excel(writer, sheet_name="Summary by SKU", index=False)
        detail.to_excel(writer, sheet_name="Detail SKU Site", index=False)
        qa_summary.to_excel(writer, sheet_name="QA Summary", index=False)
        unmapped.to_excel(writer, sheet_name="QA Unmapped SiteCode", index=False)
        definitions.to_excel(writer, sheet_name="Definitions", index=False)
        if include_calc_example:
            calc_example.to_excel(writer, sheet_name="Calculation Example", index=False)

    return {
        "status": "succeeded",
        "status_label": "Succeeded",
        "selected_period": "2026-03",
        "last_run_period": "2026-03",
        "inputs_changed_since_last_run": False,
        "result": {
            "status": "success",
            "period": "2026-03",
            "detail_row_count": 2,
            "qa_summary_row_count": 2,
            "unmapped_site_count": 1,
            "lost_value_net_raw": 150.0,
            "artifacts": {
                "workbook": str(workbook),
                "detail_csv": str(Path(f"{base}_detail.csv").resolve()),
                "summary_site_csv": str(Path(f"{base}_summary_site.csv").resolve()),
                "summary_sku_csv": str(Path(f"{base}_summary_sku.csv").resolve()),
                "summary_total_csv": str(Path(f"{base}_summary_total.csv").resolve()),
                "qa_summary_csv": str(Path(f"{base}_qa_summary.csv").resolve()),
            },
        },
    }
