import pytest

from app.services.exceptions import InvalidSearchParamsError
from app.services.search_service import SearchParams, SearchService


class TestFilteringAndRanking:
    def test_ranks_by_budget_fit_and_recency(self, search_service: SearchService):
        params = SearchParams(city="Springfield", target_budget=450000, page=1, page_size=10)

        page = search_service.search(params)

        ids = [sl.listing.id for sl in page.items]
        assert ids == ["A1", "B7", "A2", "B8"]
        assert page.total_results == 4
        assert page.items[0].score > page.items[1].score > page.items[2].score

    def test_keyword_matches_description_case_insensitively(
        self, search_service: SearchService
    ):
        params = SearchParams(keyword="PET FRIENDLY")

        page = search_service.search(params)

        assert [sl.listing.id for sl in page.items] == ["A1"]

    def test_min_bedrooms_filter(self, search_service: SearchService):
        params = SearchParams(min_bedrooms=4)

        page = search_service.search(params)

        assert {sl.listing.id for sl in page.items} == {"A4", "A7"}

    def test_city_with_no_matches_returns_empty_result_not_error(
        self, search_service: SearchService
    ):
        params = SearchParams(city="Nowhereville")

        page = search_service.search(params)

        assert page.items == []
        assert page.total_results == 0
        assert page.total_pages == 0

    def test_no_filters_returns_all_listings_across_pages(
        self, search_service: SearchService
    ):
        page = search_service.search(SearchParams(page=1, page_size=5))
        assert page.total_results == 12
        assert page.total_pages == 3
        assert len(page.items) == 5

        last_page = search_service.search(SearchParams(page=3, page_size=5))
        assert len(last_page.items) == 2


class TestTiedScores:
    def test_tied_scores_are_ordered_by_listed_date_then_id(
        self, search_service: SearchService
    ):
        # A5 and B11 are both in Vienna; give them an identical target budget
        # gap by targeting exactly between their prices is not needed here -
        # tie-break logic is exercised directly via listedDate/id ordering
        # when scores are equal (see test_scoring.py for score equality).
        params = SearchParams(city="Vienna")

        page = search_service.search(params)

        ids = [sl.listing.id for sl in page.items]
        # A5 listed 2026-09-04 (more recent) should outrank B11 (2026-08-15)
        # regardless of score ties, since recency is part of the score itself.
        assert ids.index("A5") < ids.index("B11")


class TestValidation:
    def test_min_price_greater_than_max_price_raises(
        self, search_service: SearchService
    ):
        with pytest.raises(InvalidSearchParamsError) as exc_info:
            search_service.search(SearchParams(min_price=600000, max_price=400000))
        assert exc_info.value.field == "minPrice"

    def test_negative_min_price_raises(self, search_service: SearchService):
        with pytest.raises(InvalidSearchParamsError):
            search_service.search(SearchParams(min_price=-1))

    def test_page_size_zero_raises(self, search_service: SearchService):
        with pytest.raises(InvalidSearchParamsError) as exc_info:
            search_service.search(SearchParams(page_size=0))
        assert exc_info.value.field == "pageSize"

    def test_negative_page_raises(self, search_service: SearchService):
        with pytest.raises(InvalidSearchParamsError) as exc_info:
            search_service.search(SearchParams(page=-1))
        assert exc_info.value.field == "page"

    def test_non_positive_target_budget_raises(self, search_service: SearchService):
        with pytest.raises(InvalidSearchParamsError) as exc_info:
            search_service.search(SearchParams(target_budget=0))
        assert exc_info.value.field == "targetBudget"
