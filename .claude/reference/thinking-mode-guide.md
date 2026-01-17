# Thinking Mode Allocation Guide

## Complexity Assessment Framework

### Default Mode (No Thinking)

**Use Cases**: Simple, well-understood tasks with clear patterns
**Time Budget**: Immediate response
**Examples**:

```typescript
// Variable renaming
const userId = user.id; // ← Default mode sufficient

// Adding log statements
console.log('Processing user:', userId); // ← Default mode

// Simple function calls
const result = calculateTotal(items); // ← Default mode
```

**Triggers**:
- "Rename variable X to Y"
- "Add logging to this function"
- "Fix typo in string"
- "Update import statement"

---

### Think Mode

**Use Cases**: Moderate complexity requiring planning and consideration
**Time Budget**: 1-3 minutes of reasoning
**Examples**:

```typescript
// ✅ GOOD: API design requiring thinking
// Think about: validation, error handling, response format
async function createUser(userData: UserInput): Promise<UserResponse> {
  // Multiple design decisions:
  // - Input validation strategy
  // - Error response format
  // - Database transaction handling
  // - Password hashing approach
}

// ❌ BAD: Over-thinking simple tasks
const name = user.firstName + ' ' + user.lastName; // Don't use think for this
```

**Decision Points Requiring Think Mode**:
- API contract design (input/output schemas)
- Error handling strategies
- Data validation approaches
- Simple refactoring with multiple moving parts
- Test structure organization
- Database query optimization

**Think Mode Checklist**:
- [ ] Multiple approaches to consider
- [ ] Trade-offs to evaluate
- [ ] Integration points to verify
- [ ] Moderate architectural impact

---

### Think Hard Mode

**Use Cases**: Complex problems requiring deep analysis
**Time Budget**: 3-7 minutes of reasoning
**Examples**:

```typescript
// ✅ GOOD: Complex authentication system
// Think hard about: security, session management, token rotation
class AuthenticationService {
  async authenticate(credentials: LoginCredentials): Promise<AuthResult> {
    // Complex decisions:
    // - JWT vs session-based auth
    // - Refresh token rotation strategy
    // - Rate limiting implementation
    // - Multi-factor authentication flow
    // - Password reset security
    // - Session invalidation
  }
}

// Database schema migration
// Think hard about: data migration, rollback strategy, zero-downtime
class UserMigration {
  async up(): Promise<void> {
    // Consider: backward compatibility, data integrity, performance
  }
}
```

**Decision Points Requiring Think Hard**:
- Security architecture decisions
- Database schema changes with migrations
- Performance-critical algorithms
- Integration with external systems
- Complex state management
- Distributed system design patterns

**Think Hard Checklist**:
- [ ] Security implications significant
- [ ] Performance impact substantial
- [ ] Multiple system boundaries involved
- [ ] Failure modes need analysis
- [ ] Rollback/recovery strategy required

---

### Think Harder Mode

**Use Cases**: Critical systems requiring exhaustive analysis
**Time Budget**: 7-15 minutes of reasoning
**Examples**:

```python
# ✅ GOOD: Financial transaction processing
class PaymentProcessor:
    async def process_payment(self, payment_data: PaymentData) -> TransactionResult:
        # Critical decisions requiring think harder:
        # - ACID transaction guarantees
        # - Idempotency handling
        # - Fraud detection integration
        # - PCI compliance requirements
        # - Money precision and rounding
        # - Failure recovery mechanisms
        # - Audit trail requirements
        # - Regulatory compliance
```

```typescript
// Cryptographic implementation
class SecurityModule {
  async encryptSensitiveData(data: string, context: SecurityContext): Promise<EncryptedData> {
    // Think harder about:
    // - Encryption algorithm selection
    // - Key derivation functions
    // - Salt generation and storage
    // - Timing attack prevention
    // - Key rotation strategy
    // - Compliance requirements (FIPS, SOC2)
  }
}
```

**Decision Points Requiring Think Harder**:
- Cryptographic implementations
- Financial transaction processing
- Healthcare data handling (HIPAA)
- Real-time system critical paths
- Distributed transaction coordination
- Compliance-critical features

**Think Harder Checklist**:
- [ ] Legal/compliance implications
- [ ] Financial impact of errors
- [ ] Life/safety considerations
- [ ] Cryptographic security required
- [ ] Distributed system consistency
- [ ] Zero-tolerance failure scenarios

---

### Ultrathink Mode

**Use Cases**: Fundamental architectural decisions and novel problems
**Time Budget**: 15+ minutes of deep reasoning
**Examples**:

```typescript
// ✅ GOOD: Complete system architecture redesign
// Ultrathink: entire system's future depends on these decisions
interface SystemArchitecture {
  // Fundamental decisions requiring ultrathink:
  // - Microservices vs monolith
  // - Event-driven vs request-response
  // - CQRS vs traditional CRUD
  // - Database sharding strategy
  // - Cross-cutting concerns (logging, monitoring, security)
  // - Technology stack selection
  // - Deployment and DevOps strategy
  // - Team organization impact
  // - 5-year scalability planning
}

// Novel algorithm development
class OptimizationEngine {
  // Custom algorithm for complex optimization problem
  // Ultrathink: mathematical proofs, complexity analysis, edge cases
  calculateOptimalSolution(constraints: ComplexConstraints): Solution {
    // Novel approach requiring deep mathematical reasoning
  }
}
```

**Decision Points Requiring Ultrathink**:
- Complete system architecture design
- Novel algorithm development
- Zero-trust security architecture
- Distributed system consensus mechanisms
- Machine learning model architecture
- Real-time system with sub-millisecond requirements

**Ultrathink Checklist**:
- [ ] Affects entire system architecture
- [ ] Novel problem without established patterns
- [ ] Research-level complexity
- [ ] Multiple conflicting requirements
- [ ] Long-term strategic implications
- [ ] Requires mathematical/theoretical analysis

---

## Mode Selection Decision Tree

```
Is this a well-known pattern I've implemented before?
├─ YES → Default Mode
└─ NO → Continue evaluation

Does this require choosing between 2-3 clear alternatives?
├─ YES → Think Mode
└─ NO → Continue evaluation

Are there security, performance, or integration complexities?
├─ YES → Think Hard Mode
└─ NO → Continue evaluation

Is this a critical system or novel problem requiring research?
├─ YES → Think Harder Mode
└─ NO → Continue evaluation

Does this affect fundamental architecture or require novel solutions?
├─ YES → Ultrathink Mode
└─ NO → Reconsider complexity (likely Think Hard)
```

## Anti-Patterns: When NOT to Use Thinking Modes

### ❌ Over-thinking Simple Tasks
```typescript
// Don't use think mode for:
const fullName = `${firstName} ${lastName}`; // String concatenation
items.push(newItem); // Array manipulation
user.isActive = true; // Property assignment
```

### ❌ Under-thinking Complex Tasks
```typescript
// DO use think harder for:
function processFinancialTransaction(amount: number) {
  return amount; // Missing: validation, precision, audit, compliance
}
```

### ❌ Wrong Mode for Context
```typescript
// Wrong: Using ultrathink for simple refactoring
function extractUtilityFunction() { } // Think mode sufficient

// Wrong: Using default for security-critical code
function hashPassword(password: string) { } // Think harder required
```

## Integration with TDD

- **RED Phase**: Think about test design and edge cases
- **GREEN Phase**: Default mode for minimal implementation
- **REFACTOR Phase**: Think hard about design improvements

## Best Practices

1. **Start Lower**: Begin with lower thinking mode, escalate if needed
2. **Time Box**: Don't exceed thinking time budgets
3. **Document Decisions**: Capture reasoning from think harder/ultrathink
4. **Review Mode Choice**: If solution seems wrong, reconsider complexity level
5. **Context Matters**: Same code might need different thinking based on criticality