# Contributing to Enterprise Hub

Thank you for your interest in contributing to Enterprise Hub! This document provides guidelines and instructions for contributing.

## 🎯 Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- Git
- A GitHub account

### Development Setup

1. **Fork the repository** on GitHub

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/enterprise-hub.git
   cd enterprise-hub
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/ChunkyTortoise/enterprise-hub.git
   ```

4. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

6. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Development Workflow

### Making Changes

1. **Keep your fork synced**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Make your changes**
   - Write clean, readable code
   - Follow the existing code style
   - Add docstrings to new functions/classes
   - Update documentation as needed

3. **Test your changes**
   ```bash
   # Run tests
   pytest
   
   # Check code style
   black --check .
   flake8 .
   
   # Type checking
   mypy ghl_real_estate_ai/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "Brief description of changes"
   ```
   
   **Commit Message Guidelines:**
   - Use present tense ("Add feature" not "Added feature")
   - Use imperative mood ("Move cursor to..." not "Moves cursor to...")
   - Limit first line to 72 characters
   - Reference issues and pull requests when relevant

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**
   - Go to the original repository on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template
   - Wait for review

## 📋 Code Style Guidelines

### Python Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://github.com/psf/black) for code formatting
- Maximum line length: 88 characters (Black default)
- Use type hints for function signatures

### Code Quality

```python
# Good: Type hints and docstring
def get_stock_data(ticker: str, period: str = "1y") -> pd.DataFrame:
    """
    Fetch stock data from Yahoo Finance.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        period: Time period for data (e.g., '1y', '6mo')
    
    Returns:
        DataFrame containing stock data
    
    Raises:
        ValueError: If ticker is invalid
    """
    # Implementation
    pass

# Bad: No type hints or docstring
def get_data(t, p="1y"):
    # Implementation
    pass
```

### Documentation

- Add docstrings to all public functions and classes
- Use Google-style docstrings
- Update README.md if adding new features
- Add comments for complex logic

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names

```python
def test_get_stock_data_valid_ticker():
    """Test that valid ticker returns data."""
    df = get_stock_data("AAPL", "1mo")
    assert df is not None
    assert not df.empty

def test_get_stock_data_invalid_ticker():
    """Test that invalid ticker handles error gracefully."""
    df = get_stock_data("INVALID_TICKER", "1mo")
    assert df is None
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_data_loader.py

# Run specific test
pytest tests/test_data_loader.py::test_get_stock_data_valid_ticker
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Description**: Clear description of the bug
2. **Steps to reproduce**: Numbered steps to reproduce the issue
3. **Expected behavior**: What you expected to happen
4. **Actual behavior**: What actually happened
5. **Environment**: 
   - OS (macOS, Windows, Linux)
   - Python version
   - Package versions
6. **Screenshots**: If applicable

## 💡 Feature Requests

When suggesting features, please include:

1. **Problem**: What problem does this solve?
2. **Proposed solution**: How should it work?
3. **Alternatives**: What alternatives have you considered?
4. **Additional context**: Any other relevant information

## 📦 Pull Request Guidelines

### Before Submitting

- [ ] Code follows style guidelines
- [ ] Tests pass locally
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages are clear
- [ ] Branch is up to date with main

### PR Checklist

Your PR should:
- Have a clear title and description
- Reference related issues (e.g., "Fixes #123")
- Be focused on a single feature/fix
- Include tests for new functionality
- Update documentation as needed

### Review Process

1. Maintainer will review your PR
2. Address any requested changes
3. Once approved, maintainer will merge
4. Your contribution will be included in the next release!

## 🏗️ Project Structure

```
EnterpriseHub/
├── ghl_real_estate_ai/  # Main application package
│   ├── api/             # FastAPI routes and middleware
│   ├── services/        # Business logic and AI services
│   ├── models/          # SQLAlchemy models
│   └── tests/           # Unit and integration tests
├── tests/               # Additional test suite
└── docs/                # Documentation
```

## 🎨 Module Development

When adding new functionality:

1. Create services in `ghl_real_estate_ai/services/`
2. Add routes in `ghl_real_estate_ai/api/routes/`
3. Add models in `ghl_real_estate_ai/models/`
4. Write tests in `tests/`
5. Update README.md

## ❓ Questions?

If you have questions:
- Check existing issues and discussions
- Create a new issue with the "question" label
- Reach out to maintainers

## 🙏 Thank You!

Your contributions make this project better for everyone. We appreciate your time and effort!

---

**Happy coding! 🚀**
