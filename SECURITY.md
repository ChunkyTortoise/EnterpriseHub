# Security Policy

## 🔒 Reporting a Vulnerability

The Enterprise Hub team takes security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please DO NOT create a public GitHub issue for security vulnerabilities.**

Instead, report security issues via:

1. **Email**: Send details to the maintainer (check GitHub profile for contact)
2. **GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature
   - Go to the Security tab
   - Click "Report a vulnerability"
   - Fill in the details

### What to Include

Please include as much information as possible:

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Full paths of affected source files
- Location of the affected code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment
- Suggested fix (if you have one)

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Depends on severity
  - **Critical**: Within 7 days
  - **High**: Within 14 days
  - **Medium**: Within 30 days
  - **Low**: Within 90 days

## 🛡️ Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅ Yes             |
| Older   | ❌ No              |

We only support the latest version. Please update to the most recent release.

## 🔐 Security Best Practices

### For Users

1. **Never commit secrets**
   - Use `.env` files for API keys (already in `.gitignore`)
   - Use Streamlit Secrets for cloud deployment
   - Never hardcode credentials

2. **Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Use HTTPS**
   - Always access the app over HTTPS in production
   - Streamlit Cloud provides this by default

4. **Validate inputs**
   - Be cautious with data from untrusted sources
   - The app validates user inputs, but always verify external data

### For Contributors

1. **Code Review**
   - All PRs require review before merging
   - Security-sensitive changes need extra scrutiny

2. **Dependency Security**
   - Run `pip-audit` to check for known vulnerabilities
   - Keep dependencies up to date

3. **Input Validation**
   - Sanitize all user inputs
   - Use type hints and validation

4. **Error Handling**
   - Never expose sensitive information in error messages
   - Log errors securely

## Security Architecture

### Current Implementation

1. **API Rate Limiting** -- 100 req/min per client, 10 req/s for CRM sync
2. **Authentication** -- JWT tokens (1-hour expiry), API key validation
3. **Data Protection** -- PII encrypted at rest (Fernet), parameterized queries only
4. **Caching** -- 3-tier cache (L1 memory, L2 Redis, L3 PostgreSQL), no PII in cache keys
5. **Input Validation** -- Pydantic V2 strict validation at all API boundaries
6. **Compliance** -- DRE, Fair Housing, CCPA, CAN-SPAM adherence

## 📝 Security Updates

Security updates will be:
- Released as soon as possible
- Documented in release notes
- Announced in README

## 🙏 Acknowledgments

We appreciate responsible disclosure and will acknowledge contributors who report valid security issues (unless they prefer to remain anonymous).

---

**Thank you for helping keep Enterprise Hub secure! 🔒**
