from dataclasses import dataclass
from app.models import Listing
from app.repositories.base import ListingRepository
from app.services.exceptions import InvalidSearchParamsError
from app.services.filters import (
    CityFilter,
    CompositeFilter,
    DuplicateAddressFilter,
    KeywordFilter,
    MinBedroomsFilter,
    PriceRangeFilter,
)
from app.services.pagination import Page, Paginator
from app.services.scoring import BudgetRecencyScorer, ScoringStrategy


@dataclass(frozen=True)
class SearchParams:
    min_price: float | None = None
    max_price: float | None = None
    min_bedrooms: int | None = None
    city: str | None = None
    keyword: str | None = None
    target_budget: float | None = None
    page: int = 1
    page_size: int = 10


@dataclass(frozen=True)
class ScoredListing:
    listing: Listing
    score: float


class SearchService:
    """Orchestrates the search pipeline: validate -> fetch -> filter -> score
    -> sort -> paginate. Each step is delegated to its own class, so this is
    the seam most likely to gain a new step (e.g. a new ranking factor)
    without becoming a god-object.
    """

    def __init__(
        self,
        repository: ListingRepository,
        scorer: ScoringStrategy | None = None,
    ):
        self._repository = repository
        self._scorer = scorer or BudgetRecencyScorer()

    def search(self, params: SearchParams) -> Page[ScoredListing]:
        self._validate(params)

        listings = self._repository.get_all()
        matched = self._build_filter(params).apply(listings)
        scored_listing = [
            ScoredListing(
                listing=listing,
                score=self._scorer.score(listing, params.target_budget),
            )
            for listing in matched
        ]

        ranked = self._rank(scored_listing)

        return Paginator.paginate(ranked, params.page, params.page_size)

    @staticmethod
    def _build_filter(params: SearchParams) -> CompositeFilter:
        return CompositeFilter(
            [
                PriceRangeFilter(params.min_price, params.max_price),
                MinBedroomsFilter(params.min_bedrooms),
                CityFilter(params.city),
                KeywordFilter(params.keyword),
                # Always applied, independent of user-supplied params: feeds
                # from multiple sources can list the same property twice
                # with slightly different address formatting.
                DuplicateAddressFilter(),
            ]
        )

    @staticmethod
    def _rank(scored: list[ScoredListing]) -> list[ScoredListing]:
        # Three stable sorts, lowest-priority first: final order is
        # score desc, then listedDate desc, then id asc as a deterministic
        # tiebreaker (duplicate listings from different MLS sources often
        # tie on score).
        # ranked = sorted(scored, key=lambda sl: sl.listing.id)
        # ranked.sort(key=lambda sl: sl.listing.listed_date, reverse=True)
        # ranked.sort(key=lambda sl: sl.score, reverse=True)
        # return ranked
        return sorted(scored, key=lambda sl: sl.score, reverse=True)

    @staticmethod
    def _validate(params: SearchParams) -> None:
        if params.min_price is not None and params.min_price < 0:
            raise InvalidSearchParamsError("minPrice must be >= 0", field="minPrice")
        if params.max_price is not None and params.max_price < 0:
            raise InvalidSearchParamsError("maxPrice must be >= 0", field="maxPrice")
        if (
            params.min_price is not None
            and params.max_price is not None
            and params.min_price > params.max_price
        ):
            raise InvalidSearchParamsError(
                "minPrice cannot be greater than maxPrice", field="minPrice"
            )
        if params.min_bedrooms is not None and params.min_bedrooms < 0:
            raise InvalidSearchParamsError(
                "minBedrooms must be >= 0", field="minBedrooms"
            )
        if params.target_budget is not None and params.target_budget <= 0:
            raise InvalidSearchParamsError(
                "targetBudget must be greater than 0", field="targetBudget"
            )
        if params.page <= 0:
            raise InvalidSearchParamsError("page must be greater than 0", field="page")
        if params.page_size <= 0:
            raise InvalidSearchParamsError(
                "pageSize must be greater than 0", field="pageSize"
            )
