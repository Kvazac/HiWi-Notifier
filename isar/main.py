from __future__ import annotations
import argparse, os, sys
from pathlib import Path
from typing import Any
import yaml
from .client import GreenhouseClient
from .discord import send_job, send_test
from .matcher import match_job
from .state import load_state, mark_seen, prune, save_state

def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Isar Aerospace Greenhouse notifier")
    parser.add_argument("--config", default="isar-config.yml")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--test-notification", action="store_true")
    parser.add_argument("--test-listing", action="store_true")
    return parser.parse_args()

def main() -> int:
    args = parse_args()
    config = load_config(Path(args.config))
    notification_config = config.get("notifications", {})
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL", "").strip()

    if args.test_notification:
        if not webhook_url:
            raise RuntimeError("DISCORD_WEBHOOK_URL is required")
        send_test(webhook_url, str(notification_config.get("username", "Isar Aerospace Job Watcher")))
        print("Isar Aerospace test notification sent.")
        return 0

    api = config.get("api", {})
    client = GreenhouseClient(
        board_token=str(api.get("board_token", "isaraerospace")),
        timeout=int(api.get("timeout_seconds", 30)),
    )
    jobs = client.fetch_jobs()

    if args.test_listing:
        if not webhook_url:
            raise RuntimeError("DISCORD_WEBHOOK_URL is required")
        for job in jobs:
            result = match_job(job, config.get("matching", {}))
            if result.matched:
                send_job(webhook_url, job, result, notification_config)
                print(f"Real Isar listing test sent: id={job.job_id}, title={job.title}")
                return 0
        raise RuntimeError("No current Isar Aerospace job matched the configured student/intern filters")

    state_cfg = config.get("state", {})
    state_path = Path(state_cfg.get("path", "data/isar-state.json"))
    state = load_state(state_path)
    first_run = not bool(state.get("initialized"))
    first_run_mode = str(state_cfg.get("first_run_mode", "mark_seen"))

    if first_run and first_run_mode == "mark_seen":
        for job in jobs:
            if job.stable_id:
                mark_seen(state, job.stable_id)
        state["initialized"] = True
        prune(state, int(state_cfg.get("retention_days", 180)))
        if not args.dry_run:
            save_state(state_path, state)
        print(f"Initialized with {len(jobs)} current jobs; sent nothing.")
        return 0

    matched = sent = 0
    for job in jobs:
        if not job.stable_id or job.stable_id in state["seen"]:
            continue
        result = match_job(job, config.get("matching", {}))
        if result.matched:
            matched += 1
            if args.dry_run:
                print(f"MATCH {job.job_id}: {job.title} | {job.location}")
            else:
                if not webhook_url:
                    raise RuntimeError("DISCORD_WEBHOOK_URL is required")
                send_job(webhook_url, job, result, notification_config)
                sent += 1
        if not args.dry_run:
            mark_seen(state, job.stable_id)

    if not args.dry_run:
        state["initialized"] = True
        prune(state, int(state_cfg.get("retention_days", 180)))
        save_state(state_path, state)

    print(f"Fetched {len(jobs)} jobs; matched {matched}; sent {sent}; dry_run={args.dry_run}.")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
