from __future__ import annotations
import html, re
from typing import Any
import requests
from .matcher import MatchResult
from .models import Job

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")

class DiscordError(RuntimeError):
    pass

def _plain_text(value: str) -> str:
    return _SPACE_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", value))).strip()

def _post(webhook_url: str, payload: dict[str, Any], label: str) -> None:
    try:
        response = requests.post(webhook_url, params={"wait": "true"}, json=payload, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise DiscordError(f"{label}: {exc}") from exc

def send_job(webhook_url: str, job: Job, result: MatchResult, config: dict[str, Any]) -> None:
    max_chars = int(config.get("max_description_characters", 900))
    description = _plain_text(job.content)
    if len(description) > max_chars:
        description = description[:max_chars - 1].rstrip() + "…"

    payload = {
        "username": str(config.get("username", "Isar Aerospace Job Watcher")),
        "embeds": [{
            "title": f"🚀 {job.title}"[:256],
            "url": job.absolute_url,
            "description": description[:4096] or "New matching Isar Aerospace position.",
            "fields": [
                {"name": "Location", "value": job.location or "Unknown", "inline": True},
                {"name": "Job ID", "value": job.job_id or "Unknown", "inline": True},
                {"name": "Matched because", "value": ", ".join(result.reasons)[:1024], "inline": False},
            ],
            "footer": {"text": "Isar Aerospace · Greenhouse"},
        }],
        "allowed_mentions": {"parse": []},
    }
    _post(webhook_url, payload, "Discord Isar job notification failed")

def send_test(webhook_url: str, username: str = "Isar Aerospace Job Watcher") -> None:
    payload = {
        "username": username,
        "embeds": [{
            "title": "🧪 Isar Aerospace notifier test",
            "description": "The Isar Aerospace Discord notifier is configured correctly.",
            "fields": [
                {"name": "Role filter", "value": "Working Student · Werkstudent · Intern · Internship · Praktikant · Praktikum", "inline": False},
                {"name": "Status", "value": "✅ Discord delivery successful", "inline": False},
            ],
            "footer": {"text": "Test only — no job state was changed."},
        }],
        "allowed_mentions": {"parse": []},
    }
    _post(webhook_url, payload, "Discord Isar test notification failed")
