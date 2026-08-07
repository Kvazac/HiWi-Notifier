from src.matcher import match_listing
from src.models import Listing


def listing(title: str, description: str = "") -> Listing:
    return Listing(
        listing_id="id",
        title=title,
        link="https://example.com",
        description=description,
        published=None,
    )


def test_include_any_matches_case_insensitively() -> None:
    result = match_listing(
        listing("Studentische Hilfskraft für Softwareentwicklung"),
        {"include_any": ["softwareentwicklung"]},
    )
    assert result.matched


def test_exclusion_wins() -> None:
    result = match_listing(
        listing("Python role", "Marketing team"),
        {"include_any": ["python"], "exclude_any": ["marketing"]},
    )
    assert not result.matched


def test_weighted_score() -> None:
    result = match_listing(
        listing("Python and machine learning"),
        {
            "weighted_terms": {"python": 3, "machine learning": 4},
            "minimum_score": 6,
        },
    )
    assert result.matched
    assert result.score == 7
