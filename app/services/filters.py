from abc import ABC, abstractmethod

from app.domain.models import Listing


class ListingFilter(ABC):
    """Strategy interface: one filter dimension, one class.

    Adding a new filter (e.g. maxBedrooms, status) means adding one new
    class here - CompositeFilter and SearchService need no changes.
    """

    @abstractmethod
    def matches(self, listing: Listing) -> bool:
        raise NotImplementedError


class PriceRangeFilter(ListingFilter):
    def __init__(self, min_price: float | None, max_price: float | None):
        self._min_price = min_price
        self._max_price = max_price

    def matches(self, listing: Listing) -> bool:
        if self._min_price is not None and listing.price < self._min_price:
            return False
        if self._max_price is not None and listing.price > self._max_price:
            return False
        return True


class MinBedroomsFilter(ListingFilter):
    def __init__(self, min_bedrooms: int | None):
        self._min_bedrooms = min_bedrooms

    def matches(self, listing: Listing) -> bool:
        if self._min_bedrooms is None:
            return True
        return listing.bedrooms >= self._min_bedrooms


class CityFilter(ListingFilter):
    """Case-insensitive substring match, to tolerate minor formatting
    inconsistencies between feeds (e.g. trailing whitespace, casing)."""

    def __init__(self, city: str | None):
        self._city = city.strip().lower() if city else None

    def matches(self, listing: Listing) -> bool:
        if not self._city:
            return True
        return self._city in listing.city.strip().lower()


class KeywordFilter(ListingFilter):
    """Case-insensitive substring match against the free-text description."""

    def __init__(self, keyword: str | None):
        self._keyword = keyword.strip().lower() if keyword else None

    def matches(self, listing: Listing) -> bool:
        if not self._keyword:
            return True
        return self._keyword in listing.description.lower()


class CompositeFilter(ListingFilter):
    """ANDs together only the filters that were actually supplied."""

    def __init__(self, filters: list[ListingFilter]):
        self._filters = filters

    def matches(self, listing: Listing) -> bool:
        return all(f.matches(listing) for f in self._filters)

    def apply(self, listings: list[Listing]) -> list[Listing]:
        return [listing for listing in listings if self.matches(listing)]
