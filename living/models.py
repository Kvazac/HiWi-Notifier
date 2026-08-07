from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class HousingListing:
    listing_id: str
    uuid: str
    type: str
    number_of_rooms: float | None
    available_from: str | None
    available_until: str | None
    city: str
    district: str
    postal_code: str
    total_rent: float | None
    deposit: float | None
    square_meter: float | None
    seeking_students: bool | None
    publication_date: str | None
    is_listing_public: bool | None
    is_active: bool | None

    @classmethod
    def from_graphql(cls, raw: dict[str, Any]) -> "HousingListing":
        return cls(
            listing_id=str(raw.get("id") or ""),
            uuid=str(raw.get("uuid") or ""),
            type=str(raw.get("type") or ""),
            number_of_rooms=raw.get("numberOfRooms"),
            available_from=raw.get("availableFrom"),
            available_until=raw.get("availableUntil"),
            city=str(raw.get("city") or ""),
            district=str(raw.get("district") or ""),
            postal_code=str(raw.get("postalCode") or ""),
            total_rent=raw.get("totalRent"),
            deposit=raw.get("deposit"),
            square_meter=raw.get("squareMeter"),
            seeking_students=raw.get("seekingStudents"),
            publication_date=raw.get("publicationDate"),
            is_listing_public=raw.get("isListingPublic"),
            is_active=raw.get("isActive"),
        )

    @property
    def stable_id(self) -> str:
        return self.uuid or self.listing_id
