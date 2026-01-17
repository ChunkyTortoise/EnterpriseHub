# TDD Patterns and Best Practices

## Classic TDD Patterns

### Fake It ('Til You Make It)
Start with hardcoded values, then gradually generalize.

```python
# RED: Test expects fibonacci(5) == 5
def test_fibonacci_fifth_number():
    assert fibonacci(5) == 5

# GREEN: Hardcode the answer
def fibonacci(n):
    return 5

# Next test forces generalization
def test_fibonacci_sequence():
    assert fibonacci(1) == 1
    assert fibonacci(2) == 1
    assert fibonacci(3) == 2
    assert fibonacci(4) == 3
    assert fibonacci(5) == 5
```

### Triangulation
Use multiple examples to drive toward the general solution.

```typescript
// Multiple tests to triangulate the algorithm
it('should validate single character password as weak', () => {
    expect(validatePassword('a')).toBe('weak');
});

it('should validate medium length password as medium', () => {
    expect(validatePassword('password123')).toBe('medium');
});

it('should validate complex password as strong', () => {
    expect(validatePassword('P@ssw0rd123!')).toBe('strong');
});
```

### Baby Steps
Make the smallest possible change to pass the test.

```python
# Start with empty implementation
def calculate_discount(price, customer_type):
    return 0

# Add just enough logic for first test
def calculate_discount(price, customer_type):
    if customer_type == 'premium':
        return price * 0.1
    return 0

# Gradually add more cases
```

## Test Data Patterns

### Object Mother Pattern
Centralized creation of test objects with meaningful defaults.

```python
class CustomerMother:
    @staticmethod
    def premium_customer():
        return Customer(
            name="John Doe",
            email="john@example.com",
            type="premium",
            registration_date=date(2020, 1, 1)
        )

    @staticmethod
    def basic_customer():
        return Customer(
            name="Jane Smith",
            email="jane@example.com",
            type="basic",
            registration_date=date(2023, 1, 1)
        )
```

### Test Builder Pattern
Fluent interface for creating test data with variations.

```typescript
class OrderBuilder {
    private order: Order = new Order();

    withCustomer(customer: Customer): OrderBuilder {
        this.order.customer = customer;
        return this;
    }

    withItem(item: string, price: number): OrderBuilder {
        this.order.items.push({ item, price });
        return this;
    }

    withDiscount(percentage: number): OrderBuilder {
        this.order.discount = percentage;
        return this;
    }

    build(): Order {
        return this.order;
    }
}

// Usage in tests
const order = new OrderBuilder()
    .withCustomer(premiumCustomer)
    .withItem("laptop", 1000)
    .withDiscount(10)
    .build();
```

## Mocking Strategies

### Test Doubles Hierarchy
1. **Dummy** - Objects passed but never used
2. **Fake** - Working implementation with shortcuts
3. **Stub** - Returns predefined responses
4. **Spy** - Records how methods were called
5. **Mock** - Verifies behavior expectations

### Dependency Injection for Testing
```python
class EmailService:
    def __init__(self, smtp_client=None):
        self.smtp_client = smtp_client or SMTPClient()

    def send_welcome_email(self, user):
        message = f"Welcome {user.name}!"
        return self.smtp_client.send(user.email, message)

# Test with mock
def test_send_welcome_email():
    # Arrange
    mock_smtp = Mock()
    email_service = EmailService(mock_smtp)
    user = User(name="John", email="john@test.com")

    # Act
    result = email_service.send_welcome_email(user)

    # Assert
    mock_smtp.send.assert_called_once_with(
        "john@test.com",
        "Welcome John!"
    )
```

## Advanced TDD Techniques

### Outside-In TDD
Start with acceptance tests, work inward to unit tests.

```python
# Step 1: Acceptance test
def test_user_can_place_order():
    # High-level workflow test
    response = client.post('/orders', json={
        'customer_id': 1,
        'items': [{'id': 1, 'quantity': 2}]
    })
    assert response.status_code == 201
    assert 'order_id' in response.json()

# Step 2: Controller unit tests
def test_order_controller_validates_customer():
    # Test controller behavior
    pass

# Step 3: Service unit tests
def test_order_service_calculates_total():
    # Test business logic
    pass
```

### Characterization Tests
For legacy code without tests.

```python
# Capture current behavior before refactoring
def test_legacy_tax_calculation():
    # Document the existing behavior, even if it seems wrong
    result = legacy_tax_calculator.calculate(100, "CA", "premium")
    assert result == 8.25  # This is what it currently returns

    # After understanding, replace with correct behavior test
```

### Mutation Testing
Verify test quality by introducing bugs.

```bash
# Use mutation testing tools
pip install mutpy
mutpy --target src/ --unit-test tests/
```

## Test Organization Patterns

### Arrange-Act-Assert (AAA)
Clear three-phase structure for all tests.

```typescript
describe('UserRegistration', () => {
    it('should create user with valid data', () => {
        // Arrange
        const userData = {
            email: 'test@example.com',
            password: 'SecurePass123!',
            name: 'Test User'
        };

        // Act
        const result = userService.register(userData);

        // Assert
        expect(result.success).toBe(true);
        expect(result.user.email).toBe('test@example.com');
    });
});
```

### Given-When-Then (BDD Style)
Behavior-driven test structure.

```python
def test_user_authentication():
    # Given a registered user
    user = create_user(email="test@example.com", password="password123")

    # When attempting to login with correct credentials
    result = auth_service.login("test@example.com", "password123")

    # Then authentication should succeed
    assert result.success is True
    assert result.token is not None
```

## Error Handling Patterns

### Exception Testing
```python
def test_should_raise_exception_for_invalid_email():
    with pytest.raises(ValidationError) as exc_info:
        User.create(email="invalid-email", name="Test")

    assert "Invalid email format" in str(exc_info.value)
```

### Error State Testing
```typescript
it('should handle network failure gracefully', async () => {
    // Arrange
    const mockClient = jest.fn().mockRejectedValue(
        new Error('Network timeout')
    );
    const service = new ApiService(mockClient);

    // Act
    const result = await service.fetchUserData(123);

    // Assert
    expect(result.error).toBe('Failed to fetch user data');
    expect(result.data).toBeNull();
});
```

## Performance Testing Patterns

### Timing Constraints
```python
import time

def test_user_search_performance():
    start_time = time.time()

    results = user_service.search("john", limit=100)

    execution_time = time.time() - start_time
    assert execution_time < 0.5  # Must complete within 500ms
    assert len(results) <= 100
```

### Memory Usage Testing
```python
import tracemalloc

def test_memory_usage_within_limits():
    tracemalloc.start()

    # Execute memory-intensive operation
    result = process_large_dataset(data)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert peak < 100 * 1024 * 1024  # Less than 100MB
```

## Refactoring Safety Patterns

### Golden Master Testing
Capture complex output for refactoring safety.

```python
def test_report_generation_golden_master():
    # Generate report with current implementation
    report = generate_monthly_report(sample_data)

    # Compare with approved output
    with open('approved_report.json', 'r') as f:
        approved = json.load(f)

    assert report == approved
```

### Parallel Run Testing
Run old and new implementations side by side.

```python
def test_new_algorithm_matches_old():
    test_cases = load_test_cases()

    for input_data in test_cases:
        old_result = old_algorithm(input_data)
        new_result = new_algorithm(input_data)

        assert new_result == old_result
```

## Common Anti-Patterns to Avoid

### Ice Cream Cone Testing
**Problem:** More UI tests than unit tests
**Solution:** Follow testing pyramid (more unit, fewer integration, minimal UI)

### Test Interdependence
**Problem:** Tests that depend on execution order
**Solution:** Each test should be independent and idempotent

### Over-Mocking
**Problem:** Mocking everything leads to testing implementation
**Solution:** Mock only external dependencies, test real object interactions

### Assertion Roulette
**Problem:** Multiple assertions without clear failure messages
**Solution:** One logical assertion per test, clear assertion messages

### Happy Path Only
**Problem:** Testing only successful scenarios
**Solution:** Include error cases, edge conditions, and boundary values

## TDD Red Flags

Watch for these signs that TDD is going off track:

1. **Tests written after code** - Defeats the purpose
2. **Tests that never fail** - May not be testing anything useful
3. **Brittle tests** - Break when refactoring
4. **Slow test suite** - Discourages running tests frequently
5. **Complex test setup** - Indicates poor design
6. **Testing implementation details** - Couples tests to code structure

Apply these patterns consistently to maintain the discipline and benefits of Test-Driven Development.