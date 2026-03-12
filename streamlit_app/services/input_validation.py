"""Slot-aware validation for staged upload files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd

try:
    from streamlit_app.services.upload_staging import get_upload_slot
except ModuleNotFoundError:
    from services.upload_staging import get_upload_slot


@dataclass(frozen=True)
class ValidationFinding:
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True)
class ValidationSummary:
    row_count: int | None = None
    date_field: str | None = None
    min_date: str | None = None
    max_date: str | None = None
    month_hints: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "row_count": self.row_count,
            "date_field": self.date_field,
            "min_date": self.min_date,
            "max_date": self.max_date,
            "month_hints": list(self.month_hints),
        }


@dataclass(frozen=True)
class InputValidationResult:
    slot_key: str
    source_name: str
    staged_path: str
    errors: tuple[ValidationFinding, ...] = ()
    warnings: tuple[ValidationFinding, ...] = ()
    summary: ValidationSummary = field(default_factory=ValidationSummary)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, object]:
        return {
            "slot_key": self.slot_key,
            "source_name": self.source_name,
            "staged_path": self.staged_path,
            "is_valid": self.is_valid,
            "errors": [issue.as_dict() for issue in self.errors],
            "warnings": [issue.as_dict() for issue in self.warnings],
            "summary": self.summary.as_dict(),
        }


@dataclass(frozen=True)
class SlotValidationContract:
    required_columns: tuple[str, ...]
    read_frame: Callable[[Path], pd.DataFrame]


_SLOT_CONTRACTS: dict[str, SlotValidationContract] = {
    "sales": SlotValidationContract(
        required_columns=("Purchase Date", "Sku", "stock", "Quantity", "Gross", "Net", "Product Name"),
        read_frame=lambda path: pd.read_excel(path)
        if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}
        else pd.read_csv(path, encoding="utf-16", sep="\t"),
    ),
    "stock": SlotValidationContract(
        required_columns=("posting_date", "site_code", "article_code", "stock_balance"),
        read_frame=pd.read_csv,
    ),
    "sku_live": SlotValidationContract(
        required_columns=("skuNo",),
        read_frame=pd.read_csv,
    ),
}


def validate_staged_input(staged_file: Mapping[str, object]) -> InputValidationResult:
    slot_key = str(staged_file.get("slot_key") or "")
    source_name = str(staged_file.get("source_name") or "")
    staged_path = str(staged_file.get("staged_path") or "")

    if slot_key not in _SLOT_CONTRACTS:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="unknown_slot",
            message=f"Validation does not support upload slot '{slot_key}'.",
        )

    if not staged_path:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="missing_staged_path",
            message="Staged upload metadata is missing a file path.",
        )

    path = Path(staged_path).expanduser()
    if not path.exists() or not path.is_file():
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="missing_staged_file",
            message=f"Staged file does not exist: {path}",
        )

    slot = get_upload_slot(slot_key)
    suffix = path.suffix.lower() or Path(source_name).suffix.lower()
    if suffix not in slot.accepted_extensions:
        expected = ", ".join(slot.accepted_extensions)
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="unsupported_format",
            message=f"{slot.label} files must use one of: {expected}",
        )

    contract = _SLOT_CONTRACTS[slot_key]
    try:
        frame = contract.read_frame(path)
    except Exception as exc:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="unreadable_file",
            message=f"Could not read staged {slot.label.lower()} file: {exc}",
        )

    missing_columns = [column for column in contract.required_columns if column not in frame.columns]
    if missing_columns:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            code="missing_required_columns",
            message=f"Missing required columns: {', '.join(missing_columns)}",
        )

    return InputValidationResult(
        slot_key=slot_key,
        source_name=source_name,
        staged_path=str(path),
    )


def _result_with_error(
    *,
    slot_key: str,
    source_name: str,
    staged_path: str,
    code: str,
    message: str,
) -> InputValidationResult:
    return InputValidationResult(
        slot_key=slot_key,
        source_name=source_name,
        staged_path=staged_path,
        errors=(ValidationFinding(code=code, message=message),),
    )
