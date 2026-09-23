from functools import lru_cache

from app.config import settings
from app.repositories.json_file_repository import JsonFileListingRepository
from app.services.search_service import SearchService


@lru_cache
def get_repository() -> JsonFileListingRepository:
    """Singleton so the JSON file is only read once per process. Swapping
    to PostgresListingRepository later means changing only this function."""
    return JsonFileListingRepository(settings.data_file_path)


def get_search_service() -> SearchService:
    return SearchService(repository=get_repository())
