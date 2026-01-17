# Security Implementation Guide

## Input Validation and Sanitization

### Data Validation Patterns

```typescript
// ✅ GOOD: Comprehensive input validation
import { z } from 'zod';
import DOMPurify from 'dompurify';

const UserInputSchema = z.object({
  email: z.string().email().max(255),
  name: z.string().min(1).max(100).regex(/^[a-zA-Z\s'-]+$/),
  age: z.number().int().min(13).max(150).optional(),
  bio: z.string().max(1000).optional(),
});

class InputValidator {
  static validateUser(input: unknown): UserInput {
    try {
      return UserInputSchema.parse(input);
    } catch (error) {
      throw new ValidationError('Invalid user input', error.issues);
    }
  }

  static sanitizeHTML(input: string): string {
    return DOMPurify.sanitize(input, {
      ALLOWED_TAGS: ['p', 'br', 'strong', 'em'],
      ALLOWED_ATTR: []
    });
  }

  static sanitizeSQL(input: string): string {
    // Remove SQL injection patterns
    return input.replace(/['";\\]/g, '').trim();
  }
}

// Route handler with validation
app.post('/api/users', async (req, res) => {
  try {
    const validatedInput = InputValidator.validateUser(req.body);
    const sanitizedBio = validatedInput.bio
      ? InputValidator.sanitizeHTML(validatedInput.bio)
      : undefined;

    const user = await userService.createUser({
      ...validatedInput,
      bio: sanitizedBio
    });

    res.status(201).json({ success: true, data: user });
  } catch (error) {
    if (error instanceof ValidationError) {
      res.status(400).json({ success: false, error: error.message });
    } else {
      res.status(500).json({ success: false, error: 'Internal server error' });
    }
  }
});

// ❌ BAD: No validation, direct database insertion
app.post('/api/users', async (req, res) => {
  const user = await db.users.create(req.body); // Direct insertion, unsafe!
  res.json(user);
});
```

### SQL Injection Prevention

```typescript
// ✅ GOOD: Parameterized queries with ORM
class UserRepository {
  async findByEmail(email: string): Promise<User | null> {
    // Prisma automatically parameterizes queries
    return await this.db.user.findUnique({
      where: { email }  // Safe: email is parameterized
    });
  }

  async searchUsers(searchTerm: string, limit: number): Promise<User[]> {
    // Safe parameterized raw query when needed
    return await this.db.$queryRaw<User[]>`
      SELECT id, email, name
      FROM users
      WHERE name ILIKE ${`%${searchTerm}%`}  -- Parameterized
      LIMIT ${limit}
    `;
  }
}

// ❌ BAD: String concatenation vulnerable to injection
class UnsafeUserRepository {
  async findByEmail(email: string): Promise<User | null> {
    const query = `SELECT * FROM users WHERE email = '${email}'`; // Vulnerable!
    return await this.db.raw(query);
  }
}
```

## Authentication and Authorization

### JWT Implementation

```typescript
// ✅ GOOD: Secure JWT handling
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import crypto from 'crypto';

interface JWTPayload {
  userId: string;
  role: string;
  sessionId: string;
  iat: number;
  exp: number;
}

class AuthService {
  private readonly accessTokenSecret: string;
  private readonly refreshTokenSecret: string;
  private readonly tokenBlacklist = new Set<string>();

  constructor() {
    this.accessTokenSecret = process.env.JWT_ACCESS_SECRET ||
      (() => { throw new Error('JWT_ACCESS_SECRET required'); })();
    this.refreshTokenSecret = process.env.JWT_REFRESH_SECRET ||
      (() => { throw new Error('JWT_REFRESH_SECRET required'); })();
  }

  async hashPassword(password: string): Promise<string> {
    const saltRounds = 12;
    return await bcrypt.hash(password, saltRounds);
  }

  async validatePassword(password: string, hash: string): Promise<boolean> {
    return await bcrypt.compare(password, hash);
  }

  generateTokenPair(userId: string, role: string): { accessToken: string, refreshToken: string } {
    const sessionId = crypto.randomUUID();

    const accessToken = jwt.sign(
      { userId, role, sessionId },
      this.accessTokenSecret,
      {
        expiresIn: '15m',
        issuer: 'your-app',
        audience: 'your-app-users'
      }
    );

    const refreshToken = jwt.sign(
      { userId, sessionId, type: 'refresh' },
      this.refreshTokenSecret,
      {
        expiresIn: '7d',
        issuer: 'your-app',
        audience: 'your-app-users'
      }
    );

    return { accessToken, refreshToken };
  }

  verifyAccessToken(token: string): JWTPayload {
    if (this.tokenBlacklist.has(token)) {
      throw new Error('Token has been revoked');
    }

    try {
      return jwt.verify(token, this.accessTokenSecret, {
        issuer: 'your-app',
        audience: 'your-app-users'
      }) as JWTPayload;
    } catch (error) {
      throw new Error('Invalid or expired token');
    }
  }

  revokeToken(token: string): void {
    this.tokenBlacklist.add(token);
    // In production, store in Redis or database for persistence
  }
}

// ❌ BAD: Insecure JWT implementation
class UnsafeAuthService {
  generateToken(userId: string): string {
    return jwt.sign({ userId }, 'hardcoded-secret', { expiresIn: '1y' }); // Weak!
  }

  verifyToken(token: string): any {
    return jwt.verify(token, 'hardcoded-secret'); // No validation!
  }
}
```

### Role-Based Access Control (RBAC)

```typescript
// ✅ GOOD: Comprehensive RBAC system
enum Permission {
  READ_USERS = 'read:users',
  WRITE_USERS = 'write:users',
  DELETE_USERS = 'delete:users',
  READ_ADMIN = 'read:admin',
  MANAGE_ROLES = 'manage:roles'
}

interface Role {
  name: string;
  permissions: Permission[];
}

class AuthorizationService {
  private readonly roles: Map<string, Role> = new Map([
    ['admin', {
      name: 'admin',
      permissions: [
        Permission.READ_USERS,
        Permission.WRITE_USERS,
        Permission.DELETE_USERS,
        Permission.READ_ADMIN,
        Permission.MANAGE_ROLES
      ]
    }],
    ['user', {
      name: 'user',
      permissions: [Permission.READ_USERS]
    }],
    ['guest', {
      name: 'guest',
      permissions: []
    }]
  ]);

  hasPermission(userRole: string, requiredPermission: Permission): boolean {
    const role = this.roles.get(userRole);
    return role?.permissions.includes(requiredPermission) ?? false;
  }

  requirePermission(requiredPermission: Permission) {
    return (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      if (!this.hasPermission(req.user.role, requiredPermission)) {
        return res.status(403).json({
          error: 'Insufficient permissions',
          required: requiredPermission,
          userRole: req.user.role
        });
      }

      next();
    };
  }

  requireOwnership(resourceUserId: string, requestingUserId: string): boolean {
    return resourceUserId === requestingUserId;
  }
}

// Usage in routes
const authz = new AuthorizationService();

app.get('/api/admin/users',
  authenticateToken,
  authz.requirePermission(Permission.READ_ADMIN),
  async (req, res) => {
    // Only admins can access this endpoint
  }
);

app.delete('/api/users/:id',
  authenticateToken,
  authz.requirePermission(Permission.DELETE_USERS),
  async (req: AuthenticatedRequest, res) => {
    const { id } = req.params;

    // Additional ownership check for non-admin users
    if (req.user.role !== 'admin' &&
        !authz.requireOwnership(id, req.user.userId)) {
      return res.status(403).json({ error: 'Can only delete own account' });
    }

    await userService.deleteUser(id);
    res.status(204).send();
  }
);

// ❌ BAD: String-based role checking without proper structure
function checkAdmin(req: any, res: any, next: any) {
  if (req.user && req.user.role === 'admin') { // String comparison, fragile
    next();
  } else {
    res.status(403).send('Forbidden');
  }
}
```

## Cryptographic Security

### Data Encryption

```typescript
// ✅ GOOD: Secure encryption with proper key management
import crypto from 'crypto';

class EncryptionService {
  private readonly algorithm = 'aes-256-gcm';
  private readonly keyDerivationIterations = 100000;

  private deriveKey(password: string, salt: Buffer): Buffer {
    return crypto.pbkdf2Sync(
      password,
      salt,
      this.keyDerivationIterations,
      32,
      'sha256'
    );
  }

  encrypt(plaintext: string, password: string): EncryptedData {
    const salt = crypto.randomBytes(16);
    const iv = crypto.randomBytes(12); // GCM IV should be 12 bytes
    const key = this.deriveKey(password, salt);

    const cipher = crypto.createCipherGCM(this.algorithm, key, iv);

    let encrypted = cipher.update(plaintext, 'utf8', 'hex');
    encrypted += cipher.final('hex');

    const authTag = cipher.getAuthTag();

    return {
      encrypted,
      salt: salt.toString('hex'),
      iv: iv.toString('hex'),
      authTag: authTag.toString('hex'),
      algorithm: this.algorithm
    };
  }

  decrypt(encryptedData: EncryptedData, password: string): string {
    const salt = Buffer.from(encryptedData.salt, 'hex');
    const iv = Buffer.from(encryptedData.iv, 'hex');
    const authTag = Buffer.from(encryptedData.authTag, 'hex');
    const key = this.deriveKey(password, salt);

    const decipher = crypto.createDecipherGCM(this.algorithm, key, iv);
    decipher.setAuthTag(authTag);

    let decrypted = decipher.update(encryptedData.encrypted, 'hex', 'utf8');
    decrypted += decipher.final('utf8');

    return decrypted;
  }
}

// ❌ BAD: Weak encryption
class WeakEncryption {
  encrypt(data: string, key: string): string {
    const cipher = crypto.createCipher('aes192', key); // Deprecated algorithm
    let encrypted = cipher.update(data, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    return encrypted; // No authentication, vulnerable to tampering
  }
}
```

### Secure Random Generation

```typescript
// ✅ GOOD: Cryptographically secure random generation
class SecureRandomService {
  generateSecureToken(length: number = 32): string {
    return crypto.randomBytes(length).toString('hex');
  }

  generateSecurePassword(length: number = 16): string {
    const charset = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
    const values = crypto.randomBytes(length);

    return Array.from(values)
      .map(byte => charset[byte % charset.length])
      .join('');
  }

  generateCSRFToken(): string {
    return crypto.randomBytes(32).toString('base64url');
  }

  generateAPIKey(): string {
    const prefix = 'sk_';
    const randomPart = crypto.randomBytes(32).toString('base64url');
    return `${prefix}${randomPart}`;
  }
}

// ❌ BAD: Weak random generation
class WeakRandom {
  generateToken(): string {
    return Math.random().toString(36); // Predictable!
  }
}
```

## Security Headers and HTTPS

### Express Security Middleware

```typescript
// ✅ GOOD: Comprehensive security headers
import helmet from 'helmet';
import rateLimit from 'express-rate-limit';

const app = express();

// Security headers
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      scriptSrc: ["'self'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      fontSrc: ["'self'"],
      objectSrc: ["'none'"],
      mediaSrc: ["'self'"],
      frameSrc: ["'none'"],
    },
  },
  crossOriginEmbedderPolicy: false,
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
    preload: true
  }
}));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: {
    error: 'Too many requests from this IP, please try again later'
  },
  standardHeaders: true,
  legacyHeaders: false,
});

app.use('/api', limiter);

// Stricter rate limiting for authentication endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5, // Only 5 login attempts per 15 minutes
  skipSuccessfulRequests: true,
});

app.use('/api/auth/login', authLimiter);

// CORS configuration
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || ['http://localhost:3000'],
  credentials: true,
  optionsSuccessStatus: 200
}));

// ❌ BAD: No security headers
const unsafeApp = express();
unsafeApp.use(cors({ origin: '*' })); // Allow all origins
// No rate limiting, no security headers
```

## OWASP Top 10 Compliance

### 1. Injection Prevention

```typescript
// ✅ GOOD: Parameterized queries and validation
class SafeUserService {
  async searchUsers(query: string, filters: SearchFilters): Promise<User[]> {
    // Validate input
    const sanitizedQuery = query.trim().substring(0, 100);
    const validatedFilters = SearchFiltersSchema.parse(filters);

    // Use parameterized query
    return this.db.user.findMany({
      where: {
        name: { contains: sanitizedQuery, mode: 'insensitive' },
        role: validatedFilters.role,
        isActive: validatedFilters.isActive ?? true
      },
      take: validatedFilters.limit || 50
    });
  }
}
```

### 2. Broken Authentication Prevention

```typescript
// ✅ GOOD: Secure session management
class SessionManager {
  private activeSessions = new Map<string, SessionData>();

  async createSession(userId: string): Promise<SessionInfo> {
    // Invalidate existing sessions for security
    this.invalidateUserSessions(userId);

    const sessionId = crypto.randomUUID();
    const expiresAt = new Date(Date.now() + 30 * 60 * 1000); // 30 minutes

    const sessionData: SessionData = {
      userId,
      createdAt: new Date(),
      expiresAt,
      lastActivity: new Date()
    };

    this.activeSessions.set(sessionId, sessionData);

    return {
      sessionId,
      expiresAt,
      csrfToken: crypto.randomBytes(32).toString('hex')
    };
  }

  validateSession(sessionId: string): SessionData | null {
    const session = this.activeSessions.get(sessionId);

    if (!session || session.expiresAt < new Date()) {
      this.activeSessions.delete(sessionId);
      return null;
    }

    // Update last activity
    session.lastActivity = new Date();
    return session;
  }

  invalidateUserSessions(userId: string): void {
    for (const [sessionId, session] of this.activeSessions) {
      if (session.userId === userId) {
        this.activeSessions.delete(sessionId);
      }
    }
  }
}
```

### 3. Sensitive Data Exposure Prevention

```typescript
// ✅ GOOD: Data classification and protection
class DataProtectionService {
  // Define data sensitivity levels
  private readonly sensitiveFields = new Set([
    'password', 'ssn', 'creditCard', 'bankAccount'
  ]);

  private readonly piiFields = new Set([
    'email', 'phone', 'address', 'fullName'
  ]);

  sanitizeForLogging(data: any): any {
    if (typeof data !== 'object' || data === null) {
      return data;
    }

    const sanitized = { ...data };

    Object.keys(sanitized).forEach(key => {
      if (this.sensitiveFields.has(key)) {
        sanitized[key] = '[REDACTED]';
      } else if (this.piiFields.has(key) && sanitized[key]) {
        // Partial masking for PII
        const value = sanitized[key].toString();
        sanitized[key] = value.length > 4
          ? `${value.substring(0, 2)}***${value.slice(-2)}`
          : '***';
      }
    });

    return sanitized;
  }

  sanitizeForResponse(user: User, requestingUserRole: string): Partial<User> {
    const publicFields: Partial<User> = {
      id: user.id,
      name: user.name,
      createdAt: user.createdAt
    };

    if (requestingUserRole === 'admin') {
      return {
        ...publicFields,
        email: user.email,
        role: user.role,
        isActive: user.isActive
      };
    }

    return publicFields;
  }
}
```

## Security Testing

```typescript
// ✅ GOOD: Security-focused testing
describe('Security Tests', () => {
  describe('Input Validation', () => {
    it('should reject XSS attempts in user input', async () => {
      const maliciousInput = {
        name: '<script>alert("XSS")</script>',
        bio: '<img src=x onerror=alert("XSS")>'
      };

      await expect(userService.createUser(maliciousInput))
        .rejects
        .toThrow('Invalid user input');
    });

    it('should prevent SQL injection in search', async () => {
      const sqlInjection = "'; DROP TABLE users; --";

      const result = await userService.searchUsers(sqlInjection);

      // Should not throw error and should return safe results
      expect(Array.isArray(result)).toBe(true);
    });
  });

  describe('Authentication', () => {
    it('should reject weak passwords', async () => {
      const weakPasswords = ['123456', 'password', 'abc123'];

      for (const password of weakPasswords) {
        await expect(authService.register('test@example.com', password))
          .rejects
          .toThrow('Password does not meet security requirements');
      }
    });

    it('should invalidate tokens after logout', async () => {
      const { accessToken } = await authService.login('test@example.com', 'StrongPass123!');

      await authService.logout(accessToken);

      expect(() => authService.verifyToken(accessToken))
        .toThrow('Token has been revoked');
    });
  });

  describe('Authorization', () => {
    it('should prevent privilege escalation', async () => {
      const userToken = generateUserToken();

      const response = await request(app)
        .post('/api/admin/users')
        .set('Authorization', `Bearer ${userToken}`)
        .send({ role: 'admin' });

      expect(response.status).toBe(403);
    });
  });
});
```

## Security Checklist

### Pre-Deployment Security Review
- [ ] All inputs validated and sanitized
- [ ] Parameterized queries used (no string concatenation)
- [ ] Strong authentication implemented (bcrypt, JWT with short expiry)
- [ ] Authorization checks on all protected endpoints
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] Rate limiting implemented
- [ ] HTTPS enforced in production
- [ ] Sensitive data properly encrypted at rest
- [ ] Error messages don't leak sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] Dependencies scanned for vulnerabilities
- [ ] Security tests passing

### Production Monitoring
- [ ] Failed authentication attempts monitored
- [ ] Unusual access patterns detected
- [ ] Security headers verified
- [ ] Certificate expiry monitoring
- [ ] Dependency vulnerability scanning automated
- [ ] Security incident response plan ready