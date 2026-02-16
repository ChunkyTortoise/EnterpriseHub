# AI DevOps Suite

**Unified AI DevOps platform** combining agent monitoring, prompt registry, and data pipeline tools.

## Features

- **Agent Monitoring**: Track telemetry, metrics (P50/P95/P99), anomaly detection, and alerting
- **Prompt Registry**: Git-like versioning, A/B testing with statistical significance, safety validation
- **Data Pipeline**: Web scraping (httpx + BeautifulSoup), scheduled jobs (APScheduler), LLM extraction
- **BI Dashboard**: Streamlit-powered analytics and visualization

## Quick Start

### 1. Install Dependencies

```bash
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database, Redis, and API keys
```

### 3. Run Database Migrations

```bash
alembic upgrade head
```

### 4. Start the API Server

```bash
uvicorn devops_suite.main:app --reload
```

Server runs at http://localhost:8000

API docs at http://localhost:8000/docs

### 5. Start the Dashboard (Optional)

```bash
streamlit run src/devops_suite/dashboard/app.py
```

## Running Tests

```bash
# All tests
pytest tests/

# With coverage
pytest tests/ --cov=devops_suite --cov-report=html

# Specific module
pytest tests/test_monitoring/
pytest tests/test_prompt_registry/
pytest tests/test_data_pipeline/
pytest tests/test_api/
```

**Test Coverage**: 136+ tests covering monitoring, versioning, A/B testing, scheduling, scraping, and APIs.

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

Services:
- API: http://localhost:8000
- Dashboard: http://localhost:8501
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Monitoring    │    │ Prompt Registry  │    │  Data Pipeline  │
│  (Telemetry)    │◄──►│  (Versioning)    │◄──►│  (Scraping)     │
│                 │    │                  │    │                 │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         └──────────────────────┼───────────────────────┘
                    ┌───────────▼──────────┐
                    │    FastAPI Core      │
                    │  (8 REST endpoints)  │
                    └───────────┬──────────┘
                    ┌───────────▼──────────┐
                    │   PostgreSQL + Redis │
                    └──────────────────────┘
```

## API Endpoints

- **Telemetry**: POST `/api/v1/events`, GET `/api/v1/dashboards`
- **Alerts**: GET/POST/DELETE `/api/v1/alerts`
- **Prompts**: GET/POST `/api/v1/prompts`, `/api/v1/experiments`
- **Pipeline**: GET/POST `/api/v1/jobs`, `/api/v1/schedules`, `/api/v1/extractions`
- **Health**: GET `/health`

## Project Structure

```
ai-devops-suite/
├── src/devops_suite/
│   ├── api/              # FastAPI routers (8 endpoints)
│   ├── models/           # SQLAlchemy models (4 modules)
│   ├── monitoring/       # Metrics, alerts, anomaly detection
│   ├── prompt_registry/  # Versioning, A/B testing, safety
│   ├── data_pipeline/    # Scraping, scheduling, extraction
│   ├── dashboard/        # Streamlit BI components
│   ├── config.py         # Pydantic settings
│   └── main.py           # FastAPI app factory
├── tests/                # 136+ pytest tests
│   ├── test_monitoring/
│   ├── test_prompt_registry/
│   ├── test_data_pipeline/
│   └── test_api/
├── alembic/              # Database migrations
│   └── versions/001_initial_schema.py
├── docker-compose.yml    # Multi-service deployment
├── Dockerfile            # Production container
└── pyproject.toml        # Python 3.11+ dependencies
```

## Development

### Adding a New Feature

1. **Create models** in `src/devops_suite/models/`
2. **Add API endpoints** in `src/devops_suite/api/`
3. **Write tests** in `tests/test_*/`
4. **Generate migration**: `alembic revision --autogenerate -m "Description"`
5. **Apply migration**: `alembic upgrade head`

### Code Quality

```bash
# Format code
ruff format .

# Lint
ruff check .

# Type check
pyright src/
```

## Environment Variables

See `.env.example` for all configuration options.

**Required**:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string

**Optional**:
- `STRIPE_SECRET_KEY`: For billing features
- `SENTRY_DSN`: For error tracking
- `SCRAPER_RATE_LIMIT`: Web scraping rate (default: 2.0 req/s)

## Production Deployment

1. **Set environment variables** (use `.env` or cloud secrets manager)
2. **Run migrations**: `alembic upgrade head`
3. **Start with Gunicorn**:
   ```bash
   gunicorn devops_suite.main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```
4. **Enable monitoring**: Configure Sentry DSN for error tracking
5. **Scale horizontally**: Add more API workers behind load balancer

## License

MIT

## Support

For issues or questions, see the [issue tracker](https://github.com/your-org/ai-devops-suite/issues).
