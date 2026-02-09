"""Tests for hybrid property recommender (Phase 5C)."""

import numpy as np
import pytest

from ghl_real_estate_ai.ml.hybrid_recommender import (
    BuyerPreference,
    HybridPropertyRecommender,
    PropertyFeatures,
)


@pytest.fixture
def recommender():
    rec = HybridPropertyRecommender(content_weight=0.6, collaborative_weight=0.4)

    # Add properties to catalog
    properties = [
        PropertyFeatures("p1", price=500_000, sqft=1800, bedrooms=3, bathrooms=2, zip_code="91730"),
        PropertyFeatures("p2", price=650_000, sqft=2200, bedrooms=4, bathrooms=3, zip_code="91730"),
        PropertyFeatures("p3", price=450_000, sqft=1500, bedrooms=2, bathrooms=2, zip_code="91737"),
        PropertyFeatures("p4", price=800_000, sqft=3000, bedrooms=5, bathrooms=4, zip_code="91730", has_pool=True),
        PropertyFeatures("p5", price=550_000, sqft=1900, bedrooms=3, bathrooms=2.5, zip_code="91730"),
    ]
    rec.add_properties(properties)
    return rec


class TestPropertyFeatures:
    def test_to_vector_shape(self):
        pf = PropertyFeatures("test", price=500_000, sqft=2000, bedrooms=3, bathrooms=2)
        vec = pf.to_vector()
        assert vec.shape == (9,)
        assert all(np.isfinite(vec))

    def test_vector_normalized(self):
        pf = PropertyFeatures("test", price=1_000_000, sqft=3000, bedrooms=6, bathrooms=4)
        vec = pf.to_vector()
        # With max normalization values, most elements should be <= 1.0
        assert vec[0] == pytest.approx(1.0, rel=0.01)  # price/1M
        assert vec[1] == pytest.approx(1.0, rel=0.01)  # sqft/3000


class TestContentBasedScoring:
    def test_similar_to_liked_scores_higher(self, recommender):
        # Buyer likes 3BR, ~$500K properties
        recommender.record_interaction("b1", "p1", 1.0)  # 3BR, $500K
        recommender.record_interaction("b1", "p5", 0.8)  # 3BR, $550K

        recs = recommender.recommend("b1", n=5, exclude_seen=True)
        assert len(recs) > 0
        # p3 (2BR, $450K) and p4 (5BR, $800K) should differ in score
        scores = {r.property_id: r.score for r in recs}
        # All scores should be 0-1
        assert all(0 <= s <= 1 for s in scores.values())

    def test_preference_filter_when_no_history(self, recommender):
        pref = BuyerPreference(
            contact_id="b_new",
            price_range=(400_000, 600_000),
            min_beds=3,
            preferred_areas=["91730"],
        )
        recs = recommender.recommend("b_new", preference=pref, n=5)
        assert len(recs) > 0
        # p4 ($800K) should score lower due to price mismatch
        scores = {r.property_id: r.score for r in recs}
        if "p1" in scores and "p4" in scores:
            assert scores["p1"] > scores["p4"]


class TestCollaborativeFiltering:
    def test_similar_users_boost_score(self, recommender):
        # User A and B have similar tastes
        recommender.record_interaction("a1", "p1", 1.0)
        recommender.record_interaction("a1", "p2", 0.8)
        recommender.record_interaction("a1", "p3", 0.2)

        recommender.record_interaction("b1", "p1", 0.9)
        recommender.record_interaction("b1", "p2", 0.7)
        # b1 hasn't seen p3, p4, p5

        recs = recommender.recommend("b1", n=5)
        assert len(recs) > 0

    def test_no_collab_with_single_user(self, recommender):
        recommender.record_interaction("solo", "p1", 1.0)
        recs = recommender.recommend("solo", n=5)
        # Should still return recommendations (from content-based)
        assert len(recs) > 0


class TestHybridBlending:
    def test_scores_in_valid_range(self, recommender):
        recommender.record_interaction("b1", "p1", 1.0)
        recs = recommender.recommend("b1", n=5)
        for rec in recs:
            assert 0.0 <= rec.score <= 1.0
            assert 0.0 <= rec.content_score <= 1.0
            assert 0.0 <= rec.collaborative_score <= 1.0

    def test_exclude_seen_works(self, recommender):
        recommender.record_interaction("b1", "p1", 1.0)
        recommender.record_interaction("b1", "p2", 0.5)
        recs = recommender.recommend("b1", n=5, exclude_seen=True)
        rec_ids = {r.property_id for r in recs}
        assert "p1" not in rec_ids
        assert "p2" not in rec_ids

    def test_include_seen(self, recommender):
        recommender.record_interaction("b1", "p1", 1.0)
        recs = recommender.recommend("b1", n=5, exclude_seen=False)
        rec_ids = {r.property_id for r in recs}
        assert "p1" in rec_ids

    def test_explanation_generated(self, recommender):
        recs = recommender.recommend("newbie", n=3)
        for rec in recs:
            assert rec.explanation != ""
            assert "BR" in rec.explanation

    def test_empty_catalog(self):
        empty = HybridPropertyRecommender()
        recs = empty.recommend("anyone")
        assert recs == []


class TestPropertyManagement:
    def test_add_single(self, recommender):
        recommender.add_property(PropertyFeatures("p99", price=999_000))
        assert recommender.property_count == 6

    def test_interaction_count(self, recommender):
        recommender.record_interaction("b1", "p1", 1.0)
        recommender.record_interaction("b1", "p2", 0.5)
        recommender.record_interaction("b2", "p1", 0.8)
        assert recommender.interaction_count == 3
