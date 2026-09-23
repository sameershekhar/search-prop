import math
from datetime import date

from app.domain.models import Listing
from app.services.scoring import BudgetRecencyScorer

TODAY = date(2026, 9, 23)


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
        listed_date="2026-09-23",
        status="active",
        description="Charming home with a view.",
    )
    defaults.update(overrides)
    return Listing(**defaults)


class TestPriceFit:
    def test_price_matches_target_budget_exactly(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        listing = make_listing(price=500000, listed_date="2026-09-23")

        score = scorer.score(listing, target_budget=500000)

        # price_fit=1.0, recency_fit=1.0 (listed today) -> full score.
        assert score == 1.0

    def test_price_far_from_target_budget_lowers_score(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        near = make_listing(price=500000, listed_date="2026-09-23")
        far = make_listing(price=1000000, listed_date="2026-09-23")

        assert scorer.score(near, target_budget=500000) > scorer.score(
            far, target_budget=500000
        )

    def test_price_fit_clamped_at_zero_when_wildly_off_budget(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        listing = make_listing(price=10_000_000, listed_date="2026-09-23")

        score = scorer.score(listing, target_budget=100000)

        # price_fit clamps to 0, so only the recency component remains.
        assert score == BudgetRecencyScorer.RECENCY_WEIGHT

    def test_no_target_budget_falls_back_to_neutral_price_fit(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        cheap = make_listing(price=100000, listed_date="2026-09-23")
        expensive = make_listing(price=10_000_000, listed_date="2026-09-23")

        assert scorer.score(cheap, target_budget=None) == scorer.score(
            expensive, target_budget=None
        )


class TestRecencyFit:
    def test_more_recent_listing_scores_higher(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        newer = make_listing(listed_date="2026-09-20")
        older = make_listing(listed_date="2026-08-01")

        assert scorer.score(newer, target_budget=None) > scorer.score(
            older, target_budget=None
        )

    def test_listed_today_gives_full_recency_component(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        listing = make_listing(listed_date="2026-09-23")

        score = scorer.score(listing, target_budget=None)

        assert math.isclose(score, 1.0)

    def test_decay_matches_documented_formula(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        listing = make_listing(listed_date="2026-08-24")  # 30 days before TODAY

        score = scorer.score(listing, target_budget=None)
        expected_recency = math.exp(-30 / BudgetRecencyScorer.RECENCY_DECAY_DAYS)
        # No target_budget => price_fit is neutral (1.0), so the full score
        # is price_weight*1.0 + recency_weight*expected_recency.
        expected_score = (
            BudgetRecencyScorer.PRICE_WEIGHT
            + BudgetRecencyScorer.RECENCY_WEIGHT * expected_recency
        )

        assert math.isclose(score, expected_score, rel_tol=1e-9)


class TestTieBreaking:
    def test_equal_price_and_date_produce_equal_scores(self):
        scorer = BudgetRecencyScorer(today=TODAY)
        a = make_listing(id="A", price=500000, listed_date="2026-09-10")
        b = make_listing(id="B", price=500000, listed_date="2026-09-10")

        assert scorer.score(a, target_budget=500000) == scorer.score(
            b, target_budget=500000
        )
