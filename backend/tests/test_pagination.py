import pytest

from app.services.pagination import Paginator


class TestPaginator:
    def test_first_page_full(self):
        items = list(range(10))

        page = Paginator.paginate(items, page=1, page_size=4)

        assert page.items == [0, 1, 2, 3]
        assert page.total_results == 10
        assert page.total_pages == 3

    def test_last_partial_page(self):
        items = list(range(10))

        page = Paginator.paginate(items, page=3, page_size=4)

        assert page.items == [8, 9]
        assert page.total_pages == 3

    def test_page_beyond_last_page_is_empty_not_error(self):
        items = list(range(10))

        page = Paginator.paginate(items, page=99, page_size=4)

        assert page.items == []
        assert page.total_results == 10
        assert page.total_pages == 3

    def test_empty_input_list(self):
        page = Paginator.paginate([], page=1, page_size=10)

        assert page.items == []
        assert page.total_results == 0
        assert page.total_pages == 0

    def test_page_size_larger_than_result_count(self):
        items = list(range(3))

        page = Paginator.paginate(items, page=1, page_size=50)

        assert page.items == [0, 1, 2]
        assert page.total_pages == 1

    def test_page_size_zero_raises(self):
        with pytest.raises(ValueError):
            Paginator.paginate([1, 2, 3], page=1, page_size=0)

    def test_negative_page_size_raises(self):
        with pytest.raises(ValueError):
            Paginator.paginate([1, 2, 3], page=1, page_size=-5)

    def test_page_zero_raises(self):
        with pytest.raises(ValueError):
            Paginator.paginate([1, 2, 3], page=0, page_size=10)

    def test_negative_page_raises(self):
        with pytest.raises(ValueError):
            Paginator.paginate([1, 2, 3], page=-1, page_size=10)
