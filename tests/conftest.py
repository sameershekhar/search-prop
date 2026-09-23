import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_search_service
from app.domain.mappers import listing_from_dict
from app.domain.models import Listing
from app.main import create_app
from app.repositories.in_memory_repository import InMemoryListingRepository
from app.services.scoring import BudgetRecencyScorer
from app.services.search_service import SearchService

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "listings.json"

# Fixed "today" so recency scoring is deterministic across test runs.
FIXED_TODAY = date(2026, 9, 23)


@pytest.fixture
def sample_listings() -> list[Listing]:
    raw = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return [listing_from_dict(item) for item in raw]


@pytest.fixture
def in_memory_repo(sample_listings: list[Listing]) -> InMemoryListingRepository:
    return InMemoryListingRepository(sample_listings)


@pytest.fixture
def search_service(in_memory_repo: InMemoryListingRepository) -> SearchService:
    return SearchService(
        repository=in_memory_repo,
        scorer=BudgetRecencyScorer(today=FIXED_TODAY),
    )


@pytest.fixture
def client(in_memory_repo: InMemoryListingRepository) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_search_service] = lambda: SearchService(
        repository=in_memory_repo,
        scorer=BudgetRecencyScorer(today=FIXED_TODAY),
    )
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
