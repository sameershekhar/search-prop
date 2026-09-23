from fastapi.testclient import TestClient


class TestSearchEndpoint:
    def test_returns_ranked_results(self, client: TestClient):
        response = client.get(
            "/api/listings/search",
            params={"city": "Springfield", "targetBudget": 450000},
        )

        assert response.status_code == 200
        body = response.json()
        assert body["totalResults"] == 4
        assert [r["id"] for r in body["results"]] == ["A1", "B7", "A2", "B8"]
        assert set(body["results"][0].keys()) >= {"address", "price", "bedrooms", "score"}

    def test_no_matches_returns_empty_list_not_error(self, client: TestClient):
        response = client.get(
            "/api/listings/search", params={"city": "Nowhereville"}
        )

        assert response.status_code == 200
        body = response.json()
        assert body["results"] == []
        assert body["totalResults"] == 0

    def test_default_pagination_returns_first_page(self, client: TestClient):
        response = client.get("/api/listings/search")

        assert response.status_code == 200
        body = response.json()
        assert body["page"] == 1
        assert body["pageSize"] == 10
        assert body["totalResults"] == 12
        assert len(body["results"]) == 10

    def test_pagination_moves_between_pages(self, client: TestClient):
        first = client.get(
            "/api/listings/search", params={"page": 1, "pageSize": 5}
        ).json()
        second = client.get(
            "/api/listings/search", params={"page": 2, "pageSize": 5}
        ).json()

        first_ids = {r["id"] for r in first["results"]}
        second_ids = {r["id"] for r in second["results"]}
        assert first_ids.isdisjoint(second_ids)

    def test_min_price_greater_than_max_price_returns_400(self, client: TestClient):
        response = client.get(
            "/api/listings/search",
            params={"minPrice": 600000, "maxPrice": 400000},
        )

        assert response.status_code == 400
        body = response.json()
        assert body["field"] == "minPrice"
        assert "error" in body

    def test_page_size_zero_returns_400(self, client: TestClient):
        response = client.get("/api/listings/search", params={"pageSize": 0})

        assert response.status_code == 400
        assert response.json()["field"] == "pageSize"

    def test_non_numeric_price_returns_422(self, client: TestClient):
        # Structurally invalid input (wrong type) is caught by FastAPI/Pydantic
        # query validation before it ever reaches SearchService.
        response = client.get(
            "/api/listings/search", params={"minPrice": "not-a-number"}
        )

        assert response.status_code == 422
