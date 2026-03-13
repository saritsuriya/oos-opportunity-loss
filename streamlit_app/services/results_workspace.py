"""Read-only results loader for the Phase 4 review and export workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import pandas as pd

try:
    from streamlit_app.services.run_workflow import RUN_STATUS_SUCCEEDED
except ModuleNotFoundError:
    from services.run_workflow import RUN_STATUS_SUCCEEDED


@dataclass(frozen=True)
class ReviewExportArtifact:
    key: str
    label: str
    file_type: str
    path: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "key": self.key,
            "label": self.label,
            "file_type": self.file_type,
            "path": str(self.path),
            "filename": self.path.name,
        }


@dataclass(frozen=True)
class ResultsWorkspacePayload:
    period: str
    workbook_path: Path
    output_dir: Path
    overview: dict[str, object]
    summary_total: pd.DataFrame
    summary_site: pd.DataFrame
    summary_sku: pd.DataFrame
    detail: pd.DataFrame
    qa_summary: pd.DataFrame
    unmapped_site: pd.DataFrame
    definitions: pd.DataFrame
    calculation_example: pd.DataFrame
    export_manifest: tuple[ReviewExportArtifact, ...]
    is_current: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "period": self.period,
            "workbook_path": str(self.workbook_path),
            "output_dir": str(self.output_dir),
            "overview": dict(self.overview),
            "summary_total_rows": int(len(self.summary_total.index)),
            "summary_site_rows": int(len(self.summary_site.index)),
            "summary_sku_rows": int(len(self.summary_sku.index)),
            "detail_rows": int(len(self.detail.index)),
            "qa_summary_rows": int(len(self.qa_summary.index)),
            "unmapped_site_rows": int(len(self.unmapped_site.index)),
            "definitions_rows": int(len(self.definitions.index)),
            "calculation_example_rows": int(len(self.calculation_example.index)),
            "export_manifest": [artifact.as_dict() for artifact in self.export_manifest],
            "is_current": self.is_current,
        }


@dataclass(frozen=True)
class ResultsWorkspaceLoadResult:
    ok: bool
    payload: ResultsWorkspacePayload | None
    error_type: str | None = None
    error_message: str | None = None

    @classmethod
    def success(cls, payload: ResultsWorkspacePayload) -> "ResultsWorkspaceLoadResult":
        return cls(ok=True, payload=payload)

    @classmethod
    def failure(
        cls,
        *,
        error_type: str,
        error_message: str,
    ) -> "ResultsWorkspaceLoadResult":
        return cls(
            ok=False,
            payload=None,
            error_type=error_type,
            error_message=error_message,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "payload": self.payload.as_dict() if self.payload else None,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


class ResultsWorkspaceError(Exception):
    """Base class for Phase 4 result-loading failures."""


class InvalidResultsWorkspaceState(ResultsWorkspaceError):
    """Raised when Phase 4 cannot derive a valid completed run from session state."""


class MissingResultsArtifact(ResultsWorkspaceError):
    """Raised when a required result artifact file is missing."""


class ResultsWorkbookReadError(ResultsWorkspaceError):
    """Raised when workbook-only trust sheets cannot be loaded."""


def load_results_workspace(
    run_workflow_state: Mapping[str, Any],
) -> ResultsWorkspaceLoadResult:
    try:
        payload = _load_results_workspace_payload(run_workflow_state)
        return ResultsWorkspaceLoadResult.success(payload)
    except ResultsWorkspaceError as exc:
        return ResultsWorkspaceLoadResult.failure(
            error_type=type(exc).__name__,
            error_message=str(exc),
        )
    except Exception as exc:  # pragma: no cover - defensive fallback
        return ResultsWorkspaceLoadResult.failure(
            error_type=type(exc).__name__,
            error_message=str(exc),
        )


def _load_results_workspace_payload(
    run_workflow_state: Mapping[str, Any],
) -> ResultsWorkspacePayload:
    result_payload = _resolve_completed_run_result(run_workflow_state)
    export_manifest = _build_export_manifest(result_payload)

    artifact_paths = {artifact.key: artifact.path for artifact in export_manifest}
    workbook_path = artifact_paths["workbook"]
    output_dir = workbook_path.parent.resolve()

    summary_total = _read_csv_artifact(artifact_paths["summary_total_csv"], "summary_total_csv")
    summary_site = _read_csv_artifact(artifact_paths["summary_site_csv"], "summary_site_csv")
    summary_sku = _read_csv_artifact(artifact_paths["summary_sku_csv"], "summary_sku_csv")
    detail = _read_csv_artifact(artifact_paths["detail_csv"], "detail_csv")
    qa_summary = _read_csv_artifact(artifact_paths["qa_summary_csv"], "qa_summary_csv")
    unmapped_site = _read_workbook_sheet(workbook_path, "QA Unmapped SiteCode")
    definitions = _read_workbook_sheet(workbook_path, "Definitions")
    calculation_example = _read_workbook_sheet(workbook_path, "Calculation Example")

    period = str(result_payload.get("period") or run_workflow_state.get("last_run_period") or "")
    if not period:
        raise InvalidResultsWorkspaceState(
            "Completed run payload is missing the period needed for the review workspace."
        )

    overview = _build_overview(
        run_workflow_state=run_workflow_state,
        result_payload=result_payload,
        summary_total=summary_total,
    )

    return ResultsWorkspacePayload(
        period=period,
        workbook_path=workbook_path,
        output_dir=output_dir,
        overview=overview,
        summary_total=summary_total,
        summary_site=summary_site,
        summary_sku=summary_sku,
        detail=detail,
        qa_summary=qa_summary,
        unmapped_site=unmapped_site,
        definitions=definitions,
        calculation_example=calculation_example,
        export_manifest=export_manifest,
        is_current=not bool(run_workflow_state.get("inputs_changed_since_last_run")),
    )


def _resolve_completed_run_result(
    run_workflow_state: Mapping[str, Any],
) -> Mapping[str, Any]:
    if not isinstance(run_workflow_state, Mapping) or not run_workflow_state:
        raise InvalidResultsWorkspaceState(
            "No completed run is available yet for the review workspace."
        )

    status = str(run_workflow_state.get("status") or "")
    if status != RUN_STATUS_SUCCEEDED:
        raise InvalidResultsWorkspaceState(
            "A successful frozen V5 run is required before results can be reviewed."
        )

    result_payload = run_workflow_state.get("result")
    if not isinstance(result_payload, Mapping):
        raise InvalidResultsWorkspaceState(
            "The successful run did not retain a structured result payload for review."
        )

    result_status = str(result_payload.get("status") or "")
    if result_status not in {"success", RUN_STATUS_SUCCEEDED}:
        raise InvalidResultsWorkspaceState(
            "The stored run payload is not marked as a successful completed run."
        )

    return result_payload


def _build_export_manifest(
    result_payload: Mapping[str, Any],
) -> tuple[ReviewExportArtifact, ...]:
    artifacts = result_payload.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise InvalidResultsWorkspaceState(
            "The completed run payload is missing its artifact manifest."
        )

    ordered_artifacts = (
        ("workbook", "Excel Workbook", "xlsx"),
        ("summary_total_csv", "Summary Total CSV", "csv"),
        ("summary_site_csv", "Summary by Site CSV", "csv"),
        ("summary_sku_csv", "Summary by SKU CSV", "csv"),
        ("detail_csv", "Detail CSV", "csv"),
        ("qa_summary_csv", "QA Summary CSV", "csv"),
    )

    manifest: list[ReviewExportArtifact] = []
    for key, label, file_type in ordered_artifacts:
        path_text = artifacts.get(key)
        if not path_text:
            raise InvalidResultsWorkspaceState(
                f"The completed run payload is missing the '{key}' artifact path."
            )
        path = Path(str(path_text)).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise MissingResultsArtifact(
                f"The completed run artifact '{key}' was not found: {path}"
            )
        manifest.append(
            ReviewExportArtifact(
                key=key,
                label=label,
                file_type=file_type,
                path=path,
            )
        )
    return tuple(manifest)


def _read_csv_artifact(path: Path, artifact_key: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except FileNotFoundError as exc:
        raise MissingResultsArtifact(
            f"The completed run artifact '{artifact_key}' was not found: {path}"
        ) from exc
    except Exception as exc:
        raise ResultsWorkspaceError(
            f"Could not read the completed run artifact '{artifact_key}': {exc}"
        ) from exc


def _read_workbook_sheet(workbook_path: Path, sheet_name: str) -> pd.DataFrame:
    try:
        return pd.read_excel(workbook_path, sheet_name=sheet_name)
    except FileNotFoundError as exc:
        raise MissingResultsArtifact(
            f"The completed run workbook was not found: {workbook_path}"
        ) from exc
    except ValueError as exc:
        raise ResultsWorkbookReadError(
            f"The completed run workbook is missing the '{sheet_name}' sheet."
        ) from exc
    except Exception as exc:
        raise ResultsWorkbookReadError(
            f"Could not read '{sheet_name}' from the completed run workbook: {exc}"
        ) from exc


def _build_overview(
    *,
    run_workflow_state: Mapping[str, Any],
    result_payload: Mapping[str, Any],
    summary_total: pd.DataFrame,
) -> dict[str, object]:
    summary_lookup = _summary_total_lookup(summary_total)
    return {
        "period": str(
            result_payload.get("period")
            or run_workflow_state.get("last_run_period")
            or run_workflow_state.get("selected_period")
            or ""
        ),
        "status_label": str(run_workflow_state.get("status_label") or "Succeeded"),
        "detail_row_count": int(result_payload.get("detail_row_count") or 0),
        "qa_summary_row_count": int(result_payload.get("qa_summary_row_count") or 0),
        "unmapped_site_count": int(result_payload.get("unmapped_site_count") or 0),
        "lost_value_net_raw": float(result_payload.get("lost_value_net_raw") or 0.0),
        "total_lost_qty_raw": float(summary_lookup.get("Total Lost Qty Raw", 0.0)),
        "total_lost_value_gross_raw": float(
            summary_lookup.get("Total Lost Value Gross Raw", 0.0)
        ),
        "total_lost_value_net_raw": float(
            summary_lookup.get("Total Lost Value Net Raw", 0.0)
        ),
        "is_current": not bool(run_workflow_state.get("inputs_changed_since_last_run")),
    }


def _summary_total_lookup(summary_total: pd.DataFrame) -> dict[str, float]:
    if "metric" not in summary_total.columns or "value" not in summary_total.columns:
        return {}
    lookup: dict[str, float] = {}
    for row in summary_total.itertuples(index=False):
        lookup[str(row.metric)] = float(pd.to_numeric(row.value, errors="coerce") or 0.0)
    return lookup
