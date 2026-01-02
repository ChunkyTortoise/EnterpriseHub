# TDD: RED → GREEN → REFACTOR

## RED Phase (Failing Test)
```typescript
it('should reject requests exceeding rate limit', async () => {
  const agent = createTestAgent();
  for (let i = 0; i < 101; i++) {
    await agent.get('/api/users');  // Trigger 101st request
  }
  expect(agent.lastResponse.status).toBe(429);  // Too Many Requests
});
```

## GREEN Phase (Minimal Implementation)
```typescript
app.use(rateLimit({
  windowMs: 15 * 60 * 1000,  // 15 minutes
  max: 100  // Requests per window
}));
```

## REFACTOR Phase (Clean Up)
- Extract magic numbers to constants
- Add comments explaining *why*
- Verify tests still pass
- Commit separately
