from __future__ import annotations
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"initialized": False, "seen": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("initialized", False)
    data.setdefault("seen", {})
    return data

def mark_seen(state: dict[str, Any], listing_id: str) -> None:
    state["seen"][listing_id] = datetime.now(timezone.utc).isoformat()

def prune(state: dict[str, Any], retention_days: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    kept = {}
    for listing_id, timestamp in state.get("seen", {}).items():
        try:
            seen_at = datetime.fromisoformat(timestamp)
        except (TypeError, ValueError):
            continue
        if seen_at >= cutoff:
            kept[listing_id] = timestamp
    state["seen"] = kept

def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)
