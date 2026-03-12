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
