# Skills Directory

This directory contains all skills for the Claude Real Estate AI Accelerator plugin.

## Structure

Skills are organized by category:

```
skills/
├── testing/              # TDD, testing patterns, quality assurance
├── debugging/            # Systematic debugging workflows
├── core/                 # Core verification and review workflows
├── deployment/           # Deployment to various platforms
├── design/               # UI/UX, design systems, theming
├── orchestration/        # Multi-agent coordination
├── real-estate-ai/       # Domain-specific AI workflows
├── automation/           # GHL integration and automation
├── cost-optimization/    # AI cost analysis and optimization
├── analytics/            # Performance metrics and analytics
├── document-automation/  # Contract and document generation
└── feature-dev/          # End-to-end feature development
```

## Skill Count

**Total Skills: 27**

- Testing: 4 skills
- Design: 3 skills
- Real Estate AI: 4 skills
- GHL Integration: 3 skills
- Deployment: 3 skills
- Multi-Agent: 2 skills
- Cost Optimization: 3 skills
- Analytics: 3 skills
- Document Automation: 3 skills
- Feature Development: 3 skills

## Usage

Skills are invoked using the Claude Code CLI:

```bash
# Invoke a skill
invoke skill-name --option=value

# Examples
invoke test-driven-development --feature="lead-scoring"
invoke frontend-design --component="PropertyCard"
invoke cost-optimization-analyzer --target="claude-api"
```

## Skill Structure

Each skill directory contains:

```
skill-name/
├── SKILL.md              # Main skill definition (required)
├── README.md             # Detailed documentation
├── reference/
│   ├── patterns.md       # Patterns and best practices
│   └── examples.md       # Code examples
├── scripts/
│   ├── script1.sh        # Zero-context scripts
│   └── script2.py
└── templates/
    └── template.py       # Code templates
```

## Adding New Skills

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on creating new skills.

## Skill Development Guidelines

1. **Token Budget**: Keep SKILL.md under 800 tokens
2. **Progressive Disclosure**: Use reference files for detailed content
3. **Zero-Context Scripts**: Scripts run without loading into context
4. **Testing**: Include tests for skill workflows
5. **Documentation**: Provide clear examples and use cases
