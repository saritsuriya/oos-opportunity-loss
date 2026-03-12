"""Cleanup helpers for temporary session workspaces."""

from __future__ import annotations

import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    from streamlit_app.runtime.temp_workspace import (
        build_session_workspace_root,
        iter_session_workspace_roots,
        latest_workspace_mtime,
    )
except ModuleNotFoundError:
    from runtime.temp_workspace import (
        build_session_workspace_root,
        iter_session_workspace_roots,
        latest_workspace_mtime,
    )


def cleanup_session_workspace(session_id: str, base_dir: str | Path | None = None) -> bool:
    workspace_root = build_session_workspace_root(session_id, base_dir=base_dir)
    if not workspace_root.exists():
        return False

    shutil.rmtree(workspace_root)
    return True


def cleanup_stale_workspaces(
    max_age: timedelta | int | float,
    *,
    base_dir: str | Path | None = None,
    now: datetime | None = None,
) -> tuple[Path, ...]:
    if isinstance(max_age, timedelta):
        max_age_seconds = max_age.total_seconds()
    else:
        max_age_seconds = float(max_age)

    reference_time = now or datetime.now(timezone.utc)
    cutoff_timestamp = reference_time.timestamp() - max_age_seconds
    removed: list[Path] = []

    for workspace_root in iter_session_workspace_roots(base_dir):
        if latest_workspace_mtime(workspace_root) > cutoff_timestamp:
            continue

        shutil.rmtree(workspace_root)
        removed.append(workspace_root)

    return tuple(removed)
