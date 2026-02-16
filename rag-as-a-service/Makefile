.PHONY: all test lint fmt type-check install clean docker-up docker-down load-test migrate

all: lint test

install:
	pip install -e ".[dev]"

test:
	python -m pytest tests/ -v --tb=short

lint:
	ruff check .

fmt:
	ruff format .

type-check:
	pyright .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

migrate:
	alembic upgrade head

load-test:
	python scripts/load_test.py --concurrency 50 --duration 30

load-test-locust:
	locust -f scripts/locustfile.py --host http://localhost:8000 --users 50 --spawn-rate 10 --run-time 60s --headless
