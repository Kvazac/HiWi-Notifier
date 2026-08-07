from __future__ import annotations

import html
import re
from typing import Any

import requests

from .matcher import MatchResult
from .models import Listing


class DiscordError(RuntimeError):
    pass


_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")


def _plain_text(value: str) -> str:
    without_tags = _TAG_RE.sub(" ", value)
    return _SPACE_RE.sub(" ", html.unescape(without_tags)).strip()


def send_listing(
    webhook_url: str,
    listing: Listing,
    result: MatchResult,
    config: dict[str, Any],
) -> None:
    max_chars = int(config.get("max_description_characters", 900))
    description = _plain_text(listing.description)
    if len(description) > max_chars:
        description = description[: max_chars - 1].rstrip() + "…"

    published = (
        listing.published.strftime("%d %b %Y, %H:%M %Z")
        if listing.published
        else "Unknown"
    )
    reasons = ", ".join(result.reasons[:8]) or "All configured filters passed"

    payload = {
        "username": str(config.get("username", "TUM Job Watcher")),
        "content": str(config.get("mention", "")).strip() or None,
        "embeds": [
            {
                "title": listing.title[:256] or "Untitled TUM listing",
                "url": listing.link,
                "description": description[:4096] or "No description supplied.",
                "fields": [
                    {"name": "Published", "value": published, "inline": True},
                    {"name": "Score", "value": str(result.score), "inline": True},
                    {"name": "Matched because", "value": reasons[:1024], "inline": False},
                ],
                "footer": {"text": "TUM Student Job RSS"},
            }
        ],
        "allowed_mentions": {"parse": []},
    }
    if payload["content"] is None:
        payload.pop("content")

    try:
        response = requests.post(
            webhook_url,
            params={"wait": "true"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DiscordError(f"Discord notification failed: {exc}") from exc


def send_test(webhook_url: str, username: str) -> None:
    payload = {
        "username": username,
        "content": "✅ TUM job notifier test succeeded.",
        "allowed_mentions": {"parse": []},
    }
    try:
        response = requests.post(
            webhook_url,
            params={"wait": "true"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DiscordError(f"Discord test notification failed: {exc}") from exc
