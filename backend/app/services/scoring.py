import math
from abc import ABC, abstractmethod
from datetime import date, datetime

from app.models import Listing


class ScoringStrategy(ABC):
    """Strategy interface for ranking a listing. Swap the implementation to
    change how relevance is computed without touching SearchService."""

    @abstractmethod
    def score(self, listing: Listing, target_budget: float | None) -> float:
        raise NotImplementedError


class BudgetRecencyScorer(ScoringStrategy):
    """Relevance = weighted blend of "how close is the price to the buyer's
    target budget" and "how recently was this listed".

    Both components are normalized to [0, 1] so the weights below are
    directly interpretable as relative importance. See backend/README.md
    for the reasoning and trade-offs behind this specific formula.
    """

    PRICE_WEIGHT = 0.7
    RECENCY_WEIGHT = 0.3
    RECENCY_DECAY_DAYS = 30.0

    def __init__(self, today: date | None = None):
        # Injectable "today" keeps recency scoring deterministic in tests.
        self._today = today or date.today()

    def score(self, listing: Listing, target_budget: float | None) -> float:
        price_fit = self._price_fit(listing.price, target_budget)
        recency_fit = self._recency_fit(listing.listed_date)
        return self.PRICE_WEIGHT * price_fit + self.RECENCY_WEIGHT * recency_fit

    @staticmethod
    def _price_fit(price: float, target_budget: float | None) -> float:
        if not target_budget:
            # No budget supplied: don't penalize any listing on price.
            return 1.0
        diff_ratio = abs(price - target_budget) / target_budget
        return max(0.0, 1.0 - diff_ratio)

    def _recency_fit(self, listed_date: str) -> float:
        listed = datetime.strptime(listed_date, "%Y-%m-%d").date()
        days_since = max(0, (self._today - listed).days)
        return math.exp(-days_since / self.RECENCY_DECAY_DAYS)
