from __future__ import annotations
import requests
from .models import Job

class GreenhouseError(RuntimeError):
    pass

class GreenhouseClient:
    def __init__(self, board_token: str = "isaraerospace", timeout: int = 30) -> None:
        self.board_token = board_token
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "isar-aerospace-discord-notifier/1.0",
            "Accept": "application/json",
        })

    @property
    def jobs_url(self) -> str:
        return f"https://boards-api.greenhouse.io/v1/boards/{self.board_token}/jobs"

    def fetch_jobs(self) -> list[Job]:
        try:
            response = self.session.get(
                self.jobs_url,
                params={"content": "true"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise GreenhouseError(f"Could not fetch Greenhouse jobs: {exc}") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            raise GreenhouseError("Greenhouse returned non-JSON content") from exc

        jobs = payload.get("jobs")
        if not isinstance(jobs, list):
            raise GreenhouseError("Greenhouse JSON response did not contain a jobs list")

        return [Job.from_greenhouse(job) for job in jobs]
