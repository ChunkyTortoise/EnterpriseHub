# Makefile for Enterprise Hub

.PHONY: help install install-dev test lint format type-check clean run build

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
	flake8 .
	black --check .
	isort --check-only .

format:  ## Auto-format code
	black .
	isort .

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

build:  ## Verify the app can be built/imported
	python -c "import app; print('✓ App imported successfully')"
	python -c "from modules import market_pulse; print('✓ market_pulse imported successfully')"
	python -c "from utils import data_loader; print('✓ data_loader imported successfully')"

all: install-dev lint type-check test  ## Run complete CI pipeline locally
