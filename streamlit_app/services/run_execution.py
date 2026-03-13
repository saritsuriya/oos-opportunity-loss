"""Run-service helpers for frozen V5 execution from staged session inputs."""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

try:
    from streamlit_app.services.v5_boundary import (
        FrozenV5RunRequest,
        RunArtifacts,
        build_frozen_v5_run_request,
        load_frozen_v5_symbols,
    )
except ModuleNotFoundError:
    from services.v5_boundary import (
        FrozenV5RunRequest,
        RunArtifacts,
        build_frozen_v5_run_request,
        load_frozen_v5_symbols,
    )


@dataclass(frozen=True)
class StagedRunInputs:
    sales_path: Path
    stock_path: Path
    sku_live_path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "sales_path": str(self.sales_path),
            "stock_path": str(self.stock_path),
            "sku_live_path": str(self.sku_live_path),
        }


@dataclass(frozen=True)
class SuggestedEvaluationMonth:
    eval_year: int | None
    eval_month: int | None
    is_confident: bool
    month_hints: tuple[str, ...]
    reason: str

    @property
    def label(self) -> str | None:
        if self.eval_year is None or self.eval_month is None:
            return None
        return f"{calendar.month_name[self.eval_month]} {self.eval_year}"

    def as_dict(self) -> dict[str, object]:
        return {
            "eval_year": self.eval_year,
            "eval_month": self.eval_month,
            "is_confident": self.is_confident,
            "label": self.label,
            "month_hints": list(self.month_hints),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class V5RunResult:
    ok: bool
    status: str
    request: FrozenV5RunRequest
    artifacts: RunArtifacts
    detail_row_count: int
    qa_summary_row_count: int
    unmapped_site_count: int
    lost_value_net_raw: float
    error_type: str | None = None
    error_message: str | None = None

    @classmethod
    def success(
        cls,
        *,
        request: FrozenV5RunRequest,
        detail: pd.DataFrame,
        qa_summary: pd.DataFrame,
        unmapped_site: pd.DataFrame,
    ) -> "V5RunResult":
        return cls(
            ok=True,
            status="success",
            request=request,
            artifacts=request.artifacts,
            detail_row_count=int(len(detail.index)),
            qa_summary_row_count=int(len(qa_summary.index)),
            unmapped_site_count=int(len(unmapped_site.index)),
            lost_value_net_raw=_sum_numeric_column(detail, "lost_value_net_raw"),
        )

    @classmethod
    def failure(cls, *, request: FrozenV5RunRequest, error: Exception) -> "V5RunResult":
        return cls(
            ok=False,
            status="failed",
            request=request,
            artifacts=request.artifacts,
            detail_row_count=0,
            qa_summary_row_count=0,
            unmapped_site_count=0,
            lost_value_net_raw=0.0,
            error_type=type(error).__name__,
            error_message=str(error),
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "status": self.status,
            "request": self.request.as_dict(),
            "artifacts": self.artifacts.as_dict(),
            "detail_row_count": self.detail_row_count,
            "qa_summary_row_count": self.qa_summary_row_count,
            "unmapped_site_count": self.unmapped_site_count,
            "lost_value_net_raw": self.lost_value_net_raw,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def resolve_staged_run_inputs(
    staged_upload_registry: Mapping[str, object],
) -> StagedRunInputs:
    return StagedRunInputs(
        sales_path=_resolve_staged_path(staged_upload_registry, "sales"),
        stock_path=_resolve_staged_path(staged_upload_registry, "stock"),
        sku_live_path=_resolve_staged_path(staged_upload_registry, "sku_live"),
    )


def suggest_evaluation_month_from_stock_file(
    stock_path: str | Path,
) -> SuggestedEvaluationMonth:
    path = Path(stock_path).expanduser().resolve()
    try:
        frame = pd.read_csv(path, usecols=["posting_date"])
    except Exception as exc:
        return SuggestedEvaluationMonth(
            eval_year=None,
            eval_month=None,
            is_confident=False,
            month_hints=(),
            reason=f"Could not read posting dates from the staged stock file: {exc}",
        )

    posting_dates = pd.to_datetime(frame["posting_date"], errors="coerce").dropna()
    if posting_dates.empty:
        return SuggestedEvaluationMonth(
            eval_year=None,
            eval_month=None,
            is_confident=False,
            month_hints=(),
            reason="The staged stock file did not contain any parseable posting dates.",
        )

    month_hints = tuple(sorted(set(posting_dates.dt.strftime("%Y-%m"))))
    if len(month_hints) == 1:
        year_text, month_text = month_hints[0].split("-", maxsplit=1)
        return SuggestedEvaluationMonth(
            eval_year=int(year_text),
            eval_month=int(month_text),
            is_confident=True,
            month_hints=month_hints,
            reason="Detected one calendar month in the staged stock file.",
        )

    return SuggestedEvaluationMonth(
        eval_year=None,
        eval_month=None,
        is_confident=False,
        month_hints=month_hints,
        reason="The staged stock file spans multiple months. Choose the evaluation month manually.",
    )


def suggest_evaluation_month(
    staged_upload_registry: Mapping[str, object],
) -> SuggestedEvaluationMonth:
    staged_inputs = resolve_staged_run_inputs(staged_upload_registry)
    return suggest_evaluation_month_from_stock_file(staged_inputs.stock_path)


def build_run_request(
    *,
    workspace_root: str | Path,
    staged_upload_registry: Mapping[str, object],
    eval_year: int,
    eval_month: int,
    baseline_recent_months: int = 6,
    baseline_fallback_months: int = 6,
) -> FrozenV5RunRequest:
    staged_inputs = resolve_staged_run_inputs(staged_upload_registry)
    return build_frozen_v5_run_request(
        workspace_root=workspace_root,
        orders_path=staged_inputs.sales_path,
        daily_stock_path=staged_inputs.stock_path,
        product_path=staged_inputs.sku_live_path,
        eval_year=eval_year,
        eval_month=eval_month,
        baseline_recent_months=baseline_recent_months,
        baseline_fallback_months=baseline_fallback_months,
    )


def execute_frozen_v5_run(
    request: FrozenV5RunRequest,
    *,
    symbols: Mapping[str, Any] | None = None,
) -> V5RunResult:
    try:
        _ensure_output_scope(request)
        request.output_dir.mkdir(parents=True, exist_ok=True)

        resolved_symbols = symbols or load_frozen_v5_symbols()
        input_paths = request.build_input_paths(resolved_symbols["InputPaths"])
        loader = resolved_symbols["DataLoaderV5"](input_paths)
        site_map_df = loader.load_site_mapping()
        product_df = loader.load_product_universe()
        orders_df = loader.load_orders()
        daily_stock_df = loader.load_daily_stock()

        model = resolved_symbols["DailyOOSOpportunityV5"](
            product_df=product_df,
            orders_df=orders_df,
            daily_stock_df=daily_stock_df,
            site_map_df=site_map_df,
            config=request.build_model_config(resolved_symbols["ModelConfig"]),
        )
        detail, qa_summary, unmapped_site = model.run()

        reporter = resolved_symbols["ReporterV5"]()
        reporter.generate(
            detail,
            qa_summary,
            unmapped_site,
            str(request.output_workbook),
        )
        _ensure_expected_artifacts_exist(request.artifacts)
        return V5RunResult.success(
            request=request,
            detail=detail,
            qa_summary=qa_summary,
            unmapped_site=unmapped_site,
        )
    except Exception as exc:
        return V5RunResult.failure(request=request, error=exc)


def _resolve_staged_path(
    staged_upload_registry: Mapping[str, object],
    slot_key: str,
) -> Path:
    slot_payload = staged_upload_registry.get(slot_key)
    current_file: Mapping[str, object] | None = None
    if isinstance(slot_payload, Mapping):
        if isinstance(slot_payload.get("current_file"), Mapping):
            current_file = slot_payload["current_file"]
        elif "staged_path" in slot_payload:
            current_file = slot_payload

    if current_file is None:
        msg = f"Missing staged file metadata for slot '{slot_key}'."
        raise KeyError(msg)

    staged_path = current_file.get("staged_path")
    if not staged_path:
        msg = f"Missing staged_path for slot '{slot_key}'."
        raise KeyError(msg)

    path = Path(str(staged_path)).expanduser().resolve()
    if not path.exists() or not path.is_file():
        msg = f"Missing staged file for slot '{slot_key}': {path}"
        raise FileNotFoundError(msg)
    return path


def _ensure_output_scope(request: FrozenV5RunRequest) -> None:
    for label, path_text in request.artifacts.as_dict().items():
        path = Path(path_text)
        if not path.is_relative_to(request.output_dir):
            msg = f"Frozen V5 artifact '{label}' escapes the active output workspace: {path}"
            raise ValueError(msg)


def _ensure_expected_artifacts_exist(artifacts: RunArtifacts) -> None:
    missing = [
        label
        for label, path_text in artifacts.as_dict().items()
        if not Path(path_text).exists()
    ]
    if missing:
        msg = f"Frozen V5 run did not produce expected artifacts: {', '.join(missing)}"
        raise FileNotFoundError(msg)


def _sum_numeric_column(frame: pd.DataFrame, column: str) -> float:
    if column not in frame.columns:
        return 0.0
    series = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    return float(series.sum())
