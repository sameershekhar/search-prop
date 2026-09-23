from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Listing:
    """Shared listing value object, used across all three layers
    (repositories, services, api) so persistence and transport details
    never leak into business logic."""

    id: str
    source: str
    address: str
    city: str
    state: str
    zip: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    latitude: float
    longitude: float
    listed_date: str  # ISO date string, e.g. "2026-08-29"
    status: str
    description: str


def listing_from_dict(item: dict) -> Listing:
    """Maps a raw JSON dict (feed field names) to a Listing."""
    return Listing(
        id=item["id"],
        source=item["source"],
        address=item["address"],
        city=item["city"],
        state=item["state"],
        zip=item["zip"],
        price=item["price"],
        bedrooms=item["bedrooms"],
        bathrooms=item["bathrooms"],
        sqft=item["sqft"],
        latitude=item["latitude"],
        longitude=item["longitude"],
        listed_date=item["listedDate"],
        status=item["status"],
        description=item["description"],
    )
