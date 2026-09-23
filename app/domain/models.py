from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Listing:
    """Domain representation of a listing, independent of persistence or API concerns."""

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
