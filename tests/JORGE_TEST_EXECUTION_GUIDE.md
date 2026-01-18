# Jorge's Revenue Platform - Test Execution Quick Reference

## Quick Start

```bash
# Run all Jorge platform tests
python tests/run_jorge_platform_validation.py

# Run specific end-to-end test suite
pytest tests/integration/test_jorge_revenue_platform_e2e.py -v

# Run with coverage
pytest tests/integration/test_jorge_revenue_platform_e2e.py \
  --cov=ghl_real_estate_ai --cov-report=html
```

## Test Suites

### 1. End-to-End Integration Tests
**File**: `tests/integration/test_jorge_revenue_platform_e2e.py`

```bash
# Run all E2E tests
pytest tests/integration/test_jorge_revenue_platform_e2e.py -v

# Run specific workflow
pytest tests/integration/test_jorge_revenue_platform_e2e.py::TestJorgeRevenuePlatformE2E::test_complete_golden_lead_workflow -v

# Run with detailed output
pytest tests/integration/test_jorge_revenue_platform_e2e.py -vv --tb=long
```

### 2. API Integration Tests
**Files**:
- `tests/api/test_pricing_optimization_routes.py`
- `tests/integration/test_pricing_system_integration.py`

```bash
# Run all API tests
pytest tests/api/test_pricing_optimization_routes.py -v
pytest tests/integration/test_pricing_system_integration.py -v

# Test specific endpoint
pytest tests/api/test_pricing_optimization_routes.py::TestPricingOptimizationRoutes::test_calculate_lead_pricing_success -v
```

### 3. Service Unit Tests
**Files**:
- `tests/services/test_dynamic_pricing_optimizer.py`
- `tests/services/test_roi_calculator_service.py`
- `tests/services/test_realtime_behavioral_network.py`

```bash
# Run all service tests
pytest tests/services/test_dynamic_pricing_optimizer.py -v
pytest tests/services/test_roi_calculator_service.py -v
```

### 4. Legacy Jorge Integration Tests
**Files**:
- `test_jorge_integration.py`
- `test_pricing_end_to_end.py`

```bash
# Run Jorge's original validation tests
pytest test_jorge_integration.py -v
pytest test_pricing_end_to_end.py -v
```

## Test Categories

### Run by Test Marker

```bash
# Run only integration tests
pytest -m integration -v

# Run only unit tests
pytest -m unit -v

# Skip slow tests
pytest -m "not slow" -v

# Run smoke tests only
pytest -m smoke -v
```

### Run by Workflow Type

```bash
# Golden lead detection tests
pytest -k "golden_lead" -v

# Pricing optimization tests
pytest -k "pricing" -v

# ROI calculator tests
pytest -k "roi" -v

# API endpoint tests
pytest -k "api" -v

# Dashboard integration tests
pytest -k "dashboard" -v
```

## Coverage Reports

### Generate HTML Coverage Report

```bash
# Full coverage with HTML report
pytest tests/ \
  --cov=ghl_real_estate_ai \
  --cov-report=html \
  --cov-report=term-missing

# Open coverage report
open htmlcov/index.html
```

### Coverage by Service

```bash
# Pricing optimizer coverage
pytest tests/services/test_dynamic_pricing_optimizer.py \
  --cov=ghl_real_estate_ai.services.dynamic_pricing_optimizer \
  --cov-report=term-missing

# ROI calculator coverage
pytest tests/services/test_roi_calculator_service.py \
  --cov=ghl_real_estate_ai.services.roi_calculator_service \
  --cov-report=term-missing
```

## Debugging Tests

### Run with Debugging

```bash
# Run with Python debugger
pytest tests/integration/test_jorge_revenue_platform_e2e.py --pdb

# Run with detailed traceback
pytest tests/integration/test_jorge_revenue_platform_e2e.py --tb=long

# Show local variables in traceback
pytest tests/integration/test_jorge_revenue_platform_e2e.py --tb=long --showlocals
```

### Run Single Test with Output

```bash
# Show all output (print statements)
pytest tests/integration/test_jorge_revenue_platform_e2e.py::TestJorgeRevenuePlatformE2E::test_complete_golden_lead_workflow -s -v

# Capture output but show on failure
pytest tests/integration/test_jorge_revenue_platform_e2e.py -v --tb=short
```

## Performance Testing

### Run with Benchmarking

```bash
# Run performance tests
pytest tests/performance/test_service6_performance_load.py -v

# Generate benchmark report
pytest tests/performance/ --benchmark-only --benchmark-save=jorge_platform
```

## Continuous Integration

### CI/CD Pipeline Commands

```bash
# Full validation suite for CI
pytest tests/ \
  --cov=ghl_real_estate_ai \
  --cov-report=xml \
  --cov-report=term \
  --junit-xml=test-results.xml \
  -v

# Quick validation (skip slow tests)
pytest tests/ -m "not slow" --tb=short -v

# Parallel execution (faster)
pytest tests/ -n auto -v
```

## Common Issues & Solutions

### Issue: Import Errors

```bash
# Install all test dependencies
pip install -r requirements-test.txt

# Install main dependencies
pip install -r requirements.txt
```

### Issue: Database Connection Errors

```bash
# Start required services
docker-compose up -d redis postgres

# Verify services are running
docker-compose ps
```

### Issue: Async Test Warnings

```bash
# Use correct asyncio mode
pytest tests/ --asyncio-mode=auto
```

### Issue: Module Not Found

```bash
# Install package in development mode
pip install -e .

# Or add to PYTHONPATH
export PYTHONPATH=/path/to/EnterpriseHub:$PYTHONPATH
```

## Test Data

### Using Test Fixtures

Tests use fixtures defined in `tests/conftest.py`:
- `jorge_location_id`: Jorge's actual GHL location
- `mock_user`: Authenticated test user
- `sample_hot_lead_webhook`: Golden lead scenario
- `sample_warm_lead_webhook`: Qualified lead scenario
- `sample_cold_lead_webhook`: Low engagement scenario

### Creating Custom Test Data

```python
# In your test file
@pytest.fixture
def custom_lead_data():
    return {
        "contact_id": "custom_contact_123",
        "questions_answered": 4,
        "budget": "$500,000",
        "timeline": "2 months"
    }

def test_custom_scenario(custom_lead_data):
    # Use custom data in test
    pass
```

## Validation Checklist

### Pre-Commit Validation

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type check
mypy ghl_real_estate_ai/

# Run tests
pytest tests/ -x --tb=short
```

### Pre-Deployment Validation

```bash
# Run complete validation suite
python tests/run_jorge_platform_validation.py

# Generate coverage report
pytest tests/ --cov=ghl_real_estate_ai --cov-report=html

# Review validation summary
cat jorge_platform_validation_report.json
```

## Expected Test Results

### Successful Validation

```
🎉 ALL VALIDATIONS PASSED - Platform Ready for Production!

Test Summary:
  • Total Tests: 114
  • Passed: 114
  • Failed: 0
  • Duration: 45.2s

Coverage Summary:
  ✅ dynamic_pricing: 95.0%
  ✅ roi_calculator: 94.0%
  ✅ golden_lead_detector: 92.0%
  ✅ api_routes: 100.0%
  ✅ overall: 95.0%
```

### Partial Failure Example

```
❌ VALIDATION FAILED - 3 test(s) failed

Critical Issues:
  ❌ API Integration Tests: 2 test(s) failed
  ❌ Performance Tests: 1 test(s) failed

Recommendations:
  • Fix failing tests before production deployment
  • Review error logs for specific failures
  • Run individual test suites for debugging
```

## Contact & Support

- **Test Suite Owner**: Jorge's Revenue Platform Team
- **Documentation**: See `/docs/testing/` for detailed guides
- **Issues**: Create issue in GitHub repo with `test-failure` label

---

**Last Updated**: January 17, 2026
**Version**: 1.0.0
