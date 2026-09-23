from app.domain.models import Listing
from app.repositories.base import ListingRepository


class InMemoryListingRepository(ListingRepository):
    """Simple list-backed repository used by tests (and any dev fallback)."""

    def __init__(self, listings: list[Listing]):
        self._listings = list(listings)

    def get_all(self) -> list[Listing]:
        return list(self._listings)
