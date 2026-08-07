from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .discord import send_listing, send_test
from .feed import fetch_listings
from .matcher import match_listing
from .state import load_state, mark_seen, prune_state, save_state


def load_config(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle) or {}
    except (OSError, yaml.YAMLError) as exc:
        raise RuntimeError(f"Could not load configuration {path}: {exc}") from exc
    return config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TUM HiWi Discord notifier")
    parser.add_argument("--config", default="config.yml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test-notification", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))

    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()
    notification_config = config.get("notifications", {})

    if args.test_notification:
        if not webhook_url:
            raise RuntimeError("DISCORD_WEBHOOK_URL is required")
        send_test(
            webhook_url,
            str(notification_config.get("username", "TUM Job Watcher")),
        )
        print("Test notification sent.")
        return 0

    feed_config = config.get("feed", {})
    listings = fetch_listings(
        str(feed_config["url"]),
        int(feed_config.get("request_timeout_seconds", 30)),
    )

    state_config = config.get("state", {})
    state_path = Path(state_config.get("path", "data/state.json"))
    state = load_state(state_path)
    first_run_mode = str(state_config.get("first_run_mode", "mark_seen"))
    first_run = not bool(state.get("initialized"))

    if first_run and first_run_mode == "mark_seen":
        for listing in listings:
            mark_seen(state, listing.listing_id)
        state["initialized"] = True
        prune_state(state, int(state_config.get("retention_days", 180)))
        if not args.dry_run:
            save_state(state_path, state)
        print(f"Initialized state with {len(listings)} existing listings; sent nothing.")
        return 0

    sent = 0
    matched = 0
    for listing in reversed(listings):
        if listing.listing_id in state["seen"]:
            continue

        result = match_listing(listing, config.get("matching", {}))
        if result.matched:
            matched += 1
            if args.dry_run:
                print(f"MATCH: {listing.title} — {listing.link}")
            else:
                if not webhook_url:
                    raise RuntimeError("DISCORD_WEBHOOK_URL is required")
                send_listing(webhook_url, listing, result, notification_config)
                sent += 1

        if not args.dry_run:
            mark_seen(state, listing.listing_id)

    if not args.dry_run:
        state["initialized"] = True
        prune_state(state, int(state_config.get("retention_days", 180)))
        save_state(state_path, state)

    print(
        f"Fetched {len(listings)} listings; "
        f"matched {matched}; sent {sent}; dry_run={args.dry_run}."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
