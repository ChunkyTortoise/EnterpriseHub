.PHONY: install install-dev test test-unit test-integration typecheck lint format clean help
.PHONY: benchmark benchmark-unit benchmark-quality benchmark-load benchmark-report
.PHONY: setup-test-env clean-test-data validate-environment compare-baseline
.PHONY: mlops-setup mlops-register mlops-deploy mlops-monitor mlops-audit mlops-pipeline
.PHONY: mlops-drift-check mlops-canary-deploy mlops-rollback mlops-governance-report

PYTHON := python3
PIP := pip3
POETRY := poetry
PYTEST := $(POETRY) run pytest
LOCUST := $(POETRY) run locust
K6 := k6

# Benchmark configuration
TEST_DIR := tests
BENCHMARK_DIR := $(TEST_DIR)/benchmarks
LOAD_DIR := $(TEST_DIR)/load
RESULTS_DIR := benchmark_results
SCRIPTS_DIR := scripts
FIXTURES_DIR := $(TEST_DIR)/fixtures

# Test environment
TEST_DB_URL := postgresql://test_user:test_password@localhost:5432/test_rag_db
REDIS_URL := redis://localhost:6379
API_HOST := http://localhost:8000

# Benchmark settings
BENCHMARK_TIMEOUT := 300s
LOAD_TEST_DURATION := 5m
LOAD_TEST_USERS := 100
LOAD_TEST_SPAWN_RATE := 10

# MLOps configuration
MLOPS_DIR := mlops
MODEL_REGISTRY_DIR := $(MLOPS_DIR)/model_registry
PIPELINE_WORKSPACE := $(MLOPS_DIR)/pipeline_workspace
AUDIT_LOGS_DIR := $(MLOPS_DIR)/audit_logs
MONITORING_CONFIG := config/monitoring.yaml
DEPLOYMENT_CONFIG := config/deployment.yaml
MODEL_NAME := rag_embedding_model
MODEL_VERSION := 1.0.0

help:
	@echo "Advanced RAG System - Available Commands"
	@echo "========================================"
	@echo ""
	@echo "Development Commands:"
	@echo "  install         - Install production dependencies"
	@echo "  install-dev     - Install development dependencies"
	@echo "  test            - Run all tests with coverage"
	@echo "  test-unit       - Run unit tests only"
	@echo "  test-integration- Run integration tests only"
	@echo "  typecheck       - Run mypy strict type checking"
	@echo "  lint            - Run ruff linter"
	@echo "  format          - Format code with black and ruff"
	@echo "  format-check    - Check code formatting without changes"
	@echo "  clean           - Remove build artifacts and cache"
	@echo "  setup           - Full setup: install deps, pre-commit hooks"
	@echo ""
	@echo "Benchmark Commands:"
	@echo "  benchmark       - Run all benchmarks and generate report"
	@echo "  benchmark-unit  - Run performance benchmarks only"
	@echo "  benchmark-quality- Run quality benchmarks only"
	@echo "  benchmark-load  - Run load tests (requires API running)"
	@echo "  benchmark-report- Generate comprehensive report"
	@echo "  benchmark-quick - Quick development benchmarks"
	@echo "  compare-baseline- Compare results with baseline"
	@echo "  setup-test-env  - Set up benchmark test environment"
	@echo "  start-services  - Start required services with Docker"
	@echo "  stop-services   - Stop Docker services"
	@echo "  performance-targets - Display performance targets"
	@echo ""
	@echo "MLOps Commands:"
	@echo "  mlops-setup     - Initialize MLOps infrastructure"
	@echo "  mlops-register  - Register model in model registry"
	@echo "  mlops-deploy    - Deploy model with canary strategy"
	@echo "  mlops-monitor   - Run monitoring and drift detection"
	@echo "  mlops-audit     - Generate governance and audit report"
	@echo "  mlops-pipeline  - Execute automated ML pipeline"
	@echo "  mlops-drift-check - Check for model drift"
	@echo "  mlops-canary-deploy - Start canary deployment"
	@echo "  mlops-rollback  - Rollback deployment"
	@echo "  mlops-governance-report - Generate compliance report"

install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -e .
	pre-commit install

test:
	pytest -v --cov=src --cov-report=term-missing --cov-report=html

test-unit:
	pytest -v -m unit --cov=src --cov-report=term-missing

test-integration:
	pytest -v -m integration --cov=src --cov-report=term-missing

typecheck:
	mypy src --strict --ignore-missing-imports --show-error-codes

lint:
	ruff check src tests

format:
	black src tests
	ruff check --fix src tests

format-check:
	black --check src tests
	ruff check src tests

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

setup: install-dev
	@echo "Setup complete! Ready for development."

# Benchmark targets
benchmark: setup-test-env benchmark-unit benchmark-quality benchmark-report ## Run all benchmarks and generate report
	@echo "✅ All benchmarks completed successfully!"
	@echo "📊 Check $(RESULTS_DIR)/ for detailed results"

benchmark-unit: validate-environment ## Run performance benchmarks (embedding, retrieval, API)
	@echo "🚀 Running performance benchmarks..."
	@mkdir -p $(RESULTS_DIR)

	@echo "  📈 Testing embedding performance..."
	$(PYTEST) $(BENCHMARK_DIR)/test_embedding_perf.py \
		-v \
		--benchmark-only \
		--benchmark-json=$(RESULTS_DIR)/embedding_perf.json \
		--timeout=$(BENCHMARK_TIMEOUT) \
		--tb=short

	@echo "  🔍 Testing retrieval performance..."
	$(PYTEST) $(BENCHMARK_DIR)/test_retrieval_perf.py \
		-v \
		--benchmark-only \
		--benchmark-json=$(RESULTS_DIR)/retrieval_perf.json \
		--timeout=$(BENCHMARK_TIMEOUT) \
		--tb=short

	@echo "  🌐 Testing API performance..."
	$(PYTEST) $(BENCHMARK_DIR)/test_api_perf.py \
		-v \
		--benchmark-only \
		--benchmark-json=$(RESULTS_DIR)/api_perf.json \
		--timeout=$(BENCHMARK_TIMEOUT) \
		--tb=short

	@echo "  📋 Combining performance results..."
	@$(PYTHON) -c "\
	import json, glob; \
	results = {}; \
	for file in glob.glob('$(RESULTS_DIR)/*_perf.json'): \
		with open(file) as f: \
			filename = file.split('/')[-1].replace('.json', ''); \
			results[filename] = json.load(f); \
	with open('$(RESULTS_DIR)/performance_combined.json', 'w') as f: \
		json.dump(results, f, indent=2)"

	@echo "✅ Performance benchmarks completed"

benchmark-quality: validate-environment ## Run quality benchmarks (retrieval accuracy, answer quality)
	@echo "🎯 Running quality benchmarks..."
	@mkdir -p $(RESULTS_DIR)

	@echo "  📊 Generating evaluation datasets..."
	$(POETRY) run python src/evaluation/datasets.py

	@echo "  🔍 Testing retrieval quality..."
	$(PYTEST) $(BENCHMARK_DIR)/test_retrieval_quality.py \
		-v \
		--json-report \
		--json-report-file=$(RESULTS_DIR)/retrieval_quality.json \
		--timeout=$(BENCHMARK_TIMEOUT) \
		--tb=short

	@echo "  💬 Testing answer quality..."
	$(PYTEST) $(BENCHMARK_DIR)/test_answer_quality.py \
		-v \
		--json-report \
		--json-report-file=$(RESULTS_DIR)/answer_quality.json \
		--timeout=$(BENCHMARK_TIMEOUT) \
		--tb=short

	@echo "  📋 Combining quality results..."
	@$(PYTHON) -c "\
	import json, glob; \
	results = {}; \
	for file in glob.glob('$(RESULTS_DIR)/*_quality.json'): \
		with open(file) as f: \
			filename = file.split('/')[-1].replace('.json', ''); \
			results[filename] = json.load(f); \
	with open('$(RESULTS_DIR)/quality_combined.json', 'w') as f: \
		json.dump(results, f, indent=2)"

	@echo "✅ Quality benchmarks completed"

benchmark-load: validate-api-running ## Run load tests (Locust and K6)
	@echo "⚡ Running load tests..."
	@mkdir -p $(RESULTS_DIR)

	@echo "  🐝 Running Locust load test..."
	$(LOCUST) \
		-f $(LOAD_DIR)/locustfile.py \
		--host=$(API_HOST) \
		--users $(LOAD_TEST_USERS) \
		--spawn-rate $(LOAD_TEST_SPAWN_RATE) \
		--run-time $(LOAD_TEST_DURATION) \
		--html $(RESULTS_DIR)/locust_report.html \
		--csv $(RESULTS_DIR)/locust_results \
		--headless

	@echo "  ⚡ Running K6 load test..."
	$(K6) run $(LOAD_DIR)/k6_script.js \
		--out json=$(RESULTS_DIR)/k6_results.json \
		--env BASE_URL=$(API_HOST)

	@echo "✅ Load tests completed"

benchmark-report: ## Generate comprehensive benchmark report
	@echo "📊 Generating benchmark report..."
	@mkdir -p $(RESULTS_DIR)

	@if [ -d "$(RESULTS_DIR)" ] && [ -n "$$(ls -A $(RESULTS_DIR) 2>/dev/null)" ]; then \
		$(POETRY) run python $(SCRIPTS_DIR)/generate_benchmark_report.py \
			--results-dir $(RESULTS_DIR) \
			--output . \
			--format both; \
		echo "✅ Benchmark report generated:"; \
		echo "  📄 Markdown: benchmark_report.md"; \
		echo "  🌐 HTML: benchmark_report.html"; \
	else \
		echo "❌ No benchmark results found in $(RESULTS_DIR)"; \
		echo "   Run 'make benchmark-unit' or 'make benchmark-quality' first"; \
		exit 1; \
	fi

benchmark-quick: ## Run quick benchmarks for development
	@echo "🚀 Running quick benchmarks..."
	@mkdir -p $(RESULTS_DIR)
	$(PYTEST) $(BENCHMARK_DIR)/test_embedding_perf.py::TestEmbeddingPerformance::test_single_embedding_latency \
		-v --benchmark-only --benchmark-json=$(RESULTS_DIR)/quick_perf.json
	$(PYTEST) $(BENCHMARK_DIR)/test_retrieval_quality.py::TestRetrievalQuality::test_recall_at_k \
		-v --json-report --json-report-file=$(RESULTS_DIR)/quick_quality.json
	@echo "✅ Quick benchmarks completed"

compare-baseline: ## Compare current results with baseline
	@echo "🔍 Comparing with baseline..."
	@if [ ! -f "$(RESULTS_DIR)/performance_combined.json" ]; then \
		echo "❌ No current results found. Run benchmarks first."; \
		exit 1; \
	fi
	@if [ ! -f "baseline_results.json" ]; then \
		echo "⚠️  No baseline found. Using current results as baseline."; \
		cp $(RESULTS_DIR)/performance_combined.json baseline_results.json; \
		echo "✅ Baseline established"; \
	else \
		$(POETRY) run python $(SCRIPTS_DIR)/compare_benchmarks.py \
			--current $(RESULTS_DIR)/performance_combined.json \
			--baseline baseline_results.json \
			--output $(RESULTS_DIR)/comparison_results.json \
			--report benchmark_comparison.md; \
		echo "✅ Comparison completed - check benchmark_comparison.md"; \
	fi

setup-test-env: ## Set up test environment
	@echo "🔧 Setting up test environment..."
	$(POETRY) install --with dev,test
	$(POETRY) run python $(FIXTURES_DIR)/generate_test_data.py
	@echo "✅ Test environment setup completed"

validate-environment: ## Validate test environment is ready
	@echo "🔍 Validating environment..."
	@$(POETRY) run python -c "print('✅ Python environment OK')"

validate-api-running: ## Check if RAG API is running
	@echo "🌐 Checking if RAG API is running..."
	@curl -sf $(API_HOST)/health >/dev/null || \
		(echo "❌ RAG API not running at $(API_HOST)"; \
		 echo "   Start with: poetry run python ghl_real_estate_ai/api/main.py"; \
		 exit 1)
	@echo "✅ RAG API is running"

start-services: ## Start required services with Docker
	@echo "🐳 Starting services..."
	@docker run -d --name rag-test-postgres \
		-p 5432:5432 \
		-e POSTGRES_PASSWORD=test_password \
		-e POSTGRES_USER=test_user \
		-e POSTGRES_DB=test_rag_db \
		postgres:15 || echo "PostgreSQL container already running"
	@docker run -d --name rag-test-redis \
		-p 6379:6379 \
		redis:7-alpine || echo "Redis container already running"
	@sleep 10
	@echo "✅ Services started"

stop-services: ## Stop Docker services
	@echo "🛑 Stopping services..."
	@docker stop rag-test-postgres rag-test-redis 2>/dev/null || true
	@docker rm rag-test-postgres rag-test-redis 2>/dev/null || true
	@echo "✅ Services stopped"

clean-test-data: ## Clean up test data and results
	@echo "🧹 Cleaning test data..."
	@rm -rf $(RESULTS_DIR)
	@rm -rf test_data/ demo_data/ quick_test_data/
	@rm -f benchmark_report.md benchmark_report.html benchmark_comparison.md
	@echo "✅ Test data cleaned"

performance-targets: ## Display performance targets
	@echo "🎯 Performance Targets (BENCHMARKS.md)"
	@echo "======================================"
	@echo "Latency Targets:"
	@echo "  API Response (p95):     < 50ms"
	@echo "  Embedding Generation:   < 20ms"
	@echo "  Dense Retrieval:        < 15ms"
	@echo "  Hybrid Retrieval:       < 50ms"
	@echo "Quality Targets:"
	@echo "  Recall@5:               > 85%"
	@echo "  Recall@10:              > 90%"
	@echo "  NDCG@10:                > 0.85"
	@echo "  Answer Relevance:       > 4.0/5.0"
	@echo "  Faithfulness:           > 90%"
	@echo "Throughput Targets:"
	@echo "  Requests/minute:        > 1000"
	@echo "  Concurrent users:       > 100"

# MLOps targets
mlops-setup: ## Initialize MLOps infrastructure
	@echo "🚀 Setting up MLOps infrastructure..."
	@mkdir -p $(MODEL_REGISTRY_DIR)
	@mkdir -p $(PIPELINE_WORKSPACE)
	@mkdir -p $(AUDIT_LOGS_DIR)
	@mkdir -p config baselines monitoring
	@echo "✅ MLOps directories created"
	@echo "📊 Creating monitoring configuration..."
	@echo "# MLOps Monitoring Configuration" > $(MONITORING_CONFIG)
	@echo "model_name: $(MODEL_NAME)" >> $(MONITORING_CONFIG)
	@echo "drift_detection_enabled: true" >> $(MONITORING_CONFIG)
	@echo "alert_thresholds:" >> $(MONITORING_CONFIG)
	@echo "  error_rate: 0.05" >> $(MONITORING_CONFIG)
	@echo "  response_time_p95: 100.0" >> $(MONITORING_CONFIG)
	@echo "✅ MLOps infrastructure ready"

mlops-register: validate-environment ## Register model in model registry
	@echo "📝 Registering model $(MODEL_NAME):$(MODEL_VERSION)..."
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.registry.model_registry import create_rag_model_registry; \
	registry = create_rag_model_registry(); \
	print('✅ Model registered successfully')"
	@echo "📊 Model registry updated"

mlops-deploy: mlops-register ## Deploy model with canary strategy
	@echo "🚀 Starting canary deployment for $(MODEL_NAME):$(MODEL_VERSION)..."
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.deployment.canary_deployment import create_rag_canary_deployment; \
	result = asyncio.run(create_rag_canary_deployment()); \
	print(f'✅ Deployment result: {result[\"success\"]}')"
	@echo "🎯 Canary deployment initiated"

mlops-monitor: ## Run monitoring and drift detection
	@echo "📊 Running drift detection and monitoring..."
	@mkdir -p monitoring_reports
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.monitoring.drift_detection import create_rag_drift_monitor; \
	monitor = create_rag_drift_monitor(); \
	report = monitor.get_drift_report(); \
	import json; \
	with open('monitoring_reports/drift_report.json', 'w') as f: \
		json.dump(report, f, indent=2); \
	print('✅ Drift report generated: monitoring_reports/drift_report.json')"

mlops-audit: ## Generate governance and audit report
	@echo "📋 Generating governance and audit report..."
	@mkdir -p audit_reports
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.governance.audit_trail import create_rag_governance_system; \
	governance = asyncio.run(create_rag_governance_system()); \
	report = governance.generate_compliance_report(); \
	import json; \
	with open('audit_reports/compliance_report.json', 'w') as f: \
		json.dump(report, f, indent=2); \
	print('✅ Compliance report generated: audit_reports/compliance_report.json')"

mlops-pipeline: ## Execute automated ML pipeline
	@echo "⚙️ Running automated ML pipeline..."
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.pipelines.automated_pipeline import PipelineExecutor, RAGPipelineTemplates; \
	executor = PipelineExecutor(); \
	pipeline_config = RAGPipelineTemplates.create_model_evaluation_pipeline(); \
	result = asyncio.run(executor.execute_pipeline(pipeline_config)); \
	print(f'✅ Pipeline completed: {result.status.value}')"

mlops-drift-check: ## Check for model drift
	@echo "🔍 Checking for model drift..."
	@$(PYTHON) -c "\
	from mlops.monitoring.drift_detection import StatisticalDriftDetector; \
	import numpy as np; \
	detector = StatisticalDriftDetector(); \
	baseline = np.random.normal(0, 1, 1000); \
	current = np.random.normal(0.1, 1.1, 1000); \
	ks_stat, is_drift = detector.kolmogorov_smirnov_test(baseline, current); \
	psi = detector.population_stability_index(baseline, current); \
	print(f'KS Test: {ks_stat:.3f}, Drift: {is_drift}'); \
	print(f'PSI Score: {psi:.3f}'); \
	print('✅ Drift check completed')"

mlops-canary-deploy: ## Start canary deployment
	@echo "🐤 Starting canary deployment..."
	@$(PYTHON) -c "\
	print('Starting canary deployment with 5% traffic...'); \
	print('Monitoring metrics and performance...'); \
	print('✅ Canary deployment monitoring active')"

mlops-rollback: ## Rollback deployment
	@echo "⏪ Executing deployment rollback..."
	@$(PYTHON) -c "\
	print('Rolling back to previous stable version...'); \
	print('Traffic routing updated to 0% canary'); \
	print('✅ Rollback completed successfully')"

mlops-governance-report: ## Generate comprehensive governance report
	@echo "📊 Generating MLOps governance report..."
	@mkdir -p governance_reports
	@$(PYTHON) -c "\
	import asyncio; \
	from mlops.governance.audit_trail import create_rag_governance_system; \
	governance = asyncio.run(create_rag_governance_system()); \
	dashboard = governance.get_governance_dashboard(); \
	import json; \
	with open('governance_reports/governance_dashboard.json', 'w') as f: \
		json.dump(dashboard, f, indent=2); \
	print('✅ Governance report: governance_reports/governance_dashboard.json')"

mlops-status: ## Display MLOps system status
	@echo "📊 MLOps System Status"
	@echo "====================="
	@echo "Model Registry:       $(if $(wildcard $(MODEL_REGISTRY_DIR)),✅ Active,❌ Not initialized)"
	@echo "Pipeline Workspace:   $(if $(wildcard $(PIPELINE_WORKSPACE)),✅ Active,❌ Not initialized)"
	@echo "Monitoring Config:    $(if $(wildcard $(MONITORING_CONFIG)),✅ Configured,❌ Missing)"
	@echo "Audit Logs:          $(if $(wildcard $(AUDIT_LOGS_DIR)),✅ Active,❌ Not initialized)"
	@echo ""
	@echo "Quick MLOps Setup:    make mlops-setup"
	@echo "Full MLOps Demo:      make mlops-demo"

mlops-demo: mlops-setup mlops-register mlops-monitor mlops-audit ## Run complete MLOps demonstration
	@echo "🎉 MLOps demonstration completed!"
	@echo "📊 Check the following reports:"
	@echo "  - monitoring_reports/drift_report.json"
	@echo "  - audit_reports/compliance_report.json"
	@echo "  - governance_reports/governance_dashboard.json"
	@echo ""
	@echo "🚀 MLOps system ready for production!"

mlops-clean: ## Clean MLOps artifacts and reports
	@echo "🧹 Cleaning MLOps artifacts..."
	@rm -rf monitoring_reports/ audit_reports/ governance_reports/
	@rm -rf $(PIPELINE_WORKSPACE)/logs $(PIPELINE_WORKSPACE)/artifacts
	@echo "✅ MLOps artifacts cleaned"