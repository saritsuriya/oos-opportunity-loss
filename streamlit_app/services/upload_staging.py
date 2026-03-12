"""Run-scoped upload staging helpers for session-local input files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping

UPLOAD_REGISTRY_KEY = "staged_input_registry"


@dataclass(frozen=True)
class UploadSlot:
    key: str
    label: str
    directory_name: str
    accepted_extensions: tuple[str, ...]
    default_extension: str


_UPLOAD_SLOTS: tuple[UploadSlot, ...] = (
    UploadSlot(
        key="sales",
        label="Sales",
        directory_name="sales",
        accepted_extensions=(".xlsx", ".xlsm", ".xls", ".tsv", ".txt"),
        default_extension=".xlsx",
    ),
    UploadSlot(
        key="stock",
        label="Stock",
        directory_name="stock",
        accepted_extensions=(".csv",),
        default_extension=".csv",
    ),
    UploadSlot(
        key="sku_live",
        label="SKU / Live",
        directory_name="sku-live",
        accepted_extensions=(".csv",),
        default_extension=".csv",
    ),
)


def get_upload_slots() -> tuple[UploadSlot, ...]:
    return _UPLOAD_SLOTS


def get_upload_slot(slot_key: str) -> UploadSlot:
    for slot in get_upload_slots():
        if slot.key == slot_key:
            return slot
    msg = f"Unknown upload slot: {slot_key}"
    raise KeyError(msg)


def build_slot_directory(workspace_input_dir: str | Path, slot_key: str) -> Path:
    workspace_root = _resolve_workspace_input_dir(workspace_input_dir)
    slot = get_upload_slot(slot_key)
    slot_dir = (workspace_root / slot.directory_name).resolve()
    if not slot_dir.is_relative_to(workspace_root):
        msg = f"Upload slot directory escapes workspace input dir: {slot_dir}"
        raise ValueError(msg)
    slot_dir.mkdir(parents=True, exist_ok=True)
    return slot_dir


def build_staged_upload_path(
    workspace_input_dir: str | Path, slot_key: str, source_name: str
) -> Path:
    slot = get_upload_slot(slot_key)
    suffix = Path(source_name).suffix.lower() or slot.default_extension
    return build_slot_directory(workspace_input_dir, slot_key) / f"current{suffix}"


def create_upload_registry(workspace_input_dir: str | Path) -> dict[str, dict[str, object]]:
    registry: dict[str, dict[str, object]] = {}
    for slot in get_upload_slots():
        slot_dir = build_slot_directory(workspace_input_dir, slot.key)
        registry[slot.key] = {
            "slot_key": slot.key,
            "label": slot.label,
            "accepted_extensions": list(slot.accepted_extensions),
            "slot_dir": str(slot_dir),
            "current_file": None,
        }
    return registry


def ensure_upload_registry(
    state: MutableMapping[str, Any],
) -> dict[str, dict[str, object]]:
    workspace_input_dir = state.get("workspace_input_dir")
    if not workspace_input_dir:
        msg = "workspace_input_dir must be set before upload staging is initialized"
        raise KeyError(msg)

    registry = create_upload_registry(str(workspace_input_dir))
    existing = state.get(UPLOAD_REGISTRY_KEY)
    if isinstance(existing, Mapping):
        for slot_key, slot_state in registry.items():
            existing_slot = existing.get(slot_key)
            if not isinstance(existing_slot, Mapping):
                continue
            current_file = existing_slot.get("current_file")
            if isinstance(current_file, Mapping):
                slot_state["current_file"] = dict(current_file)

    state[UPLOAD_REGISTRY_KEY] = registry
    return registry


def _resolve_workspace_input_dir(workspace_input_dir: str | Path) -> Path:
    workspace_root = Path(workspace_input_dir).expanduser().resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    return workspace_root
