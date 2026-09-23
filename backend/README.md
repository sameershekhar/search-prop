# SearchProp Backend — Listing Search API

A FastAPI-based REST service for searching and ranking property listings. Supports filtering by price, bedrooms, city, and free-text keyword, with relevance-based ranking driven by budget proximity and listing recency.

## Architecture

The backend follows a **3-layer architecture with strategy patterns** for extensibility (plan: add Postgres/RDS later with zero changes to business logic):

```
api  ->  services  ->  repositories
```

- **`app/models.py`**: The `Listing` value object and its JSON mapper, shared across all three layers - not a layer itself, just the common data shape everyone passes around.
- **Repositories** (`app/repositories/`): Persistence abstraction. Today: `JsonFileListingRepository` (file-based, in-memory cache). Tomorrow: `PostgresListingRepository` (AWS RDS).
- **Services** (`app/services/`): Business logic.
  - **Filters** (strategy pattern): One filter class per dimension (`PriceRangeFilter`, `MinBedroomsFilter`, `CityFilter`, `KeywordFilter`). Composed via `CompositeFilter`.
  - **Scoring** (strategy pattern): `ScoringStrategy` interface with `BudgetRecencyScorer` implementation (see *Scoring* section below).
  - **Pagination**: Pure, testable list slicing.
  - **SearchService**: Orchestrates the pipeline: validate → fetch → filter → score → sort → paginate.
- **API** (`app/api/`): FastAPI routes, Pydantic schemas, error handlers.
- **Main** (`app/main.py`): FastAPI app factory and middleware setup.

## Setup

### 1. Install dependencies

```bash
cd backend
uv sync  # or: pip install -e . && pip install pytest httpx
```

### 2. Run tests

```bash
uv run pytest -v
```

All 55 tests (filters, scoring, pagination, service logic, API endpoints, edge cases) should pass.

### 3. Start the server

```bash
uv run uvicorn app.main:app --reload --port 8000
```

Server runs at `http://localhost:8000`. OpenAPI docs at `http://localhost:8000/docs`.

## API

### Search Endpoint

```
GET /api/listings/search
```

**Query Parameters:**

- `minPrice` (optional, float): Minimum list price (USD).
- `maxPrice` (optional, float): Maximum list price (USD).
- `minBedrooms` (optional, int): Minimum bedroom count.
- `city` (optional, str): City name (case-insensitive, substring match).
- `keyword` (optional, str): Free-text search in description (case-insensitive substring match).
- `targetBudget` (optional, float): Buyer's budget; used to score listings by price proximity.
- `page` (optional, int, default=1): Page number (1-indexed).
- `pageSize` (optional, int, default=10): Results per page.

**Response:**

```json
{
  "results": [
    {
      "id": "A1",
      "source": "MLS_A",
      "address": "123 Main St, Apt 4B",
      "city": "Springfield",
      "state": "VA",
      "zip": "22150",
      "price": 450000.0,
      "bedrooms": 2,
      "bathrooms": 1.5,
      "sqft": 980,
      "latitude": 38.7893,
      "longitude": -77.1873,
      "listedDate": "2026-08-29",
      "status": "active",
      "description": "Bright top-floor condo near shops and transit. Pet friendly.",
      "score": 0.8304
    }
  ],
  "page": 1,
  "pageSize": 10,
  "totalResults": 2,
  "totalPages": 1
}
```

**Error Response:**

```json
{
  "error": "minPrice cannot be greater than maxPrice",
  "field": "minPrice"
}
```

Status: `400` for invalid params, `422` for structural violations (wrong type, missing required field).

### Example Requests

```bash
# Search Springfield, budget $450k, first 5 results
curl "http://localhost:8000/api/listings/search?city=Springfield&targetBudget=450000&pageSize=5"

# Filter: 3+ bedrooms, $400k-$600k
curl "http://localhost:8000/api/listings/search?minBedrooms=3&minPrice=400000&maxPrice=600000"

# Free-text search
curl "http://localhost:8000/api/listings/search?keyword=garage&pageSize=20"
```

## Scoring Approach

Relevance is a weighted blend of two components:

### 1. Price Fit (70% weight)

How close the listing price is to the buyer's target budget:

```
price_fit = max(0, 1 - |price - targetBudget| / targetBudget)
```

- `targetBudget=$450k, price=$450k` → fit=1.0 (perfect).
- `targetBudget=$450k, price=$300k` → fit≈0.33 (far below).
- No `targetBudget` supplied → fit=1.0 (neutral; don't penalize).

### 2. Recency (30% weight)

How recently the listing was posted. Uses exponential decay with a 30-day half-life:

```
recency_fit = exp(- days_since_listed / 30)
```

- Listed today → fit≈1.0.
- Listed 30 days ago → fit≈0.37.
- Listed 60 days ago → fit≈0.14.

### Combined Formula

```
score = 0.7 × price_fit + 0.3 × recency_fit
```

**Trade-offs:**

- **70/30 split favors price over recency.** A buyer's budget fit matters most; recency is a secondary signal. Change the weights in `BudgetRecencyScorer` to adjust priorities.
- **Exponential decay for recency.** Listings decay smoothly, not abruptly (e.g., a 40-day listing isn't penalized as harshly as day-30, but day-1 is still strongly preferred).
- **No fuzzy matching on city/keyword.** Simple substring match works well for this small, consistent dataset. For production with millions of listings, fuzzy matching (levenshtein distance, soundex) would be worth adding.
- **No SQL-side filtering.** Everything happens in Python after loading listings. At 12 records, this is negligible; at scale (100k+ listings), push filtering to SQL (e.g., Postgres `WHERE price BETWEEN ... AND city ILIKE ...`).
- **Deterministic tiebreaker.** When two listings tie on score, they're ordered by listing date (desc) then ID (asc). Example: duplicate listings from different MLS sources (same address, price, date) will be stable across runs.

## Data

Sample listings (`data/listings.json`) are loaded once at startup and cached in memory. To load a different dataset:

```bash
SEARCHPROP_DATA_FILE=/path/to/your/listings.json uv run uvicorn app.main:app
```

Or edit `app/config.py` to change the default path.

### JSON Schema

```json
{
  "id": "A1",
  "source": "MLS_A",
  "address": "123 Main St, Apt 4B",
  "city": "Springfield",
  "state": "VA",
  "zip": "22150",
  "price": 450000,
  "bedrooms": 2,
  "bathrooms": 1.5,
  "sqft": 980,
  "latitude": 38.7893,
  "longitude": -77.1873,
  "listedDate": "2026-08-29",
  "status": "active",
  "description": "Bright top-floor condo near shops and transit. Pet friendly."
}
```

## Future: RDS Integration

To migrate to AWS RDS Postgres:

1. Update `app/config.py` to read `DATABASE_URL` env var.
2. Implement `PostgresListingRepository` in `app/repositories/postgres_repository.py` using SQLAlchemy.
3. Update `app/dependencies.py` to use the Postgres repo.
4. **No changes** to filters, scoring, pagination, or SearchService.

The repository interface abstracts persistence, so the entire business logic layer remains testable and swappable.

## Testing

Run the full suite:

```bash
uv run pytest -v
```

**Coverage:**

- **Filters**: boundary conditions (price ranges, substring matching, case-insensitivity), composite filters.
- **Scoring**: price-fit, recency decay, no-budget fallback, tie-breaking.
- **Pagination**: full pages, partial pages, page beyond bounds, edge cases (empty list, page-size > total).
- **SearchService**: end-to-end filtering + scoring + ranking, validation (minPrice > maxPrice, invalid page/pageSize).
- **API**: HTTP status codes (200, 400, 422), response shape, error message format.

All tests use an in-memory repository seeded from `data/listings.json`, so no external dependencies (no Postgres required to run tests).

## Error Handling

Invalid input is caught and returned as structured errors (never a silent empty result or a 500):

| Error | Status | Example |
|-------|--------|---------|
| `minPrice > maxPrice` | 400 | `{"error": "...", "field": "minPrice"}` |
| `pageSize <= 0` | 400 | `{"error": "...", "field": "pageSize"}` |
| Non-numeric price | 422 | FastAPI/Pydantic validation error |
| City with no matches | 200 | `{"results": [], "totalResults": 0}` ← valid, not error |

## Performance Notes

- **Latency**: ~10-50ms per request (load JSON once, filter/score/paginate in Python on 12 records).
- **Memory**: ~1-2MB for dataset + service instances. Scales linearly with listing count until I/O or DB becomes the bottleneck.
- **Concurrency**: Stateless FastAPI app; run multiple worker processes via `uvicorn --workers N`.

## License

Internal exercise / interview project.
