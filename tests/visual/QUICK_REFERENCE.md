# Visual Testing Quick Reference

One-page reference for common visual testing commands and workflows.

## Setup (First Time Only)

```bash
# Run automated setup
./tests/visual/setup_visual_tests.sh

# Or manual setup
pip install -r requirements.txt
playwright install chromium
```

## Running Tests

### Basic Commands

```bash
# Start Streamlit (in terminal 1)
streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# Run all visual tests (in terminal 2)
pytest tests/visual/ -v

# Run visual regression tests only
pytest tests/visual/test_component_snapshots.py -v

# Run accessibility tests only
pytest tests/visual/test_accessibility.py -v
```

### Specific Tests

```bash
# Single component
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot -v

# Critical components only
pytest tests/visual/ -m critical -v

# Accessibility only
pytest tests/visual/ -m accessibility -v

# Responsive tests only
pytest tests/visual/ -m responsive -v
```

### With Options

```bash
# Capture/update screenshots
pytest tests/visual/test_component_snapshots.py --screenshot=on

# Verbose output with screenshots
pytest tests/visual/ --screenshot=on -vv

# Stop on first failure
pytest tests/visual/ -x

# Run in parallel (fast)
pytest tests/visual/ -n auto
```

## Baseline Management

### Capture Initial Baselines

```bash
# First run - captures all baselines
pytest tests/visual/test_component_snapshots.py --screenshot=on
```

### Update Baselines

```bash
# Update ALL baselines (use carefully!)
pytest tests/visual/test_component_snapshots.py --screenshot=on --update-snapshots

# Update single component
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot \
  --screenshot=on --update-snapshots

# Review changes before committing
git diff tests/visual/snapshots/

# Commit updated baselines
git add tests/visual/snapshots/
git commit -m "chore: update visual regression baselines"
```

## Reviewing Failures

### Visual Differences

When tests fail, check:

```bash
# View diff images
open tests/visual/test-results/*/  # macOS
xdg-open tests/visual/test-results/*/  # Linux

# Compare files
- *-actual.png     # What we got
- *-expected.png   # What we expected (baseline)
- *-diff.png       # Highlighted differences
```

### Accessibility Violations

```bash
# Run accessibility tests with verbose output
pytest tests/visual/test_accessibility.py -vv

# Check specific violation type
pytest tests/visual/test_accessibility.py::test_color_contrast -vv
```

## Common Workflows

### Pull Request Testing

```bash
# Before PR: Run full test suite
pytest tests/visual/ --screenshot=on -v

# Fix any failures, then commit
git add .
git commit -m "fix: resolve visual regressions"

# CI will run tests automatically on PR
```

### After UI Changes

```bash
# 1. Make UI changes in code
# 2. Start Streamlit
streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# 3. Run visual tests to see what changed
pytest tests/visual/test_component_snapshots.py -v

# 4. Review differences
open tests/visual/test-results/

# 5a. If changes are intentional - update baselines
pytest tests/visual/test_component_snapshots.py --screenshot=on --update-snapshots

# 5b. If changes are bugs - fix the code and re-test
```

### Testing New Component

```bash
# 1. Add component to Streamlit app with data-testid
# <div data-testid="my-new-component">...</div>

# 2. Add component to COMPONENTS list in test_component_snapshots.py
# COMPONENTS = [..., 'my-new-component']

# 3. Run tests to capture baseline
pytest tests/visual/test_component_snapshots.py::test_all_components_snapshot[my-new-component] \
  --screenshot=on

# 4. Verify baseline looks correct
open tests/visual/snapshots/my-new-component_baseline.png
```

## Debugging

### Tests Timeout

```bash
# Increase timeout
pytest tests/visual/ --timeout=600

# Check if Streamlit is running
curl http://localhost:8501
```

### Baselines Not Found

```bash
# Capture baselines first
pytest tests/visual/test_component_snapshots.py --screenshot=on
```

### Component Not Found

```bash
# Check component has data-testid attribute
grep -r "data-testid.*my-component" ghl_real_estate_ai/streamlit_demo/

# Check Streamlit is rendering component
open http://localhost:8501
```

### Flaky Tests

```bash
# Run single test multiple times
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot \
  --count=10

# If intermittent failures, add freezing or increase wait times
```

## CI/CD

### Trigger Manual Baseline Update

1. Go to GitHub Actions
2. Select "Visual Regression Testing" workflow
3. Click "Run workflow"
4. Select branch
5. Click "Run workflow" button

### View CI Results

```bash
# In GitHub PR, check:
- Actions tab for workflow status
- Files changed for screenshot diffs
- Artifacts for failure screenshots
```

## Performance

### Fast Testing (Development)

```bash
# Test only critical components
pytest tests/visual/ -m critical -v

# Single component
pytest tests/visual/test_component_snapshots.py::test_property_card_snapshot -v

# Parallel execution
pytest tests/visual/ -n 4  # 4 parallel workers
```

### Full Testing (Pre-Commit)

```bash
# All tests, all components
pytest tests/visual/ --screenshot=on -v
```

## Useful Markers

```bash
# Critical components only
pytest tests/visual/ -m critical

# Accessibility tests
pytest tests/visual/ -m accessibility

# Responsive tests
pytest tests/visual/ -m responsive

# Slow tests (skip during development)
pytest tests/visual/ -m "not slow"

# Smoke tests (quick validation)
pytest tests/visual/ -m smoke
```

## Environment Variables

```bash
# Demo mode (uses mock data)
DEMO_MODE=true pytest tests/visual/

# Custom Streamlit port
STREAMLIT_PORT=8502 pytest tests/visual/

# Headless browser (default in tests)
PLAYWRIGHT_HEADLESS=true pytest tests/visual/

# Debug mode (show browser)
PLAYWRIGHT_HEADLESS=false pytest tests/visual/
```

## Troubleshooting

```bash
# Check Python packages
pip list | grep -E "playwright|axe|pytest"

# Check Playwright browsers
playwright --version

# Reinstall Playwright
playwright install chromium --force

# Clear pytest cache
pytest --cache-clear

# Verbose debug output
pytest tests/visual/ -vvv --tb=long
```

## Resources

- Full README: `tests/visual/README.md`
- Setup script: `./tests/visual/setup_visual_tests.sh`
- CI workflow: `.github/workflows/visual-regression.yml`
- Synthesis plan: `.claude/FRONTEND_EXCELLENCE_SYNTHESIS.md`

## Quick Tips

1. **Always review diffs before updating baselines**
2. **Freeze dynamic content** (timestamps, IDs) in tests
3. **Use appropriate tolerance** for complex components
4. **Test responsively** for critical components
5. **Run accessibility tests** before every PR
6. **Keep baselines in version control**
7. **Document intentional visual changes** in commits
8. **Use markers** to organize and filter tests
9. **Run in parallel** for faster feedback
10. **Check CI results** before merging PRs
