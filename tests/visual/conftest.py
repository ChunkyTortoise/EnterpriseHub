"""
Playwright fixtures for visual regression testing.

Provides:
- Browser fixture (session-scoped, reused across tests)
- Page fixture with 1920x1080 viewport
- Streamlit app fixture with automatic navigation
"""
import pytest
from playwright.sync_api import sync_playwright, Browser, Page, BrowserContext


@pytest.fixture(scope="session")
def browser() -> Browser:
    """
    Session-scoped browser instance.

    Launches headless Chromium browser once for entire test session.
    Automatically closes when session ends.

    Yields:
        Browser: Playwright Browser instance
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-dev-shm-usage',  # Avoid shared memory issues in CI
                '--no-sandbox',              # Required for Docker/CI
            ]
        )
        yield browser
        browser.close()


@pytest.fixture
def context(browser: Browser) -> BrowserContext:
    """
    Browser context with fixed viewport size.

    Creates new context for each test with 1920x1080 viewport.
    This ensures consistent screenshots across different environments.

    Args:
        browser: Session-scoped browser instance

    Yields:
        BrowserContext: New browser context
    """
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        device_scale_factor=1,  # Consistent pixel density
        locale='en-US',         # Consistent locale for date/time formatting
    )
    yield context
    context.close()


@pytest.fixture
def page(context: BrowserContext) -> Page:
    """
    New page in browser context.

    Creates fresh page for each test to avoid state pollution.

    Args:
        context: Browser context fixture

    Yields:
        Page: New page instance
    """
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture
def streamlit_app(page: Page) -> Page:
    """
    Navigate to Streamlit app and wait for it to be ready.

    Navigates to localhost:8501 and waits for Streamlit's main container
    to be rendered. This ensures the app is fully loaded before tests run.

    Args:
        page: Page fixture

    Returns:
        Page: Page with Streamlit app loaded

    Raises:
        TimeoutError: If app doesn't load within 30 seconds
    """
    # Navigate to Streamlit app
    page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)

    # Wait for Streamlit to be ready
    page.wait_for_selector('[data-testid="stApp"]', timeout=30000)

    # Wait for any initial loading animations to complete
    page.wait_for_timeout(1000)

    return page


@pytest.fixture
def freeze_dynamic_content(page: Page) -> callable:
    """
    Utility fixture to freeze dynamic content before screenshots.

    Returns a function that freezes timestamps, random IDs, and other
    dynamic elements to prevent false positives in visual regression tests.

    Args:
        page: Page fixture

    Returns:
        callable: Function to freeze dynamic content

    Usage:
        freeze_dynamic_content()  # Freezes all dynamic content
        freeze_dynamic_content('[data-testid="specific-component"]')  # Freeze specific component
    """
    def freeze(selector: str = 'body'):
        """
        Freeze dynamic content within selector.

        Args:
            selector: CSS selector for container to freeze (default: 'body')
        """
        page.evaluate(f"""
            (selector) => {{
                const container = document.querySelector(selector);
                if (!container) return;

                // Freeze timestamps
                container.querySelectorAll('[data-dynamic="timestamp"]').forEach(el => {{
                    el.textContent = '2026-01-16 12:00:00';
                }});

                // Freeze random IDs
                container.querySelectorAll('[data-dynamic="id"]').forEach(el => {{
                    el.textContent = 'FROZEN_ID_12345';
                }});

                // Freeze dates
                container.querySelectorAll('[data-dynamic="date"]').forEach(el => {{
                    el.textContent = 'Jan 16, 2026';
                }});

                // Freeze any element with data-dynamic attribute
                container.querySelectorAll('[data-dynamic]').forEach(el => {{
                    if (!el.dataset.frozen) {{
                        el.dataset.frozen = el.textContent;
                        el.textContent = 'FROZEN_FOR_TEST';
                    }}
                }});

                // Disable animations
                const style = document.createElement('style');
                style.textContent = `
                    * {{
                        animation-duration: 0s !important;
                        transition-duration: 0s !important;
                    }}
                `;
                container.appendChild(style);
            }}
        """, selector)

    return freeze
