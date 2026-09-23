from abc import ABC, abstractmethod

from app.domain.models import Listing


class ListingRepository(ABC):
    """Persistence-agnostic source of listings.

    Concrete implementations (JSON file today, Postgres/RDS later) plug in
    here without the search/filtering/scoring logic ever knowing which one
    is in use.
    """

    @abstractmethod
    def get_all(self) -> list[Listing]:
        raise NotImplementedError
