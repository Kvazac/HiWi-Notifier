from __future__ import annotations
from typing import Any
import requests
from .models import HousingListing

GET_LISTINGS_QUERY = """
query GetListings(
  $resultLimit: Int,
  $pageOffset: Int,
  $orderBy: ListingSortOrder,
  $filter: ListingFilter
) {
  listings(
    resultLimit: $resultLimit
    pageOffset: $pageOffset
    orderBy: $orderBy
    filter: $filter
  ) {
    id
    uuid
    type
    numberOfRooms
    availableFrom
    availableUntil
    city
    tumLocation
    district
    postalCode
    totalRent
    deposit
    squareMeter
    tags
    seekingStudents
    publicationDate
    isListingPublic
    isActive
  }
}
"""

class LivingClientError(RuntimeError):
    pass

class LivingClient:
    def __init__(self, base_url: str, timeout: int = 30) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "tum-living-discord-notifier/1.0",
            "Accept": "application/json",
            "Referer": f"{self.base_url}/listings?viewMode=list",
        })

    def _bootstrap(self) -> str:
        response = self.session.get(f"{self.base_url}/api/me", timeout=self.timeout)
        try:
            payload = response.json()
        except ValueError as exc:
            raise LivingClientError(
                f"/api/me returned non-JSON content (HTTP {response.status_code})"
            ) from exc

        csrf = payload.get("csrf")
        if not csrf:
            raise LivingClientError(
                f"/api/me did not provide a CSRF token (HTTP {response.status_code})"
            )
        return str(csrf)

    def fetch_listings(self, result_limit: int = 50) -> list[HousingListing]:
        csrf = self._bootstrap()
        payload: dict[str, Any] = {
            "operationName": "GetListings",
            "variables": {
                "pageOffset": 0,
                "filter": {
                    "activationStatus": [True],
                    "tags": [],
                    "hasNoMoveOutDate": False,
                },
                "orderBy": "MOST_RECENT",
                "resultLimit": result_limit,
            },
            "query": GET_LISTINGS_QUERY,
        }

        response = self.session.post(
            f"{self.base_url}/graphql",
            headers={
                "csrf-token": csrf,
                "Origin": self.base_url,
                "Referer": f"{self.base_url}/listings?viewMode=list",
            },
            json=payload,
            timeout=self.timeout,
        )

        try:
            data = response.json()
        except ValueError as exc:
            raise LivingClientError(
                f"GraphQL returned non-JSON content (HTTP {response.status_code})"
            ) from exc

        if data.get("errors"):
            messages = "; ".join(str(err.get("message", err)) for err in data["errors"])
            raise LivingClientError(f"GraphQL error: {messages}")

        listings = ((data.get("data") or {}).get("listings") or [])
        return [HousingListing.from_graphql(item) for item in listings]
