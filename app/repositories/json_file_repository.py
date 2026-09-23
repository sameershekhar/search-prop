import json
from pathlib import Path

from app.models import Listing, listing_from_dict
from app.repositories.base import ListingRepository


class JsonFileListingRepository(ListingRepository):
    """Loads listings from a local JSON file and caches them in memory.

    Placeholder for the eventual PostgresListingRepository (AWS RDS): both
    implement the same ListingRepository interface, so swapping one for the
    other requires no changes to the service or API layers.
    """

    def __init__(self, file_path: Path | str):
        self._file_path = Path(file_path)
        self._cache: list[Listing] | None = None

    def get_all(self) -> list[Listing]:
        if self._cache is None:
            self._cache = self._load()
        return list(self._cache)

    def _load(self) -> list[Listing]:
        raw = json.loads(self._file_path.read_text(encoding="utf-8"))
        return [listing_from_dict(item) for item in raw]
