from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"initialized": False, "seen": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read state file {path}: {exc}") from exc

    data.setdefault("initialized", False)
    data.setdefault("seen", {})
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def mark_seen(state: dict[str, Any], listing_id: str) -> None:
    state["seen"][listing_id] = datetime.now(timezone.utc).isoformat()


def prune_state(state: dict[str, Any], retention_days: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    retained: dict[str, str] = {}

    for listing_id, timestamp in state.get("seen", {}).items():
        try:
            seen_at = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            continue
        if seen_at >= cutoff:
            retained[listing_id] = timestamp

    state["seen"] = retained
