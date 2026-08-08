from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

import yaml

from .client import LivingClient
from .discord import send_listing, send_test
from .matcher import matches
from .state import load_state, mark_seen, prune, save_state


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TUM Living Discord notifier"
    )

    parser.add_argument(
        "--config",
        default="living-config.yml",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
    )

    parser.add_argument(
        "--test-notification",
        action="store_true",
    )

    parser.add_argument(
        "--test-listing",
        action="store_true",
        help=(
            "Fetch a current listing and send it as a test "
            "without modifying state"
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))

    notification_config = config.get("notifications", {})

    webhook_url = os.getenv(
        "DISCORD_WEBHOOK_URL",
        "",
    ).strip()

    # Simple Discord delivery test.
    if args.test_notification:
        if not webhook_url:
            raise RuntimeError(
                "DISCORD_WEBHOOK_URL is required"
            )

        send_test(
            webhook_url,
            str(
                notification_config.get(
                    "username",
                    "TUM Living Watcher",
                )
            ),
        )

        print("TUM Living test notification sent.")
        return 0

    api = config.get("api", {})

    client = LivingClient(
        str(
            api.get(
                "base_url",
                "https://living.tum.de",
            )
        ),
        int(
            api.get(
                "timeout_seconds",
                30,
            )
        ),
    )

    # Real listing test.
    # This happens BEFORE loading or modifying state.
    if args.test_listing:
        if not webhook_url:
            raise RuntimeError(
                "DISCORD_WEBHOOK_URL is required"
            )

        listings = client.fetch_listings(
            int(
                api.get(
                    "result_limit",
                    50,
                )
            )
        )

        if not listings:
            raise RuntimeError(
                "TUM Living returned no listings"
            )

        # Prefer the newest listing matching the configured filters.
        chosen_listing = None
        chosen_result = None

        for listing in listings:
            result = matches(
                listing,
                config.get(
                    "matching",
                    {},
                ),
            )

            if result.matched:
                chosen_listing = listing
                chosen_result = result
                break

        if chosen_listing is None:
            raise RuntimeError(
                "No current TUM Living listing matched "
                "the configured filters"
            )

        send_listing(
            webhook_url,
            chosen_listing,
            chosen_result,
            notification_config,
        )

        print(
            "Real listing test sent: "
            f"id={chosen_listing.listing_id}, "
            f"uuid={chosen_listing.uuid}"
        )

        return 0

    listings = client.fetch_listings(
        int(
            api.get(
                "result_limit",
                50,
            )
        )
    )

    state_cfg = config.get("state", {})
    state_path = Path(
        state_cfg.get(
            "path",
            "data/living-state.json",
        )
    )

    state = load_state(state_path)

    first_run = not bool(
        state.get("initialized")
    )

    first_run_mode = str(
        state_cfg.get(
            "first_run_mode",
            "mark_seen",
        )
    )

    if (
        first_run
        and first_run_mode == "mark_seen"
    ):
        for listing in listings:
            if listing.stable_id:
                mark_seen(
                    state,
                    listing.stable_id,
                )

        state["initialized"] = True

        prune(
            state,
            int(
                state_cfg.get(
                    "retention_days",
                    180,
                )
            ),
        )

        if not args.dry_run:
            save_state(
                state_path,
                state,
            )

        print(
            f"Initialized with "
            f"{len(listings)} current listings; "
            f"sent nothing."
        )

        return 0

    matched = 0
    sent = 0

    for listing in reversed(listings):
        if not listing.stable_id:
            continue

        if listing.stable_id in state["seen"]:
            continue

        result = matches(
            listing,
            config.get(
                "matching",
                {},
            ),
        )

        if result.matched:
            matched += 1

            if args.dry_run:
                print(
                    f"MATCH {listing.listing_id}: "
                    f"{listing.type} | "
                    f"{listing.city} | "
                    f"€{listing.total_rent} | "
                    f"{listing.square_meter}m²"
                )
            else:
                if not webhook_url:
                    raise RuntimeError(
                        "DISCORD_WEBHOOK_URL is required"
                    )

                send_listing(
                    webhook_url,
                    listing,
                    result,
                    notification_config,
                )

                sent += 1

        if not args.dry_run:
            mark_seen(
                state,
                listing.stable_id,
            )

    if not args.dry_run:
        state["initialized"] = True

        prune(
            state,
            int(
                state_cfg.get(
                    "retention_days",
                    180,
                )
            ),
        )

        save_state(
            state_path,
            state,
        )

    print(
        f"Fetched {len(listings)} listings; "
        f"matched {matched}; "
        f"sent {sent}; "
        f"dry_run={args.dry_run}."
    )

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(
            f"ERROR: {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
