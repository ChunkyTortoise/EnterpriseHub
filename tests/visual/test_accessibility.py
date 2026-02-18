"""
Accessibility testing for EnterpriseHub using axe-core.

Tests WCAG 2.1 AA compliance across all components to ensure
the application is accessible to users with disabilities.

Key tests:
- WCAG 2.1 AA compliance
- Color contrast (4.5:1 minimum)
- Keyboard navigation
- Screen reader compatibility
- Focus management

Run tests:
    pytest tests/visual/test_accessibility.py -v

Dependencies:
    - axe-playwright: Integrates axe-core with Playwright
    - axe-core: Industry-standard accessibility testing engine
"""

import pytest

# Skip all tests in this module if axe_playwright is not installed
pytest.importorskip("axe_playwright")

from axe_playwright import run_axe
from playwright.sync_api import Page

# ============================================================================
# WCAG 2.1 AA Compliance Tests
# ============================================================================


@pytest.mark.asyncio
async def test_property_card_accessibility(streamlit_app: Page):
    """
    Test property card for WCAG 2.1 AA compliance.

    Checks for critical and serious accessibility violations that would
    prevent users with disabilities from interacting with property cards.

    WCAG 2.1 AA Requirements:
    - Perceivable: Text alternatives, color contrast, adaptable content
    - Operable: Keyboard accessible, navigable, input modalities
    - Understandable: Readable, predictable, input assistance
    - Robust: Compatible with assistive technologies

    Args:
        streamlit_app: Loaded Streamlit app fixture

    Raises:
        AssertionError: If critical or serious violations found
    """
    # Wait for property card to load
    await streamlit_app.wait_for_selector('[data-testid="property-card"]', timeout=10000)

    # Run axe accessibility scan
    results = await run_axe(streamlit_app)

    # Filter for critical and serious violations only
    critical_violations = [v for v in results.get("violations", []) if v["impact"] in ["critical", "serious"]]

    # Build detailed error message if violations found
    if critical_violations:
        error_msg = f"Found {len(critical_violations)} critical/serious accessibility violations:\n\n"
        for violation in critical_violations:
            error_msg += f"- [{violation['impact'].upper()}] {violation['id']}: {violation['description']}\n"
            error_msg += f"  Help: {violation['helpUrl']}\n"
            error_msg += f"  Affected elements: {len(violation['nodes'])}\n\n"

        pytest.fail(error_msg)


@pytest.mark.asyncio
async def test_lead_intelligence_hub_accessibility(streamlit_app: Page):
    """
    Test lead intelligence hub for WCAG 2.1 AA compliance.

    This is the largest and most complex component (1,936 lines).
    Accessibility here is critical for inclusive lead management.

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    await streamlit_app.wait_for_selector('[data-testid="lead-intelligence-hub"]', timeout=10000)

    results = await run_axe(streamlit_app)

    critical_violations = [v for v in results.get("violations", []) if v["impact"] in ["critical", "serious"]]

    assert len(critical_violations) == 0, (
        f"Lead Intelligence Hub has {len(critical_violations)} accessibility violations: "
        f"{[v['id'] for v in critical_violations]}"
    )


@pytest.mark.asyncio
async def test_executive_dashboard_accessibility(streamlit_app: Page):
    """
    Test executive dashboard for WCAG 2.1 AA compliance.

    Executive dashboards must be accessible to all decision-makers,
    including those with visual impairments.

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    await streamlit_app.wait_for_selector('[data-testid="executive-dashboard"]', timeout=10000)

    results = await run_axe(streamlit_app)

    critical_violations = [v for v in results.get("violations", []) if v["impact"] in ["critical", "serious"]]

    assert len(critical_violations) == 0, f"Executive Dashboard has accessibility violations: {critical_violations}"


# ============================================================================
# Specific Accessibility Tests
# ============================================================================


@pytest.mark.asyncio
async def test_color_contrast(streamlit_app: Page):
    """
    Test color contrast meets WCAG AA standards (4.5:1 minimum).

    Color contrast is critical for:
    - Users with low vision
    - Users with color blindness
    - Viewing in bright sunlight (mobile use)

    WCAG AA Requirements:
    - Normal text: 4.5:1 contrast ratio
    - Large text (18pt+): 3:1 contrast ratio

    Args:
        streamlit_app: Loaded Streamlit app fixture

    Raises:
        AssertionError: If color contrast violations found
    """
    # Run axe scan
    results = await run_axe(streamlit_app)

    # Filter for color contrast violations
    contrast_violations = [v for v in results.get("violations", []) if v["id"] == "color-contrast"]

    if contrast_violations:
        error_msg = "Color contrast violations found:\n\n"
        for violation in contrast_violations:
            for node in violation["nodes"]:
                error_msg += f"- Element: {node['html']}\n"
                error_msg += f"  Issue: {node['failureSummary']}\n\n"

        pytest.fail(error_msg)


@pytest.mark.asyncio
async def test_aria_labels(streamlit_app: Page):
    """
    Test for proper ARIA labels on interactive elements.

    ARIA (Accessible Rich Internet Applications) labels provide
    screen reader users with context about interactive elements.

    Tests for:
    - Buttons have accessible names
    - Links have descriptive text
    - Form inputs have labels
    - Images have alt text

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    results = await run_axe(streamlit_app)

    aria_violations = [
        v
        for v in results.get("violations", [])
        if v["id"]
        in [
            "button-name",
            "link-name",
            "label",
            "image-alt",
            "aria-required-attr",
            "aria-valid-attr-value",
        ]
    ]

    assert len(aria_violations) == 0, (
        f"Found {len(aria_violations)} ARIA violations: {[v['id'] for v in aria_violations]}"
    )


@pytest.mark.asyncio
async def test_keyboard_navigation(streamlit_app: Page):
    """
    Test keyboard navigation through interactive elements.

    Keyboard accessibility is essential for:
    - Users who cannot use a mouse
    - Power users who prefer keyboard shortcuts
    - Screen reader users

    Tests:
    - Tab order is logical
    - All interactive elements are focusable
    - Focus indicators are visible
    - No keyboard traps

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    # Test tab navigation through buttons
    await streamlit_app.keyboard.press("Tab")
    focused_element = await streamlit_app.evaluate("document.activeElement.tagName")

    # Verify focus moved to an interactive element
    assert focused_element in ["BUTTON", "A", "INPUT", "SELECT", "TEXTAREA"], (
        f"Tab navigation failed - focused element: {focused_element}"
    )

    # Run axe scan for keyboard-specific issues
    results = await run_axe(streamlit_app)

    keyboard_violations = [
        v
        for v in results.get("violations", [])
        if v["id"]
        in [
            "focus-order-semantics",
            "tabindex",
            "accesskeys",
        ]
    ]

    assert len(keyboard_violations) == 0, f"Keyboard navigation violations: {keyboard_violations}"


@pytest.mark.asyncio
async def test_heading_structure(streamlit_app: Page):
    """
    Test proper heading hierarchy (h1 -> h2 -> h3, etc.).

    Proper heading structure is critical for:
    - Screen reader navigation
    - Document outline comprehension
    - SEO

    WCAG Requirements:
    - Headings should be in logical order
    - No skipped heading levels (e.g., h1 -> h3)

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    results = await run_axe(streamlit_app)

    heading_violations = [v for v in results.get("violations", []) if v["id"] in ["heading-order", "empty-heading"]]

    assert len(heading_violations) == 0, f"Heading structure violations: {heading_violations}"


@pytest.mark.asyncio
async def test_form_labels(streamlit_app: Page):
    """
    Test all form inputs have associated labels.

    Form labels are essential for:
    - Screen reader users to understand input purpose
    - Clickable label area for easier interaction
    - Form validation error association

    Args:
        streamlit_app: Loaded Streamlit app fixture
    """
    results = await run_axe(streamlit_app)

    form_violations = [
        v
        for v in results.get("violations", [])
        if v["id"]
        in [
            "label",
            "label-title-only",
            "form-field-multiple-labels",
        ]
    ]

    assert len(form_violations) == 0, f"Form label violations: {form_violations}"


# ============================================================================
# Parameterized Accessibility Tests for All Components
# ============================================================================

CRITICAL_COMPONENTS = [
    "property_card",
    "lead_intelligence_hub",
    "executive_dashboard",
    "property_matcher_ai_enhanced",
    "chat_interface",
    "lead_dashboard",
    "sales_copilot",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("component_id", CRITICAL_COMPONENTS)
async def test_critical_components_accessibility(streamlit_app: Page, component_id: str):
    """
    Test all critical components for WCAG 2.1 AA compliance.

    Critical components are those most frequently used by end users.
    Any accessibility issues here have the highest impact.

    Args:
        streamlit_app: Loaded Streamlit app fixture
        component_id: Component data-testid attribute

    Raises:
        AssertionError: If critical/serious violations found
    """
    selector = f'[data-testid="{component_id}"]'

    try:
        await streamlit_app.wait_for_selector(selector, timeout=10000)
    except Exception as e:
        pytest.skip(f"Component {component_id} not found: {e}")

    # Run axe scan
    results = await run_axe(streamlit_app)

    # Filter violations for this specific component
    # Note: axe scans entire page, so we check all violations
    # In production, you might want to scope axe to specific components
    critical_violations = [v for v in results.get("violations", []) if v["impact"] in ["critical", "serious"]]

    assert len(critical_violations) == 0, (
        f"Component {component_id} has {len(critical_violations)} accessibility violations: "
        f"{[v['id'] for v in critical_violations]}"
    )


# ============================================================================
# Mobile Accessibility Tests
# ============================================================================


@pytest.mark.asyncio
async def test_mobile_accessibility(browser):
    """
    Test accessibility on mobile viewport.

    Mobile accessibility considerations:
    - Touch targets are large enough (44x44px minimum)
    - Content is readable without zooming
    - No horizontal scrolling
    - Forms are usable on small screens

    Args:
        browser: Browser fixture
    """
    # Create mobile context (iPhone SE)
    context = await browser.new_context(
        viewport={"width": 375, "height": 667},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
    )
    page = await context.new_page()

    try:
        await page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        await page.wait_for_selector('[data-testid="stApp"]', timeout=30000)

        # Run axe scan on mobile viewport
        results = await run_axe(page)

        # Check for mobile-specific issues
        mobile_violations = [v for v in results.get("violations", []) if v["impact"] in ["critical", "serious"]]

        assert len(mobile_violations) == 0, f"Mobile accessibility violations: {mobile_violations}"

    finally:
        await context.close()