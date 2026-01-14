# Essential Development Commands

## Quick Start
```bash
# Run the main application (redirects to Elite v4.0)
streamlit run app.py

# Run the core Streamlit demo directly
streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# Launch Jorge's premium demo with all features
python ghl_real_estate_ai/streamlit_demo/launch_jorge_demo.py
```

## Development Workflow
```bash
# Install all dependencies
make install

# Install development dependencies + pre-commit hooks
make install-dev

# Run tests with coverage
make test

# Fast test run without coverage
make test-fast

# Code quality checks
make lint          # flake8, black, isort
make format        # Auto-format with black + isort
make type-check    # mypy type checking
make security      # bandit + pip-audit

# Clean build artifacts
make clean

# Complete CI pipeline locally
make all
```

## Testing Commands
```bash
# Run all tests with HTML coverage report
pytest --cov=. --cov-report=html --cov-report=term-missing

# Run specific test file
pytest tests/test_lead_scorer.py

# Run tests with verbose output
pytest -v

# Open coverage report
open htmlcov/index.html
```

## Docker & Deployment
```bash
# Build and run with Docker
docker build -t enterprisehub .
docker-compose up -d

# Railway deployment (backend)
railway login
railway deploy

# Environment setup
cp .env.example .env
# Edit .env with your API keys
```

## Git & Version Control
```bash
# Pre-commit hooks (auto-installed with make install-dev)
pre-commit run --all-files

# Standard workflow
git checkout -b feature/ui-enhancement
git commit -m "feat: enhance lead intelligence UI"
git push origin feature/ui-enhancement
```

## Streamlit Specific
```bash
# Run on specific port
streamlit run app.py --server.port 8502

# Run with specific theme
streamlit run app.py --theme.base light

# Clear Streamlit cache
streamlit cache clear
```

## System Commands (macOS/Darwin)
```bash
# File operations
ls -la                 # List files with permissions
find . -name "*.py"    # Find Python files
grep -r "pattern" .    # Search for text patterns

# Process management
ps aux | grep streamlit    # Find Streamlit processes
lsof -i :8501             # Check what's using port 8501
```