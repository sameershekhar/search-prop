function Pagination({ page, totalPages, onPageChange, disabled }) {
  const hasPrevious = page > 1;
  const hasNext = page < totalPages;

  return (
    <nav className="pagination" aria-label="Search results pages">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={disabled || !hasPrevious}
      >
        Previous
      </button>
      <span className="pagination__label">
        Page {page} of {totalPages}
      </span>
      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={disabled || !hasNext}
      >
        Next
      </button>
    </nav>
  );
}

export default Pagination;
