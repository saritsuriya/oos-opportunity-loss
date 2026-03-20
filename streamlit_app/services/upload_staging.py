"""Run-scoped upload staging helpers for session-local input files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, MutableMapping
from uuid import uuid4

from channel_profiles import get_required_upload_slots

UPLOAD_REGISTRY_KEY = "staged_input_registry"


@dataclass(frozen=True)
class UploadSlot:
    key: str
    label: str
    directory_name: str
    accepted_extensions: tuple[str, ...]
    default_extension: str


@dataclass(frozen=True)
class StagedInputFile:
    slot_key: str
    source_name: str
    size_bytes: int
    staged_path: str

    def as_dict(self) -> dict[str, object]:
        return {
            "slot_key": self.slot_key,
            "source_name": self.source_name,
            "size_bytes": self.size_bytes,
            "staged_path": self.staged_path,
        }


_UPLOAD_SLOTS: tuple[UploadSlot, ...] = (
    UploadSlot(
        key="sales",
        label="Sales",
        directory_name="sales",
        accepted_extensions=(".xlsx", ".xlsm", ".xls", ".csv", ".tsv", ".txt"),
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
        accepted_extensions=(".xlsx", ".xlsm", ".xls", ".csv"),
        default_extension=".csv",
    ),
    UploadSlot(
        key="site_mapping",
        label="Site Mapping",
        directory_name="site-mapping",
        accepted_extensions=(".xlsx", ".xlsm", ".xls", ".csv"),
        default_extension=".xlsx",
    ),
)


def get_upload_slots() -> tuple[UploadSlot, ...]:
    return _UPLOAD_SLOTS


def get_active_upload_slots(channel_key: str) -> tuple[UploadSlot, ...]:
    required_keys = set(get_required_upload_slots(channel_key))
    return tuple(slot for slot in get_upload_slots() if slot.key in required_keys)


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


def stage_uploaded_file(
    uploaded_file: Any,
    slot_key: str,
    workspace_input_dir: str | Path,
    registry: MutableMapping[str, dict[str, object]] | None = None,
) -> dict[str, object]:
    source_name = _get_uploaded_file_name(uploaded_file)
    payload = _read_uploaded_bytes(uploaded_file)
    staged_path = build_staged_upload_path(workspace_input_dir, slot_key, source_name)
    slot_dir = staged_path.parent
    temp_path = slot_dir / f".incoming-{uuid4().hex}{staged_path.suffix}"

    temp_path.write_bytes(payload)
    for existing_path in slot_dir.glob("current*"):
        if existing_path != temp_path and existing_path.is_file():
            existing_path.unlink()
    temp_path.replace(staged_path)

    metadata = StagedInputFile(
        slot_key=slot_key,
        source_name=source_name,
        size_bytes=len(payload),
        staged_path=str(staged_path),
    ).as_dict()
    if registry is not None:
        registry[slot_key]["current_file"] = metadata
    return metadata


def _resolve_workspace_input_dir(workspace_input_dir: str | Path) -> Path:
    workspace_root = Path(workspace_input_dir).expanduser().resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    return workspace_root


def _get_uploaded_file_name(uploaded_file: Any) -> str:
    source_name = getattr(uploaded_file, "name", "")
    if not source_name:
        msg = "uploaded_file must expose a source filename via .name"
        raise TypeError(msg)
    return str(source_name)


def _read_uploaded_bytes(uploaded_file: Any) -> bytes:
    if hasattr(uploaded_file, "getbuffer"):
        return bytes(uploaded_file.getbuffer())
    if hasattr(uploaded_file, "getvalue"):
        return bytes(uploaded_file.getvalue())
    if hasattr(uploaded_file, "read"):
        payload = uploaded_file.read()
        if hasattr(uploaded_file, "seek"):
            uploaded_file.seek(0)
        return bytes(payload)
    msg = "uploaded_file must provide getbuffer(), getvalue(), or read()"
    raise TypeError(msg)
