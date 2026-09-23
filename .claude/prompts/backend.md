# Backend Specification — Listing Search Service

## 1. Requirements

Build a Python FastAPI REST API for searching property listings stored in AWS RDS PostgreSQL.

The backend must:

* Expose `GET /api/listings/search`
* Support filtering by:

  * `minPrice`
  * `maxPrice`
  * `minBedrooms`
  * `city`
  * `keyword`
* Support `targetBudget` for relevance scoring.
* Support pagination using `page` and `pageSize`.
* Return ranked listings with relevance scores and pagination metadata.
* Handle invalid input with clear HTTP errors.
* Return an empty result set for valid searches with no matches.
* Keep filtering, scoring, pagination, persistence, and API concerns separated.
* Be easy to extend with new filters, ranking factors, and endpoints.

---

## 2. API Contract

### Endpoint

`GET /api/listings/search`

### Query Parameters

| Parameter      | Type    | Required | Description                                         |
| -------------- | ------- | -------: | --------------------------------------------------- |
| `minPrice`     | number  |       No | Minimum property price, inclusive                   |
| `maxPrice`     | number  |       No | Maximum property price, inclusive                   |
| `minBedrooms`  | integer |       No | Minimum number of bedrooms, inclusive               |
| `city`         | string  |       No | Case-insensitive city filter                        |
| `keyword`      | string  |       No | Case-insensitive keyword search against description |
| `targetBudget` | number  |       No | Budget used for relevance scoring                   |
| `page`         | integer |       No | Page number, default `1`                            |
| `pageSize`     | integer |       No | Results per page, default `10`                      |

Example:

`GET /api/listings/search?city=Springfield&minPrice=400000&maxPrice=500000&targetBudget=450000&page=1&pageSize=5`

### Successful Response

HTTP `200`

Response must contain:

```text
{
  "results": [...],
  "pagination": {
    "page": 1,
    "pageSize": 5,
    "totalResults": 2,
    "totalPages": 1,
    "hasNext": false,
    "hasPrevious": false
  }
}
```

Each result must contain at minimum:

* `id`
* `source`
* `address`
* `city`
* `state`
* `zip`
* `price`
* `bedrooms`
* `bathrooms`
* `sqft`
* `latitude`
* `longitude`
* `listedDate`
* `status`
* `description`
* `score`

---

## 3. Listing Domain Model

A listing contains:

* `id: string`
* `source: string`
* `address: string`
* `city: string`
* `state: string`
* `zip: string`
* `price: number`
* `bedrooms: integer`
* `bathrooms: number`
* `sqft: integer`
* `latitude: number`
* `longitude: number`
* `listedDate: date`
* `status: active | pending | sold`
* `description: string`

Listing identity is `(source, id)` because `id` is only unique within an individual MLS source.

The domain model must remain independent of SQLAlchemy and FastAPI/Pydantic models.

---

## 4. Search and Filtering Rules

Filtering must happen before scoring and pagination.

Pipeline:

```text
Validate
  ↓
Fetch listings
  ↓
Filter
  ↓
Score
  ↓
Sort
  ↓
Paginate
  ↓
Return response
```

### Price

* `minPrice`: `price >= minPrice`
* `maxPrice`: `price <= maxPrice`
* Both boundaries are inclusive.
* If both are supplied, `minPrice <= maxPrice`.

### Bedrooms

`bedrooms >= minBedrooms`

### City

* Case-insensitive matching.
* Use exact city matching.
* Leading/trailing whitespace should not affect matching.

### Keyword

* Case-insensitive.
* Match against `description`.
* Simple substring matching is sufficient.
* Empty/omitted keyword imposes no constraint.

### Multiple filters

All supplied filters use AND semantics.

Example:

```text
city = Springfield
AND
minPrice = 400000
AND
maxPrice = 500000
AND
minBedrooms = 2
```

---

## 5. Validation and Error Handling

### API-level validation

FastAPI/Pydantic must handle structural validation such as:

* invalid numeric values
* negative `minPrice`
* negative `maxPrice`
* negative `minBedrooms`
* invalid page number
* invalid `pageSize`
* invalid `targetBudget`

Structural validation errors return HTTP `422`.

### Business validation

Cross-field rules must be handled by the service/domain layer.

Example:

```text
minPrice > maxPrice
```

must return HTTP `400`.

Use a consistent error structure:

```text
{
  "error": "Invalid search parameters",
  "field": "minPrice",
  "message": "minPrice cannot be greater than maxPrice"
}
```

### No-match behavior

A valid search with no matching listings is not an error.

Return:

```text
HTTP 200

results = []
totalResults = 0
```

### Pagination validation

* `page >= 1`
* `pageSize > 0`
* Use a reasonable maximum page size.
* Requesting a page beyond the final page returns `200` with an empty result list.

---

## 6. Relevance Scoring

Implement a `ScoringStrategy` interface with `BudgetRecencyScorer` as the initial implementation.

### Price-fit

When `targetBudget` is provided:

```text
priceFit = max(0, 1 - abs(price - targetBudget) / targetBudget)
```

Clamp the result to `[0, 1]`.

Exact target budget produces a price-fit score of `1.0`.

### Recency

Use exponential decay:

```text
recency = exp(-daysSinceListed / 30)
```

`30` must be a named configuration/constant.

Newer listings receive a higher recency score.

### Combined score

```text
score = 0.7 * priceFit + 0.3 * recency
```

The weights must be named constants so they can easily be changed.

### No target budget

When `targetBudget` is omitted:

* price-fit is neutral
* ranking effectively uses recency

### Sorting

Sort by:

1. `score` descending
2. `listedDate` descending
3. `id` ascending

The ordering must be deterministic.

---

## 7. Pagination Contract

Pagination occurs only after filtering, scoring, and sorting.

The paginator must return:

* `results`
* `page`
* `pageSize`
* `totalResults`
* `totalPages`
* `hasNext`
* `hasPrevious`

Required behavior:

* Empty dataset → empty results.
* Normal page → corresponding slice.
* Last partial page → return remaining records.
* Page beyond final page → empty results, HTTP 200.
* `pageSize` larger than total results → return all results.
* Invalid `pageSize` → validation error.

---

## 8. Architecture and Responsibilities

Use strict separation of concerns.

```text
FastAPI Route
     ↓
SearchService
     ↓
 ┌───┼─────────────┐
 ↓   ↓             ↓
Filter  Scoring  Pagination
     ↓
ListingRepository
     ↓
PostgreSQL
```

### API Layer

Responsible for:

* HTTP request/response
* query parameter parsing
* Pydantic schemas
* dependency injection
* HTTP error mapping

### SearchService

Responsible only for orchestrating:

* validation
* repository access
* filters
* scoring
* sorting
* pagination
* response mapping

### Filter Strategies

Each filter implements:

`matches(listing) -> bool`

Initial strategies:

* `PriceRangeFilter`
* `MinBedroomsFilter`
* `CityFilter`
* `KeywordFilter`
* `CompositeFilter`

### Scoring Strategy

Interface:

`score(listing, target_budget) -> float`

Initial implementation:

`BudgetRecencyScorer`

### Pagination

`Paginator` must contain only pagination logic and no database/API dependencies.

### Repository

`ListingRepository` defines:

`get_all() -> list[Listing]`

Implementations:

* `PostgresListingRepository`
* `InMemoryListingRepository`

The repository must not contain filtering, scoring, sorting, or pagination logic.

---

## 9. Persistence

Use AWS RDS PostgreSQL through SQLAlchemy.

Database configuration must come from:

`DATABASE_URL`

Do not hard-code:

* username
* password
* hostname
* database credentials

The database table must represent the listing domain fields.

Create a seed utility that:

1. Creates the listings table if required.
2. Reads `sample_listings.json`.
3. Inserts/upserts the sample listings.
4. Can be executed independently.

Tests must use `InMemoryListingRepository` and must never require RDS.

---

## 10. Dependency Injection

FastAPI dependency injection must allow the repository implementation to be replaced.

Production:

```text
PostgresListingRepository
```

Tests:

```text
InMemoryListingRepository
```

The `SearchService` must not directly instantiate the PostgreSQL repository.

This is required for testability and future repository replacement.

---

## 11. Testing Requirements

Use pytest.

### Filter tests

Test:

* minimum price
* maximum price
* inclusive boundaries
* minimum bedrooms
* case-insensitive city
* case-insensitive keyword
* omitted filters
* multiple filters together

### Scoring tests

Test:

* exact target budget → `1.0` price-fit
* property far from budget
* no target budget
* newer listing receives higher recency
* deterministic tie-breaking

### Pagination tests

Test:

* empty list
* first page
* middle page
* final partial page
* page beyond final page
* pageSize larger than result count
* invalid page/pageSize

### Search service tests

Test:

* normal search
* no city matches
* no keyword matches
* invalid price range
* target-budget ranking
* pagination after sorting

### API tests

Test:

* successful request → `200`
* no results → `200`
* invalid structural input → `422`
* invalid price range → `400`
* response schema
* pagination metadata

All tests must use the in-memory repository.

---

## 12. CORS and Configuration

Configure CORS so the Vite React development application can call the FastAPI backend locally.

CORS origins must be configurable through environment/configuration.

Database configuration must also come from environment variables.

Provide `.env.example` without real credentials.

---

## 13. Extensibility Requirements

The implementation must make the following changes easy without rewriting `SearchService`:

### New filter

Example:

`status=active`

Expected approach:

```text
Create StatusFilter
        ↓
Add to filter construction
```

### New scoring factor

Example:

`bedroomScore`

Expected approach:

```text
Create/extend scoring strategy
        ↓
Change configured weights
```

### New repository

Example:

```text
InMemoryListingRepository
PostgresListingRepository
Future ElasticsearchListingRepository
```

The service layer should not need to know persistence details.

### New API endpoint

API routes and schemas should remain separated from domain/service logic.

---

## 14. Non-Functional Requirements

The backend should prioritize:

* correctness
* testability
* readability
* deterministic behavior
* maintainability
* extensibility
* clear separation of concerns

The dataset is intentionally small, so optimization for millions of listings is not required.

Filtering/scoring/pagination may remain in Python for this exercise.

Do not introduce caching, distributed systems, background workers, or search engines unless a future requirement requires them.

---

## 15. Deliverables

The backend implementation must provide:

```text
app/
├── main.py
├── config.py
├── domain/
├── repositories/
├── db/
├── services/
└── api/

tests/
├── conftest.py
├── test_filters.py
├── test_scoring.py
├── test_pagination.py
├── test_search_service.py
└── test_api.py

.env.example
README.md
pyproject.toml
```

The final backend must:

1. Start successfully with FastAPI/Uvicorn.
2. Connect to AWS RDS using `DATABASE_URL`.
3. Seed the sample listings.
4. Expose the search endpoint.
5. Return correctly filtered and ranked results.
6. Return correct pagination metadata.
7. Handle invalid parameters correctly.
8. Pass the pytest suite.
9. Provide an API contract that the React frontend can consume without backend changes.
