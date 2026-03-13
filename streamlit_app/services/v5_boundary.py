"""Reusable boundary between the Streamlit app and the frozen V5 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
import sys
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
SITE_MAPPING_CANDIDATES: tuple[Path, ...] = (
    REPO_ROOT / "v5_daily_oos_opportunity" / "data" / "Site mapping.csv",
    REPO_ROOT / "v4_daily_oos_opportunity" / "data" / "Site mapping.csv",
    REPO_ROOT / "v2_opportunity_loss" / "data" / "Site mapping.csv",
)


@dataclass(frozen=True)
class BoundaryModule:
    import_path: str
    responsibility: str


@dataclass(frozen=True)
class V5BoundaryOverview:
    pipeline_name: str
    integration_mode: str
    site_mapping_path: str
    staged_inputs: tuple[str, ...]
    staged_outputs: tuple[str, ...]
    modules: tuple[BoundaryModule, ...]
    notes: tuple[str, ...]


@dataclass(frozen=True)
class RunBlueprint:
    workspace_root: Path
    input_dir: Path
    output_dir: Path
    output_workbook: Path
    output_detail_csv: Path
    output_summary_site_csv: Path
    output_summary_sku_csv: Path
    output_summary_total_csv: Path
    output_qa_summary_csv: Path
    bundled_site_mapping: Path | None
    eval_year: int
    eval_month: int


@dataclass(frozen=True)
class RunArtifacts:
    workbook: Path
    detail_csv: Path
    summary_site_csv: Path
    summary_sku_csv: Path
    summary_total_csv: Path
    qa_summary_csv: Path

    def as_dict(self) -> dict[str, str]:
        return {
            "workbook": str(self.workbook),
            "detail_csv": str(self.detail_csv),
            "summary_site_csv": str(self.summary_site_csv),
            "summary_sku_csv": str(self.summary_sku_csv),
            "summary_total_csv": str(self.summary_total_csv),
            "qa_summary_csv": str(self.qa_summary_csv),
        }


@dataclass(frozen=True)
class FrozenV5RunRequest:
    orders_path: Path
    daily_stock_path: Path
    product_path: Path
    site_mapping_path: Path
    output_dir: Path
    output_workbook: Path
    artifacts: RunArtifacts
    eval_year: int
    eval_month: int
    baseline_recent_months: int = 6
    baseline_fallback_months: int = 6

    @property
    def period(self) -> str:
        return f"{self.eval_year}-{self.eval_month:02d}"

    def build_input_paths(self, input_paths_type: type[Any]) -> Any:
        return input_paths_type(
            orders_path=str(self.orders_path),
            daily_stock_path=str(self.daily_stock_path),
            site_mapping_path=str(self.site_mapping_path),
            product_path=str(self.product_path),
        )

    def build_model_config(self, model_config_type: type[Any]) -> Any:
        return model_config_type(
            eval_year=self.eval_year,
            eval_month=self.eval_month,
            baseline_recent_months=self.baseline_recent_months,
            baseline_fallback_months=self.baseline_fallback_months,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "orders_path": str(self.orders_path),
            "daily_stock_path": str(self.daily_stock_path),
            "product_path": str(self.product_path),
            "site_mapping_path": str(self.site_mapping_path),
            "output_dir": str(self.output_dir),
            "output_workbook": str(self.output_workbook),
            "artifacts": self.artifacts.as_dict(),
            "eval_year": self.eval_year,
            "eval_month": self.eval_month,
            "baseline_recent_months": self.baseline_recent_months,
            "baseline_fallback_months": self.baseline_fallback_months,
        }


@dataclass(frozen=True)
class BundledSiteMappingStatus:
    is_ready: bool
    status_label: str
    path: str
    total_rows: int = 0
    active_mapping_rows: int = 0
    site_count: int = 0
    virtual_site_count: int = 0
    sample_virtual_sites: tuple[str, ...] = ()
    details: tuple[str, ...] = ()


def locate_bundled_site_mapping() -> Path | None:
    for candidate in SITE_MAPPING_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def build_run_blueprint(workspace_root: str | Path, eval_year: int, eval_month: int) -> RunBlueprint:
    workspace = Path(workspace_root).resolve()
    period = f"{eval_year}-{eval_month:02d}"
    output_dir = workspace / "outputs"
    base_name = output_dir / f"OOS_Opportunity_Lost_{period}_V5"
    output_workbook = output_dir / f"OOS_Opportunity_Lost_{period}_V5.xlsx"
    return RunBlueprint(
        workspace_root=workspace,
        input_dir=workspace / "inputs",
        output_dir=output_dir,
        output_workbook=output_workbook,
        output_detail_csv=Path(f"{base_name}_detail.csv"),
        output_summary_site_csv=Path(f"{base_name}_summary_site.csv"),
        output_summary_sku_csv=Path(f"{base_name}_summary_sku.csv"),
        output_summary_total_csv=Path(f"{base_name}_summary_total.csv"),
        output_qa_summary_csv=Path(f"{base_name}_qa_summary.csv"),
        bundled_site_mapping=locate_bundled_site_mapping(),
        eval_year=eval_year,
        eval_month=eval_month,
    )


def build_run_artifacts(output_dir: str | Path, eval_year: int, eval_month: int) -> RunArtifacts:
    resolved_output_dir = Path(output_dir).resolve()
    period = f"{eval_year}-{eval_month:02d}"
    base_name = resolved_output_dir / f"OOS_Opportunity_Lost_{period}_V5"
    return RunArtifacts(
        workbook=resolved_output_dir / f"OOS_Opportunity_Lost_{period}_V5.xlsx",
        detail_csv=Path(f"{base_name}_detail.csv"),
        summary_site_csv=Path(f"{base_name}_summary_site.csv"),
        summary_sku_csv=Path(f"{base_name}_summary_sku.csv"),
        summary_total_csv=Path(f"{base_name}_summary_total.csv"),
        qa_summary_csv=Path(f"{base_name}_qa_summary.csv"),
    )


def build_frozen_v5_run_request(
    *,
    workspace_root: str | Path,
    orders_path: str | Path,
    daily_stock_path: str | Path,
    product_path: str | Path,
    eval_year: int,
    eval_month: int,
    baseline_recent_months: int = 6,
    baseline_fallback_months: int = 6,
) -> FrozenV5RunRequest:
    blueprint = build_run_blueprint(workspace_root, eval_year, eval_month)
    site_mapping_path = blueprint.bundled_site_mapping
    if site_mapping_path is None:
        msg = "Bundled site mapping not found for frozen V5 execution."
        raise FileNotFoundError(msg)

    resolved_orders = Path(orders_path).expanduser().resolve()
    resolved_daily_stock = Path(daily_stock_path).expanduser().resolve()
    resolved_product = Path(product_path).expanduser().resolve()
    for label, path in (
        ("orders", resolved_orders),
        ("daily_stock", resolved_daily_stock),
        ("product", resolved_product),
        ("site_mapping", site_mapping_path),
    ):
        if not path.exists() or not path.is_file():
            msg = f"Frozen V5 run input '{label}' not found: {path}"
            raise FileNotFoundError(msg)

    artifacts = build_run_artifacts(blueprint.output_dir, eval_year, eval_month)
    return FrozenV5RunRequest(
        orders_path=resolved_orders,
        daily_stock_path=resolved_daily_stock,
        product_path=resolved_product,
        site_mapping_path=site_mapping_path.resolve(),
        output_dir=blueprint.output_dir,
        output_workbook=artifacts.workbook,
        artifacts=artifacts,
        eval_year=eval_year,
        eval_month=eval_month,
        baseline_recent_months=baseline_recent_months,
        baseline_fallback_months=baseline_fallback_months,
    )


def get_boundary_overview() -> V5BoundaryOverview:
    site_mapping = locate_bundled_site_mapping()
    return V5BoundaryOverview(
        pipeline_name="Frozen V5 daily OOS opportunity pipeline",
        integration_mode="App code stages files, then calls existing V5 Python modules directly.",
        site_mapping_path=str(site_mapping) if site_mapping else "Bundled site mapping not found",
        staged_inputs=("orders", "daily_stock", "product", "site_mapping"),
        staged_outputs=("xlsx_workbook", "detail_csv", "summary_csv", "qa_csv"),
        modules=(
            BoundaryModule(
                import_path="v5_daily_oos_opportunity.data_loader_v5",
                responsibility="Normalizes staged order, stock, product, and site-mapping files.",
            ),
            BoundaryModule(
                import_path="v5_daily_oos_opportunity.analyzer_v5",
                responsibility="Runs the frozen V5 daily OOS opportunity calculation.",
            ),
            BoundaryModule(
                import_path="v5_daily_oos_opportunity.reporter_v5",
                responsibility="Generates workbook and CSV outputs for the active run.",
            ),
        ),
        notes=(
            "Keep the Streamlit runtime as the operator shell, not a second analytics engine.",
            "Later phases should construct InputPaths and ModelConfig through this boundary instead of importing the CLI entrypoint.",
            "Site mapping remains bundled configuration in the MVP and is resolved before user uploads are processed.",
        ),
    )


@lru_cache(maxsize=1)
def get_bundled_site_mapping_status() -> BundledSiteMappingStatus:
    site_mapping = locate_bundled_site_mapping()
    if site_mapping is None:
        return BundledSiteMappingStatus(
            is_ready=False,
            status_label="Bundled site mapping unavailable",
            path="Bundled site mapping not found",
            details=("The bundled site-mapping file could not be resolved from the frozen V5 assets.",),
        )

    try:
        frame = pd.read_csv(site_mapping)
    except Exception as exc:
        return BundledSiteMappingStatus(
            is_ready=False,
            status_label="Bundled site mapping unreadable",
            path=str(site_mapping),
            details=(f"The bundled site-mapping file could not be read: {exc}",),
        )

    required_columns = ("Virtual Location", "Site", "Active")
    missing_columns = tuple(column for column in required_columns if column not in frame.columns)
    if missing_columns:
        return BundledSiteMappingStatus(
            is_ready=False,
            status_label="Bundled site mapping missing required columns",
            path=str(site_mapping),
            details=(f"Missing required columns: {', '.join(missing_columns)}",),
        )

    active_rows = frame.loc[frame["Active"].fillna("").astype(str).str.strip().ne("")]
    site_codes = tuple(sorted(set(active_rows["Site"].dropna().astype(str).str.strip())))
    virtual_sites = tuple(
        sorted(set(active_rows["Virtual Location"].dropna().astype(str).str.strip()))
    )

    return BundledSiteMappingStatus(
        is_ready=True,
        status_label="Bundled site mapping active",
        path=str(site_mapping),
        total_rows=int(len(frame.index)),
        active_mapping_rows=int(len(active_rows.index)),
        site_count=len(site_codes),
        virtual_site_count=len(virtual_sites),
        sample_virtual_sites=virtual_sites[:5],
        details=(
            "This mapping is system-owned and read-only for the MVP upload workflow.",
            "Operators do not need to upload a separate site-map file in this step.",
        ),
    )


def load_frozen_v5_symbols() -> dict[str, Any]:
    _ensure_repo_root_on_syspath()
    loader_module = import_module("v5_daily_oos_opportunity.data_loader_v5")
    analyzer_module = import_module("v5_daily_oos_opportunity.analyzer_v5")
    reporter_module = import_module("v5_daily_oos_opportunity.reporter_v5")

    return {
        "InputPaths": getattr(loader_module, "InputPaths"),
        "DataLoaderV5": getattr(loader_module, "DataLoaderV5"),
        "ModelConfig": getattr(analyzer_module, "ModelConfig"),
        "DailyOOSOpportunityV5": getattr(analyzer_module, "DailyOOSOpportunityV5"),
        "ReporterV5": getattr(reporter_module, "ReporterV5"),
    }


def _ensure_repo_root_on_syspath() -> None:
    repo_root_text = str(REPO_ROOT)
    if repo_root_text not in sys.path:
        sys.path.insert(0, repo_root_text)
