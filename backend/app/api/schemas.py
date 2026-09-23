from pydantic import BaseModel


class ListingResult(BaseModel):
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
    listedDate: str
    status: str
    description: str
    score: float


class SearchResponse(BaseModel):
    results: list[ListingResult]
    page: int
    pageSize: int
    totalResults: int
    totalPages: int
    


class ErrorResponse(BaseModel):
    error: str
    field: str | None = None
