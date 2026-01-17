# CI/CD Quick Start Guide

**Get started with the EnterpriseHub CI/CD system in 5 minutes**

---

## Quick Installation

### 1. Install Dependencies (1 minute)

```bash
# Install Python packages
pip install pytest pytest-cov pyyaml jsonschema detect-secrets bandit safety pre-commit

# Or use requirements
pip install -r requirements-dev.txt
```

### 2. Initialize Pre-Commit (1 minute)

```bash
# Install pre-commit hooks
pre-commit install

# Test the installation
pre-commit run --all-files
```

### 3. Verify Setup (1 minute)

```bash
# Run verification script
bash .claude/scripts/verify-ci-cd-setup.sh
```

### 4. Generate Initial Reports (2 minutes)

```bash
# Generate documentation
python .claude/scripts/generate-docs.py

# Generate metrics dashboard
python .claude/scripts/generate-metrics-dashboard.py

# View generated files
ls docs/
ls .claude/metrics/
```

---

## What You Get

### ✅ 6 GitHub Actions Workflows

1. **Skills Validation** - Tests all 14 skills
2. **Hooks Validation** - Validates hook syntax and performance
3. **Plugin Validation** - Comprehensive plugin health checks
4. **Security Scan** - Multi-layer security validation
5. **Cost Optimization** - Token usage and cost monitoring
6. **Release Automation** - Automated plugin releases

### ✅ Pre-Commit Hooks (15+ rules)

- Secrets detection
- Python linting (ruff)
- Type checking (mypy)
- Security scanning (bandit)
- YAML validation
- Shell script validation
- And more...

### ✅ Quality Gates (50+ thresholds)

- Test coverage: 80%
- Security issues: 0 critical/high
- Hook latency: <500ms
- Token budget: 1.5M daily
- And more...

### ✅ Automation Scripts

- Metrics dashboard generator
- Documentation auto-generator
- CI/CD initializer
- Setup verifier

---

## Quick Tests

### Test Pre-Commit Hooks

```bash
# Run all hooks
pre-commit run --all-files

# Run specific hook
pre-commit run ruff
pre-commit run mypy
```

### Test Skills Validation

```bash
# Run integration tests
pytest .claude/skills/scripts/integration_tests.py -v

# Test specific skill structure
python -c "import yaml; print(yaml.safe_load(open('.claude/skills/MANIFEST.yaml'))['metadata'])"
```

### Test Security Scanning

```bash
# Scan for secrets
detect-secrets scan --baseline .secrets.baseline

# Run bandit
bandit -r ghl_real_estate_ai -f json

# Check dependencies
safety check
```

### Generate Reports

```bash
# Metrics dashboard
python .claude/scripts/generate-metrics-dashboard.py
cat .claude/metrics/dashboard.md

# Documentation
python .claude/scripts/generate-docs.py
ls docs/
```

---

## First Commit

### Trigger GitHub Actions

```bash
# Stage all CI/CD files
git add .github/workflows/
git add .pre-commit-config.yaml
git add .claude/quality-gates.yaml
git add .claude/scripts/

# Commit with conventional commit format
git commit -m "chore: add comprehensive CI/CD and quality automation system"

# Push to trigger workflows
git push origin main

# View workflow runs
open https://github.com/YOUR_USERNAME/EnterpriseHub/actions
```

---

## Common Commands

### Daily Development

```bash
# Before committing (automatic with pre-commit)
pre-commit run --all-files

# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=ghl_real_estate_ai --cov-report=term-missing
```

### Weekly Maintenance

```bash
# Update pre-commit hooks
pre-commit autoupdate

# Generate metrics dashboard
python .claude/scripts/generate-metrics-dashboard.py

# Review quality gates
cat .claude/quality-gates.yaml
```

### Monthly Review

```bash
# Generate comprehensive reports
python .claude/scripts/generate-docs.py
python .claude/scripts/generate-metrics-dashboard.py

# Review all generated docs
cat docs/INDEX.md
cat .claude/metrics/dashboard.md
```

---

## Troubleshooting

### Pre-Commit Hook Fails

```bash
# Update hooks
pre-commit autoupdate

# Clear cache
pre-commit clean

# Reinstall
pre-commit uninstall
pre-commit install
```

### GitHub Actions Workflow Fails

1. Check workflow logs in GitHub Actions tab
2. Run the same commands locally
3. Review quality gates for threshold violations
4. Check secrets are properly configured

### Skills Validation Fails

```bash
# Validate MANIFEST.yaml
python -c "import yaml; yaml.safe_load(open('.claude/skills/MANIFEST.yaml'))"

# Run integration tests
pytest .claude/skills/scripts/integration_tests.py -v
```

---

## Key Files

### Configuration Files

- `.github/workflows/` - All GitHub Actions workflows
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `.claude/quality-gates.yaml` - Quality thresholds and standards
- `.claude/settings.json` - Claude Code configuration

### Automation Scripts

- `.claude/scripts/generate-metrics-dashboard.py` - Metrics dashboard
- `.claude/scripts/generate-docs.py` - Documentation generator
- `.claude/scripts/initialize-ci-cd.sh` - System initializer
- `.claude/scripts/verify-ci-cd-setup.sh` - Setup verifier

### Documentation

- `CI_CD_IMPLEMENTATION_SUMMARY.md` - Complete system overview
- `.github/workflows/README.md` - Workflows documentation
- `CI_CD_QUICK_START.md` - This file
- `docs/` - Auto-generated documentation

---

## Next Steps

### Immediate (Today)

1. ✅ Install dependencies
2. ✅ Run verification script
3. ✅ Make first commit
4. ✅ Watch workflows run

### Short-term (This Week)

1. Review metrics dashboard daily
2. Monitor workflow performance
3. Adjust quality gates if needed
4. Gather team feedback

### Long-term (This Month)

1. Analyze cost optimization reports
2. Implement recommended optimizations
3. Create team documentation
4. Plan Phase 2 enhancements

---

## Support

**Documentation**:
- System overview: `CI_CD_IMPLEMENTATION_SUMMARY.md`
- Workflows guide: `.github/workflows/README.md`
- Quality gates: `.claude/quality-gates.yaml`

**Scripts**:
- Initialize: `bash .claude/scripts/initialize-ci-cd.sh`
- Verify: `bash .claude/scripts/verify-ci-cd-setup.sh`
- Metrics: `python .claude/scripts/generate-metrics-dashboard.py`
- Docs: `python .claude/scripts/generate-docs.py`

**GitHub Actions**:
- Workflows: `https://github.com/YOUR_USERNAME/EnterpriseHub/actions`
- Settings: `https://github.com/YOUR_USERNAME/EnterpriseHub/settings/actions`

---

## Success Metrics

After 1 week:
- [ ] All workflows running successfully
- [ ] Pre-commit hooks catching issues
- [ ] Metrics dashboard generated daily
- [ ] Documentation up to date
- [ ] Zero critical security issues

After 1 month:
- [ ] 80%+ test coverage maintained
- [ ] Cost optimization recommendations implemented
- [ ] Team using CI/CD effectively
- [ ] Quality gates tuned for project
- [ ] Process improvements identified

---

**Last Updated**: 2026-01-16
**Quick Start Version**: 1.0.0
**Status**: Ready to Use ✅
