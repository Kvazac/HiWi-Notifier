from __future__ import annotations

from typing import Any

import requests

from .matcher import MatchResult
from .models import HousingListing


class DiscordError(RuntimeError):
    pass


def _money(value: float | None) -> str:
    return "Unknown" if value is None else f"€{float(value):,.0f}"


def _size(value: float | None) -> str:
    return "Unknown" if value is None else f"{float(value):g} m²"


def _post(webhook_url: str, payload: dict[str, Any], error_label: str) -> None:
    try:
        response = requests.post(
            webhook_url,
            params={"wait": "true"},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DiscordError(f"{error_label}: {exc}") from exc


def send_listing(
    webhook_url: str,
    listing: HousingListing,
    result: MatchResult,
    config: dict[str, Any],
) -> None:
    title = listing.type.replace("_", " ").title() or "TUM Living listing"
    district = listing.district.replace("_", " ").title() if listing.district else ""
    location = ", ".join(part for part in [listing.city, district] if part)

    payload = {
        "username": str(config.get("username", "TUM Living Watcher")),
        "embeds": [
            {
                "title": f"🏠 {title}",
                "url": "https://living.tum.de/listings?viewMode=list",
                "description": (
                    f"New matching TUM Living listing "
                    f"(ID {listing.listing_id})."
                ),
                "fields": [
                    {
                        "name": "Rent",
                        "value": _money(listing.total_rent),
                        "inline": True,
                    },
                    {
                        "name": "Size",
                        "value": _size(listing.square_meter),
                        "inline": True,
                    },
                    {
                        "name": "Available from",
                        "value": listing.available_from or "Unknown",
                        "inline": True,
                    },
                    {
                        "name": "Location",
                        "value": location or "Unknown",
                        "inline": False,
                    },
                    {
                        "name": "Matched because",
                        "value": ", ".join(result.reasons)[:1024],
                        "inline": False,
                    },
                ],
                "footer": {"text": "TUM Living"},
            }
        ],
        "allowed_mentions": {"parse": []},
    }

    _post(webhook_url, payload, "Discord housing notification failed")


def send_test(
    webhook_url: str,
    username: str = "TUM Living Watcher",
) -> None:
    payload = {
        "username": username,
        "embeds": [
            {
                "title": "🧪 TUM Living notifier test",
                "description": (
                    "The TUM Living Discord notifier is configured correctly."
                ),
                "fields": [
                    {
                        "name": "Status",
                        "value": "✅ Discord delivery successful",
                        "inline": False,
                    },
                    {
                        "name": "Current filters",
                        "value": "Munich · ≤ €1,200 · student eligible",
                        "inline": False,
                    },
                ],
                "footer": {
                    "text": "Test only — no listing or state was processed."
                },
            }
        ],
        "allowed_mentions": {"parse": []},
    }

    _post(webhook_url, payload, "Discord housing test notification failed")
