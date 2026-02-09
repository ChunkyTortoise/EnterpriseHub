# Security Policy

## Reporting a Vulnerability

The {project} team takes security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please DO NOT create a public GitHub issue for security vulnerabilities.**

Instead, report security issues via:

1. **GitHub Security Advisory**: Use GitHub's private vulnerability reporting feature
   - Go to the Security tab
   - Click "Report a vulnerability"
   - Fill in the details
2. **Email**: Send details to the maintainer (check GitHub profile for contact)

### What to Include

- Type of vulnerability (e.g., XSS, SQL injection, authentication bypass)
- Full paths of affected source files
- Location of the affected code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact assessment

### Response Timeline

| Severity | Initial Response | Fix Timeline |
|----------|-----------------|-------------|
| Critical | 48 hours | 7 days |
| High | 48 hours | 14 days |
| Medium | 7 days | 30 days |
| Low | 7 days | 90 days |

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest | Yes |
| Older | No |

## Security Best Practices

### For Users

1. **Never commit secrets** -- Use `.env` files (already in `.gitignore`) or environment variables
2. **Keep dependencies updated** -- Run `pip install --upgrade -r requirements.txt`
3. **Use HTTPS** in production
4. **Validate inputs** -- The app validates user inputs, but always verify data from untrusted sources

### For Contributors

1. **Code Review** -- All PRs require review before merging
2. **Dependency Security** -- Run `pip-audit` to check for known vulnerabilities
3. **Input Validation** -- Sanitize all user inputs, use Pydantic models
4. **Error Handling** -- Never expose sensitive information in error messages

## Acknowledgments

We appreciate responsible disclosure and will acknowledge contributors who report valid security issues (unless they prefer to remain anonymous).
