from __future__ import annotations
import html, re
from dataclasses import dataclass
from typing import Any
from .models import Job

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

@dataclass(frozen=True)
class MatchResult:
    matched: bool
    reasons: tuple[str, ...]

def _plain_text(value: str) -> str:
    return _SPACE_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", value))).strip()

def _norm(value: str) -> str:
    return _SPACE_RE.sub(" ", value.casefold()).strip()

def match_job(job: Job, config: dict[str, Any]) -> MatchResult:
    title = _norm(job.title)
    body = _norm(_plain_text(job.content))
    location = _norm(job.location)
    searchable = f"{title}\n{body}\n{location}"

    title_terms = [_norm(str(x)) for x in (config.get("title_include_any") or []) if str(x).strip()]
    hits = [term for term in title_terms if term in title]
    if title_terms and not hits:
        return MatchResult(False, ("title did not match student/intern terms",))

    excluded = [
        term for term in [_norm(str(x)) for x in (config.get("exclude_any") or []) if str(x).strip()]
        if term in searchable
    ]
    if excluded:
        return MatchResult(False, tuple(f"excluded: {term}" for term in excluded))

    location_terms = [_norm(str(x)) for x in (config.get("locations") or []) if str(x).strip()]
    location_hits = [term for term in location_terms if term in location]
    if location_terms and not location_hits:
        return MatchResult(False, ("location not selected",))

    reasons = [*(f"title: {term}" for term in hits), *(f"location: {term}" for term in location_hits)]
    return MatchResult(True, tuple(reasons or ["student/intern role"]))
