# Technology Stack

## Core Framework
- **Streamlit 1.41+**: Primary web framework for interactive dashboards
- **Python 3.11+**: Main programming language
- **FastAPI + Uvicorn**: Backend API services for webhook handling

## AI & Machine Learning
- **Anthropic Claude 3.5 Sonnet**: Primary AI reasoning engine via API (anthropic==0.18.1)
- **LangGraph + LangChain**: Multi-agent workflows and orchestration
- **ChromaDB**: Vector database for semantic search and memory
- **Sentence Transformers**: Text embeddings for similarity matching
- **TextBlob**: Natural language processing

## Data Processing & Visualization
- **Pandas 2.1.3+**: Data manipulation and analysis
- **NumPy 1.26.2+**: Numerical computing for performance optimization
- **Plotly 5.17.0**: Interactive charts and visualizations
- **SciPy 1.11.4+**: Statistical analysis and A/B testing
- **scikit-learn 1.3.2+**: Machine learning algorithms

## Real Estate & Financial Data
- **yfinance 0.2.33**: Market data for financial analysis modules
- **ta 0.11.0**: Technical analysis indicators

## Authentication & Security
- **python-jose[cryptography]**: JWT token handling
- **passlib[bcrypt]**: Password hashing
- **python-multipart**: Form data handling

## Development & Deployment
- **pytest**: Testing framework (517+ tests)
- **flake8**: Code linting
- **black**: Code formatting
- **mypy**: Type checking
- **pre-commit**: Git hooks for quality gates

## Infrastructure
- **Docker + docker-compose**: Containerization
- **Railway**: Backend deployment platform
- **Streamlit Cloud**: Frontend deployment
- **GitHub Actions**: CI/CD pipeline