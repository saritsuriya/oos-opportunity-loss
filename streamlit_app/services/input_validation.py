"""Slot-aware validation for staged upload files."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Mapping

import pandas as pd

from channel_profiles import (
    CHANNEL_TH,
    get_channel_profile,
    get_site_mapping_virtual_sites,
    normalize_channel_key,
    normalize_virtual_site,
)

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
    channel_key: str = CHANNEL_TH
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
            "channel_key": self.channel_key,
            "is_valid": self.is_valid,
            "errors": [issue.as_dict() for issue in self.errors],
            "warnings": [issue.as_dict() for issue in self.warnings],
            "summary": self.summary.as_dict(),
        }


@dataclass(frozen=True)
class SlotValidationContract:
    required_columns: tuple[str, ...]
    read_frame: Callable[[Path], pd.DataFrame]
    date_field: str | None = None


NEAR_EMPTY_ROW_COUNT = 1


_SLOT_CONTRACTS: dict[str, SlotValidationContract] = {
    "stock": SlotValidationContract(
        required_columns=("posting_date", "site_code", "article_code", "stock_balance"),
        read_frame=pd.read_csv,
        date_field="posting_date",
    ),
    "site_mapping": SlotValidationContract(
        required_columns=("Virtual Location", "Site", "Active"),
        read_frame=lambda path: pd.read_excel(path, sheet_name="Include")
        if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}
        else pd.read_csv(path),
    ),
}


def validate_staged_input(
    staged_file: Mapping[str, object],
    *,
    channel_key: str = CHANNEL_TH,
) -> InputValidationResult:
    slot_key = str(staged_file.get("slot_key") or "")
    source_name = str(staged_file.get("source_name") or "")
    staged_path = str(staged_file.get("staged_path") or "")
    normalized_channel = normalize_channel_key(channel_key)

    if slot_key not in {"sales", "stock", "sku_live", "site_mapping"}:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            channel_key=normalized_channel,
            code="unknown_slot",
            message=f"Validation does not support upload slot '{slot_key}'.",
        )

    if not staged_path:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            channel_key=normalized_channel,
            code="missing_staged_path",
            message="Staged upload metadata is missing a file path.",
        )

    path = Path(staged_path).expanduser()
    if not path.exists() or not path.is_file():
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            channel_key=normalized_channel,
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
            channel_key=normalized_channel,
            code="unsupported_format",
            message=f"{slot.label} files must use one of: {expected}",
        )

    contract = _resolve_contract(slot_key, normalized_channel)
    try:
        frame = contract.read_frame(path)
    except Exception as exc:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            channel_key=normalized_channel,
            code="unreadable_file",
            message=f"Could not read staged {slot.label.lower()} file: {exc}",
        )

    missing_columns = [column for column in contract.required_columns if column not in frame.columns]
    if missing_columns:
        return _result_with_error(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=staged_path,
            channel_key=normalized_channel,
            code="missing_required_columns",
            message=f"Missing required columns: {', '.join(missing_columns)}",
        )

    site_mapping_errors = _build_site_mapping_errors(slot_key, frame, normalized_channel)
    if site_mapping_errors:
        return InputValidationResult(
            slot_key=slot_key,
            source_name=source_name,
            staged_path=str(path),
            channel_key=normalized_channel,
            errors=site_mapping_errors,
        )

    summary = _build_summary(slot_key, frame, contract, normalized_channel)
    return InputValidationResult(
        slot_key=slot_key,
        source_name=source_name,
        staged_path=str(path),
        channel_key=normalized_channel,
        warnings=_build_warnings(summary),
        summary=summary,
    )


def _result_with_error(
    *,
    slot_key: str,
    source_name: str,
    staged_path: str,
    channel_key: str,
    code: str,
    message: str,
) -> InputValidationResult:
    return InputValidationResult(
        slot_key=slot_key,
        source_name=source_name,
        staged_path=staged_path,
        channel_key=channel_key,
        errors=(ValidationFinding(code=code, message=message),),
    )


def _build_summary(
    slot_key: str,
    frame: pd.DataFrame,
    contract: SlotValidationContract,
    channel_key: str,
) -> ValidationSummary:
    row_count = int(len(frame.index))
    date_field = contract.date_field
    if not date_field:
        return ValidationSummary(row_count=row_count)

    parsed_dates = (
        _parse_date_field(slot_key, frame[date_field], channel_key=channel_key)
        if date_field in frame.columns
        else pd.Series()
    )
    parsed_dates = parsed_dates.dropna()
    if parsed_dates.empty:
        return ValidationSummary(row_count=row_count, date_field=date_field)

    normalized = pd.to_datetime(parsed_dates, errors="coerce").dropna().dt.normalize()
    month_hints = tuple(sorted(set(normalized.dt.strftime("%Y-%m"))))
    return ValidationSummary(
        row_count=row_count,
        date_field=date_field,
        min_date=normalized.min().date().isoformat(),
        max_date=normalized.max().date().isoformat(),
        month_hints=month_hints,
    )


def _build_warnings(summary: ValidationSummary) -> tuple[ValidationFinding, ...]:
    warnings: list[ValidationFinding] = []
    if summary.row_count == 0:
        warnings.append(
            ValidationFinding(
                code="empty_dataset",
                message="The file parsed successfully but contains no data rows.",
            )
        )
    elif summary.row_count is not None and summary.row_count <= NEAR_EMPTY_ROW_COUNT:
        warnings.append(
            ValidationFinding(
                code="near_empty_dataset",
                message="The file parsed successfully but contains very few rows.",
            )
        )

    if len(summary.month_hints) > 1:
        warnings.append(
            ValidationFinding(
                code="multiple_month_hints",
                message="Detected data from multiple months in the uploaded file.",
            )
        )
    return tuple(warnings)


def _build_site_mapping_errors(
    slot_key: str,
    frame: pd.DataFrame,
    channel_key: str,
) -> tuple[ValidationFinding, ...]:
    if slot_key != "site_mapping":
        return ()

    active_rows = frame.copy()
    active_rows["Active"] = active_rows["Active"].fillna("").astype(str).str.strip().str.upper()
    active_rows = active_rows[active_rows["Active"] == "X"].copy()
    if active_rows.empty:
        return (
            ValidationFinding(
                code="site_mapping_no_active_rows",
                message="The site-mapping file does not contain any active rows marked with 'X'.",
            ),
        )

    allowed_virtual_sites = set(get_site_mapping_virtual_sites(channel_key))
    if not allowed_virtual_sites:
        return ()

    matched_rows = active_rows[
        active_rows["Virtual Location"].map(normalize_virtual_site).isin(allowed_virtual_sites)
    ]
    if not matched_rows.empty:
        return ()

    channel_label = get_channel_profile(channel_key).label
    return (
        ValidationFinding(
            code="site_mapping_no_channel_rows",
            message=(
                f"The site-mapping file does not contain any active {channel_label} virtual locations. "
                "Check that the uploaded workbook matches the selected channel."
            ),
        ),
    )


def _parse_date_field(slot_key: str, series: pd.Series, *, channel_key: str = CHANNEL_TH) -> pd.Series:
    raw = series.astype(str)
    if slot_key == "sales":
        first_pass = pd.to_datetime(raw, errors="coerce", dayfirst=False)
        second_pass = pd.to_datetime(raw, errors="coerce", dayfirst=True)
        return second_pass if second_pass.notna().sum() > first_pass.notna().sum() else first_pass
    return pd.to_datetime(raw, errors="coerce")


def _resolve_contract(slot_key: str, channel_key: str) -> SlotValidationContract:
    if slot_key == "sales":
        if channel_key == CHANNEL_TH:
            return SlotValidationContract(
                required_columns=("Purchase Date", "Sku", "stock", "Quantity", "Gross", "Net", "Product Name"),
                read_frame=lambda path: pd.read_excel(path)
                if path.suffix.lower() in {".xlsx", ".xlsm", ".xls"}
                else pd.read_csv(path, encoding="utf-16", sep="\t"),
                date_field="Purchase Date",
            )
        profile = get_channel_profile(channel_key)
        return SlotValidationContract(
            required_columns=("DATE", "SKU", "DESCRIPTION", "QTY", "GROSS", "NET", "Storage Location"),
            read_frame=lambda path, sheet_name=profile.sales_sheet: pd.read_excel(path, sheet_name=sheet_name, header=1),
            date_field="DATE",
        )
    if slot_key == "sku_live":
        if channel_key == CHANNEL_TH:
            return SlotValidationContract(
                required_columns=("skuNo",),
                read_frame=pd.read_csv,
            )
        profile = get_channel_profile(channel_key)
        return SlotValidationContract(
            required_columns=("SKU CODE", "WEB STATUS"),
            read_frame=lambda path, sheet_names=profile.product_sheets: _read_product_workbook_for_validation(path, sheet_names),
        )
    return _SLOT_CONTRACTS[slot_key]


def _read_product_workbook_for_validation(path: Path, sheet_names: tuple[str, ...]) -> pd.DataFrame:
    workbook = pd.ExcelFile(path)
    missing_sheets = [sheet for sheet in sheet_names if sheet not in workbook.sheet_names]
    if missing_sheets:
        raise ValueError(f"Workbook missing expected sheets: {missing_sheets}")
    frames = [pd.read_excel(path, sheet_name=sheet_name, header=1) for sheet_name in sheet_names]
    return pd.concat(frames, ignore_index=True)
