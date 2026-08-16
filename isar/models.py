from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class Job:
    job_id: str
    title: str
    location: str
    absolute_url: str
    updated_at: str | None
    content: str

    @classmethod
    def from_greenhouse(cls, raw: dict[str, Any]) -> "Job":
        loc_raw = raw.get("location") or {}
        location = str(loc_raw.get("name") or "") if isinstance(loc_raw, dict) else str(loc_raw or "")
        return cls(
            job_id=str(raw.get("id") or ""),
            title=str(raw.get("title") or "").strip(),
            location=location.strip(),
            absolute_url=str(raw.get("absolute_url") or "").strip(),
            updated_at=str(raw.get("updated_at")) if raw.get("updated_at") is not None else None,
            content=str(raw.get("content") or ""),
        )

    @property
    def stable_id(self) -> str:
        return self.job_id or self.absolute_url
