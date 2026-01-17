# Pull Request

## Description

Brief description of what this PR accomplishes.

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Style/UI update (formatting, styling, no code change)
- [ ] ♻️ Refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Configuration change

## Component Type

- [ ] Skill (new or updated skill)
- [ ] Agent (new or updated agent)
- [ ] Hook (new or updated hook)
- [ ] MCP Profile (new or updated profile)
- [ ] Script (automation or utility script)
- [ ] Documentation
- [ ] Example/Template

## Changes Made

### Skills
- [ ] New skill: `skill-name`
- [ ] Updated skill: `skill-name`
- [ ] Removed skill: `skill-name`

### Agents
- [ ] New agent: `agent-name`
- [ ] Updated agent: `agent-name`
- [ ] Removed agent: `agent-name`

### Hooks
- [ ] New hook: `hook-name` (PreToolUse/PostToolUse)
- [ ] Updated hook: `hook-name`
- [ ] Removed hook: `hook-name`

### Other Changes
- List significant changes here

## Testing

### Manual Testing Completed
- [ ] Skill invocation tested successfully
- [ ] Agent coordination tested
- [ ] Hook validation tested
- [ ] Integration with existing components tested
- [ ] Error handling validated

### Test Commands
```bash
# Commands used to test this PR
./scripts/validate-plugin.sh
invoke skill-name --test
```

### Test Results
```
Paste test output here
```

## Documentation

- [ ] README.md updated (if needed)
- [ ] SKILL.md created/updated (for skills)
- [ ] Agent README updated (for agents)
- [ ] CHANGELOG.md updated
- [ ] Examples added/updated
- [ ] Comments added to complex code

## Performance Impact

- **Estimated Time Savings**: [e.g., 80%]
- **Token Usage**: [e.g., reduced by 15%]
- **Execution Time**: [e.g., <500ms]

## Breaking Changes

If this PR includes breaking changes, describe:

1. What breaks
2. Migration path
3. Version bump required

## Checklist

### Code Quality
- [ ] Code follows plugin style guidelines
- [ ] Self-review of code completed
- [ ] Comments added for complex logic
- [ ] No hardcoded secrets or credentials
- [ ] Error handling implemented
- [ ] Logging added where appropriate

### Testing
- [ ] All tests pass
- [ ] New tests added for new functionality
- [ ] Edge cases covered
- [ ] Performance tested

### Documentation
- [ ] User-facing documentation updated
- [ ] Code comments are clear
- [ ] Examples provided
- [ ] CHANGELOG.md updated

### Security
- [ ] No sensitive data exposed
- [ ] Input validation implemented
- [ ] Secrets management reviewed
- [ ] Security best practices followed

### Integration
- [ ] Compatible with existing skills
- [ ] Compatible with existing agents
- [ ] MCP profile compatibility verified
- [ ] Hooks don't conflict

## Related Issues

Closes #[issue number]
Relates to #[issue number]

## Screenshots (if applicable)

Add screenshots to demonstrate UI changes or workflow improvements.

## Additional Notes

Any additional information reviewers should know:
- Dependencies added
- Configuration changes required
- Future improvement opportunities
- Known limitations

## Reviewer Focus Areas

What should reviewers pay special attention to?

- [ ] Security validation
- [ ] Performance optimization
- [ ] Code organization
- [ ] Documentation clarity
- [ ] Test coverage

---

**By submitting this PR, I confirm that:**
- [ ] I have read and followed the [CONTRIBUTING.md](../CONTRIBUTING.md) guidelines
- [ ] My code follows the plugin's coding standards
- [ ] I have tested my changes thoroughly
- [ ] I have updated relevant documentation
- [ ] This PR is ready for review
