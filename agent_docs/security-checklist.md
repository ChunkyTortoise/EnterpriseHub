# Security Pre-Deploy Checklist

- [ ] No `.env` or secrets in code
- [ ] All endpoints protected by authentication
- [ ] Authorization checked: user owns resource
- [ ] Input validated (email format, length limits)
- [ ] Output escaped (no XSS)
- [ ] SQL parameterized (no injection)
- [ ] No console.logs with sensitive data
- [ ] Dependencies scanned: `npm audit`, `safety check`

## OWASP Essentials
1. **Injection**: Use Prisma/prepared statements
2. **Auth**: 2FA, rate limiting, strong hashing (bcrypt)
3. **Sensitive Data**: HTTPS only, encryption at rest
4. **Access Control**: RBAC on every endpoint
