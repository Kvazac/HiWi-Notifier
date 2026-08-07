from __future__ import annotations

import hashlib
import html.entities
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser
import requests

from .models import Listing


class FeedError(RuntimeError):
    pass


# XML only recognizes these five named entities.
_XML_ENTITIES = {"amp", "lt", "gt", "apos", "quot"}
_NAMED_ENTITY_PATTERN = re.compile(r"&([A-Za-z][A-Za-z0-9]+);")


def _sanitize_xml_entities(payload: bytes) -> str:
    """
    Convert HTML-only named entities, such as &nbsp;, into Unicode.

    Unknown entities are escaped so that they remain visible text rather
    than causing the entire RSS document to fail XML parsing.
    """
    text = payload.decode("utf-8", errors="replace")

    def replace_entity(match: re.Match[str]) -> str:
        name = match.group(1)

        if name in _XML_ENTITIES:
            return match.group(0)

        replacement = (
            html.entities.html5.get(f"{name};")
            or html.entities.html5.get(name)
        )

        if replacement is not None:
            return replacement

        return f"&amp;{name};"

    return _NAMED_ENTITY_PATTERN.sub(replace_entity, text)


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
            headers={
                "User-Agent": "tum-hiwi-discord-notifier/1.0",
                "Accept": "application/rss+xml, application/xml, text/xml",
            },
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise FeedError(f"Could not download RSS feed: {exc}") from exc

    sanitized_feed = _sanitize_xml_entities(response.content)
    parsed = feedparser.parse(sanitized_feed)

    if not parsed.entries:
        parser_error = getattr(
            parsed,
            "bozo_exception",
            "feed contained no entries",
        )
        raise FeedError(f"Could not parse RSS feed: {parser_error}")

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
                    entry.get("published")
                    or entry.get("updated")
                ),
                author=str(entry.get("author", "")).strip(),
            )
        )

    return listings
