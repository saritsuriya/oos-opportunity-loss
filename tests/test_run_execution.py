from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.run_execution import (
    build_run_request,
    execute_frozen_v5_run,
    suggest_evaluation_month,
)


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
        lambda *_args, **_kwargs: site_mapping_path,
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
    assert request.channel_key == "th"
    assert request.eval_year == 2026
    assert request.eval_month == 4
    assert request.output_dir == (workspace_root / "outputs").resolve()
    assert request.output_workbook == request.artifacts.workbook
    assert request.artifacts.workbook.parent == request.output_dir
    assert request.artifacts.workbook.name == "OOS_Opportunity_Lost_TH_2026-04_V5.xlsx"
    assert request.artifacts.detail_csv.parent == request.output_dir
    assert request.artifacts.summary_site_csv.parent == request.output_dir
    assert request.artifacts.summary_sku_csv.parent == request.output_dir
    assert request.artifacts.summary_total_csv.parent == request.output_dir
    assert request.artifacts.qa_summary_csv.parent == request.output_dir


def test_build_run_request_uses_bundled_site_mapping_for_non_th_channel(
    tmp_path: Path, monkeypatch
) -> None:
    workspace_root = tmp_path / "session-zeta"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales-cn.xlsx",
        stock_dates=("2026-02-01", "2026-02-14"),
        sku_name="sku-cn.xlsx",
    )
    bundled_site_mapping_path = workspace_root / "bundled-site-map-cn.xlsx"
    bundled_site_mapping_path.write_text(
        "Virtual Location,Site,Active\nwh-bkk,1001,X\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "streamlit_app.services.v5_boundary.locate_bundled_site_mapping",
        lambda *_args, **_kwargs: bundled_site_mapping_path,
    )

    request = build_run_request(
        workspace_root=workspace_root,
        staged_upload_registry=staged_registry,
        channel_key="kingpowercn",
        eval_year=2026,
        eval_month=2,
    )

    assert request.channel_key == "kingpowercn"
    assert request.site_mapping_path == bundled_site_mapping_path.resolve()


def test_execute_frozen_v5_run_returns_structured_success_payload(
    tmp_path: Path, monkeypatch
) -> None:
    workspace_root = tmp_path / "session-delta"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales.tsv",
        stock_dates=("2026-04-01", "2026-04-15"),
        sku_name="sku-live.csv",
    )
    site_mapping_path = workspace_root / "bundled-site-map.csv"
    site_mapping_path.write_text(
        "Virtual Location,Site,Active\nwh-bkk,1001,X\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "streamlit_app.services.v5_boundary.locate_bundled_site_mapping",
        lambda *_args, **_kwargs: site_mapping_path,
    )

    request = build_run_request(
        workspace_root=workspace_root,
        staged_upload_registry=staged_registry,
        eval_year=2026,
        eval_month=4,
    )
    captured: dict[str, object] = {}

    result = execute_frozen_v5_run(request, symbols=_build_success_symbols(captured))

    assert result.ok is True
    assert result.status == "success"
    assert result.detail_row_count == 1
    assert result.qa_summary_row_count == 1
    assert result.unmapped_site_count == 1
    assert result.lost_value_net_raw == 12.5
    assert result.artifacts.workbook == request.artifacts.workbook
    assert result.artifacts.detail_csv.exists()
    assert result.artifacts.summary_site_csv.exists()
    assert result.artifacts.summary_sku_csv.exists()
    assert result.artifacts.summary_total_csv.exists()
    assert result.artifacts.qa_summary_csv.exists()
    assert captured["orders_path"] == str(request.orders_path)
    assert captured["daily_stock_path"] == str(request.daily_stock_path)
    assert captured["site_mapping_path"] == str(request.site_mapping_path)
    assert captured["product_path"] == str(request.product_path)
    assert captured["channel_key"] == "th"
    assert captured["eval_year"] == 2026
    assert captured["eval_month"] == 4
    assert captured["baseline_recent_months"] == 6
    assert captured["baseline_fallback_months"] == 6
    payload = result.as_dict()
    assert payload["period"] == "2026-04"
    assert payload["output_dir"] == str(request.output_dir)
    assert payload["output_workbook"] == str(request.output_workbook)


def test_execute_frozen_v5_run_returns_structured_failure_payload(
    tmp_path: Path, monkeypatch
) -> None:
    workspace_root = tmp_path / "session-epsilon"
    staged_registry = _build_staged_registry(
        workspace_root,
        sales_name="sales.tsv",
        stock_dates=("2026-04-01", "2026-04-15"),
        sku_name="sku-live.csv",
    )
    site_mapping_path = workspace_root / "bundled-site-map.csv"
    site_mapping_path.write_text(
        "Virtual Location,Site,Active\nwh-bkk,1001,X\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "streamlit_app.services.v5_boundary.locate_bundled_site_mapping",
        lambda *_args, **_kwargs: site_mapping_path,
    )

    request = build_run_request(
        workspace_root=workspace_root,
        staged_upload_registry=staged_registry,
        eval_year=2026,
        eval_month=4,
    )

    result = execute_frozen_v5_run(
        request,
        symbols=_build_failure_symbols(RuntimeError("analysis failed")),
    )

    assert result.ok is False
    assert result.status == "failed"
    assert result.error_type == "RuntimeError"
    assert result.error_message == "analysis failed"
    assert result.detail_row_count == 0
    assert result.qa_summary_row_count == 0
    assert result.unmapped_site_count == 0
    assert result.lost_value_net_raw == 0.0
    assert result.artifacts.workbook == request.artifacts.workbook
    payload = result.as_dict()
    assert payload["status"] == "failed"
    assert payload["error_type"] == "RuntimeError"
    assert payload["output_dir"] == str(request.output_dir)


def _build_staged_registry(
    workspace_root: Path,
    *,
    sales_name: str,
    stock_dates: tuple[str, ...],
    sku_name: str,
    site_mapping_name: str | None = None,
) -> dict[str, dict[str, object]]:
    input_dir = workspace_root / "inputs"
    sales_path = input_dir / "sales" / sales_name
    stock_path = input_dir / "stock" / "current.csv"
    sku_live_path = input_dir / "sku-live" / sku_name
    site_mapping_path = input_dir / "site-mapping" / site_mapping_name if site_mapping_name else None

    sales_path.parent.mkdir(parents=True, exist_ok=True)
    stock_path.parent.mkdir(parents=True, exist_ok=True)
    sku_live_path.parent.mkdir(parents=True, exist_ok=True)
    if site_mapping_path is not None:
        site_mapping_path.parent.mkdir(parents=True, exist_ok=True)

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

    registry = {
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
    if site_mapping_path is not None:
        site_mapping_path.write_text(
            "Virtual Location,Site,Active\nwh-bkk,1001,X\n",
            encoding="utf-8",
        )
        registry["site_mapping"] = {
            "current_file": {
                "slot_key": "site_mapping",
                "source_name": site_mapping_path.name,
                "staged_path": str(site_mapping_path),
            }
        }
    return registry


def _build_success_symbols(captured: dict[str, object]) -> dict[str, object]:
    class InputPaths:
        def __init__(
            self,
            *,
            orders_path: str,
            daily_stock_path: str,
            site_mapping_path: str,
            product_path: str,
            channel_key: str,
        ) -> None:
            captured["orders_path"] = orders_path
            captured["daily_stock_path"] = daily_stock_path
            captured["site_mapping_path"] = site_mapping_path
            captured["product_path"] = product_path
            captured["channel_key"] = channel_key
            self.orders_path = orders_path
            self.daily_stock_path = daily_stock_path
            self.site_mapping_path = site_mapping_path
            self.product_path = product_path
            self.channel_key = channel_key

    class DataLoaderV5:
        def __init__(self, paths: InputPaths) -> None:
            self.paths = paths

        def load_site_mapping(self) -> pd.DataFrame:
            return pd.DataFrame({"site_code": ["1001"], "virtual_site": ["wh-bkk"]})

        def load_product_universe(self) -> pd.DataFrame:
            return pd.DataFrame({"sku": ["SKU-1"], "product_name": ["Sample SKU"]})

        def load_orders(self) -> pd.DataFrame:
            return pd.DataFrame({"sku": ["SKU-1"], "quantity": [1]})

        def load_daily_stock(self) -> pd.DataFrame:
            return pd.DataFrame({"sku": ["SKU-1"], "stock_balance": [5]})

    class ModelConfig:
        def __init__(
            self,
            *,
            eval_year: int,
            eval_month: int,
            baseline_recent_months: int,
            baseline_fallback_months: int,
        ) -> None:
            captured["eval_year"] = eval_year
            captured["eval_month"] = eval_month
            captured["baseline_recent_months"] = baseline_recent_months
            captured["baseline_fallback_months"] = baseline_fallback_months

    class DailyOOSOpportunityV5:
        def __init__(
            self,
            *,
            product_df: pd.DataFrame,
            orders_df: pd.DataFrame,
            daily_stock_df: pd.DataFrame,
            site_map_df: pd.DataFrame,
            config: ModelConfig,
        ) -> None:
            self.product_df = product_df
            self.orders_df = orders_df
            self.daily_stock_df = daily_stock_df
            self.site_map_df = site_map_df
            self.config = config

        def run(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            detail = pd.DataFrame({"lost_value_net_raw": [12.5]})
            qa_summary = pd.DataFrame({"metric": ["ok"], "value": [1]})
            unmapped_site = pd.DataFrame({"site_code": ["missing-site"]})
            return detail, qa_summary, unmapped_site

    class ReporterV5:
        def generate(
            self,
            detail: pd.DataFrame,
            qa_summary: pd.DataFrame,
            unmapped_site: pd.DataFrame,
            output_xlsx: str,
        ) -> str:
            workbook_path = Path(output_xlsx)
            workbook_path.parent.mkdir(parents=True, exist_ok=True)
            workbook_path.write_text("workbook", encoding="utf-8")
            workbook_path.with_name(f"{workbook_path.stem}_detail.csv").write_text(
                detail.to_csv(index=False),
                encoding="utf-8",
            )
            workbook_path.with_name(
                f"{workbook_path.stem}_summary_site.csv"
            ).write_text("summary_site\n", encoding="utf-8")
            workbook_path.with_name(
                f"{workbook_path.stem}_summary_sku.csv"
            ).write_text("summary_sku\n", encoding="utf-8")
            workbook_path.with_name(
                f"{workbook_path.stem}_summary_total.csv"
            ).write_text("summary_total\n", encoding="utf-8")
            workbook_path.with_name(
                f"{workbook_path.stem}_qa_summary.csv"
            ).write_text(qa_summary.to_csv(index=False), encoding="utf-8")
            return str(workbook_path)

    return {
        "InputPaths": InputPaths,
        "DataLoaderV5": DataLoaderV5,
        "ModelConfig": ModelConfig,
        "DailyOOSOpportunityV5": DailyOOSOpportunityV5,
        "ReporterV5": ReporterV5,
    }


def _build_failure_symbols(error: Exception) -> dict[str, object]:
    symbols = _build_success_symbols({})

    class FailingDailyOOSOpportunityV5:
        def __init__(
            self,
            *,
            product_df: pd.DataFrame,
            orders_df: pd.DataFrame,
            daily_stock_df: pd.DataFrame,
            site_map_df: pd.DataFrame,
            config: object,
        ) -> None:
            self.product_df = product_df
            self.orders_df = orders_df
            self.daily_stock_df = daily_stock_df
            self.site_map_df = site_map_df
            self.config = config

        def run(self) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
            raise error

    symbols["DailyOOSOpportunityV5"] = FailingDailyOOSOpportunityV5
    return symbols
