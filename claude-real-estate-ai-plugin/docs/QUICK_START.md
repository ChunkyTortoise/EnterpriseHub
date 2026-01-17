# Quick Start Guide

Get started with the Claude Real Estate AI Accelerator in 5 minutes.

## Installation

### Prerequisites

- **Python**: 3.11+ ([Download](https://www.python.org/downloads/))
- **Node.js**: 18+ (optional, [Download](https://nodejs.org/))
- **Claude Code**: 2.1.0+ ([Installation Guide](https://docs.anthropic.com/claude/docs/claude-code))

### Install Plugin

```bash
# Clone or install the plugin
claude plugin install https://github.com/enterprisehub/claude-real-estate-ai-plugin.git

# Or install from local directory
cd claude-real-estate-ai-plugin
./scripts/install.sh
```

## First Steps

### 1. Explore Available Skills

```bash
# View all skills
cat skills/MANIFEST.yaml

# See skill categories
ls skills/
```

**Skill Categories:**
- `testing/` - TDD, race conditions, anti-patterns
- `design/` - UI/UX, theming, components
- `deployment/` - Vercel, Railway, validation
- `real-estate-ai/` - Property matching, lead scoring
- `cost-optimization/` - Token usage, model selection
- `analytics/` - Performance metrics, ROI calculation

### 2. Try Your First Skill

**Test-Driven Development:**

```bash
# Invoke TDD skill for a new feature
invoke test-driven-development --feature="user-authentication"
```

**This will:**
1. Guide you through RED phase (write failing test)
2. Guide you through GREEN phase (implement feature)
3. Guide you through REFACTOR phase (clean up code)
4. Validate test coverage and quality

**Expected Output:**
```
✓ Test file created: tests/test_user_authentication.py
✓ Test fails as expected (RED phase)
✓ Implementation created: src/user_authentication.py
✓ Tests pass (GREEN phase)
✓ Code refactored for quality
✓ Coverage: 95% (target: 80%)
```

### 3. Deploy Your Application

**Deploy to Railway:**

```bash
invoke railway-deploy --project="my-real-estate-app"
```

**This will:**
1. Validate Railway CLI installation
2. Check environment configuration
3. Run pre-deployment tests
4. Deploy to Railway
5. Verify deployment health
6. Provide deployment URL

### 4. Create a Streamlit Component

**Build UI Component:**

```bash
invoke streamlit-component-builder --name="PropertyCard"
```

**This will:**
1. Generate component boilerplate
2. Apply design system patterns
3. Add caching strategies
4. Include test file
5. Provide usage examples

## Common Workflows

### TDD Workflow

```bash
# 1. Start with TDD skill
invoke test-driven-development --feature="property-search"

# 2. Follow prompts for:
#    - Test file creation
#    - Implementation
#    - Refactoring
#    - Coverage validation
```

### UI Development Workflow

```bash
# 1. Create component
invoke streamlit-component-builder --name="SearchFilters"

# 2. Apply theming
invoke theme-factory --theme="real-estate-luxury"

# 3. Validate design consistency
invoke frontend-design --validate
```

### Cost Optimization Workflow

```bash
# 1. Analyze current costs
invoke cost-optimization-analyzer

# 2. Optimize token usage
invoke token-usage-optimizer

# 3. Review model selection
invoke model-selection-advisor
```

### Multi-Agent Workflow

```bash
# 1. Coordinate multiple development streams
invoke subagent-driven-development --agents="frontend,backend,testing"

# 2. Dispatch parallel tasks
invoke dispatching-parallel-agents --tasks="api-endpoints,ui-components,tests"
```

## Real Estate AI Features

### Property Matching

```bash
# Generate ML-based property matcher
invoke property-matcher-generator --algorithm="collaborative-filtering"
```

### Lead Scoring

```bash
# Optimize lead scoring model
invoke lead-scoring-optimizer --target-metric="conversion-rate"
```

### Market Analysis

```bash
# Analyze market trends
invoke market-intelligence-analyzer --region="San Francisco Bay Area"
```

### Automated CMA

```bash
# Generate comparative market analysis
invoke automated-cma-generator --address="123 Main St, San Francisco, CA"
```

## Integration Examples

### GoHighLevel Integration

```bash
# Set up GHL webhook handler
invoke ghl-webhook-handler --endpoint="/webhooks/ghl"

# Sync contacts with GHL
invoke ghl-contact-sync --direction="bidirectional"

# Automate pipeline stages
invoke ghl-pipeline-automator --pipeline="Lead Nurture"
```

### API Development

```bash
# Generate FastAPI endpoint
invoke api-endpoint-generator --resource="properties" --methods="GET,POST,PUT,DELETE"
```

### Document Automation

```bash
# Generate listing contract
invoke contract-generator --template="residential-listing"

# Build property proposal
invoke proposal-builder --property-id="prop-12345"

# Create market report
invoke market-report-generator --period="Q1-2026"
```

## MCP Profiles

Switch profiles based on your workflow:

```bash
# Streamlit/UI development
export CLAUDE_PROFILE=streamlit-dev

# Backend services
export CLAUDE_PROFILE=backend-services

# Testing and QA
export CLAUDE_PROFILE=testing-qa
```

## Hooks System

The plugin includes enterprise-grade hooks for:

### Security Validation

- **Secrets Protection**: Blocks .env, .key, .pem files
- **Path Traversal Prevention**: Blocks ../ patterns
- **SQL Injection Detection**: AI-powered vulnerability analysis
- **GHL API Validation**: Rate limiting and credential checks

### Audit Logging

- **File Operations**: All writes/edits logged
- **Bash Commands**: Complete command history
- **GHL API Calls**: API usage tracking

### Cost Control

- **Subagent Rate Limiting**: 10 per 5 minutes
- **Hook Performance Monitoring**: <500ms target
- **Token Usage Tracking**: Optimization insights

## Troubleshooting

### Skill Not Found

```bash
# Check skill exists
ls skills/testing/test-driven-development/

# Verify manifest
cat skills/MANIFEST.yaml | grep test-driven-development
```

### Agent Coordination Issues

```bash
# Check agent status
cat agents/README.md

# Test agent communication
invoke subagent-driven-development --test
```

### Hook Validation Errors

```bash
# Test hooks
./hooks/test-hooks.sh

# View hook logs
cat .claude/metrics/hook-performance.jsonl | jq '.'
```

### Installation Issues

```bash
# Re-run installation
./scripts/install.sh

# Validate plugin
./scripts/validate-plugin.sh
```

## Performance Metrics

Expected time savings by skill category:

| Skill Category          | Time Savings | Use Cases                    |
|-------------------------|--------------|------------------------------|
| TDD Workflow            | 83%          | Feature development          |
| UI Component Creation   | 88%          | Streamlit dashboards         |
| Deployment Pipeline     | 75%          | Railway/Vercel deploys       |
| API Endpoint Generation | 80%          | FastAPI development          |
| Document Automation     | 85%          | Contracts, proposals         |
| Cost Optimization       | 70%          | Token/model optimization     |
| **Average**             | **82%**      | All workflows                |

## Next Steps

1. **Explore Examples**: Check `examples/` directory for code samples
2. **Review Documentation**: Read skill-specific docs in `skills/*/README.md`
3. **Join Community**: [Discord](https://discord.gg/real-estate-ai-devs)
4. **Customize**: Fork and extend skills for your use case

## Support

- **Documentation**: [docs.enterprisehub.dev](https://docs.enterprisehub.dev/plugins/real-estate-ai)
- **GitHub Issues**: [Report bugs or request features](https://github.com/enterprisehub/claude-real-estate-ai-plugin/issues)
- **Discord**: [Real Estate AI Developers Community](https://discord.gg/real-estate-ai-devs)

---

**Happy Coding! 🚀**
