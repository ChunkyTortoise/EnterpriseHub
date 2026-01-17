# Testing Patterns Reference

**Token Budget**: ~3-4k tokens (load on-demand only)
**Trigger**: When writing tests, debugging test failures, or improving test coverage

## Test Organization

### 1. Test File Structure

```
ghl_real_estate_ai/
├── services/
│   ├── cache_service.py
│   ├── cache_service.test.py          # Co-located unit tests
│   ├── claude_assistant.py
│   ├── claude_assistant.test.py
├── tests/
│   ├── integration/                    # Cross-service tests
│   │   ├── test_ghl_sync.py
│   │   ├── test_lead_workflow.py
│   ├── e2e/                           # End-to-end tests
│   │   ├── test_user_journey.py
│   ├── fixtures/                       # Shared test data
│   │   ├── contacts.py
│   │   ├── properties.py
│   ├── conftest.py                     # Pytest configuration
```

### 2. Test Naming Conventions

```python
import pytest

class TestCacheService:
    """Group related tests in classes."""

    def test_set_and_get_value_success(self):
        """Test names explain behavior and expected outcome."""
        # Arrange
        cache = CacheService()
        key, value = "test_key", "test_value"

        # Act
        cache.set(key, value)
        result = cache.get(key)

        # Assert
        assert result == value

    def test_get_nonexistent_key_returns_none(self):
        """Test edge cases explicitly."""
        cache = CacheService()
        result = cache.get("nonexistent")
        assert result is None

    def test_set_with_ttl_expires_after_timeout(self):
        """Test time-dependent behavior."""
        import time

        cache = CacheService()
        cache.set("temp_key", "temp_value", ttl=1)

        # Value exists immediately
        assert cache.get("temp_key") == "temp_value"

        # Wait for expiry
        time.sleep(1.1)

        # Value expired
        assert cache.get("temp_key") is None
```

### 3. Arrange-Act-Assert Pattern

```python
def test_user_registration_creates_account():
    """Clear separation of test phases."""

    # Arrange: Set up test data and preconditions
    user_data = {
        "email": "test@example.com",
        "password": "SecurePass123!",
        "name": "Test User"
    }

    # Act: Execute the operation being tested
    result = register_user(user_data)

    # Assert: Verify expected outcomes
    assert result.success is True
    assert result.user.email == user_data["email"]
    assert result.user.password != user_data["password"]  # Should be hashed
    assert result.user.id is not None
```

## Test Fixtures and Factories

### 1. Pytest Fixtures

```python
# tests/conftest.py

import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

@pytest.fixture(scope="session")
def db_engine():
    """Create test database engine once per test session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(db_engine) -> Generator[Session, None, None]:
    """Create fresh database session for each test."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def sample_contact(db_session):
    """Create sample contact for tests."""
    contact = Contact(
        name="John Doe",
        email="john@example.com",
        phone="+1234567890",
        status="active"
    )
    db_session.add(contact)
    db_session.commit()
    return contact

# Usage in tests
def test_update_contact(db_session, sample_contact):
    """Use fixtures for clean test setup."""
    sample_contact.name = "Jane Doe"
    db_session.commit()

    updated = db_session.query(Contact).filter_by(id=sample_contact.id).first()
    assert updated.name == "Jane Doe"
```

### 2. Factory Pattern

```python
# tests/fixtures/factories.py

from datetime import datetime, timedelta
import random

class ContactFactory:
    """Generate test contacts with realistic data."""

    @staticmethod
    def create(
        name: str = None,
        email: str = None,
        status: str = "active",
        **kwargs
    ) -> Contact:
        """Create single contact."""
        if not name:
            name = f"Test User {random.randint(1000, 9999)}"
        if not email:
            email = f"test{random.randint(1000, 9999)}@example.com"

        return Contact(
            name=name,
            email=email,
            status=status,
            created_at=kwargs.get("created_at", datetime.utcnow()),
            **kwargs
        )

    @staticmethod
    def create_batch(count: int, **kwargs) -> list[Contact]:
        """Create multiple contacts."""
        return [ContactFactory.create(**kwargs) for _ in range(count)]

# Usage
def test_bulk_operations():
    contacts = ContactFactory.create_batch(100, status="lead")
    # Test with realistic dataset
```

## Async Testing

### 1. Async Test Functions

```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_async_function():
    """Test async operations."""
    result = await some_async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_async_with_timeout():
    """Test with timeout to prevent hanging."""
    try:
        result = await asyncio.wait_for(
            some_slow_async_function(),
            timeout=5.0
        )
        assert result is not None
    except asyncio.TimeoutError:
        pytest.fail("Operation timed out")
```

### 2. Async Fixtures

```python
@pytest.fixture
async def async_client():
    """Async HTTP client fixture."""
    async with httpx.AsyncClient() as client:
        yield client

@pytest.mark.asyncio
async def test_api_endpoint(async_client):
    response = await async_client.get("/api/v1/contacts")
    assert response.status_code == 200
```

## Mocking and Patching

### 1. Mock External Dependencies

```python
from unittest.mock import Mock, patch, AsyncMock

def test_external_api_call():
    """Mock external API to avoid real network calls."""

    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"success": True}

    with patch('requests.get', return_value=mock_response):
        result = fetch_data_from_api()
        assert result["success"] is True

@pytest.mark.asyncio
async def test_async_external_call():
    """Mock async external calls."""

    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"data": "test"}

        result = await fetch_async_data()
        assert result["data"] == "test"
```

### 2. Mock Environment Variables

```python
@patch.dict(os.environ, {
    "DATABASE_URL": "sqlite:///:memory:",
    "API_KEY": "test_key",
    "DEBUG": "true"
})
def test_with_custom_env():
    """Test with specific environment configuration."""
    config = load_config()
    assert config.debug is True
    assert config.api_key == "test_key"
```

## Test Coverage

### 1. Coverage Configuration

```ini
# pytest.ini

[tool:pytest]
testpaths = tests ghl_real_estate_ai
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

addopts =
    --cov=ghl_real_estate_ai
    --cov-report=term-missing
    --cov-report=html
    --cov-report=json
    --cov-branch
    --cov-fail-under=80
    -v
    --strict-markers
```

### 2. Measuring Coverage

```bash
# Run tests with coverage
pytest --cov=ghl_real_estate_ai --cov-report=html

# View coverage report
open htmlcov/index.html

# Check specific file coverage
pytest --cov=ghl_real_estate_ai/services/cache_service.py --cov-report=term-missing
```

## Test Performance

### 1. Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("test@example.com", True),
    ("invalid.email", False),
    ("user@domain", False),
    ("user@domain.com", True),
])
def test_email_validation(input, expected):
    """Test multiple cases efficiently."""
    result = validate_email(input)
    assert result == expected
```

### 2. Test Markers

```python
# Mark slow tests
@pytest.mark.slow
def test_large_dataset_processing():
    """Test with large dataset (slow)."""
    pass

# Mark integration tests
@pytest.mark.integration
def test_database_integration():
    """Test database integration."""
    pass

# Run fast tests only
# pytest -m "not slow"

# Run integration tests only
# pytest -m integration
```

## Test Anti-Patterns (Avoid)

### ❌ BAD: Dependent Tests

```python
# Don't do this - tests should be independent
class TestUserFlow:
    user_id = None

    def test_1_create_user(self):
        self.user_id = create_user()  # Modifies class state

    def test_2_update_user(self):
        update_user(self.user_id)  # Depends on test_1
```

### ✅ GOOD: Independent Tests

```python
class TestUserFlow:
    @pytest.fixture
    def user(self):
        """Each test gets fresh user."""
        return create_user()

    def test_create_user(self, user):
        assert user.id is not None

    def test_update_user(self, user):
        update_user(user.id)
        # Test is self-contained
```

### ❌ BAD: Testing Implementation Details

```python
def test_internal_method():
    """Don't test private methods directly."""
    obj = MyClass()
    result = obj._internal_helper()  # Testing implementation
    assert result == "expected"
```

### ✅ GOOD: Testing Public Interface

```python
def test_public_behavior():
    """Test through public interface."""
    obj = MyClass()
    result = obj.public_method()
    assert result == "expected"  # Implementation details abstracted
```

---

**Reference Updates**: Review when testing practices evolve
**Last Updated**: 2026-01-16
