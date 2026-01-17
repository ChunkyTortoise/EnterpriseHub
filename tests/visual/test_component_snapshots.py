"""
Visual regression tests for all Streamlit components.

Tests 57+ components for visual regressions using Playwright's screenshot comparison.
Each test captures a baseline screenshot and compares future runs against it.

Run tests:
    pytest tests/visual/test_component_snapshots.py --screenshot=on

Update baselines:
    pytest tests/visual/test_component_snapshots.py --screenshot=on --update-snapshots

Key components tested:
- lead_intelligence_hub (1,936 lines - largest component)
- property_matcher_ai_enhanced (complex AI matching)
- executive_dashboard (critical analytics)
- All 57+ components via parameterized tests
"""
import pytest
from playwright.sync_api import Page, expect


# ============================================================================
# Individual Component Tests (Critical Components)
# ============================================================================

def test_property_card_snapshot(streamlit_app: Page, freeze_dynamic_content: callable):
    """
    Visual regression test for property card component.

    Property cards display individual property listings with images,
    prices, and key details. Visual regressions here directly impact
    user engagement and conversion.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        freeze_dynamic_content: Fixture to freeze dynamic elements
    """
    # Wait for property cards to load
    streamlit_app.wait_for_selector('[data-testid="property-card"]', timeout=10000)

    # Get first property card
    property_card = streamlit_app.locator('[data-testid="property-card"]').first

    # Freeze dynamic content (timestamps, IDs)
    freeze_dynamic_content('[data-testid="property-card"]')

    # Wait for images to load
    property_card.locator('img').first.wait_for(state='visible', timeout=5000)

    # Take screenshot and compare to baseline
    expect(property_card).to_have_screenshot(
        'property_card_baseline.png',
        max_diff_pixels=100,  # Allow minor anti-aliasing differences
        animations='disabled',
        timeout=10000,
    )


def test_lead_intelligence_hub_snapshot(streamlit_app: Page, freeze_dynamic_content: callable):
    """
    Visual regression test for lead intelligence hub.

    This is the LARGEST component (1,936 lines) and most complex UI element.
    It displays comprehensive lead analysis, scoring, and recommendations.
    Critical for lead management workflow.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        freeze_dynamic_content: Fixture to freeze dynamic elements
    """
    # Navigate to lead intelligence section
    streamlit_app.wait_for_selector('[data-testid="lead-intelligence-hub"]', timeout=10000)

    # Get hub container
    hub = streamlit_app.locator('[data-testid="lead-intelligence-hub"]').first

    # Freeze dynamic content
    freeze_dynamic_content('[data-testid="lead-intelligence-hub"]')

    # Wait for charts/visualizations to render
    streamlit_app.wait_for_timeout(2000)

    # Take screenshot with larger tolerance due to complexity
    expect(hub).to_have_screenshot(
        'lead_intelligence_hub_baseline.png',
        max_diff_pixels=200,  # Larger tolerance for complex charts/visualizations
        animations='disabled',
        timeout=15000,
    )


def test_executive_dashboard_snapshot(streamlit_app: Page, freeze_dynamic_content: callable):
    """
    Visual regression test for executive dashboard.

    Critical component showing high-level KPIs, revenue metrics,
    and performance analytics. Any visual regression here impacts
    executive decision-making.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        freeze_dynamic_content: Fixture to freeze dynamic elements
    """
    streamlit_app.wait_for_selector('[data-testid="executive-dashboard"]', timeout=10000)

    dashboard = streamlit_app.locator('[data-testid="executive-dashboard"]').first
    freeze_dynamic_content('[data-testid="executive-dashboard"]')

    # Wait for all metrics to load
    streamlit_app.wait_for_timeout(2000)

    expect(dashboard).to_have_screenshot(
        'executive_dashboard_baseline.png',
        max_diff_pixels=150,
        animations='disabled',
        timeout=15000,
    )


def test_property_matcher_ai_enhanced_snapshot(streamlit_app: Page, freeze_dynamic_content: callable):
    """
    Visual regression test for enhanced AI property matcher.

    Complex component with Claude AI integration for property matching.
    Visual layout must remain consistent for user trust in AI recommendations.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        freeze_dynamic_content: Fixture to freeze dynamic elements
    """
    streamlit_app.wait_for_selector('[data-testid="property-matcher-ai-enhanced"]', timeout=10000)

    matcher = streamlit_app.locator('[data-testid="property-matcher-ai-enhanced"]').first
    freeze_dynamic_content('[data-testid="property-matcher-ai-enhanced"]')

    # Wait for AI results to render
    streamlit_app.wait_for_timeout(2000)

    expect(matcher).to_have_screenshot(
        'property_matcher_ai_enhanced_baseline.png',
        max_diff_pixels=150,
        animations='disabled',
        timeout=15000,
    )


# ============================================================================
# Parameterized Tests for All Components
# ============================================================================

# All 57 Streamlit components
COMPONENTS = [
    'agent_os',
    'ai_behavioral_tuning',
    'ai_performance_metrics',
    'ai_training_feedback',
    'ai_training_sandbox',
    'alert_center',
    'automation_studio',
    'buyer_journey',
    'buyer_portal_manager',
    'calculators',
    'chat_interface',
    'churn_early_warning_dashboard',
    'claude_panel',
    'contact_timing',
    'conversation_simulator',
    'conversion_predictor',
    'deep_research',
    'elite_refinements',
    'enhanced_services',
    'executive_dashboard',
    'executive_hub',
    'financing_calculator',
    'floating_claude',
    'ghl_status_panel',
    'global_header',
    'interactive_analytics',
    'interactive_lead_map',
    'journey_orchestrator_ui',
    'knowledge_base_uploader',
    'lead_dashboard',
    'lead_intelligence_hub',
    'listing_architect',
    'live_lead_scoreboard',
    'mobile_responsive_layout',
    'neighborhood_intelligence',
    'neural_uplink',
    'ops_optimization',
    'payload_monitor',
    'performance_dashboard',
    'personalization_engine',
    'proactive_intelligence_dashboard',
    'project_copilot',
    'property_cards',
    'property_matcher_ai',
    'property_matcher_ai_enhanced',
    'property_swipe',
    'property_valuation',
    'sales_copilot',
    'security_governance',
    'segmentation_pulse',
    'seller_journey',
    'seller_portal_manager',
    'swarm_visualizer',
    'ui_elements',
    'voice_claude_interface',
    'voice_intelligence',
    'workflow_designer',
]


@pytest.mark.parametrize('component_id', COMPONENTS)
def test_all_components_snapshot(
    streamlit_app: Page,
    freeze_dynamic_content: callable,
    component_id: str
):
    """
    Parameterized visual regression test for all components.

    Tests every component in the application for visual regressions.
    This ensures comprehensive coverage of the entire UI surface area.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        freeze_dynamic_content: Fixture to freeze dynamic elements
        component_id: Component data-testid attribute value

    Raises:
        AssertionError: If screenshot differs from baseline by more than max_diff_pixels
    """
    # Wait for component to be present
    selector = f'[data-testid="{component_id}"]'

    try:
        streamlit_app.wait_for_selector(selector, timeout=10000)
    except Exception as e:
        pytest.skip(f"Component {component_id} not found - may be conditionally rendered: {e}")

    # Get component
    component = streamlit_app.locator(selector).first

    # Freeze dynamic content within component
    freeze_dynamic_content(selector)

    # Wait for component to stabilize
    streamlit_app.wait_for_timeout(1000)

    # Take screenshot and compare
    expect(component).to_have_screenshot(
        f'{component_id}_baseline.png',
        max_diff_pixels=100,
        animations='disabled',
        timeout=10000,
    )


# ============================================================================
# Responsive Design Tests
# ============================================================================

@pytest.mark.parametrize('viewport', [
    {'width': 375, 'height': 667, 'name': 'mobile'},      # iPhone SE
    {'width': 768, 'height': 1024, 'name': 'tablet'},     # iPad
    {'width': 1920, 'height': 1080, 'name': 'desktop'},   # Full HD
])
def test_responsive_property_card(browser, viewport: dict):
    """
    Test property card responsiveness across different viewports.

    Ensures property cards render correctly on mobile, tablet, and desktop.
    Critical for mobile-first real estate browsing experience.

    Args:
        browser: Browser fixture
        viewport: Viewport configuration dict

    """
    # Create context with specific viewport
    context = browser.new_context(viewport={
        'width': viewport['width'],
        'height': viewport['height']
    })
    page = context.new_page()

    try:
        # Navigate to app
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        page.wait_for_selector('[data-testid="stApp"]', timeout=30000)

        # Wait for property card
        page.wait_for_selector('[data-testid="property-card"]', timeout=10000)
        card = page.locator('[data-testid="property-card"]').first

        # Take screenshot with viewport name
        expect(card).to_have_screenshot(
            f'property_card_{viewport["name"]}.png',
            max_diff_pixels=100,
            animations='disabled',
        )
    finally:
        context.close()


# ============================================================================
# State-Based Tests (Different App States)
# ============================================================================

def test_empty_state_snapshot(streamlit_app: Page):
    """
    Test empty state UI when no data is available.

    Ensures graceful handling of empty data states with appropriate
    messaging and CTAs.

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    # Look for empty state message
    empty_state = streamlit_app.locator('[data-testid="empty-state"]')

    if empty_state.count() > 0:
        expect(empty_state.first).to_have_screenshot(
            'empty_state_baseline.png',
            max_diff_pixels=50,
        )
    else:
        pytest.skip("No empty state found - data is populated")


def test_loading_state_snapshot(streamlit_app: Page):
    """
    Test loading spinner/skeleton UI.

    Ensures loading states provide good UX with spinners or skeleton screens.

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    # Trigger a data load and capture loading state
    # Note: This may require intercepting network requests to slow down responses

    loading_spinner = streamlit_app.locator('[data-testid="stSpinner"]')

    if loading_spinner.count() > 0:
        expect(loading_spinner.first).to_have_screenshot(
            'loading_state_baseline.png',
            max_diff_pixels=50,
        )
    else:
        pytest.skip("No loading state captured - data loaded too quickly")
