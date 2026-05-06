# Makefile for Enterprise Hub

.PHONY: help install install-dev test lint format type-check clean run demo build verify-public verify-focused verify-full artifact-policy-check route-metadata-audit ghl-setup ghl-setup-check ghl-setup-guide compile-check no-mock-check metrics-snapshot weekly-pilot-kpis weekly-proof-pack persist-pilot-data pilot-proof-pack pilot-proof-pack-sync revenue-ops-qa

help:  ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

install-dev:  ## Install development dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
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

artifact-policy-check:  ## Guard against tracked local artifacts and secret-shaped files
	python3 scripts/ci/tracked_artifact_policy.py

route-metadata-audit:  ## Enforce FastAPI response_model and status_code coverage for portal_api
	python3 scripts/ci/route_metadata_audit.py portal_api --fail-on-missing

verify-public:  ## Fast reviewer-facing gate: lint, compile, and test collection
	ruff check .
	python3 scripts/ci/compile_check.py
	python3 scripts/ci/route_metadata_audit.py portal_api --fail-on-missing
	python3 scripts/ci/tracked_artifact_policy.py
	pytest --collect-only --override-ini='addopts=' -q
	python3 scripts/ci/tracked_artifact_policy.py

verify-focused:  ## Reviewer-focused targeted tests for evals, orchestration, SQL safety, and Jorge pipeline
	pytest tests/test_eval_harness.py tests/unit/test_claude_orchestrator.py tests/unit/test_sql_safety.py tests/test_response_pipeline.py --override-ini='addopts=' -q

verify-full:  ## Deeper local gate for maintainers
	ruff check .
	python3 scripts/ci/compile_check.py
	python3 scripts/ci/no_mock_in_prod.py
	mypy ghl_real_estate_ai/
	pytest

metrics-snapshot:  ## Generate weekly proof-pack metrics snapshot
	python3 scripts/generate_metrics_snapshot.py

weekly-pilot-kpis:  ## Aggregate weekly pilot KPI records from outcome events
	python3 scripts/generate_weekly_pilot_kpis.py

weekly-proof-pack:  ## Render weekly executive proof-pack markdown from KPI CSV
	python3 scripts/generate_weekly_executive_proof_pack.py --tenant-id tenant_demo

persist-pilot-data:  ## Persist outcome events and KPI rows to database tables
	python3 scripts/persist_revenue_pilot_data.py

pilot-proof-pack:  ## End-to-end weekly pipeline (KPI CSV + executive proof-pack)
	python3 scripts/generate_weekly_pilot_kpis.py
	python3 scripts/generate_weekly_executive_proof_pack.py --tenant-id tenant_demo

pilot-proof-pack-sync:  ## End-to-end weekly pipeline + DB sync (CI-safe when DB is unavailable)
	python3 scripts/generate_weekly_pilot_kpis.py
	python3 scripts/generate_weekly_executive_proof_pack.py --tenant-id tenant_demo
	python3 scripts/persist_revenue_pilot_data.py --allow-db-unavailable

revenue-ops-qa:  ## Validate proposal and revenue tracking artifacts
	python3 scripts/ci/revenue_ops_qa.py

format:  ## Auto-format code
	ruff check --fix .
	ruff format .

type-check:  ## Run type checking
	mypy ghl_real_estate_ai/

security:  ## Run security checks
	bandit -r . -ll
	pip-audit

clean:  ## Clean up build artifacts and cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .mypy_cache htmlcov .coverage

run:  ## Run the Streamlit app
	streamlit run streamlit_cloud/app.py

demo:  ## Run in demo mode (no API keys, DB, or Redis required)
	DEMO_MODE=true streamlit run ghl_real_estate_ai/streamlit_demo/app.py

build:  ## Verify the app can be built/imported
	python3 -m py_compile portal_api/app.py ghl_real_estate_ai/streamlit_demo/app.py streamlit_cloud/app.py

ghl-setup:  ## Audit GHL field configuration
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper

ghl-setup-check:  ## Check GHL fields (CI mode, exits 1 on missing)
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --check-only

ghl-setup-guide:  ## Print step-by-step GHL setup instructions
	python -m ghl_real_estate_ai.ghl_utils.env_field_mapper --setup

all: install-dev verify-full  ## Run complete CI pipeline locally
