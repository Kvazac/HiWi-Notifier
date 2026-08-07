from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import Listing


@dataclass(frozen=True)
class MatchResult:
    matched: bool
    score: int
    reasons: tuple[str, ...]


def _normalized_terms(values: list[Any] | None) -> list[str]:
    return [str(value).casefold().strip() for value in (values or []) if str(value).strip()]


def match_listing(listing: Listing, config: dict[str, Any]) -> MatchResult:
    text = listing.searchable_text.casefold()
    title = listing.title.casefold()

    include_any = _normalized_terms(config.get("include_any"))
    include_all = _normalized_terms(config.get("include_all"))
    exclude_any = _normalized_terms(config.get("exclude_any"))
    title_include_any = _normalized_terms(config.get("title_include_any"))
    regex_any = [str(value) for value in config.get("regex_any", []) if str(value).strip()]

    reasons: list[str] = []

    excluded = [term for term in exclude_any if term in text]
    if excluded:
        return MatchResult(False, 0, tuple(f"excluded: {term}" for term in excluded))

    if include_any:
        hits = [term for term in include_any if term in text]
        if not hits:
            return MatchResult(False, 0, ("no include_any term matched",))
        reasons.extend(f"keyword: {term}" for term in hits)

    missing_required = [term for term in include_all if term not in text]
    if missing_required:
        return MatchResult(False, 0, tuple(f"missing: {term}" for term in missing_required))
    reasons.extend(f"required: {term}" for term in include_all)

    if title_include_any:
        title_hits = [term for term in title_include_any if term in title]
        if not title_hits:
            return MatchResult(False, 0, ("no title_include_any term matched",))
        reasons.extend(f"title: {term}" for term in title_hits)

    if regex_any:
        regex_hits: list[str] = []
        for pattern in regex_any:
            try:
                if re.search(pattern, listing.searchable_text, flags=re.IGNORECASE):
                    regex_hits.append(pattern)
            except re.error as exc:
                raise ValueError(f"Invalid regex {pattern!r}: {exc}") from exc
        if not regex_hits:
            return MatchResult(False, 0, ("no regex matched",))
        reasons.extend(f"regex: {pattern}" for pattern in regex_hits)

    weighted_terms = config.get("weighted_terms", {}) or {}
    score = 0
    for raw_term, raw_weight in weighted_terms.items():
        term = str(raw_term).casefold().strip()
        weight = int(raw_weight)
        if term and term in text:
            score += weight
            reasons.append(f"{term}: +{weight}")

    minimum_score = int(config.get("minimum_score", 0))
    if score < minimum_score:
        return MatchResult(False, score, (f"score {score} below {minimum_score}",))

    return MatchResult(True, score, tuple(reasons))
