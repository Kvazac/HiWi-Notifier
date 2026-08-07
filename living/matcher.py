from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from .models import HousingListing

@dataclass(frozen=True)
class MatchResult:
    matched: bool
    reasons: tuple[str, ...]

def _norm(value: str) -> str:
    return value.casefold().strip()

def matches(listing: HousingListing, config: dict[str, Any]) -> MatchResult:
    reasons: list[str] = []

    max_rent = config.get("max_total_rent")
    if max_rent is not None:
        if listing.total_rent is None or float(listing.total_rent) > float(max_rent):
            return MatchResult(False, ("rent above limit or unavailable",))
        reasons.append(f"rent ≤ €{float(max_rent):.0f}")

    min_size = config.get("min_square_meters")
    if min_size is not None:
        if listing.square_meter is None or float(listing.square_meter) < float(min_size):
            return MatchResult(False, ("size below minimum or unavailable",))
        reasons.append(f"size ≥ {float(min_size):g} m²")

    cities = [_norm(str(v)) for v in (config.get("cities") or [])]
    if cities:
        if _norm(listing.city) not in cities:
            return MatchResult(False, ("city not preferred",))
        reasons.append(f"city: {listing.city}")

    types = [_norm(str(v)) for v in (config.get("types") or [])]
    if types:
        if _norm(listing.type) not in types:
            return MatchResult(False, ("listing type not selected",))
        reasons.append(f"type: {listing.type}")

    if bool(config.get("require_student_eligible", False)):
        if listing.seeking_students is not True:
            return MatchResult(False, ("not marked student-eligible",))
        reasons.append("student eligible")

    if listing.is_active is False:
        return MatchResult(False, ("inactive",))

    return MatchResult(True, tuple(reasons))
