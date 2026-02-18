"""
Comprehensive tests for enhanced primitive components.
Validates metric, badge, and performance optimization implementations.
"""

from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest


class TestMetricPrimitive:
    """Test suite for the enhanced metric primitive component."""

    def test_metric_component_basic_rendering(self):
        """Test basic metric rendering without errors."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_metric, MetricConfig

render_obsidian_metric(
    value="$2.4M",
    label="Revenue",
    config=MetricConfig(variant='success', size='medium')
)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify metric HTML was injected
        assert any("$2.4M" in str(m.body) for m in at.markdown)
        assert any("Revenue" in str(m.body) for m in at.markdown)

    def test_metric_config_variants(self):
        """Test all metric variants render correctly."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_metric, MetricConfig

# Test all variants
variants = ['default', 'success', 'warning', 'error', 'premium']
for variant in variants:
    render_obsidian_metric(
        value=f"Test {variant}",
        label=f"{variant.title()} Metric",
        config=MetricConfig(variant=variant, size='small')
    )
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify all variants were rendered
        variants = ["default", "success", "warning", "error", "premium"]
        for variant in variants:
            assert any(f"Test {variant}" in str(m.body) for m in at.markdown)

    def test_metric_with_trend_indicators(self):
        """Test metric with trend indicators and comparisons."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_metric, MetricConfig

render_obsidian_metric(
    value=847,
    label="Hot Leads",
    config=MetricConfig(
        variant='success',
        trend='up',
        show_comparison=True,
        size='large',
        glow_effect=True
    ),
    comparison_value="+18% vs last month",
    metric_icon='fire'
)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify trend and comparison elements
        assert any("847" in str(m.body) for m in at.markdown)
        assert any("Hot Leads" in str(m.body) for m in at.markdown)
        assert any("+18% vs last month" in str(m.body) for m in at.markdown)

    def test_metric_size_variants(self):
        """Test different metric size configurations."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_metric, MetricConfig

sizes = ['small', 'medium', 'large']
for size in sizes:
    render_obsidian_metric(
        value=f"{size.title()} Value",
        label=f"{size.title()} Size",
        config=MetricConfig(size=size)
    )
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify all sizes were rendered
        sizes = ["small", "medium", "large"]
        for size in sizes:
            assert any(f"{size.title()} Value" in str(m.body) for m in at.markdown)


class TestBadgePrimitive:
    """Test suite for the enhanced badge primitive component."""

    def test_badge_component_basic_rendering(self):
        """Test basic badge rendering without errors."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_badge, BadgeConfig

render_obsidian_badge(
    "HOT QUALIFIED",
    config=BadgeConfig(variant='hot', show_icon=True)
)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify badge HTML was injected
        assert any("HOT QUALIFIED" in str(m.body) for m in at.markdown)

    def test_badge_temperature_variants(self):
        """Test lead temperature badge variants."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import lead_temperature_badge

# Test temperature convenience function
temperatures = ['hot', 'warm', 'cold']
for temp in temperatures:
    lead_temperature_badge(temp)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify temperature badges were rendered
        assert any("HOT LEAD" in str(m.body) for m in at.markdown)
        assert any("WARM LEAD" in str(m.body) for m in at.markdown)
        assert any("COLD LEAD" in str(m.body) for m in at.markdown)

    def test_badge_status_variants(self):
        """Test status badge variants."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import status_badge

# Test status convenience function  
statuses = [
    ('success', 'Approved'),
    ('warning', 'Pending Review'),
    ('error', 'Failed'),
    ('info', 'Information')
]
for status, text in statuses:
    status_badge(status, text)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify status badges were rendered
        assert any("APPROVED" in str(m.body) for m in at.markdown)
        assert any("PENDING REVIEW" in str(m.body) for m in at.markdown)

    def test_badge_all_variants(self):
        """Test all badge variants for completeness."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_badge, BadgeConfig

variants = [
    'hot', 'warm', 'cold', 
    'success', 'warning', 'error', 'info',
    'premium', 'elite', 'standard',
    'active', 'inactive', 'pending',
    'priority', 'urgent', 'normal'
]

for variant in variants:
    render_obsidian_badge(
        f"{variant.upper()}",
        config=BadgeConfig(
            variant=variant,
            size='sm',
            show_icon=True,
            glow_effect=(variant in ['hot', 'elite', 'urgent'])
        )
    )
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify key variants were rendered
        key_variants = ["HOT", "SUCCESS", "PREMIUM", "ELITE", "URGENT"]
        for variant in key_variants:
            assert any(variant in str(m.body) for m in at.markdown)

    def test_badge_size_and_effects(self):
        """Test badge sizes and special effects."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import render_obsidian_badge, BadgeConfig

# Test size variants
sizes = ['xs', 'sm', 'md', 'lg']
for size in sizes:
    render_obsidian_badge(
        f"{size.upper()} Size",
        config=BadgeConfig(size=size, variant='info')
    )

# Test effects
render_obsidian_badge(
    "GLOW EFFECT",
    config=BadgeConfig(variant='premium', glow_effect=True)
)

render_obsidian_badge(
    "PULSE ANIMATION",
    config=BadgeConfig(variant='hot', pulse_animation=True)
)
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify size variants were rendered
        assert any("XS SIZE" in str(m.body) for m in at.markdown)
        assert any("LG SIZE" in str(m.body) for m in at.markdown)
        assert any("GLOW EFFECT" in str(m.body) for m in at.markdown)


class TestPerformanceOptimizations:
    """Test suite for performance optimization components."""

    def test_performance_optimizer_initialization(self):
        """Test PerformanceOptimizer class initialization."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import get_performance_optimizer

# Initialize optimizer
perf = get_performance_optimizer()

# Display cache stats
st.write(f"Cache Hit Rate: {perf.cache_hit_rate}")
st.write(f"Total Requests: {perf.cache_stats['total_requests']}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify cache stats are displayed
        assert any("Cache Hit Rate:" in str(w.body) for w in at.text)
        assert any("Total Requests:" in str(w.body) for w in at.text)

    @patch("ghl_real_estate_ai.streamlit_demo.components.performance_optimizations.CacheService")
    def test_optimized_lead_analytics(self, mock_cache_service):
        """Test optimized lead analytics with mocked cache service."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import optimized_lead_analytics

# Test with basic filters
filters = {
    'min_score': 70,
    'temperature': ['hot', 'warm'],
    'sectors': ['Austin', 'Dallas']
}

# This should use caching
df = optimized_lead_analytics("test_hash", filters)

st.write(f"Data shape: {df.shape}")
st.write(f"Columns: {list(df.columns)}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify data was processed
        assert any("Data shape:" in str(w.body) for w in at.text)
        assert any("Columns:" in str(w.body) for w in at.text)

    def test_optimized_chart_creation(self):
        """Test optimized chart creation functionality."""
        test_script = """
import streamlit as st
import pandas as pd
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import create_optimized_chart

# Create sample data
data = {
    'lead_id': range(1, 101),
    'score': [70 + (i % 30) for i in range(100)],
    'temperature': ['hot', 'warm', 'cold'] * 34,
    'sector': ['Austin', 'Dallas'] * 50,
    'value': [250000 + (i * 1000) for i in range(100)]
}
df = pd.DataFrame(data)

# Store in session state for chart function
st.session_state['chart_data_test_hash'] = df

# Create charts
config = {'bins': 20}
fig = create_optimized_chart('lead_scores', 'test_hash', config)

st.write(f"Chart created: {type(fig).__name__}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify chart was created
        assert any("Chart created:" in str(w.body) for w in at.text)

    def test_data_hash_generation(self):
        """Test data hash generation for cache keys."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import generate_data_hash

# Test hash generation
filter_str = "{'min_score': 70, 'temperature': ['hot']}"
hash_key = generate_data_hash(filter_str)

st.write(f"Generated hash: {hash_key}")
st.write(f"Hash length: {len(hash_key)}")

# Test that same input gives same hash
hash_key2 = generate_data_hash(filter_str)
st.write(f"Hashes match: {hash_key == hash_key2}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify hash generation works
        assert any("Generated hash:" in str(w.body) for w in at.text)
        assert any("Hash length:" in str(w.body) for w in at.text)
        assert any("Hashes match: True" in str(w.body) for w in at.text)


class TestOptimizedLeadDashboard:
    """Test suite for the optimized lead dashboard implementation."""

    def test_optimized_dashboard_rendering(self):
        """Test that optimized dashboard renders without errors."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.lead_dashboard_optimized import render_lead_dashboard_optimized

# Mock session state data
if 'lead_score' not in st.session_state:
    st.session_state.lead_score = 85

render_lead_dashboard_optimized()
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify key elements are present
        assert any("LEAD INTELLIGENCE TELEMETRY" in str(m.body) for m in at.markdown)
        assert any("SARAH MARTINEZ" in str(m.body) for m in at.markdown)

    def test_cached_data_retrieval(self):
        """Test that lead data caching works correctly."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.lead_dashboard_optimized import get_lead_data

# Test data retrieval
lead_data = get_lead_data()

st.write(f"Lead name: {lead_data['name']}")
st.write(f"Sector: {lead_data['sector']}")
st.write(f"Temperature: {lead_data['temperature']}")
st.write(f"Tags count: {len(lead_data['tags'])}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify cached data structure
        assert any("Lead name: SARAH MARTINEZ" in str(w.body) for w in at.text)
        assert any("Sector: AUSTIN" in str(w.body) for w in at.text)
        assert any("Temperature: hot" in str(w.body) for w in at.text)


class TestIntegrationScenarios:
    """Integration tests for combined primitive usage."""

    def test_dashboard_with_all_primitives(self):
        """Test dashboard using all enhanced primitives together."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.primitives import (
    render_obsidian_card, CardConfig,
    render_obsidian_metric, MetricConfig,
    render_obsidian_badge, BadgeConfig,
    lead_temperature_badge
)

# Create a mini dashboard with all primitives
st.title("Integration Test Dashboard")

# Header card
render_obsidian_card(
    title="Test Dashboard",
    content="This dashboard uses all primitive components",
    config=CardConfig(variant='premium')
)

# Metrics row
col1, col2, col3 = st.columns(3)

with col1:
    render_obsidian_metric(
        value="$1.2M",
        label="Revenue",
        config=MetricConfig(variant='success', trend='up', show_comparison=True),
        comparison_value="+15% vs Q3",
        metric_icon='dollar-sign'
    )

with col2:
    render_obsidian_metric(
        value=456,
        label="Hot Leads",
        config=MetricConfig(variant='premium', size='medium', glow_effect=True),
        metric_icon='fire'
    )

with col3:
    render_obsidian_metric(
        value="87%",
        label="Conversion Rate",
        config=MetricConfig(variant='warning', trend='down'),
        comparison_value="-3% vs target"
    )

# Badge row
st.markdown("#### Status Indicators")
lead_temperature_badge('hot')
render_obsidian_badge("Premium Client", BadgeConfig(variant='premium', show_icon=True))
render_obsidian_badge("High Priority", BadgeConfig(variant='priority', glow_effect=True))

st.success("All primitives rendered successfully!")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify integration success
        assert any("Integration Test Dashboard" in str(t.body) for t in at.title)
        assert any("All primitives rendered successfully!" in str(a.body) for a in at.success)

    def test_performance_monitoring_dashboard(self):
        """Test performance monitoring integration."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import demonstrate_performance_improvements

# Run performance demonstration
demonstrate_performance_improvements()
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify performance dashboard elements
        assert any("PERFORMANCE OPTIMIZATION DEMONSTRATION" in str(m.body) for m in at.markdown)
        assert any("Multi-level Caching Strategy" in str(m.body) for m in at.markdown)


@pytest.fixture
def mock_cache_service():
    """Mock cache service for testing."""
    with patch("ghl_real_estate_ai.services.cache_service.CacheService") as mock:
        mock_instance = Mock()
        mock_instance.get = AsyncMock(return_value=None)
        mock_instance.set = AsyncMock(return_value=True)
        mock.return_value = mock_instance
        yield mock_instance


# Performance benchmarks
class TestPerformanceBenchmarks:
    """Performance benchmark tests to validate optimization claims."""

    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate calculation accuracy."""
        test_script = """
import streamlit as st
from ghl_real_estate_ai.streamlit_demo.components.performance_optimizations import PerformanceOptimizer


# Create optimizer and simulate cache operations
perf = PerformanceOptimizer()

# Simulate requests
perf.cache_stats['total_requests'] = 100
perf.cache_stats['hits'] = 85
perf.cache_stats['misses'] = 15

hit_rate = perf.cache_hit_rate

st.write(f"Hit rate: {hit_rate}%")
st.write(f"Expected 85%: {hit_rate == 85.0}")
"""
        at = AppTest.from_string(test_script)
        at.run()

        assert not at.exception
        # Verify hit rate calculation
        assert any("Hit rate: 85.0%" in str(w.body) for w in at.text)
        assert any("Expected 85%: True" in str(w.body) for w in at.text)


if __name__ == "__main__":
    # Run tests with coverage reporting
    pytest.main(
        [
            __file__,
            "--cov=ghl_real_estate_ai.streamlit_demo.components.primitives",
            "--cov=ghl_real_estate_ai.streamlit_demo.components.performance_optimizations",
            "--cov=ghl_real_estate_ai.streamlit_demo.components.lead_dashboard_optimized",
            "--cov-report=html",
            "--cov-report=term",
            "-v",
        ]
    )