# Language-Specific Standards Guide

## TypeScript/JavaScript Standards

### Type Safety and Strict Mode

```typescript
// ✅ GOOD: Strict TypeScript with explicit types
interface UserData {
  readonly id: string;
  email: string;
  name: string;
  createdAt: Date;
  preferences?: UserPreferences;
}

async function fetchUserWithOrders(userId: string): Promise<UserWithOrders> {
  const user = await userRepository.findById(userId);
  if (!user) {
    throw new NotFoundError(`User ${userId} not found`);
  }

  const orders = await orderRepository.findByUserId(userId);
  return { ...user, orders };
}

// ❌ BAD: Loose typing, unclear contracts
function getU(uid: any): any {
  return db.user.findOne(uid).then((u: any) =>
    db.order.find({uid}).then((o: any) => ({u, o}))
  );
}
```

### Error Handling Patterns

```typescript
// ✅ GOOD: Custom error classes with proper typing
export class ValidationError extends Error {
  constructor(
    message: string,
    public readonly field: string,
    public readonly value: unknown
  ) {
    super(message);
    this.name = 'ValidationError';
  }
}

// Result pattern for operations that can fail
type Result<T, E = Error> = {
  success: true;
  data: T;
} | {
  success: false;
  error: E;
};

async function createUser(userData: UserInput): Promise<Result<User, ValidationError>> {
  try {
    const validated = await validateUserData(userData);
    const user = await userRepository.create(validated);
    return { success: true, data: user };
  } catch (error) {
    if (error instanceof ValidationError) {
      return { success: false, error };
    }
    throw error; // Re-throw unexpected errors
  }
}

// ❌ BAD: Silent failures, unclear error types
async function createUser(userData: any) {
  try {
    return await db.user.create(userData);
  } catch (e) {
    return null; // Lost error information
  }
}
```

### Async/Await Best Practices

```typescript
// ✅ GOOD: Proper async/await with error handling
async function processUserBatch(userIds: string[]): Promise<ProcessingResult[]> {
  const results = await Promise.allSettled(
    userIds.map(async (id) => {
      const user = await fetchUser(id);
      const enriched = await enrichUserData(user);
      return await processUser(enriched);
    })
  );

  return results.map((result, index) => ({
    userId: userIds[index],
    success: result.status === 'fulfilled',
    data: result.status === 'fulfilled' ? result.value : undefined,
    error: result.status === 'rejected' ? result.reason : undefined,
  }));
}

// ❌ BAD: Mixed promise patterns, poor error handling
function processUsers(userIds: any[]) {
  return Promise.all(userIds.map(id =>
    fetchUser(id).then(user =>
      enrichUserData(user).then(enriched =>
        processUser(enriched).catch(() => null)
      )
    )
  ));
}
```

### React Component Patterns

```tsx
// ✅ GOOD: Functional component with proper typing
interface UserProfileProps {
  userId: string;
  onUpdate?: (user: User) => void;
  className?: string;
}

export const UserProfile: React.FC<UserProfileProps> = ({
  userId,
  onUpdate,
  className
}) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const loadUser = async () => {
      try {
        setLoading(true);
        const userData = await fetchUser(userId);
        if (!cancelled) {
          setUser(userData);
          setError(null);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Unknown error');
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadUser();
    return () => { cancelled = true; };
  }, [userId]);

  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!user) return null;

  return (
    <div className={className}>
      <h2>{user.name}</h2>
      <p>{user.email}</p>
    </div>
  );
};

// ❌ BAD: No types, missing cleanup, poor error handling
export const UserProfile = ({ userId, onUpdate }) => {
  const [user, setUser] = useState();

  useEffect(() => {
    fetchUser(userId).then(setUser);
  }, [userId]);

  return <div>{user?.name}</div>;
};
```

---

## Python Standards

### Type Hints and Documentation

```python
# ✅ GOOD: Complete type hints with docstrings
from typing import Optional, List, Dict, Union
from decimal import Decimal
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UserData:
    id: str
    email: str
    name: str
    created_at: datetime
    is_active: bool = True

class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(
        self,
        email: str,
        name: str,
        metadata: Optional[Dict[str, str]] = None
    ) -> UserData:
        """Create a new user with validation.

        Args:
            email: Valid email address
            name: User's display name
            metadata: Optional user metadata

        Returns:
            Created user data

        Raises:
            ValidationError: If email format invalid
            DuplicateError: If email already exists
        """
        if not self._validate_email(email):
            raise ValidationError(f"Invalid email format: {email}")

        existing = await self._repository.find_by_email(email)
        if existing:
            raise DuplicateError(f"Email already exists: {email}")

        return await self._repository.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )

# ❌ BAD: No types, unclear function contracts
def create_user(email, name, metadata=None):
    # What types? What errors? What does it return?
    return db.create(email, name, metadata)
```

### Error Handling and Validation

```python
# ✅ GOOD: Custom exceptions with proper hierarchy
class UserServiceError(Exception):
    """Base exception for user service operations."""
    pass

class ValidationError(UserServiceError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str, value: str) -> None:
        super().__init__(message)
        self.field = field
        self.value = value

class DuplicateError(UserServiceError):
    """Raised when attempting to create duplicate resource."""
    pass

# Result pattern for operations that can fail
from typing import Union, TypeVar, Generic

T = TypeVar('T')
E = TypeVar('E', bound=Exception)

class Result(Generic[T, E]):
    def __init__(self, value: T = None, error: E = None) -> None:
        self._value = value
        self._error = error

    @property
    def is_success(self) -> bool:
        return self._error is None

    @property
    def value(self) -> T:
        if self._error:
            raise self._error
        return self._value

    @property
    def error(self) -> Optional[E]:
        return self._error

async def safe_create_user(email: str, name: str) -> Result[UserData, UserServiceError]:
    try:
        user = await user_service.create_user(email, name)
        return Result(value=user)
    except UserServiceError as e:
        return Result(error=e)

# ❌ BAD: Generic exceptions, lost error context
def create_user(email, name):
    try:
        return db.create_user(email, name)
    except Exception:
        return None  # Lost all error information
```

### Async Patterns and Context Management

```python
# ✅ GOOD: Proper async patterns with context managers
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

class DatabaseService:
    async def __aenter__(self) -> 'DatabaseService':
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._disconnect()

@asynccontextmanager
async def database_transaction() -> AsyncIterator[DatabaseService]:
    """Context manager for database transactions with rollback."""
    db = DatabaseService()
    try:
        await db.begin_transaction()
        yield db
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    finally:
        await db.close()

async def process_user_batch(user_ids: List[str]) -> List[ProcessResult]:
    """Process users in parallel with proper error handling."""
    semaphore = asyncio.Semaphore(10)  # Limit concurrent operations

    async def process_single_user(user_id: str) -> ProcessResult:
        async with semaphore:
            try:
                async with database_transaction() as db:
                    user = await db.fetch_user(user_id)
                    result = await process_user_data(user)
                    await db.save_result(result)
                    return ProcessResult(success=True, user_id=user_id, data=result)
            except Exception as e:
                logger.exception(f"Failed to process user {user_id}")
                return ProcessResult(success=False, user_id=user_id, error=str(e))

    tasks = [process_single_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks, return_exceptions=False)

# ❌ BAD: No connection management, no error boundaries
async def process_users(user_ids):
    results = []
    for uid in user_ids:
        user = await db.fetch_user(uid)  # No connection management
        result = await process_user_data(user)  # No error handling
        results.append(result)
    return results
```

### Dataclass and Pydantic Integration

```python
# ✅ GOOD: Pydantic models for validation
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    role: UserRole = UserRole.USER
    age: Optional[int] = Field(None, ge=13, le=150)

    @validator('name')
    def name_must_not_be_only_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be only whitespace')
        return v.strip()

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    name: str
    role: UserRole
    created_at: datetime
    is_active: bool

    class Config:
        orm_mode = True  # Allow creation from ORM objects

# ❌ BAD: Manual validation, no type safety
def validate_user_data(data):
    errors = []
    if not data.get('email') or '@' not in data['email']:
        errors.append('Invalid email')
    if not data.get('name') or len(data['name']) > 100:
        errors.append('Invalid name')
    return errors
```

---

## Common Anti-Patterns Across Languages

### ❌ Inconsistent Error Handling
```typescript
// Mixed error patterns in same codebase
function a() { throw new Error(); }
function b() { return null; }
function c() { return { error: 'failed' }; }
```

### ❌ Weak Typing
```python
# Using Any/any everywhere defeats type safety
def process_data(data: Any) -> Any:
    return data
```

### ❌ Side Effects in Pure Functions
```typescript
// Function has hidden side effects
function calculateTotal(items: Item[]): number {
  logActivity('Calculating total'); // Side effect!
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

### ❌ Inconsistent Naming Conventions
```python
# Mixed naming styles
class UserService:
    def createUser(self):     # camelCase in Python
        pass

    def find_by_id(self):     # snake_case
        pass
```

## Code Review Checklist

### TypeScript/JavaScript
- [ ] Strict TypeScript mode enabled
- [ ] No `any` types without justification
- [ ] Async/await preferred over Promises
- [ ] Error handling consistent across modules
- [ ] React hooks follow rules (dependencies, cleanup)

### Python
- [ ] Type hints on all public functions
- [ ] Docstrings follow Google/NumPy style
- [ ] Async context managers for resources
- [ ] Custom exceptions inherit from appropriate base
- [ ] Pydantic models for data validation