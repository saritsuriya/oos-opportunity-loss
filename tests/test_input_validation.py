from __future__ import annotations

import sys
from pathlib import Path
from typing import Callable

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streamlit_app.services.input_validation import validate_staged_input
from streamlit_app.services.upload_staging import StagedInputFile


def write_valid_sales_excel(path: Path) -> None:
    pd.DataFrame(
        {
            "Purchase Date": ["2026-02-01", "2026-02-28"],
            "Sku": ["SKU-1", "SKU-2"],
            "stock": ["bkk-out", "dmk-out"],
            "Quantity": [2, 4],
            "Gross": [100, 200],
            "Net": [90, 180],
            "Product Name": ["Bag", "Watch"],
        }
    ).to_excel(path, index=False)


def write_valid_sales_tsv(path: Path) -> None:
    pd.DataFrame(
        {
            "Purchase Date": ["2026-02-01", "2026-02-28"],
            "Sku": ["SKU-1", "SKU-2"],
            "stock": ["bkk-out", "dmk-out"],
            "Quantity": [2, 4],
            "Gross": [100, 200],
            "Net": [90, 180],
            "Product Name": ["Bag", "Watch"],
        }
    ).to_csv(path, index=False, sep="\t", encoding="utf-16")


def write_empty_stock_csv(path: Path) -> None:
    pd.DataFrame(columns=["posting_date", "site_code", "article_code", "stock_balance"]).to_csv(path, index=False)


def write_valid_stock_csv(path: Path) -> None:
    pd.DataFrame(
        {
            "posting_date": ["2026-02-01", "2026-02-15"],
            "site_code": ["BKK", "DMK"],
            "article_code": ["SKU-1", "SKU-2"],
            "stock_balance": [5, 7],
        }
    ).to_csv(path, index=False)


def write_multi_month_stock_csv(path: Path) -> None:
    pd.DataFrame(
        {
            "posting_date": ["2026-02-01", "2026-03-01"],
            "site_code": ["BKK", "BKK"],
            "article_code": ["SKU-1", "SKU-2"],
            "stock_balance": [5, 7],
        }
    ).to_csv(path, index=False)


def write_valid_sku_csv(path: Path) -> None:
    pd.DataFrame(
        {
            "skuNo": ["SKU-1", "SKU-2"],
            "productName": ["Bag", "Watch"],
            "status": ["Live", "Live"],
        }
    ).to_csv(path, index=False)


def write_near_empty_sku_csv(path: Path) -> None:
    pd.DataFrame({"skuNo": ["SKU-1"], "productName": ["Bag"], "status": ["Live"]}).to_csv(path, index=False)


def write_sales_missing_columns(path: Path) -> None:
    pd.DataFrame(
        {
            "Purchase Date": ["2026-02-01"],
            "Sku": ["SKU-1"],
            "stock": ["bkk-out"],
            "Quantity": [2],
        }
    ).to_excel(path, index=False)


def write_stock_missing_columns(path: Path) -> None:
    pd.DataFrame(
        {
            "posting_date": ["2026-02-01"],
            "site_code": ["BKK"],
        }
    ).to_csv(path, index=False)


def write_sku_missing_columns(path: Path) -> None:
    pd.DataFrame({"productName": ["Bag"]}).to_csv(path, index=False)


def test_critical_rejects_unsupported_formats_for_each_slot(tmp_path: Path) -> None:
    cases = (
        ("sales", "sales.csv"),
        ("stock", "stock.xlsx"),
        ("sku_live", "sku-live.txt"),
    )

    for slot_key, filename in cases:
        metadata = write_raw_metadata(tmp_path, slot_key=slot_key, filename=filename, payload=b"placeholder")

        result = validate_staged_input(metadata)

        assert result.is_valid is False
        assert [issue.code for issue in result.errors] == ["unsupported_format"]


@pytest.mark.parametrize(
    ("slot_key", "filename", "payload"),
    (
        ("sales", "sales.xlsx", b"not-an-excel-workbook"),
        ("stock", "stock.csv", b"\xff\xfe\xfd"),
        ("sku_live", "sku-live.csv", b"\xff\xfe\xfd"),
    ),
)
def test_critical_rejects_unreadable_files_for_each_slot(
    tmp_path: Path,
    slot_key: str,
    filename: str,
    payload: bytes,
) -> None:
    metadata = write_raw_metadata(tmp_path, slot_key=slot_key, filename=filename, payload=payload)

    result = validate_staged_input(metadata)

    assert result.is_valid is False
    assert [issue.code for issue in result.errors] == ["unreadable_file"]


@pytest.mark.parametrize(
    ("slot_key", "filename", "writer"),
    (
        ("sales", "sales.xlsx", write_sales_missing_columns),
        ("stock", "stock.csv", write_stock_missing_columns),
        ("sku_live", "sku-live.csv", write_sku_missing_columns),
    ),
)
def test_critical_rejects_missing_required_columns_for_each_slot(
    tmp_path: Path,
    slot_key: str,
    filename: str,
    writer: Callable[[Path], None],
) -> None:
    metadata = write_tabular_metadata(tmp_path, slot_key=slot_key, filename=filename, writer=writer)

    result = validate_staged_input(metadata)

    assert result.is_valid is False
    assert [issue.code for issue in result.errors] == ["missing_required_columns"]


def test_warnings_include_sales_summary_month_hints(tmp_path: Path) -> None:
    metadata = write_tabular_metadata(
        tmp_path,
        slot_key="sales",
        filename="sales.xlsx",
        writer=write_valid_sales_excel,
    )

    result = validate_staged_input(metadata)

    assert result.is_valid is True
    assert result.warnings == ()
    assert result.summary.row_count == 2
    assert result.summary.date_field == "Purchase Date"
    assert result.summary.min_date == "2026-02-01"
    assert result.summary.max_date == "2026-02-28"
    assert result.summary.month_hints == ("2026-02",)


def test_warnings_include_empty_dataset_warning_for_stock(tmp_path: Path) -> None:
    metadata = write_tabular_metadata(
        tmp_path,
        slot_key="stock",
        filename="stock.csv",
        writer=write_empty_stock_csv,
    )

    result = validate_staged_input(metadata)

    assert result.is_valid is True
    assert [issue.code for issue in result.warnings] == ["empty_dataset"]
    assert result.summary.row_count == 0
    assert result.summary.date_field == "posting_date"
    assert result.summary.month_hints == ()


def test_warnings_include_multiple_month_hint_warning_for_stock(tmp_path: Path) -> None:
    metadata = write_tabular_metadata(
        tmp_path,
        slot_key="stock",
        filename="stock.csv",
        writer=write_multi_month_stock_csv,
    )

    result = validate_staged_input(metadata)

    assert result.is_valid is True
    assert [issue.code for issue in result.warnings] == ["multiple_month_hints"]
    assert result.summary.row_count == 2
    assert result.summary.min_date == "2026-02-01"
    assert result.summary.max_date == "2026-03-01"
    assert result.summary.month_hints == ("2026-02", "2026-03")


def test_warnings_include_near_empty_warning_for_sku_live(tmp_path: Path) -> None:
    metadata = write_tabular_metadata(
        tmp_path,
        slot_key="sku_live",
        filename="sku-live.csv",
        writer=write_near_empty_sku_csv,
    )

    result = validate_staged_input(metadata)

    assert result.is_valid is True
    assert [issue.code for issue in result.warnings] == ["near_empty_dataset"]
    assert result.summary.row_count == 1
    assert result.summary.date_field is None
    assert result.summary.month_hints == ()


@pytest.mark.parametrize(
    ("slot_key", "filename", "writer", "expected_row_count"),
    (
        ("sales", "sales.xlsx", write_valid_sales_excel, 2),
        ("sales", "sales.tsv", write_valid_sales_tsv, 2),
        ("stock", "stock.csv", write_valid_stock_csv, 2),
        ("sku_live", "sku-live.csv", write_valid_sku_csv, 2),
    ),
)
def test_validation_contract_accepts_supported_formats_for_each_slot(
    tmp_path: Path,
    slot_key: str,
    filename: str,
    writer: Callable[[Path], None],
    expected_row_count: int,
) -> None:
    metadata = write_tabular_metadata(tmp_path, slot_key=slot_key, filename=filename, writer=writer)

    result = validate_staged_input(metadata)

    assert result.is_valid is True
    assert result.errors == ()
    assert result.warnings == ()
    assert result.summary.row_count == expected_row_count


def test_validation_contract_keeps_blocking_errors_separate_from_warnings(tmp_path: Path) -> None:
    blocking = validate_staged_input(
        write_raw_metadata(
            tmp_path,
            slot_key="stock",
            filename="stock.csv",
            payload=b"\xff\xfe\xfd",
        )
    )
    warning = validate_staged_input(
        write_tabular_metadata(
            tmp_path,
            slot_key="sku_live",
            filename="sku-live.csv",
            writer=write_near_empty_sku_csv,
        )
    )

    assert [issue.code for issue in blocking.errors] == ["unreadable_file"]
    assert blocking.warnings == ()
    assert blocking.summary.row_count is None

    assert warning.errors == ()
    assert [issue.code for issue in warning.warnings] == ["near_empty_dataset"]
    assert warning.summary.row_count == 1


def test_validation_contract_serializes_ui_summary_shape(tmp_path: Path) -> None:
    metadata = write_tabular_metadata(
        tmp_path,
        slot_key="stock",
        filename="stock.csv",
        writer=write_multi_month_stock_csv,
    )

    result = validate_staged_input(metadata).as_dict()

    assert result["is_valid"] is True
    assert result["errors"] == []
    assert result["warnings"] == [
        {
            "code": "multiple_month_hints",
            "message": "Detected data from multiple months in the uploaded file.",
        }
    ]
    assert result["summary"] == {
        "row_count": 2,
        "date_field": "posting_date",
        "min_date": "2026-02-01",
        "max_date": "2026-03-01",
        "month_hints": ["2026-02", "2026-03"],
    }


def write_tabular_metadata(
    tmp_path: Path,
    *,
    slot_key: str,
    filename: str,
    writer: Callable[[Path], None],
) -> dict[str, object]:
    path = tmp_path / filename
    writer(path)
    return build_metadata(slot_key=slot_key, source_name=filename, staged_path=path)


def write_raw_metadata(
    tmp_path: Path,
    *,
    slot_key: str,
    filename: str,
    payload: bytes,
) -> dict[str, object]:
    path = tmp_path / filename
    path.write_bytes(payload)
    return build_metadata(slot_key=slot_key, source_name=filename, staged_path=path)


def build_metadata(*, slot_key: str, source_name: str, staged_path: Path) -> dict[str, object]:
    return StagedInputFile(
        slot_key=slot_key,
        source_name=source_name,
        size_bytes=staged_path.stat().st_size,
        staged_path=str(staged_path),
    ).as_dict()
