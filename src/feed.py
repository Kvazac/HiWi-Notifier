from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import requests

from .models import Listing


class FeedError(RuntimeError):
    pass


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError, OverflowError):
        return None


def _stable_id(entry: Any) -> str:
    raw = (
        entry.get("id")
        or entry.get("guid")
        or entry.get("link")
        or f"{entry.get('title', '')}|{entry.get('published', '')}"
    )
    return hashlib.sha256(str(raw).encode("utf-8")).hexdigest()


def fetch_listings(url: str, timeout: int = 30) -> list[Listing]:
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={"User-Agent": "tum-hiwi-discord-notifier/1.0"},
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FeedError(f"Could not download RSS feed: {exc}") from exc

    parsed = feedparser.parse(response.content)
    if parsed.bozo and not parsed.entries:
        raise FeedError(f"Could not parse RSS feed: {parsed.bozo_exception}")

    listings: list[Listing] = []
    for entry in parsed.entries:
        listings.append(
            Listing(
                listing_id=_stable_id(entry),
                title=str(entry.get("title", "")).strip(),
                link=str(entry.get("link", "")).strip(),
                description=str(
                    entry.get("summary")
                    or entry.get("description")
                    or ""
                ).strip(),
                published=_parse_date(
                    entry.get("published") or entry.get("updated")
                ),
                author=str(entry.get("author", "")).strip(),
            )
        )
    return listings
