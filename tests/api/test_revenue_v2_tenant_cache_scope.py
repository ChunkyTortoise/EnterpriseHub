from ghl_real_estate_ai.api.routes.revenue_v2 import _cache_key


def test_cache_keys_are_tenant_scoped_for_same_resource_id():
    key_a = _cache_key(tenant_id="tenant_a", route_name="property-intelligence", resource_id="prop_1")
    key_b = _cache_key(tenant_id="tenant_b", route_name="property-intelligence", resource_id="prop_1")

    assert key_a != key_b
    assert key_a.startswith("tenant:tenant_a:")
    assert key_b.startswith("tenant:tenant_b:")
