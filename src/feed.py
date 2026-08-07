from __future__ import annotations

import hashlib
import html
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests
from lxml import etree

from .models import Listing


class FeedError(RuntimeError):
    pass


_INVALID_XML_CHARS = re.compile(
    "["
    "\x00-\x08"
    "\x0B\x0C"
    "\x0E-\x1F"
    "\x7F-\x84"
    "\x86-\x9F"
    "]"
)


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


def _stable_id(guid: str, link: str, title: str, published: str) -> str:
    raw = guid or link or f"{title}|{published}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _element_text(element: etree._Element | None) -> str:
    if element is None:
        return ""

    return "".join(element.itertext()).strip()


def _child_text(item: etree._Element, name: str) -> str:
    for child in item:
        local_name = etree.QName(child).localname

        if local_name == name:
            return _element_text(child)

    return ""


def _clean_payload(payload: bytes) -> bytes:
    text = payload.decode("utf-8", errors="replace")

    # Remove characters that XML 1.0 does not permit.
    text = _INVALID_XML_CHARS.sub("", text)

    return text.encode("utf-8")


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

    parser = etree.XMLParser(
        recover=True,
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
    )

    try:
        root = etree.fromstring(
            _clean_payload(response.content),
            parser=parser,
        )
    except etree.XMLSyntaxError as exc:
        raise FeedError(f"Could not recover RSS feed: {exc}") from exc

    if root is None:
        raise FeedError("RSS parser returned no document root")

    items = root.xpath("//*[local-name()='item']")

    if not items:
        errors = "; ".join(
            str(error)
            for error in parser.error_log[:5]
        )
        raise FeedError(
            f"Recovered RSS document contained no items. Parser errors: {errors}"
        )

    listings: list[Listing] = []

    for item in items:
        title = html.unescape(_child_text(item, "title"))
        link = _child_text(item, "link")
        description = html.unescape(_child_text(item, "description"))
        published_raw = _child_text(item, "pubDate")
        guid = _child_text(item, "guid")
        author = _child_text(item, "author")

        listings.append(
            Listing(
                listing_id=_stable_id(
                    guid=guid,
                    link=link,
                    title=title,
                    published=published_raw,
                ),
                title=title,
                link=link,
                description=description,
                published=_parse_date(published_raw),
                author=author,
            )
        )

    return listings
