from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.run_execution import build_run_request, suggest_evaluation_month


def test_suggest_evaluation_month_uses_single_stock_month(tmp_path: Path) -> None:
    workspace_root = tmp_path / "session-alpha"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales.tsv",
        stock_dates=("2026-02-01", "2026-02-14", "2026-02-28"),
        sku_name="sku-live.csv",
    )

    suggestion = suggest_evaluation_month(staged_registry)

    assert suggestion.is_confident is True
    assert suggestion.eval_year == 2026
    assert suggestion.eval_month == 2
    assert suggestion.label == "February 2026"
    assert suggestion.month_hints == ("2026-02",)


def test_suggest_evaluation_month_flags_multi_month_stock_file(tmp_path: Path) -> None:
    workspace_root = tmp_path / "session-beta"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales.tsv",
        stock_dates=("2026-02-28", "2026-03-01"),
        sku_name="sku-live.csv",
    )

    suggestion = suggest_evaluation_month(staged_registry)

    assert suggestion.is_confident is False
    assert suggestion.eval_year is None
    assert suggestion.eval_month is None
    assert suggestion.month_hints == ("2026-02", "2026-03")
    assert "multiple months" in suggestion.reason.lower()


def test_build_run_request_uses_staged_inputs_and_selected_month(
    tmp_path: Path, monkeypatch
) -> None:
    workspace_root = tmp_path / "session-gamma"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales.tsv",
        stock_dates=("2026-02-01", "2026-02-14"),
        sku_name="sku-live.csv",
    )
    site_mapping_path = workspace_root / "bundled-site-map.csv"
    site_mapping_path.write_text(
        "Virtual Location,Site,Active\nwh-bkk,1001,X\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "streamlit_app.services.v5_boundary.locate_bundled_site_mapping",
        lambda: site_mapping_path,
    )

    request = build_run_request(
        workspace_root=workspace_root,
        staged_upload_registry=staged_registry,
        eval_year=2026,
        eval_month=4,
    )

    assert request.orders_path == Path(
        staged_registry["sales"]["current_file"]["staged_path"]
    ).resolve()
    assert request.daily_stock_path == Path(
        staged_registry["stock"]["current_file"]["staged_path"]
    ).resolve()
    assert request.product_path == Path(
        staged_registry["sku_live"]["current_file"]["staged_path"]
    ).resolve()
    assert request.site_mapping_path == site_mapping_path.resolve()
    assert request.eval_year == 2026
    assert request.eval_month == 4
    assert request.output_dir == (workspace_root / "outputs").resolve()
    assert request.output_workbook == request.artifacts.workbook
    assert request.artifacts.workbook.parent == request.output_dir
    assert request.artifacts.workbook.name == "OOS_Opportunity_Lost_2026-04_V5.xlsx"
    assert request.artifacts.detail_csv.parent == request.output_dir
    assert request.artifacts.summary_site_csv.parent == request.output_dir
    assert request.artifacts.summary_sku_csv.parent == request.output_dir
    assert request.artifacts.summary_total_csv.parent == request.output_dir
    assert request.artifacts.qa_summary_csv.parent == request.output_dir


def _build_staged_registry(
    workspace_root: Path,
    *,
    sales_name: str,
    stock_dates: tuple[str, ...],
    sku_name: str,
) -> dict[str, dict[str, object]]:
    input_dir = workspace_root / "inputs"
    sales_path = input_dir / "sales" / sales_name
    stock_path = input_dir / "stock" / "current.csv"
    sku_live_path = input_dir / "sku-live" / sku_name

    sales_path.parent.mkdir(parents=True, exist_ok=True)
    stock_path.parent.mkdir(parents=True, exist_ok=True)
    sku_live_path.parent.mkdir(parents=True, exist_ok=True)

    sales_path.write_text(
        "Purchase Date\tSku\tstock\tQuantity\tGross\tNet\tProduct Name\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        {
            "posting_date": list(stock_dates),
            "site_code": ["1001"] * len(stock_dates),
            "article_code": ["SKU-1"] * len(stock_dates),
            "stock_balance": [5] * len(stock_dates),
        }
    ).to_csv(stock_path, index=False)
    pd.DataFrame(
        {
            "skuNo": ["SKU-1"],
            "productName": ["Sample SKU"],
            "status": ["Live"],
        }
    ).to_csv(sku_live_path, index=False)

    return {
        "sales": {
            "current_file": {
                "slot_key": "sales",
                "source_name": sales_path.name,
                "staged_path": str(sales_path),
            }
        },
        "stock": {
            "current_file": {
                "slot_key": "stock",
                "source_name": stock_path.name,
                "staged_path": str(stock_path),
            }
        },
        "sku_live": {
            "current_file": {
                "slot_key": "sku_live",
                "source_name": sku_live_path.name,
                "staged_path": str(sku_live_path),
            }
        },
    }
