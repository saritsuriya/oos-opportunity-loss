"""Reusable boundary between the Streamlit app and the frozen V5 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from pathlib import Path
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
    bundled_site_mapping: Path | None
    eval_year: int
    eval_month: int


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
    return RunBlueprint(
        workspace_root=workspace,
        input_dir=workspace / "inputs",
        output_dir=workspace / "outputs",
        output_workbook=workspace / "outputs" / f"OOS_Opportunity_Lost_{period}_V5.xlsx",
        bundled_site_mapping=locate_bundled_site_mapping(),
        eval_year=eval_year,
        eval_month=eval_month,
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
