class InvalidSearchParamsError(Exception):
    """Raised when search parameters are structurally valid but violate a
    business rule (e.g. minPrice > maxPrice). Mapped to an HTTP 400 by the
    API layer - never a crash or a silently wrong result.
    """

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.message = message
        self.field = field
