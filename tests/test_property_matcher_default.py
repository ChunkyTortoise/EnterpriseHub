import pytest
pytestmark = pytest.mark.integration

import pytest

@pytest.mark.unit
from ghl_real_estate_ai.services import property_matcher as pm


def test_property_matcher_uses_rancho_default(monkeypatch):
    monkeypatch.setattr(pm, "CURRENT_MARKET", "rancho_cucamonga")
    matcher = pm.PropertyMatcher()
    assert matcher.listings_path.name == "property_listings_rancho.json"
