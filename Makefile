# Makefile for Enterprise Hub

.PHONY: help install install-dev test lint format type-check clean run demo build ghl-setup ghl-setup-check ghl-setup-guide compile-check no-mock-check metrics-snapshot revenue-ops-qa

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -r dev-requirements.txt
	pre-commit install

test:  ## Run tests with coverage
	pytest --cov=. --cov-report=html --cov-report=term-missing

test-fast:  ## Run tests without coverage
	pytest

lint:  ## Run all linters
	ruff check .

compile-check:  ## Parse gate for tracked production modules
	python3 scripts/ci/compile_check.py

no-mock-check:  ## Guard v2 production routes against mock/fallback logic
	python3 scripts/ci/no_mock_in_prod.py

metrics-snapshot:  ## Generate weekly proof-pack metrics snapshot
	python3 scripts/generate_metrics_snapshot.py

revenue-ops-qa:  ## Validate proposal and revenue tracking artifacts
	python3 scripts/ci/revenue_ops_qa.py

format:  ## Auto-format code
	ruff check --fix .
	ruff format .

type-check:  ## Run type checking
	mypy app.py modules/ utils/

security:  ## Run security checks
	bandit -r . -ll
	pip-audit

clean:  ## Clean up build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

run:  ## Run the Streamlit app
	streamlit run app.py

demo:  ## Run in demo mode (no API keys, DB, or Redis required)
	DEMO_MODE=true streamlit run ghl_real_estate_ai/streamlit_demo/app.py

build:  ## Verify the app can be built/imported
	python -c "import app; print('✓ App imported successfully')"
	python -c "from modules import market_pulse; print('✓ market_pulse imported successfully')"
	python -c "from utils import data_loader; print('✓ data_loader imported successfully')"

ghl-setup:  ## Audit GHL field configuration
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper

ghl-setup-check:  ## Check GHL fields (CI mode, exits 1 on missing)
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only

ghl-setup-guide:  ## Print step-by-step GHL setup instructions
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --setup

all: install-dev lint type-check test  ## Run complete CI pipeline locally
