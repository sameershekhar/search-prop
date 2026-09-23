from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Page(Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total_results: int
    total_pages: int


class Paginator:
    """Pure, I/O-free slicing of an already-ordered list. Owns pagination's
    own invariants (page/pageSize must be positive); business-rule
    validation for the wider search request lives in SearchService."""

    @staticmethod
    def paginate(items: list[T], page: int, page_size: int) -> Page[T]:
        if page_size <= 0:
            raise ValueError("pageSize must be greater than 0")
        if page <= 0:
            raise ValueError("page must be greater than 0")

        total_results = len(items)
        total_pages = -(-total_results // page_size) if total_results else 0

        start = (page - 1) * page_size
        end = start + page_size

        return Page(
            items=items[start:end],
            page=page,
            page_size=page_size,
            total_results=total_results,
            total_pages=total_pages,
        )
