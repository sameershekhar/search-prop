from fastapi import APIRouter, Depends, Query
from app.api.schemas import ListingResult, SearchResponse
from app.dependencies import get_search_service
from app.services.search_service import ScoredListing, SearchParams, SearchService

router = APIRouter(prefix="/api/listings", tags=["listings"])


@router.get("/health")
def health_check():
    return {"status": "healthy"}


@router.get("/search", response_model=SearchResponse)
def search_listings(
    minPrice: float | None = Query(default=None),
    maxPrice: float | None = Query(default=None),
    minBedrooms: int | None = Query(default=None),
    city: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    targetBudget: float | None = Query(default=None),
    page: int = Query(default=1),
    pageSize: int = Query(default=10),
    service: SearchService = Depends(get_search_service),
) -> SearchResponse:
    params = SearchParams(
        min_price=minPrice,
        max_price=maxPrice,
        min_bedrooms=minBedrooms,
        city=city,
        keyword=keyword,
        target_budget=targetBudget,
        page=page,
        page_size=pageSize,
    )

    result_page = service.search(params)

    return SearchResponse(
        results=[_to_listing_result(sl) for sl in result_page.items],
        page=result_page.page,
        pageSize=result_page.page_size,
        totalResults=result_page.total_results,
        totalPages=result_page.total_pages,
    )


def _to_listing_result(scored: ScoredListing) -> ListingResult:
    listing = scored.listing
    return ListingResult(
        id=listing.id,
        source=listing.source,
        address=listing.address,
        city=listing.city,
        state=listing.state,
        zip=listing.zip,
        price=listing.price,
        bedrooms=listing.bedrooms,
        bathrooms=listing.bathrooms,
        sqft=listing.sqft,
        latitude=listing.latitude,
        longitude=listing.longitude,
        listedDate=listing.listed_date,
        status=listing.status,
        description=listing.description,
        score=round(scored.score, 4),
    )
