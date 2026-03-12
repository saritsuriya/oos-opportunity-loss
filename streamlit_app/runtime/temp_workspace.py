"""Temporary workspace primitives for stateless Streamlit sessions."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE_ROOT_ENV_VAR = "OOS_WORKSPACE_BASE_DIR"
WORKSPACE_NAMESPACE = "oos-opportunity-lost"
INPUTS_DIRNAME = "inputs"
OUTPUTS_DIRNAME = "outputs"
METADATA_FILENAME = ".workspace.json"

_INVALID_SESSION_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class SessionWorkspace:
    session_id: str
    root: Path
    input_dir: Path
    output_dir: Path
    metadata_path: Path

    def as_session_state(self) -> dict[str, str]:
        return {
            "workspace_root": str(self.root),
            "workspace_input_dir": str(self.input_dir),
            "workspace_output_dir": str(self.output_dir),
        }


def sanitize_session_id(session_id: str) -> str:
    normalized = _INVALID_SESSION_CHARS.sub("-", session_id.strip()).strip("-_.").lower()
    if not normalized:
        msg = "session_id must contain at least one safe filename character"
        raise ValueError(msg)
    return normalized


def get_workspace_base_dir(base_dir: str | Path | None = None) -> Path:
    if base_dir is not None:
        root = Path(base_dir)
    else:
        env_root = os.getenv(WORKSPACE_ROOT_ENV_VAR)
        if env_root:
            root = Path(env_root)
        else:
            root = Path(tempfile.gettempdir()) / WORKSPACE_NAMESPACE / "streamlit-sessions"
    root = root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def build_session_workspace_root(session_id: str, base_dir: str | Path | None = None) -> Path:
    return get_workspace_base_dir(base_dir) / f"session-{sanitize_session_id(session_id)}"


def ensure_session_workspace(session_id: str, base_dir: str | Path | None = None) -> SessionWorkspace:
    root = build_session_workspace_root(session_id, base_dir=base_dir)
    input_dir = root / INPUTS_DIRNAME
    output_dir = root / OUTPUTS_DIRNAME
    metadata_path = root / METADATA_FILENAME

    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    created_at = now
    if metadata_path.exists():
        try:
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}
        created_at = str(existing.get("created_at", now))

    metadata_path.write_text(
        json.dumps(
            {
                "session_id": session_id,
                "workspace_root": str(root),
                "input_dir": INPUTS_DIRNAME,
                "output_dir": OUTPUTS_DIRNAME,
                "created_at": created_at,
                "last_accessed_at": now,
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return SessionWorkspace(
        session_id=session_id,
        root=root,
        input_dir=input_dir,
        output_dir=output_dir,
        metadata_path=metadata_path,
    )


def iter_session_workspace_roots(base_dir: str | Path | None = None) -> tuple[Path, ...]:
    root = get_workspace_base_dir(base_dir)
    return tuple(sorted(path for path in root.iterdir() if path.is_dir() and path.name.startswith("session-")))


def latest_workspace_mtime(workspace_root: str | Path) -> float:
    root = Path(workspace_root)
    latest_mtime = root.stat().st_mtime
    for child in root.rglob("*"):
        latest_mtime = max(latest_mtime, child.stat().st_mtime)
    return latest_mtime
