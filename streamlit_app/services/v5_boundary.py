"""Reusable boundary between the Streamlit app and the frozen V5 pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

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
