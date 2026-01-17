# CI/CD & Quality Automation System

Comprehensive CI/CD pipeline and quality automation for EnterpriseHub project and plugin.

---

## Overview

This CI/CD system provides:

- **Skills Validation**: Tests individual skills and cross-skill compatibility
- **Hooks Validation**: Validates hook syntax, security patterns, and performance
- **Plugin Validation**: Comprehensive plugin health checks
- **Security Scanning**: Secrets detection, dependency audits, code security
- **Cost Optimization**: Token usage analysis and cost monitoring
- **Automated Releases**: Plugin packaging and distribution

---

## Workflows

### 1. Skills Validation (`skills-validation.yml`)

**Triggers**:
- Push to `.claude/skills/**`
- Pull requests affecting skills
- Manual dispatch

**Jobs**:
- ✅ Validate MANIFEST.yaml structure
- ✅ Test each skill individually (14 skills)
- ✅ Cross-skill compatibility matrix
- ✅ Generate coverage report

**Run time**: ~5-8 minutes

### 2. Hooks Validation (`hooks-validation.yml`)

**Triggers**:
- Push to `.claude/hooks/**`
- Pull requests affecting hooks
- Manual dispatch

**Jobs**:
- ✅ YAML and shell script syntax validation
- ✅ Security pattern tests (block secrets, dangerous commands)
- ✅ Performance benchmarks (< 500ms latency)
- ✅ Integration tests with skills

**Run time**: ~3-5 minutes

### 3. Plugin Validation (`plugin-validation.yml`)

**Triggers**:
- Push to `claude-real-estate-ai-plugin/**`
- Pull requests affecting plugin
- Manual dispatch

**Jobs**:
- ✅ Validate plugin.json manifest
- ✅ Test all plugin skills
- ✅ Validate hook scripts
- ✅ Test MCP server configurations
- ✅ Check documentation completeness
- ✅ Full integration test suite

**Run time**: ~6-10 minutes

### 4. Security Scan (`security-scan.yml`)

**Triggers**:
- Push to any Python/JS/TS files
- Pull requests
- Weekly schedule (Sunday midnight)
- Manual dispatch

**Jobs**:
- 🔐 Secrets detection (detect-secrets)
- 🛡️ Python security scan (Bandit)
- 📦 Dependency audit (Safety)
- ⚡ Code quality checks (complexity, SQL injection)

**Run time**: ~4-6 minutes

### 5. Cost Optimization Check (`cost-optimization-check.yml`)

**Triggers**:
- Every 6 hours (schedule)
- Push to cost-related files
- Manual dispatch

**Jobs**:
- 📊 Token usage analysis
- 🔧 MCP server overhead monitoring
- 💚 Session health checks
- 📄 Generate optimization report

**Run time**: ~2-3 minutes

**Artifacts**:
- Cost optimization report (Markdown)
- Token usage analysis (JSON)

### 6. Release Automation (`release.yml`)

**Triggers**:
- Git tags matching `v*.*.*`
- Manual dispatch with version input

**Jobs**:
- ✅ Validate release (all tests)
- 📦 Build plugin packages (.tar.gz, .zip)
- 📝 Generate changelog from commits
- 🚀 Create GitHub release
- 📚 Update documentation
- 📢 Post release announcement

**Run time**: ~8-12 minutes

**Artifacts**:
- Plugin packages (tar.gz, zip)
- Changelog (Markdown)
- Release notes

---

## Pre-Commit Hooks

Integrated `.pre-commit-config.yaml` provides git-level validation:

### Hooks Included

**Security**:
- `detect-secrets`: Scan for secrets
- `detect-private-key`: Block private keys
- `bandit`: Python security scanning

**Code Quality**:
- `ruff`: Fast Python linting and formatting
- `mypy`: Type checking
- `shellcheck`: Shell script validation
- `yamllint`: YAML validation
- `markdownlint`: Markdown linting

**Project-Specific**:
- Validate Claude settings JSON
- Validate skills MANIFEST.yaml
- Validate hook syntax

### Installation

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Quality Gates

Defined in `.claude/quality-gates.yaml`:

### Code Quality Thresholds

- **Test Coverage**: 80% minimum (lines, branches)
- **Type Coverage**: 90% typed functions
- **Security Issues**: 0 critical/high, 0 medium, max 5 low
- **Complexity**: Max 10 cyclomatic complexity
- **Duplication**: Max 5% code duplication

### Performance Thresholds

- **Hooks**: < 500ms max latency, < 100ms average
- **Skills**: < 1000ms load time, < 5000 tokens
- **API**: < 2000ms max response, < 500ms average
- **Tests**: < 100ms per unit test, < 10min full suite

### Cost Thresholds

- **Daily Budget**: 1.5M tokens
- **Monthly Budget**: 45M tokens
- **MCP Overhead**: < 5000 tokens, max 3 servers
- **Cost per Feature**: < $5 target

---

## Scripts

### Generate Metrics Dashboard

```bash
python .claude/scripts/generate-metrics-dashboard.py
```

**Generates**:
- `.claude/metrics/dashboard.md`: Visual metrics dashboard
- `.claude/metrics/dashboard-data.json`: Raw metrics data

**Metrics Collected**:
- Skill usage and success rates
- Tool usage patterns
- Hook performance
- Token usage and costs
- Session health

### Generate Documentation

```bash
python .claude/scripts/generate-docs.py
```

**Generates**:
- `docs/SKILLS_CATALOG.md`: Complete skill catalog
- `docs/HOOKS.md`: Hooks documentation
- `docs/MCP_SERVERS.md`: MCP server reference
- `docs/METRICS.md`: Metrics report
- `docs/INDEX.md`: Documentation index

---

## Local Testing

### Test Individual Workflows

```bash
# Skills validation
pytest .claude/skills/scripts/integration_tests.py -v

# Hooks validation
bash .claude/scripts/hook_validator.sh

# Security scan
bandit -r ghl_real_estate_ai -f json
detect-secrets scan --baseline .secrets.baseline

# Generate metrics
python .claude/scripts/generate-metrics-dashboard.py
```

### Test Pre-Commit Hooks

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff --all-files
pre-commit run mypy --all-files
```

---

## Continuous Improvement

### Weekly Tasks

1. Review metrics dashboard for optimization opportunities
2. Check cost optimization report
3. Update quality gates if needed
4. Review skill usage patterns

### Monthly Tasks

1. Analyze full month's metrics
2. Update cost budgets based on usage
3. Review and adjust performance thresholds
4. Plan skill improvements

### Quarterly Tasks

1. Review all quality gates
2. Update CI/CD workflows
3. Assess ROI of automation
4. Plan next phase improvements

---

## Monitoring & Alerts

### GitHub Actions Status

Monitor workflow runs at: `https://github.com/USERNAME/EnterpriseHub/actions`

### Artifacts

All workflows save artifacts that can be downloaded:
- Test reports
- Coverage reports
- Security scan results
- Cost optimization reports
- Plugin packages

### Notifications

Configure GitHub Actions notifications in repository settings:
- Email notifications
- Slack integration
- Discord webhooks

---

## Troubleshooting

### Workflow Failures

**Skills Validation Failed**:
- Check MANIFEST.yaml syntax
- Verify skill file structure
- Run integration tests locally

**Security Scan Failed**:
- Review Bandit report for issues
- Check for hardcoded secrets
- Update vulnerable dependencies

**Release Failed**:
- Verify version consistency (tag vs plugin.json)
- Ensure all tests pass
- Check GitHub permissions

### Pre-Commit Hook Issues

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit uninstall
pre-commit install
```

---

## Cost Efficiency

### Workflow Optimization

- **Cache dependencies**: Speeds up runs by 50%
- **Parallel jobs**: Run independent tests concurrently
- **Conditional execution**: Skip unnecessary jobs
- **Artifact retention**: 30 days (configurable)

### Estimated Costs

Free tier GitHub Actions includes:
- 2,000 minutes/month for private repos
- Unlimited for public repos

Current usage: ~150-200 minutes/month

---

## Security

### Secrets Management

**Never commit**:
- API keys
- Passwords
- Tokens
- Certificates

**Use GitHub Secrets** for:
- ANTHROPIC_API_KEY
- GHL_API_KEY
- Deployment credentials

### Workflow Permissions

Minimal permissions by default:
- Read access to code
- Write for releases only
- No secrets in pull request workflows

---

## Future Enhancements

### Planned Improvements

1. **AI-Powered Code Review**: Claude-based PR review comments
2. **Performance Regression Detection**: Benchmark tracking
3. **Visual Regression Testing**: UI screenshot comparisons
4. **Automated Dependency Updates**: Renovate bot integration
5. **Cost Prediction**: ML-based cost forecasting

---

## Support

For issues or questions:

1. Check workflow logs in GitHub Actions
2. Review documentation in `docs/`
3. Run local tests to reproduce issues
4. Open issue with logs and context

---

**Last Updated**: 2026-01-16
**System Version**: 1.0.0
**Status**: Production Ready ✅
