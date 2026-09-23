from app.models import Listing
from app.services.filters import (
    CityFilter,
    CompositeFilter,
    KeywordFilter,
    MinBedroomsFilter,
    PriceRangeFilter,
)


def make_listing(**overrides) -> Listing:
    defaults = dict(
        id="X1",
        source="MLS_X",
        address="1 Test St",
        city="Testville",
        state="VA",
        zip="00000",
        price=500000,
        bedrooms=3,
        bathrooms=2.0,
        sqft=1500,
        latitude=0.0,
        longitude=0.0,
        listed_date="2026-09-01",
        status="active",
        description="Charming home with a view.",
    )
    defaults.update(overrides)
    return Listing(**defaults)


class TestPriceRangeFilter:
    def test_within_range_matches(self):
        f = PriceRangeFilter(min_price=400000, max_price=600000)
        assert f.matches(make_listing(price=500000)) is True

    def test_at_min_boundary_is_inclusive(self):
        f = PriceRangeFilter(min_price=500000, max_price=None)
        assert f.matches(make_listing(price=500000)) is True

    def test_at_max_boundary_is_inclusive(self):
        f = PriceRangeFilter(min_price=None, max_price=500000)
        assert f.matches(make_listing(price=500000)) is True

    def test_below_min_excluded(self):
        f = PriceRangeFilter(min_price=500000, max_price=None)
        assert f.matches(make_listing(price=499999)) is False

    def test_above_max_excluded(self):
        f = PriceRangeFilter(min_price=None, max_price=500000)
        assert f.matches(make_listing(price=500001)) is False

    def test_no_bounds_matches_everything(self):
        f = PriceRangeFilter(min_price=None, max_price=None)
        assert f.matches(make_listing(price=1)) is True


class TestMinBedroomsFilter:
    def test_meets_minimum(self):
        assert MinBedroomsFilter(3).matches(make_listing(bedrooms=3)) is True

    def test_below_minimum_excluded(self):
        assert MinBedroomsFilter(4).matches(make_listing(bedrooms=3)) is False

    def test_none_is_no_op(self):
        assert MinBedroomsFilter(None).matches(make_listing(bedrooms=0)) is True


class TestCityFilter:
    def test_case_insensitive_match(self):
        assert CityFilter("springfield").matches(make_listing(city="Springfield")) is True

    def test_whitespace_tolerant_match(self):
        assert CityFilter(" Springfield ").matches(make_listing(city="Springfield")) is True

    def test_no_match(self):
        assert CityFilter("Reston").matches(make_listing(city="Springfield")) is False

    def test_none_is_no_op(self):
        assert CityFilter(None).matches(make_listing(city="Anywhere")) is True

    def test_empty_string_is_no_op(self):
        assert CityFilter("").matches(make_listing(city="Anywhere")) is True


class TestKeywordFilter:
    def test_case_insensitive_substring_match(self):
        listing = make_listing(description="Pet friendly condo near transit.")
        assert KeywordFilter("PET FRIENDLY").matches(listing) is True

    def test_no_match(self):
        listing = make_listing(description="No pets allowed.")
        assert KeywordFilter("garage").matches(listing) is False

    def test_none_is_no_op(self):
        assert KeywordFilter(None).matches(make_listing()) is True


class TestCompositeFilter:
    def test_all_filters_must_match(self):
        composite = CompositeFilter(
            [
                PriceRangeFilter(min_price=400000, max_price=600000),
                MinBedroomsFilter(3),
                CityFilter("Springfield"),
            ]
        )
        matching = make_listing(price=500000, bedrooms=3, city="Springfield")
        non_matching = make_listing(price=500000, bedrooms=2, city="Springfield")

        assert composite.matches(matching) is True
        assert composite.matches(non_matching) is False

    def test_apply_filters_a_list(self):
        composite = CompositeFilter([MinBedroomsFilter(3)])
        listings = [make_listing(id="A", bedrooms=3), make_listing(id="B", bedrooms=2)]

        result = composite.apply(listings)

        assert [l.id for l in result] == ["A"]

    def test_empty_filter_list_matches_everything(self):
        composite = CompositeFilter([])
        assert composite.matches(make_listing()) is True
