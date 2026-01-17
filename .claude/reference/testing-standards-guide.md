# Testing Standards Guide

## Testing Pyramid and Strategy

### Unit Tests (70% of test suite)
**Scope**: Single function/method in isolation
**Speed**: < 100ms per test
**Dependencies**: Mocked/stubbed

```typescript
// ✅ GOOD: Fast, isolated unit test
describe('calculateTotal', () => {
  it('should sum item prices correctly', () => {
    const items = [
      { id: '1', price: 10.50 },
      { id: '2', price: 25.25 }
    ];

    const result = calculateTotal(items);

    expect(result).toBe(35.75);
  });

  it('should return 0 for empty array', () => {
    expect(calculateTotal([])).toBe(0);
  });

  it('should handle items with zero price', () => {
    const items = [{ id: '1', price: 0 }, { id: '2', price: 10 }];
    expect(calculateTotal(items)).toBe(10);
  });
});

// ❌ BAD: Slow, dependent on external systems
describe('calculateTotal', () => {
  it('should calculate total', async () => {
    const items = await database.getAllItems(); // External dependency
    const result = calculateTotal(items);
    expect(result).toBeGreaterThan(0); // Vague assertion
  });
});
```

### Integration Tests (20% of test suite)
**Scope**: Multiple components working together
**Speed**: < 5 seconds per test
**Dependencies**: Real but controlled (test database, containers)

```typescript
// ✅ GOOD: Focused integration test
describe('UserService Integration', () => {
  let testDb: TestDatabase;
  let userService: UserService;

  beforeEach(async () => {
    testDb = await TestDatabase.create();
    userService = new UserService(testDb);
  });

  afterEach(async () => {
    await testDb.cleanup();
  });

  it('should create user and persist to database', async () => {
    const userData = { email: 'test@example.com', name: 'Test User' };

    const user = await userService.createUser(userData);

    // Verify in-memory result
    expect(user.id).toBeDefined();
    expect(user.email).toBe(userData.email);

    // Verify database persistence
    const persisted = await testDb.findUser(user.id);
    expect(persisted.email).toBe(userData.email);
    expect(persisted.createdAt).toBeInstanceOf(Date);
  });

  it('should reject duplicate emails', async () => {
    await userService.createUser({ email: 'test@example.com', name: 'First' });

    await expect(
      userService.createUser({ email: 'test@example.com', name: 'Second' })
    ).rejects.toThrow('Email already exists');
  });
});
```

### End-to-End Tests (10% of test suite)
**Scope**: Complete user journeys
**Speed**: < 30 seconds per test
**Dependencies**: Full system (staging environment)

```typescript
// ✅ GOOD: Critical path E2E test
describe('User Registration Flow', () => {
  let browser: Browser;
  let page: Page;

  beforeAll(async () => {
    browser = await chromium.launch();
  });

  beforeEach(async () => {
    page = await browser.newPage();
    await page.goto('/register');
  });

  afterEach(async () => {
    await page.close();
  });

  afterAll(async () => {
    await browser.close();
  });

  it('should complete registration and redirect to dashboard', async () => {
    // Fill registration form
    await page.fill('[data-testid=email-input]', 'newuser@example.com');
    await page.fill('[data-testid=name-input]', 'New User');
    await page.fill('[data-testid=password-input]', 'SecurePass123!');

    // Submit form
    await page.click('[data-testid=register-button]');

    // Verify success
    await page.waitForURL('/dashboard');
    await expect(page.locator('[data-testid=welcome-message]'))
      .toContainText('Welcome, New User');

    // Verify user can perform key action
    await page.click('[data-testid=create-project-button]');
    await expect(page.locator('[data-testid=project-form]')).toBeVisible();
  });
});
```

## Test Organization and Structure

### File Naming and Location

```
src/
├── services/
│   ├── userService.ts
│   ├── userService.test.ts          ← Unit tests co-located
│   ├── paymentService.ts
│   └── paymentService.test.ts
├── __tests__/
│   ├── integration/
│   │   ├── userWorkflow.test.ts     ← Integration tests
│   │   └── paymentFlow.test.ts
│   └── e2e/
│       ├── registration.e2e.ts     ← E2E tests
│       └── checkout.e2e.ts
└── __fixtures__/
    ├── users.ts                     ← Test data factories
    ├── products.ts
    └── orders.ts
```

### Test Data Management

```typescript
// ✅ GOOD: Factory pattern for test data
// __fixtures__/users.ts
export const createTestUser = (overrides: Partial<User> = {}): User => ({
  id: `user-${Date.now()}-${Math.random()}`,
  email: `test-${Date.now()}@example.com`,
  name: 'Test User',
  role: 'user',
  createdAt: new Date(),
  isActive: true,
  ...overrides
});

export const createAdminUser = (): User =>
  createTestUser({ role: 'admin', name: 'Admin User' });

export const createInactiveUser = (): User =>
  createTestUser({ isActive: false });

// Usage in tests
it('should allow admin to delete users', () => {
  const admin = createAdminUser();
  const user = createTestUser();

  const result = userService.deleteUser(user.id, admin);
  expect(result.success).toBe(true);
});

// ❌ BAD: Hardcoded test data
it('should create user', () => {
  const user = {
    id: 'user-123',  // Hardcoded, might conflict
    email: 'test@example.com',  // Reused across tests
    name: 'Test User'
  };
  // Test implementation
});
```

### Mocking Best Practices

```typescript
// ✅ GOOD: Strategic mocking of external dependencies
describe('EmailService', () => {
  let mockEmailProvider: jest.Mocked<EmailProvider>;
  let emailService: EmailService;

  beforeEach(() => {
    // Mock external email service
    mockEmailProvider = {
      sendEmail: jest.fn(),
      validateEmail: jest.fn(),
    };

    emailService = new EmailService(mockEmailProvider);
  });

  it('should send welcome email with correct template', async () => {
    const user = createTestUser();
    mockEmailProvider.sendEmail.mockResolvedValue({ success: true });

    await emailService.sendWelcomeEmail(user);

    expect(mockEmailProvider.sendEmail).toHaveBeenCalledWith({
      to: user.email,
      template: 'welcome',
      data: { name: user.name },
      subject: expect.stringContaining('Welcome')
    });
  });

  it('should handle email provider failures gracefully', async () => {
    const user = createTestUser();
    mockEmailProvider.sendEmail.mockRejectedValue(new Error('Provider down'));

    const result = await emailService.sendWelcomeEmail(user);

    expect(result.success).toBe(false);
    expect(result.error).toContain('Failed to send email');
  });
});

// ❌ BAD: Over-mocking internal logic
describe('UserService', () => {
  it('should validate email', () => {
    const mockValidator = jest.fn().mockReturnValue(true);
    userService.validateEmail = mockValidator; // Mocking implementation detail

    userService.createUser({ email: 'test@example.com' });
    expect(mockValidator).toHaveBeenCalled(); // Testing implementation, not behavior
  });
});
```

## Async Testing Patterns

### Promise and Async/Await Testing

```typescript
// ✅ GOOD: Proper async testing with error handling
describe('AsyncUserService', () => {
  it('should create user asynchronously', async () => {
    const userData = { email: 'test@example.com', name: 'Test User' };

    const user = await userService.createUser(userData);

    expect(user.id).toBeDefined();
    expect(user.email).toBe(userData.email);
  });

  it('should reject invalid data with specific error', async () => {
    const invalidData = { email: 'invalid-email', name: '' };

    await expect(userService.createUser(invalidData))
      .rejects
      .toThrow('Invalid email format');
  });

  it('should handle concurrent operations', async () => {
    const users = Array.from({ length: 5 }, (_, i) =>
      createTestUser({ email: `user${i}@example.com` })
    );

    const createPromises = users.map(user => userService.createUser(user));
    const results = await Promise.allSettled(createPromises);

    const successes = results.filter(r => r.status === 'fulfilled');
    expect(successes).toHaveLength(5);
  });
});

// ❌ BAD: Missing await, no error testing
describe('AsyncUserService', () => {
  it('should create user', () => {
    const result = userService.createUser(userData); // Missing await
    expect(result).toBeDefined(); // Testing Promise object, not result
  });
});
```

### Testing Race Conditions and Timing

```typescript
// ✅ GOOD: Testing race conditions with proper synchronization
describe('RateLimitMiddleware', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('should reset rate limit after time window', async () => {
    const middleware = createRateLimit({ max: 1, windowMs: 60000 });
    const req = createMockRequest();

    // First request should succeed
    await middleware(req, res, next);
    expect(next).toHaveBeenCalled();

    // Second request should be rate limited
    jest.clearAllMocks();
    await middleware(req, res, next);
    expect(res.status).toHaveBeenCalledWith(429);

    // Fast-forward time past window
    jest.advanceTimersByTime(60000);

    // Third request should succeed again
    jest.clearAllMocks();
    await middleware(req, res, next);
    expect(next).toHaveBeenCalled();
  });

  it('should handle concurrent requests correctly', async () => {
    const middleware = createRateLimit({ max: 2, windowMs: 60000 });
    const req = createMockRequest();

    // Fire 5 requests simultaneously
    const promises = Array.from({ length: 5 }, () =>
      middleware(req, res, next)
    );

    await Promise.all(promises);

    // Only first 2 should succeed (rate limit = 2)
    expect(next).toHaveBeenCalledTimes(2);
    expect(res.status).toHaveBeenCalledWith(429);
  });
});
```

## Performance and Load Testing

```typescript
// ✅ GOOD: Performance testing with metrics
describe('Database Performance', () => {
  it('should handle 1000 user lookups within performance budget', async () => {
    const userIds = Array.from({ length: 1000 }, (_, i) => `user-${i}`);

    const startTime = Date.now();

    const results = await Promise.all(
      userIds.map(id => userService.findById(id))
    );

    const endTime = Date.now();
    const duration = endTime - startTime;

    expect(results).toHaveLength(1000);
    expect(duration).toBeLessThan(5000); // 5 second budget

    // Memory usage check
    const memUsage = process.memoryUsage();
    expect(memUsage.heapUsed).toBeLessThan(100 * 1024 * 1024); // 100MB budget
  });
});
```

## Coverage and Quality Metrics

### Coverage Configuration

```json
// jest.config.js
{
  "collectCoverageFrom": [
    "src/**/*.ts",
    "!src/**/*.test.ts",
    "!src/**/*.spec.ts",
    "!src/types/**",
    "!src/**/__fixtures__/**"
  ],
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 90,
      "lines": 80,
      "statements": 80
    },
    "src/services/": {
      "branches": 85,
      "functions": 95,
      "lines": 85,
      "statements": 85
    }
  },
  "coverageReporters": ["text", "html", "lcov"],
  "testTimeout": 30000
}
```

### Quality Gates Script

```typescript
// scripts/test-quality-gates.ts
interface QualityMetrics {
  coverage: CoverageReport;
  performance: PerformanceReport;
  flakiness: FlakinessReport;
}

async function validateQualityGates(): Promise<boolean> {
  const metrics = await gatherMetrics();

  const checks = [
    () => metrics.coverage.branches >= 80,
    () => metrics.coverage.functions >= 90,
    () => metrics.performance.avgTestTime < 100,
    () => metrics.flakiness.flakyTestCount === 0,
    () => metrics.performance.slowTestCount < 5,
  ];

  const results = checks.map(check => check());

  if (results.some(result => !result)) {
    console.error('Quality gates failed:', {
      coverage: metrics.coverage,
      performance: metrics.performance,
      flakiness: metrics.flakiness
    });
    process.exit(1);
  }

  return true;
}
```

## Test Anti-Patterns to Avoid

### ❌ Fragile Tests
```typescript
// Dependent on test execution order
describe('UserService', () => {
  let userId: string;

  it('should create user', () => {
    const user = userService.create({...});
    userId = user.id; // State shared between tests
  });

  it('should find created user', () => {
    const user = userService.findById(userId); // Depends on previous test
    expect(user).toBeDefined();
  });
});
```

### ❌ Testing Implementation Details
```typescript
// Testing private methods or internal state
it('should call private validation method', () => {
  const spy = jest.spyOn(userService as any, '_validateEmail');
  userService.createUser({...});
  expect(spy).toHaveBeenCalled(); // Testing implementation, not behavior
});
```

### ❌ Overuse of Mocks
```typescript
// Mocking everything defeats the purpose of testing
const mockRepository = { findById: jest.fn(), create: jest.fn() };
const mockValidator = { validate: jest.fn() };
const mockLogger = { log: jest.fn() };
const mockEmailer = { send: jest.fn() };

// Test now only verifies mock interactions, not real behavior
```

## Pre-commit Testing Checklist

- [ ] All tests pass locally
- [ ] Coverage thresholds met (80% branch, 90% function)
- [ ] No skipped/pending tests in main branch
- [ ] Performance tests within budget
- [ ] No flaky tests (run suite 3 times)
- [ ] Test files follow naming conventions
- [ ] Mock usage is justified and minimal
- [ ] Integration tests use proper test data cleanup