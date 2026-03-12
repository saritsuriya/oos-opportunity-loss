"""CLI wrapper for scheduled cleanup of stale Streamlit workspaces."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from streamlit_app.runtime.cleanup import cleanup_stale_workspaces
from streamlit_app.runtime.temp_workspace import get_workspace_base_dir


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove stale session workspaces created by the Streamlit app."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=None,
        help="Override the managed workspace root. Defaults to the app runtime location.",
    )
    parser.add_argument(
        "--max-age-hours",
        type=float,
        default=24.0,
        help="Remove workspaces older than this age in hours.",
    )
    parser.add_argument(
        "--now-iso",
        default=None,
        help="Optional ISO timestamp for deterministic runs and tests.",
    )
    return parser.parse_args(argv)


def parse_reference_time(now_iso: str | None) -> datetime | None:
    if now_iso is None:
        return None

    normalized = now_iso.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.max_age_hours <= 0:
        print("--max-age-hours must be greater than zero", file=sys.stderr)
        return 2

    base_dir = get_workspace_base_dir(args.base_dir)
    removed = cleanup_stale_workspaces(
        timedelta(hours=args.max_age_hours),
        base_dir=base_dir,
        now=parse_reference_time(args.now_iso),
    )

    print(f"Workspace root: {base_dir}")
    print(f"Max age hours: {args.max_age_hours:g}")
    if removed:
        for path in removed:
            print(f"Removed: {path}")
    else:
        print("Removed: none")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
