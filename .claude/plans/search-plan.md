# Listing Search Service — Implementation Plan

## Context

This is a take-home/live-interview exercise: build a full-stack property listing
search service (FastAPI backend + React frontend) over ~12 sample listings, backed
by AWS RDS Postgres. During the live session, the interviewer will introduce new
requirements on top of this design, so the architecture must be easy to extend
(new filters, new scoring factors, new endpoints) without rewrites — this drives
the emphasis on Strategy pattern, Repository pattern, and strict separation of
concerns (SRP) below.

The project currently only has a placeholder scaffold (`pyproject.toml`, empty
`main.py`, empty `README.md`, git initialized). Everything else is new.

## Decisions from clarification

- Backend: **FastAPI** (Pydantic validation, auto docs, async-ready, easy to test with `TestClient`).
- Frontend: **Vite + React**, plain JS (no TypeScript required).
- Persistence: **AWS RDS Postgres**, connection details supplied via env var (`DATABASE_URL`); RDS instance already provisioned by the user — no infra/provisioning steps in this plan.
- Data access: **Repository interface** (`ListingRepository` ABC) with a `PostgresListingRepository` implementation (SQLAlchemy Core/ORM) for production and an `InMemoryListingRepository` for tests — keeps filtering/scoring logic decoupled from persistence.
- Query strategy: Repository's only job is to fetch rows (`get_all()`); **all filtering, scoring, sorting, and pagination happen in Python** in a service layer, since the ranking formula is custom and not naturally SQL-expressible, and the dataset is tiny.
- Tests: **Backend pytest suite only** (core logic — filters, scoring, pagination, validation). Frontend verified manually by running the app.

## Project structure

Keep the existing root `pyproject.toml` as the backend's Python project (it's
already named `searchprop`); add a `frontend/` sibling directory for the Vite
React app. Final layout:

```
SearchProp/
  app/                        # backend package
    main.py                   # FastAPI app factory, CORS, router registration
    config.py                 # Settings (DATABASE_URL, CORS origins) via pydantic-settings
    domain/
      models.py                # Listing domain model (frozen dataclass or Pydantic model)
    repositories/
      base.py                  # ListingRepository ABC: get_all() -> list[Listing]
      postgres_repository.py   # SQLAlchemy-backed implementation
      in_memory_repository.py  # Simple list-backed implementation (used by tests, and optionally as a fallback/dev mode)
    db/
      models.py                 # SQLAlchemy ORM table definition (listings)
      session.py                 # engine + session factory from Settings.DATABASE_URL
      seed.py                    # one-off script: load sample_listings.json into Postgres
    services/
      filters.py                # Filter Strategy interface + concrete filters (PriceRangeFilter, MinBedroomsFilter, CityFilter, KeywordFilter) + a CompositeFilter that ANDs them
      scoring.py                 # ScoringStrategy interface + BudgetRecencyScorer implementation
      pagination.py              # Paginator: slices a sorted list given page/pageSize, returns page metadata
      search_service.py          # Orchestrator: repo.get_all() -> validate params -> filter -> score -> sort -> paginate -> DTO
      exceptions.py              # InvalidSearchParamsError and similar domain exceptions
    api/
      schemas.py                 # Pydantic request/response models (SearchResponse, ListingResult, ErrorResponse)
      routes.py                  # GET /api/listings/search endpoint, wires SearchService via DI
      error_handlers.py          # Maps domain exceptions -> 400 JSON responses
  tests/
    conftest.py                  # fixtures: sample listing dataset, InMemoryListingRepository, TestClient
    test_filters.py
    test_scoring.py
    test_pagination.py
    test_search_service.py       # integration of the above via SearchService + InMemoryListingRepository
    test_api.py                  # HTTP-level tests (status codes, error payloads, response shape)
  frontend/
    src/
      api/searchClient.js         # fetch wrapper for GET /api/listings/search, throws on non-2xx
      components/
        SearchForm.jsx             # controlled inputs: minPrice, maxPrice, minBedrooms, city, keyword, targetBudget, pageSize
        ResultsTable.jsx           # renders address, price, bedrooms, score for current page
        Pagination.jsx             # prev/next + page indicator, disabled at boundaries
        StatusMessage.jsx          # shared loading / error / no-results banner
      App.jsx                      # owns search state, calls API on submit/page change, renders states
      main.jsx
    index.html, package.json, vite.config.js
  sample_listings.json          # provided dataset (copied in), consumed only by db/seed.py
  pyproject.toml                # updated deps: fastapi, uvicorn, sqlalchemy, psycopg[binary], pydantic-settings, pytest, httpx
  README.md                     # setup steps, env vars, scoring approach & trade-offs
  .env.example                  # DATABASE_URL=postgresql+psycopg://user:pass@rds-host:5432/searchprop
```

## Backend design details

**Domain model** (`domain/models.py`): a plain `Listing` value object mirroring the
JSON schema (id, source, address, city, state, zip, price, bedrooms, bathrooms,
sqft, latitude, longitude, listedDate, status, description). This is what flows
through the service layer — persistence and API layers each map to/from it, so
neither SQLAlchemy nor Pydantic leaks into business logic (SRP).

**Repository layer** (`repositories/`):
- `ListingRepository` ABC defines `get_all() -> list[Listing]`.
- `PostgresListingRepository` opens a session (via `db/session.py`), runs a
  simple `SELECT *`, maps ORM rows to `Listing` domain objects.
- `InMemoryListingRepository` takes a list of `Listing` in its constructor —
  used by every backend test, so tests never touch a real database.
- `db/seed.py` is a standalone script (`python -m app.db.seed`) that creates the
  table (if missing) and upserts rows from `sample_listings.json`. Documented in
  README as a one-time setup step against the RDS instance.

**Filter strategies** (`services/filters.py`) — Strategy pattern, one class per
filter dimension, each implementing a common `matches(listing) -> bool`:
- `PriceRangeFilter(min_price, max_price)`
- `MinBedroomsFilter(min_bedrooms)`
- `CityFilter(city)` — case-insensitive exact/substring match to tolerate minor
  inconsistencies between feeds
- `KeywordFilter(keyword)` — case-insensitive substring match against `description`
- `CompositeFilter(filters: list[Filter])` — ANDs all active filters together;
  only filters for params the user actually supplied are included, so omitted
  params impose no constraint.

This makes adding a live-session filter requirement (e.g. `maxBedrooms`,
`status`) a matter of adding one new Filter class, not touching orchestration
code.

**Scoring strategy** (`services/scoring.py`) — Strategy pattern via a
`ScoringStrategy` ABC with `score(listing, target_budget) -> float`, concrete
implementation `BudgetRecencyScorer`:
- **Price-fit component**: `max(0, 1 - abs(price - targetBudget) / targetBudget)`
  when `targetBudget` is supplied (clamped to [0, 1]); if `targetBudget` is
  omitted, price-fit is treated as neutral (constant 1.0) so ranking falls back
  to pure recency.
- **Recency component**: exponential decay against days-since-listed,
  `exp(-days_since_listed / DECAY_DAYS)` with `DECAY_DAYS = 30` as a named,
  documented constant — newer listings score closer to 1, older ones decay
  smoothly rather than dropping off a cliff.
- **Combined score**: weighted sum, `0.7 * price_fit + 0.3 * recency`, weights
  as named constants on the class so they're trivially tunable if the
  interviewer asks to change the weighting live.
- Tie-breaking: when scores are equal (e.g. duplicate listings from different
  MLS sources), sort is stable and falls back to `listedDate desc, id asc` so
  ordering is deterministic and testable.

**Pagination** (`services/pagination.py`): a `Paginator` that takes the
already-filtered-and-scored, sorted list plus `page`/`pageSize`, returns the
page slice and metadata (`totalResults`, `totalPages`, `page`, `pageSize`).
Pure function/class, no I/O — easy to unit test boundary cases (page beyond
last page → empty slice, not an error; last partial page; pageSize larger than
total results).

**Validation & error handling**:
- Input validation happens at two levels: Pydantic query-param types/bounds at
  the API layer (e.g. `pageSize: int = Query(gt=0)`) catch structurally invalid
  input (non-numeric, negative) automatically as FastAPI 422s; cross-field
  business rules (`minPrice > maxPrice`) are checked explicitly in
  `SearchService` and raise `InvalidSearchParamsError`, mapped by
  `error_handlers.py` to a `400` with a clear `{ "error": "...", "field": "..." }`
  body — never a silent empty result or a 500.
- A city/keyword with no matches is **not** an error — it's a valid empty
  result set (`200` with `results: []`, `totalResults: 0`), since that's a
  legitimate search outcome, not invalid input. This distinction is called out
  explicitly in the README.

**SearchService orchestration** (`services/search_service.py`): the only class
that knows the full pipeline — validate params → `repo.get_all()` → build
`CompositeFilter` from supplied params → filter → score each surviving listing
→ sort by score desc (with tiebreak) → paginate → map to response DTOs. This is
the seam most likely to gain a new step during the live session (e.g. a new
ranking factor), so it's kept thin and delegates each step to its own class.

**API layer** (`api/`): single endpoint
`GET /api/listings/search` with query params `minPrice, maxPrice, minBedrooms,
city, keyword, targetBudget, page, pageSize`. Response schema includes, per
result, at minimum `address, price, bedrooms, score` plus the rest of the
listing fields for a richer UI. `SearchService` and the repository are wired
via FastAPI `Depends()` so tests can override the repository dependency with
`InMemoryListingRepository`.

## Frontend design details

- `SearchForm.jsx`: controlled form with all filter/ranking inputs plus a page
  size selector; validates nothing client-side beyond basic number parsing —
  server is the source of truth for validation errors, which the form surfaces
  inline.
- `searchClient.js`: single function `searchListings(params)` that builds the
  query string, fetches, and throws a typed error (with the server's message)
  on non-2xx so `App.jsx` can distinguish "validation error" from "network
  error."
- `App.jsx`: owns `{status: 'idle'|'loading'|'success'|'error', results, page, error}`
  state; re-fetches on form submit and on page change; renders `StatusMessage`
  for loading/error/no-results, otherwise `ResultsTable` + `Pagination`.
- `ResultsTable.jsx` / `Pagination.jsx`: presentational, no fetching logic —
  keeps components single-responsibility and easy to reason about when a live
  requirement changes the display (e.g. "also show sqft").

## Testing plan (pytest, `tests/`)

- `test_filters.py`: each filter individually (inclusive boundaries at
  min/max price, case-insensitive city/keyword match, no-op when param
  omitted) + `CompositeFilter` combining several.
- `test_scoring.py`: price-fit at exact target budget (=1.0), far from budget
  (→0), no targetBudget supplied (neutral fallback); recency decay ordering
  for two listings with different `listedDate`; tie-break ordering for equal
  scores.
- `test_pagination.py`: empty input list, page beyond last page, exact
  last-partial-page slice, pageSize larger than result count, pageSize ≤ 0
  raises.
- `test_search_service.py`: end-to-end through the service using
  `InMemoryListingRepository` seeded from `sample_listings.json` — covers
  "no matches for city," "minPrice > maxPrice raises," "keyword matches
  description case-insensitively," ranking order with a given targetBudget.
- `test_api.py`: `TestClient` against the FastAPI app with the repository
  dependency overridden to the in-memory one — asserts status codes (200 for
  no-matches, 400 for invalid params) and response JSON shape.
- No test touches the real RDS instance; `PostgresListingRepository` and
  `db/seed.py` are exercised manually (documented as a manual verification
  step) since credentials are environment-specific.

## README contents

- Setup: `uv sync` / `pip install -e .`, set `DATABASE_URL` (from
  `.env.example`), run `python -m app.db.seed` once, `uvicorn app.main:app --reload`;
  separately `cd frontend && npm install && npm run dev`.
- Scoring approach: explain the price-fit + recency-decay formula, the chosen
  weights, and why (documents them as tunable, calls out that it's a
  deliberately simple, explainable heuristic rather than a "correct" formula).
- Trade-offs: Python-side filtering/scoring instead of SQL (simplicity at this
  data scale vs. not scaling to large datasets); no caching of `get_all()` per
  request; city/keyword matching is simple substring match rather than fuzzy
  matching, given the small, inconsistent-but-similar sample data.

## Verification

1. Backend: `pytest` (all suites above) green.
2. Manual: start Postgres-backed API, run `db/seed.py`, hit
   `GET /api/listings/search?city=Springfield&minPrice=400000&maxPrice=500000&targetBudget=450000&page=1&pageSize=5`
   via curl/browser, confirm ranked JSON.
3. Manual: start frontend dev server, run a search through the UI, confirm
   loading → results render, confirm a deliberately invalid input (e.g.
   minPrice > maxPrice) surfaces the server's error message, confirm a
   city with no matches shows a "no results" state, confirm pagination
   controls move between pages and disable at boundaries.
