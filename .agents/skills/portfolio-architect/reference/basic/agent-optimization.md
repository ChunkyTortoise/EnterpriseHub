# Claude Code Toolchain Optimization for Portfolio Projects

## Agent Selection Matrix

### By Project Type

#### SaaS/Product Portfolio Projects
**Primary Agents:**
- `feature-dev:code-architect` - System design and component architecture
- `frontend-design:frontend-design` - UI/UX that showcases professionalism
- `pr-review-toolkit:code-reviewer` - Code quality for client review
- `agent-sdk-dev:new-sdk-app` - If building extensible platforms

**Supporting Agents:**
- `pr-review-toolkit:type-design-analyzer` - API design validation
- `pr-review-toolkit:silent-failure-hunter` - Reliability demonstration
- `Explore` - Competitive analysis and pattern research

#### Enterprise Integration Portfolio
**Primary Agents:**
- `feature-dev:code-explorer` - Understanding complex existing systems
- `feature-dev:code-architect` - Integration architecture design
- `pr-review-toolkit:code-reviewer` - Enterprise-grade code standards

**Supporting Agents:**
- `Plan` - Integration strategy development
- `Bash` - DevOps and deployment automation
- Custom security agents for compliance demonstration

#### Consulting Framework/Tool Portfolio
**Primary Agents:**
- `general-purpose` - Research and methodology development
- `feature-dev:code-architect` - Framework architecture
- `plugin-dev:agent-creator` - If building AI-powered tools

**Supporting Agents:**
- `Explore` - Industry best practice research
- Documentation-focused agents for framework explanation

## Skills Configuration

### Essential Portfolio Skills

#### Universal Skills (All Projects)
```yaml
skills:
  - test-driven-development
  - security-first-design
  - performance-optimization
  - documentation-excellence
  - client-presentation-ready
```

#### Project-Specific Skills

**SaaS Products:**
```yaml
skills:
  - user-experience-design
  - api-design-excellence
  - scalable-architecture
  - monitoring-and-observability
  - revenue-model-implementation
```

**Enterprise Integration:**
```yaml
skills:
  - enterprise-architecture-patterns
  - security-compliance
  - system-integration-design
  - legacy-system-modernization
  - change-management-consideration
```

**Consulting Frameworks:**
```yaml
skills:
  - methodology-framework-design
  - knowledge-transfer-systems
  - process-automation
  - roi-measurement-tools
  - client-self-service-enablement
```

## Hooks Configuration

### Quality Gates for Portfolio Projects
```yaml
# .claude/hooks.yaml
portfolio_quality_gates:
  PreToolUse:
    - validate_client_ready_standards.sh
    - check_professional_naming.sh
    - ensure_documentation_present.sh

  PostToolUse:
    - update_portfolio_metrics.sh
    - generate_demo_scenarios.sh

  Stop:
    - validate_portfolio_checklist.sh
    - generate_client_presentation_materials.sh
    - calculate_development_roi.sh
```

### Portfolio-Specific Hooks
```bash
# Client-Ready Code Standards
pre_commit_portfolio_check:
  - No debug logs or console.log statements
  - All functions have docstrings/comments
  - Error handling is comprehensive and user-friendly
  - UI is responsive and professional
  - All secrets are properly configured
  - Performance is optimized for demo scenarios

# Demo Preparation
post_development_hooks:
  - Generate demo data sets
  - Create client walkthrough scripts
  - Validate all user journeys work end-to-end
  - Generate project value proposition summary
  - Create technical documentation for client review
```

## Plugin Recommendations

### Core Development Plugins
- **pr-review-toolkit** - Essential for portfolio-quality code
- **feature-dev** - Comprehensive development workflow
- **agent-sdk-dev** - For building extensible solutions

### Domain-Specific Plugins
- **vercel** - For seamless demo deployment
- **frontend-design** - Professional UI that impresses clients
- **hookify** - Custom validation rules for portfolio standards

## Model Selection Strategy

### By Development Phase

| Phase | Model | Reasoning |
|-------|-------|-----------|
| **Discovery** | Opus | Strategic thinking, business understanding |
| **Architecture** | Opus | Complex system design, pattern selection |
| **Implementation** | Sonnet | Efficient coding, good balance |
| **Testing** | Sonnet | Reliable test creation |
| **Documentation** | Sonnet | Clear technical writing |
| **Demo Prep** | Opus | Client-facing materials, value articulation |

### By Project Complexity

| Complexity | Model | Agent Strategy |
|------------|-------|---------------|
| **High-Value SaaS** | Opus + Sonnet swarm | Parallel specialists |
| **Enterprise Integration** | Opus primary | Sequential with security focus |
| **Consulting Framework** | Sonnet primary | Research-heavy with Opus for strategy |

## Resource Optimization

### Context Window Management
- Use project-specific `.claude/skills/` for domain patterns
- Leverage zero-context scripts for routine validations
- Progressive disclosure for technical specifications
- Agent isolation for complex analysis tasks

### Cost Optimization
- Haiku for routine validations and code formatting
- Sonnet for core development work
- Opus only for strategic decisions and complex architecture
- Background agents for independent analysis tasks

### Development Velocity
- Pre-built skills for common portfolio patterns
- Template-based project scaffolding
- Automated quality gate enforcement
- Parallel agent execution for independent tasks