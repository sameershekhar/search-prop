# Frontend Specification — Listing Search Service

## 1. Objective & Technology

Build a simple, readable, interview-friendly React frontend for the Listing Search Service.

**Technology**

* React + Vite
* JavaScript
* Native `fetch` for API calls
* No unnecessary UI/state-management libraries
* Responsive CSS

The frontend must call the real FastAPI backend and render real listing results.

---

## 2. Project Structure & Responsibilities

```text
frontend/
├── src/
│   ├── api/
│   │   └── searchClient.js
│   ├── components/
│   │   ├── SearchForm.jsx
│   │   ├── ResultsCard.jsx
│   │   ├── ResultsList.jsx
│   │   ├── Pagination.jsx
│   │   └── StatusMessage.jsx
│   ├── App.jsx
│   └── main.jsx
├── package.json
├── vite.config.js
└── index.html
```

### Responsibilities

**App.jsx**

* Own application state.
* Own current page and page size.
* Trigger searches.
* Handle loading, success, empty, and error states.
* Pass data to child components.

**SearchForm.jsx**

* Controlled inputs for all search parameters.
* Handle form submission.
* Perform only basic client-side validation.
* Notify `App` when search is submitted.

**searchClient.js**

* Build query parameters.
* Call `GET /api/listings/search`.
* Parse successful responses.
* Convert non-2xx responses into a usable frontend error.

**ResultsCard.jsx**

* Display one listing.
* Presentational only.
* No API calls or search logic.

**ResultsList.jsx**

* Render the collection of listing cards.
* Handle empty result rendering through the appropriate UI state.

**Pagination.jsx**

* Display Previous/Next and page information.
* Use backend pagination metadata.
* No API calls directly.

**StatusMessage.jsx**

* Display loading, error, and no-results messages.

---

## 3. Search Form & API Integration

### Search Inputs

The form must provide inputs for:

| Field         | API Parameter  |
| ------------- | -------------- |
| Min Price     | `minPrice`     |
| Max Price     | `maxPrice`     |
| Min Bedrooms  | `minBedrooms`  |
| City          | `city`         |
| Keyword       | `keyword`      |
| Target Budget | `targetBudget` |
| Page Size     | `pageSize`     |

`page` is controlled internally by the application and should not be entered by the user.

### API

```text
GET /api/listings/search
```

Example:

```text
/api/listings/search?minPrice=400000&maxPrice=550000&minBedrooms=2&city=Springfield&keyword=condo&targetBudget=450000&page=1&pageSize=5
```

### Request Rules

* Omit optional parameters when the user leaves them empty.
* Convert numeric inputs to numbers before sending.
* Reset `page` to `1` whenever a new search is submitted.
* Preserve all active filters when changing pages.
* API base URL must be configurable through the frontend environment/configuration.

The backend remains the source of truth for validation.

---

## 4. Results & Card-Based Layout

Use a **vertical card-based layout**, not a table.

### Overall Layout

```text
+----------------------------------------------------------------+
|                    Listing Search Service                      |
+----------------------------------------------------------------+
| Search Filters                                                 |
|                                                                |
| Min Price    Max Price    Min Bedrooms    City                 |
| Keyword      Target Budget  Page Size              [ Search ]  |
+----------------------------------------------------------------+

Search Results (12 listings)
──────────────────────────────────────────────────────────────────

┌────────────────────────────────────────────────────────────────┐
│ 123 Main Street, Unit 4B                         $452,000      │
│ Springfield, VA 22150                           Relevance: 0.95│
│                                                                │
│ 🛏 2 Bedrooms    🛁 1.5 Bathrooms    📐 980 sqft               │
│                                                                │
│ Source: MLS_B     Status: Active     Listed: Aug 27, 2026      │
│                                                                │
│ Location: 38.7893, -77.1873                                   │
│                                                                │
│ ID: B7                                                        │
│                                                                │
│ "Top floor condo, walk to shopping. Pets allowed."             │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Another Property                                  $525,000    │
│ Springfield, VA 22150                           Relevance: 0.81│
│                                                                │
│ 🛏 3 Bedrooms    🛁 2.0 Bathrooms    📐 1,450 sqft              │
│                                                                │
│ Source: MLS_A     Status: Active     Listed: Sep 02, 2026      │
│                                                                │
│ Location: 38.7901, -77.1802                                   │
│                                                                │
│ ID: A2                                                        │
│                                                                │
│ "Updated kitchen, fenced yard, close to schools."              │
└────────────────────────────────────────────────────────────────┘

                       [ Previous ]
                    Page 1 of 3
                          [ Next ]
```

### Listing Card

Every listing result should display all returned listing fields:

```text
┌──────────────────────────────────────────────────────────────┐
│ Address                                      Price            │
│ City, State ZIP                              Relevance Score  │
├──────────────────────────────────────────────────────────────┤
│ Bedrooms     Bathrooms     Sqft                              │
├──────────────────────────────────────────────────────────────┤
│ ID           Source        Status        Listed Date          │
│ Latitude     Longitude                                         │
├──────────────────────────────────────────────────────────────┤
│ Description                                                    │
└──────────────────────────────────────────────────────────────┘
```

### Field Mapping

| Backend Field    | Frontend Display         |
| ---------------- | ------------------------ |
| `id`             | ID                       |
| `source`         | Source                   |
| `address`        | Card title               |
| `city`           | City                     |
| `state`          | State                    |
| `zip`            | ZIP                      |
| `price`          | Prominent currency value |
| `bedrooms`       | Bedrooms                 |
| `bathrooms`      | Bathrooms                |
| `sqft`           | Square feet              |
| `latitude`       | Latitude                 |
| `longitude`      | Longitude                |
| `listedDate`     | Listed date              |
| `status`         | Status badge             |
| `description`    | Description              |
| `relevanceScore` | Relevance score          |

### Visual Priority

**Primary**

* Address
* Price
* Relevance score

**Secondary**

* City/state/ZIP
* Bedrooms
* Bathrooms
* Sqft
* Status
* Listed date

**Technical metadata**

* ID
* Source
* Latitude
* Longitude

**Description**

* Display at the bottom of the card.

The UI should use simple formatting such as `$452,000`, `980 sqft`, and a readable date.

---

## 5. Application States, Pagination & Error Handling

### Application States

`App.jsx` should support:

```text
idle
loading
success
error
```

For `success` with zero results, show a dedicated:

```text
No listings found matching your criteria.
```

### Loading

While the API request is running:

```text
Searching listings...
```

The UI should prevent confusing duplicate searches while loading.

### Error

Display a readable error message when:

* API is unavailable.
* Request fails.
* Backend returns a validation error such as `minPrice > maxPrice`.
* Unexpected response is received.

Do not expose raw stack traces to the user.

### Pagination

Use the backend pagination response:

```text
page
pageSize
totalResults
totalPages
hasNext
hasPrevious
```

Display:

```text
[ Previous ]    Page 1 of 3    [ Next ]
```

Rules:

* Disable Previous on the first page.
* Disable Next on the last page.
* Changing page triggers a new API request.
* Current filters must remain unchanged.
* If the backend returns an empty page beyond the final page, display the empty results state without crashing.

---

## 6. Design, Extensibility & Acceptance Criteria

### Design Principles

* Keep the UI simple and professional.
* Prefer readability over visual complexity.
* Use reusable components.
* Keep API logic outside React presentation components.
* Keep business logic in the backend.
* Avoid unnecessary state-management or UI libraries.
* Use basic responsive CSS.
* Provide basic accessibility:

  * labels for inputs
  * buttons with clear text
  * keyboard-accessible controls
  * readable error messages

### Extensibility

The frontend structure should make future requirements easy to add, for example:

* New search filter → add form field and API parameter.
* New listing field → update `ResultsCard`.
* New sorting option → add form control and API parameter.
* New result presentation → replace or extend `ResultsCard`.
* New API endpoint → add a separate API client function.

Do not introduce abstractions that are not currently needed.

### Acceptance Criteria

The frontend is complete when:

1. React/Vite application starts successfully.
2. Search form contains all required search inputs.
3. Form calls the real FastAPI search endpoint.
4. Backend results are rendered as listing cards.
5. Every returned listing field is displayed.
6. Relevance score is displayed.
7. Pagination works using backend metadata.
8. Filters are preserved while navigating pages.
9. Loading, no-results, and error states work.
10. Invalid backend validation errors are shown clearly.
11. UI is readable and responsive.
12. Frontend contains no hardcoded listing data.
13. No unnecessary libraries or architectural complexity are introduced.
14. Existing backend code/API is not modified unless integration requires a documented change.
