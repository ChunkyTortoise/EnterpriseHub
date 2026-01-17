# Contributing to Claude Real Estate AI Accelerator

Thank you for your interest in contributing to the Claude Real Estate AI Accelerator plugin. This document provides guidelines and instructions for contributors.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Contribution Workflow](#contribution-workflow)
5. [Skill Development Guidelines](#skill-development-guidelines)
6. [Agent Development Guidelines](#agent-development-guidelines)
7. [Testing Requirements](#testing-requirements)
8. [Documentation Standards](#documentation-standards)
9. [Pull Request Process](#pull-request-process)
10. [Release Process](#release-process)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors, regardless of experience level, background, or identity.

### Our Standards

**Positive behaviors:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors:**
- Harassment, trolling, or personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

### Enforcement

Violations of the code of conduct should be reported to plugins@enterprisehub.dev. All complaints will be reviewed and investigated promptly and fairly.

---

## Getting Started

### Prerequisites

- **Claude Code**: Version 2.1.0 or higher
- **Python**: 3.11+ for Python skills
- **Node.js**: 18.0+ for deployment skills
- **Git**: For version control
- **GitHub Account**: For submitting contributions

### First Contribution

Good first issues are labeled with `good-first-issue` in the GitHub repository. These are beginner-friendly tasks that help you get familiar with the codebase.

---

## Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub
# Then clone your fork
git clone https://github.com/YOUR_USERNAME/claude-real-estate-ai-plugin.git
cd claude-real-estate-ai-plugin
```

### 2. Install Development Dependencies

```bash
# Python dependencies
pip install -r requirements-dev.txt

# Node.js dependencies (if applicable)
npm install
```

### 3. Set Up Pre-Commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install git hooks
pre-commit install
```

### 4. Create a Branch

```bash
# Create a feature branch
git checkout -b feature/your-feature-name

# Or a bugfix branch
git checkout -b fix/bug-description
```

---

## Contribution Workflow

### 1. Identify the Contribution Type

- **Bug Fix**: Fix an existing issue
- **New Skill**: Add a new skill to the ecosystem
- **Enhancement**: Improve existing skill or agent
- **Documentation**: Improve or add documentation
- **Refactoring**: Code quality improvements

### 2. Create or Update Issues

Before starting work, check if an issue exists. If not, create one describing:
- Problem or feature request
- Proposed solution
- Any relevant context or examples

### 3. Implement Changes

Follow the guidelines in this document based on contribution type.

### 4. Test Thoroughly

Run all validation and tests:

```bash
# Validate plugin structure
./scripts/validate-plugin.sh

# Run unit tests
pytest tests/

# Run integration tests
pytest tests/integration/

# Validate skill syntax
./scripts/validate-skills.sh

# Test agents
./scripts/test-agents.sh
```

### 5. Update Documentation

- Update README.md if adding features
- Add or update examples in `examples/`
- Update CHANGELOG.md with your changes
- Add inline documentation to code

### 6. Submit Pull Request

See [Pull Request Process](#pull-request-process) below.

---

## Skill Development Guidelines

### Skill Structure

```
skills/
└── category/
    └── skill-name/
        ├── SKILL.md              # Main skill definition (REQUIRED)
        ├── reference/
        │   ├── patterns.md       # Patterns and best practices
        │   └── examples.md       # Code examples
        ├── scripts/
        │   ├── script1.sh        # Zero-context scripts
        │   └── script2.py
        ├── templates/
        │   └── template.py       # Code templates
        └── README.md             # Detailed documentation
```

### SKILL.md Requirements

**Frontmatter (YAML):**

```yaml
---
name: skill-name
description: "Brief description under 100 characters. Use when [trigger pattern]."
trigger: "keyword1", "keyword2", "phrase pattern"
model: sonnet  # or haiku, opus
thinking: true  # Enable thinking mode
tools: ["Read", "Write", "Edit", "Bash"]  # Allowed tools
category: testing  # Category from plugin.json
version: 1.0.0
author: Your Name
created: 2026-01-15
updated: 2026-01-15
---
```

**Content Structure:**

```markdown
# Skill Name

## Context (Minimal - Always Loaded)
Brief description of skill purpose and when to use it.
Maximum 500 tokens.

## Workflow (Concise Steps)
1. Step 1 with reference (@reference/patterns.md)
2. Step 2
3. Step 3 (scripts/script.sh)

## Scripts (Zero-Context)
- `scripts/script1.sh` - Description
- `scripts/script2.py` - Description

## References (Load On-Demand)
- @reference/patterns.md - Description
- @reference/examples.md - Description

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Examples
See examples/skill-name-example.md for complete workflow.
```

### Token Budget Guidelines

- **SKILL.md**: 300-800 tokens (always loaded)
- **Reference files**: 2-3k tokens each (on-demand)
- **Scripts**: Zero-context (only output consumes tokens)
- **Total skill**: Under 10k tokens when fully loaded

### Script Best Practices

**Zero-Context Scripts:**

```bash
#!/bin/bash
# scripts/run_tests.sh
# This script runs without loading into context
# Only the output (stdout/stderr) consumes tokens

set -e

echo "Running test suite..."
pytest tests/ --coverage

if [ $? -eq 0 ]; then
  echo "✅ All tests passed"
  echo "Coverage: $(coverage report | tail -1 | awk '{print $NF}')"
else
  echo "❌ Tests failed"
  exit 1
fi
```

### Progressive Disclosure

**Good Example:**
```markdown
## Context
You enforce TDD discipline: RED → GREEN → REFACTOR.

## Workflow
1. **RED**: Write failing test (@reference/patterns.md)
2. **GREEN**: Minimal implementation
3. **REFACTOR**: Clean up (@reference/checklist.md)
```

**Bad Example:**
```markdown
## Context
[Includes 5000 words of detailed TDD theory, examples, and edge cases]
All loaded immediately, wasting context.
```

### Testing Skills

Each skill should include:

1. **Unit Tests**: Test individual components
2. **Integration Tests**: Test skill workflows
3. **Example Workflows**: Documented in `examples/`

```bash
# Test skill
pytest tests/skills/test_skill_name.py

# Test integration
pytest tests/integration/test_skill_name_integration.py
```

---

## Agent Development Guidelines

### Agent Structure

```
agents/
└── agent-name.md
```

### Agent Definition Format

```yaml
---
name: agent-name
description: "Expert in [domain]. Use when [trigger pattern]."
tools: ["Read", "Grep", "Glob"]  # Restricted tool set
model: opus  # Model tier
persona: security  # Persona type
context: fork  # Execution context (fork or shared)
priority: high  # Invocation priority
---

# Agent Name

## Role
You are a [domain] expert focusing on:
- Responsibility 1
- Responsibility 2
- Responsibility 3

## Workflow
1. Step 1
2. Step 2
3. Step 3

## Validation Criteria
- [ ] Check 1
- [ ] Check 2
- [ ] Check 3

## Communication Protocol
- Input format: [description]
- Output format: [description]
- Escalation: When to escalate to main agent
```

### Agent Best Practices

1. **Single Responsibility**: Each agent has one clear purpose
2. **Restricted Tools**: Minimal tool access for security
3. **Isolated Context**: Use `context: fork` for independent execution
4. **Clear Communication**: Define input/output formats
5. **Validation Criteria**: Explicit success criteria

### Agent Testing

```bash
# Test agent
./scripts/test-agents.sh agent-name

# Test agent coordination
./scripts/test-agent-coordination.sh
```

---

## Testing Requirements

### Coverage Thresholds

- **Line Coverage**: 80% minimum
- **Branch Coverage**: 80% minimum
- **Function Coverage**: 90% minimum

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test skill workflows end-to-end
3. **Agent Tests**: Test agent behavior and coordination
4. **Performance Tests**: Validate token usage and execution time

### Running Tests

```bash
# All tests
pytest tests/ --cov=. --cov-report=html

# Specific category
pytest tests/skills/
pytest tests/agents/
pytest tests/integration/

# With verbose output
pytest -v tests/

# With coverage report
pytest --cov-report=term-missing
```

### Test Naming Convention

```python
# tests/skills/test_skill_name.py
def test_skill_name_workflow_success():
    """Test successful workflow execution."""
    pass

def test_skill_name_handles_error_gracefully():
    """Test error handling when dependencies fail."""
    pass

def test_skill_name_token_usage_under_threshold():
    """Test token usage is under 10k tokens."""
    pass
```

---

## Documentation Standards

### README.md Requirements

Each skill and agent should have a README.md with:

1. **Purpose**: What the skill/agent does
2. **Usage**: How to invoke and configure
3. **Examples**: Real-world usage examples
4. **Configuration**: Available options and defaults
5. **Troubleshooting**: Common issues and solutions

### Code Documentation

```python
def process_lead_scoring(lead_data: dict) -> float:
    """
    Calculate lead score using ML model.

    Args:
        lead_data: Dictionary containing lead attributes
                   Required keys: contact_info, behavior, demographics

    Returns:
        Float score between 0.0 and 1.0 representing lead quality

    Raises:
        ValueError: If required keys are missing from lead_data
        ModelError: If ML model fails to load or score

    Examples:
        >>> lead = {"contact_info": {...}, "behavior": {...}}
        >>> score = process_lead_scoring(lead)
        >>> assert 0.0 <= score <= 1.0
    """
    pass
```

### Markdown Formatting

- Use **bold** for emphasis
- Use `code` for technical terms
- Use ```language for code blocks
- Use > for important notes
- Use tables for structured data
- Use lists for sequences

---

## Pull Request Process

### Before Submitting

1. **Run all validations**:
   ```bash
   ./scripts/validate-plugin.sh
   pytest tests/
   ```

2. **Update documentation**:
   - README.md if adding features
   - CHANGELOG.md with your changes
   - Examples if adding skills/agents

3. **Check code quality**:
   ```bash
   ruff check .
   mypy .
   ```

4. **Verify token budgets**:
   - Skill under 10k tokens fully loaded
   - SKILL.md under 800 tokens

### PR Title Format

```
[Category] Brief description

Examples:
[Skill] Add property-matcher-generator skill
[Agent] Improve security-reviewer error handling
[Docs] Update installation instructions
[Fix] Correct token counting in cost-optimizer
```

### PR Description Template

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix
- [ ] New skill
- [ ] New agent
- [ ] Enhancement
- [ ] Documentation
- [ ] Refactoring

## Related Issues
Closes #123

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed
- [ ] Token budget validated

## Documentation
- [ ] README.md updated
- [ ] CHANGELOG.md updated
- [ ] Examples added
- [ ] Code comments added

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] No secrets or sensitive data
- [ ] All tests pass
- [ ] Documentation is clear
```

### Review Process

1. **Automated Checks**: CI/CD runs validation and tests
2. **Code Review**: Maintainer reviews code quality and design
3. **Documentation Review**: Verify documentation is clear and complete
4. **Testing Review**: Ensure adequate test coverage
5. **Approval**: At least one maintainer approval required
6. **Merge**: Squash and merge into main branch

---

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):

- **Major (X.0.0)**: Breaking changes
- **Minor (x.X.0)**: New features, backward compatible
- **Patch (x.x.X)**: Bug fixes, backward compatible

### Release Checklist

1. **Update Version**:
   - `plugin.json` version field
   - CHANGELOG.md with release notes
   - README.md if needed

2. **Run Full Validation**:
   ```bash
   ./scripts/validate-plugin.sh
   pytest tests/
   ./scripts/integration-tests.py
   ```

3. **Tag Release**:
   ```bash
   git tag -a v4.0.0 -m "Release v4.0.0"
   git push origin v4.0.0
   ```

4. **Create GitHub Release**:
   - Use tag as release version
   - Copy CHANGELOG.md entry as description
   - Attach any release artifacts

5. **Announce**:
   - Discord community
   - GitHub Discussions
   - Social media (if applicable)

---

## Style Guidelines

### Python

```python
# Follow PEP 8
# Use type hints
# Maximum line length: 100 characters
# Use ruff for linting and formatting

def calculate_score(lead: dict[str, Any]) -> float:
    """Calculate lead score."""
    pass
```

### Bash

```bash
#!/bin/bash
# Use strict mode
set -euo pipefail

# Clear variable names
# Comments for complex logic
# Error handling
```

### Markdown

```markdown
# Use ATX-style headers (# ## ###)
# Blank lines between sections
# Code blocks with language identifiers
# Tables with alignment
```

---

## Getting Help

### Resources

- **Documentation**: [docs.enterprisehub.dev](https://docs.enterprisehub.dev/plugins/real-estate-ai)
- **Discord**: [Join the community](https://discord.gg/real-estate-ai-devs)
- **GitHub Discussions**: [Ask questions](https://github.com/enterprisehub/claude-real-estate-ai-plugin/discussions)

### Questions

- **General Questions**: GitHub Discussions
- **Bug Reports**: GitHub Issues
- **Feature Requests**: GitHub Discussions (Ideas category)
- **Security Issues**: Email plugins@enterprisehub.dev privately

---

## Recognition

Contributors are recognized in:

- **CONTRIBUTORS.md**: List of all contributors
- **Release Notes**: Significant contributions mentioned
- **GitHub**: Contributor badge and statistics

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing to the Claude Real Estate AI Accelerator!**

Your contributions help make real estate AI development more accessible and efficient for everyone.
