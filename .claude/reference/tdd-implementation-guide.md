# TDD Implementation Guide

## Core TDD Workflow: RED → GREEN → REFACTOR

### Phase 1: RED - Write Failing Test

**Goal**: Document expected behavior before implementation

```typescript
// ✅ GOOD: Descriptive test that documents behavior
describe('RateLimitMiddleware', () => {
  describe('when request limit exceeded', () => {
    it('should reject request with 429 status and retry-after header', async () => {
      // Arrange
      const middleware = createRateLimit({ max: 2, windowMs: 60000 });
      const mockRequest = createMockRequest({ ip: '192.168.1.1' });

      // Act: Exceed rate limit
      await middleware(mockRequest, mockResponse, nextFunction); // 1st request
      await middleware(mockRequest, mockResponse, nextFunction); // 2nd request
      await middleware(mockRequest, mockResponse, nextFunction); // 3rd request (should fail)

      // Assert
      expect(mockResponse.status).toHaveBeenCalledWith(429);
      expect(mockResponse.headers['retry-after']).toBe('60');
      expect(nextFunction).not.toHaveBeenCalled();
    });
  });
});

// ❌ BAD: Vague test name, unclear expectations
it('should work with rate limiting', () => {
  // Test implementation unclear
});
```

**RED Phase Checklist**:
- [ ] Test name explains business behavior (not technical implementation)
- [ ] Test includes edge cases (empty input, null values, boundary conditions)
- [ ] Test fails for the right reason (not syntax errors)
- [ ] Arrange-Act-Assert pattern followed
- [ ] Test is isolated (no dependencies on other tests)

### Phase 2: GREEN - Minimal Implementation

**Goal**: Make the test pass with simplest possible code

```typescript
// ✅ GOOD: Minimal implementation that passes test
export function createRateLimit(options: RateLimitOptions) {
  const requests = new Map<string, number[]>();

  return async (req: Request, res: Response, next: NextFunction) => {
    const key = req.ip;
    const now = Date.now();
    const windowStart = now - options.windowMs;

    // Get existing requests for this IP
    const userRequests = requests.get(key) || [];
    const validRequests = userRequests.filter(time => time > windowStart);

    if (validRequests.length >= options.max) {
      res.status(429).header('retry-after', Math.ceil(options.windowMs / 1000));
      return;
    }

    // Track this request
    validRequests.push(now);
    requests.set(key, validRequests);
    next();
  };
}
```

**GREEN Phase Rules**:
- Write only enough code to pass the current test
- Ignore code quality temporarily (duplication is OK)
- No premature optimization
- Focus on correctness, not performance
- Hardcode values if it makes test pass

### Phase 3: REFACTOR - Improve Design

**Goal**: Improve code quality while keeping tests green

```typescript
// ✅ GOOD: Refactored with better design
interface RateLimitStore {
  get(key: string): Promise<number[]>;
  set(key: string, requests: number[]): Promise<void>;
}

export function createRateLimit(options: RateLimitOptions) {
  const store = options.store || new MemoryStore();

  return async (req: Request, res: Response, next: NextFunction) => {
    const key = generateKey(req, options);
    const now = Date.now();

    const isAllowed = await checkRateLimit(store, key, now, options);

    if (!isAllowed) {
      return sendRateLimitResponse(res, options);
    }

    await recordRequest(store, key, now, options);
    next();
  };
}
```

**REFACTOR Checklist**:
- [ ] Extract meaningful functions and classes
- [ ] Apply SOLID principles (Single Responsibility, Open/Closed)
- [ ] Remove code duplication (DRY)
- [ ] Improve naming and readability
- [ ] Add proper error handling
- [ ] All tests still pass
- [ ] No new functionality added

## Test Organization Patterns

### Co-located Test Structure
```
src/
├── middleware/
│   ├── rateLimit.ts
│   ├── rateLimit.test.ts     ← Same directory as implementation
│   ├── auth.ts
│   └── auth.test.ts
├── services/
│   ├── userService.ts
│   └── userService.test.ts
└── __fixtures__/
    ├── users.fixture.ts      ← Shared test data
    └── requests.fixture.ts
```

### Test Naming Conventions
```typescript
describe('[ModuleName]', () => {
  describe('[methodName]', () => {
    it('should [expected outcome] when [specific condition]', () => {
      // Test implementation
    });
  });
});
```

### Test Data Factories
```typescript
// __fixtures__/users.fixture.ts
export const createTestUser = (overrides = {}) => ({
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  createdAt: new Date('2024-01-01'),
  ...overrides
});

// Usage in tests
it('should handle multiple users', () => {
  const users = createTestUsers(5);
  const result = userService.processUsers(users);
  expect(result).toHaveLength(5);
});
```

## Coverage and Quality Metrics

### Coverage Thresholds
```json
{
  "coverageThreshold": {
    "global": {
      "branches": 80,
      "functions": 90,
      "lines": 80,
      "statements": 80
    }
  }
}
```

### Quality Gates
- All tests must pass before commit
- 80% branch coverage minimum for new code
- No skipped tests in main branch
- Test execution time < 30 seconds for unit tests
- Integration tests < 5 minutes

Remember: TDD is about design, not just testing. Use tests to drive better API design and clearer interfaces.