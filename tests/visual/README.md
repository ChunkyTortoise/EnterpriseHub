# Visual Regression Testing

Comprehensive visual regression and accessibility testing infrastructure for EnterpriseHub.

## Overview

This directory contains:
- **Visual Regression Tests**: Screenshot comparison for 57+ Streamlit components
- **Accessibility Tests**: WCAG 2.1 AA compliance testing with axe-core
- **CI/CD Integration**: Automated testing in GitHub Actions

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Start Streamlit App

```bash
# In terminal 1 - Start the app
streamlit run ghl_real_estate_ai/streamlit_demo/app.py
```

### 3. Run Tests

```bash
# In terminal 2 - Run visual tests
pytest tests/visual/test_component_snapshots.py --screenshot=on -v

# Run accessibility tests
pytest tests/visual/test_accessibility.py -v

# Run all visual tests
pytest tests/visual/ -v
```

## Test Files

### `test_component_snapshots.py`
Visual regression tests for all UI components.

**Key Tests**:
- Individual tests for critical components (property_card, lead_intelligence_hub, executive_dashboard)
- Parameterized tests for all 57+ components
- Responsive design tests (mobile, tablet, desktop)
- State-based tests (empty state, loading state)

**Usage**:
```bash
# Run all snapshot tests
pytest tests/visual/test_component_snapshots.py -v

# Run specific test
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot -v

# Run only critical component tests
pytest tests/visual/test_component_snapshots.py -k "property_card or lead_intelligence" -v

# Update baselines (use carefully!)
pytest tests/visual/test_component_snapshots.py --screenshot=on --update-snapshots
```

### `test_accessibility.py`
WCAG 2.1 AA compliance tests using axe-core.

**Key Tests**:
- WCAG 2.1 AA compliance for critical components
- Color contrast validation (4.5:1 minimum)
- ARIA labels and roles
- Keyboard navigation
- Heading structure
- Form labels
- Mobile accessibility

**Usage**:
```bash
# Run all accessibility tests
pytest tests/visual/test_accessibility.py -v

# Run specific accessibility test
pytest tests/visual/test_accessibility.py::test_color_contrast -v

# Run only critical component accessibility tests
pytest tests/visual/test_accessibility.py -k "critical" -v
```

## Directory Structure

```
tests/visual/
├── __init__.py                     # Package initialization
├── README.md                       # This file
├── conftest.py                     # Playwright fixtures
├── snapshots/                      # Baseline screenshots
│   ├── property_card_baseline.png
│   ├── lead_intelligence_hub_baseline.png
│   ├── executive_dashboard_baseline.png
│   └── ... (57+ component baselines)
├── test_component_snapshots.py     # Visual regression tests
└── test_accessibility.py           # Accessibility tests
```

## Baseline Management

### Capturing Initial Baselines

**First Time Setup**:
```bash
# Start Streamlit app
streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# Capture all baselines
pytest tests/visual/test_component_snapshots.py --screenshot=on
```

This creates baseline screenshots in `tests/visual/snapshots/`.

### Updating Baselines

**When to update**:
- Intentional UI changes (new design, layout updates)
- Component refactoring that changes visual appearance
- After reviewing and approving visual differences

**How to update**:
```bash
# Update all baselines
pytest tests/visual/test_component_snapshots.py --screenshot=on --update-snapshots

# Update specific component baseline
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot \
  --screenshot=on --update-snapshots

# Commit updated baselines
git add tests/visual/snapshots/
git commit -m "chore: update visual regression baselines"
```

**⚠️ Important**: Always review visual differences before updating baselines!

### Reviewing Visual Differences

When tests fail, Playwright generates comparison artifacts:

```
tests/visual/test-results/
├── test_property_card_snapshot/
│   ├── property_card_baseline-actual.png     # Current screenshot
│   ├── property_card_baseline-expected.png   # Baseline screenshot
│   └── property_card_baseline-diff.png       # Highlighted differences
```

Review these files to determine if changes are intentional or bugs.

## CI/CD Integration

Visual regression tests run automatically on:
- Pull requests (when Streamlit files change)
- Pushes to main branch
- Manual workflow dispatch

### GitHub Actions Workflow

See `.github/workflows/visual-regression.yml` for full configuration.

**Features**:
- Automated testing on Ubuntu runners
- Artifact upload on failures (screenshots, traces)
- Test result summaries in PR comments
- Manual baseline update workflow

### Viewing Test Results in CI

1. Navigate to **Actions** tab in GitHub
2. Click on **Visual Regression Testing** workflow
3. View test results and download artifacts if tests failed

### Updating Baselines in CI

Baselines can be updated via manual workflow dispatch:

1. Go to **Actions** tab
2. Select **Visual Regression Testing** workflow
3. Click **Run workflow** → Select branch → **Run workflow**
4. Workflow will update baselines and commit them automatically

## Tolerance Configuration

Visual regression tests use `max_diff_pixels` to allow minor rendering differences:

```python
# Standard components
expect(component).to_have_screenshot(
    'component_baseline.png',
    max_diff_pixels=100,  # Tolerate up to 100 pixel differences
)

# Complex components (charts, visualizations)
expect(complex_component).to_have_screenshot(
    'complex_baseline.png',
    max_diff_pixels=200,  # Higher tolerance for dynamic content
)
```

**Adjust tolerance based on**:
- Component complexity (charts → higher tolerance)
- Dynamic content (timestamps, animations → freeze or higher tolerance)
- Browser rendering differences (anti-aliasing)

## Best Practices

### 1. Freeze Dynamic Content

Always freeze timestamps, random IDs, and dynamic content before screenshots:

```python
def test_component_with_dynamic_content(streamlit_app, freeze_dynamic_content):
    freeze_dynamic_content('[data-testid="component"]')
    # Now take screenshot
```

### 2. Wait for Content to Load

Ensure all content is fully loaded before capturing screenshots:

```python
# Wait for specific element
streamlit_app.wait_for_selector('[data-testid="component"]', timeout=10000)

# Wait for images to load
component.locator('img').first.wait_for(state='visible')

# Wait for charts to render
streamlit_app.wait_for_timeout(2000)
```

### 3. Handle Conditionally Rendered Components

Some components only render under specific conditions:

```python
try:
    streamlit_app.wait_for_selector('[data-testid="component"]', timeout=10000)
except Exception as e:
    pytest.skip(f"Component not rendered: {e}")
```

### 4. Test Different States

Test components in various states:

```python
# Empty state
test_component_empty_state()

# Loading state
test_component_loading_state()

# Error state
test_component_error_state()

# Populated state
test_component_populated_state()
```

### 5. Responsive Testing

Test critical components across viewports:

```python
@pytest.mark.parametrize('viewport', [
    {'width': 375, 'height': 667, 'name': 'mobile'},
    {'width': 768, 'height': 1024, 'name': 'tablet'},
    {'width': 1920, 'height': 1080, 'name': 'desktop'},
])
def test_responsive_component(browser, viewport):
    # Test component at each viewport size
```

## Troubleshooting

### Tests Fail Locally but Pass in CI

**Cause**: Different rendering engines or font rendering
**Solution**:
- Use Docker to match CI environment
- Increase `max_diff_pixels` tolerance
- Ensure consistent fonts across environments

### Baselines Not Found

**Cause**: Baselines haven't been captured yet
**Solution**: Run tests with `--screenshot=on` to capture baselines

### Flaky Tests (Intermittent Failures)

**Cause**: Dynamic content, animations, or timing issues
**Solution**:
- Freeze dynamic content with `freeze_dynamic_content()`
- Disable animations in tests
- Increase wait timeouts
- Use `wait_for_timeout()` for charts/visualizations

### Accessibility Tests Fail

**Cause**: WCAG violations in components
**Solution**:
- Review axe violations in test output
- Fix accessibility issues in component code
- Ensure proper ARIA labels, color contrast, keyboard navigation

## Performance Optimization

### Running Tests in Parallel

```bash
# Run tests in parallel (faster execution)
pytest tests/visual/ -n auto --dist loadscope
```

### Running Subset of Tests

```bash
# Only critical components
pytest tests/visual/test_component_snapshots.py -k "critical" -v

# Only accessibility tests
pytest tests/visual/test_accessibility.py -v

# Single component
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot -v
```

## Resources

- [Playwright Documentation](https://playwright.dev/python/)
- [pytest-playwright](https://github.com/microsoft/playwright-pytest)
- [axe-core Documentation](https://github.com/dequelabs/axe-core)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

## Support

For issues or questions:
1. Check this README
2. Review test output and artifacts
3. Consult Playwright/axe-core documentation
4. Open GitHub issue with test output and screenshots
