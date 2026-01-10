# EnterpriseHub - Gemini CLI Configuration

<!-- Extends EnterpriseHub Project Configuration -->
**⚡ Base Configuration**: This file extends `@CLAUDE.md` with Gemini CLI-specific patterns and optimizations.

**🔗 Cross-Reference Pattern**:
1. **Universal principles** → `@.claude/CLAUDE.md` (TDD, security, quality gates)
2. **Project specifics** → `@CLAUDE.md` (GHL Real Estate AI, Python, 32 skills)
3. **Gemini CLI optimizations** → This file (model selection, context management, hybrid workflow)

**📋 Quick Reference**: Inherit all EnterpriseHub architecture and domain knowledge from `@CLAUDE.md`, with Gemini CLI-specific configurations below.

---

## Section 1: Gemini CLI Advantages for EnterpriseHub

### Why Use Gemini CLI for This Project

**1. Massive Context Window (1M tokens)**
- Analyze entire codebase in single session
- Review all 650+ tests simultaneously
- Process complete GHL API documentation
- Understand full behavioral learning engine architecture

**2. Free Tier (1,000 requests/day)**
- Exploration and prototyping without cost
- Rapid iteration on ML model designs
- Quick validation of architecture decisions
- Cost-effective for research and learning

**3. Large-Scale Analysis**
- Codebase exploration across 26+ Streamlit components
- Pattern analysis across all services (ai/, ghl/, learning/, property/)
- Comprehensive test coverage analysis
- Full documentation review and updates

### When to Use Gemini CLI vs Claude Code

**Use Gemini CLI for:**
- ✅ Initial exploration of new features
- ✅ Large codebase analysis (leverage 1M context)
- ✅ Prototyping ML model architectures
- ✅ Documentation generation and review
- ✅ Learning and experimentation
- ✅ Quick scripts and utilities
- ✅ Cost-sensitive development tasks

**Use Claude Code for:**
- ✅ Production feature implementation
- ✅ Complex refactoring (Claude's code quality superior)
- ✅ Critical bug fixes requiring precision
- ✅ GHL integration logic (requires high accuracy)
- ✅ ML model training code (mathematical precision)
- ✅ Final implementation before PR
- ✅ Security-critical code

---

## Section 2: Gemini CLI Model Selection

### Model Aliases Configured

| Alias | Model | Use Case | Temperature |
|-------|-------|----------|-------------|
| **fast** (default) | gemini-2.5-flash | Development, prototyping, general tasks | 0.7 |
| **precise** | gemini-2.5-pro | ML tasks, complex logic, production code | 0.3 |
| **exploration** | gemini-2.5-flash | Codebase analysis, creative solutions | 0.9 |

### Usage Examples

```bash
# Default mode (fast, 1M context)
gemini

# Precise mode for ML model implementation
gemini --model precise

# Exploration mode for architecture analysis
gemini --model exploration

# Quick alias usage
gemini -m fast "implement lead scoring dashboard"
gemini -m precise "optimize property matching algorithm"
gemini -m exploration "analyze entire services/ directory for patterns"
```

---

## Section 3: EnterpriseHub-Specific Configuration

### Context Management

**Included Directories (automatic discovery):**
- `ghl_real_estate_ai/` - Main codebase
- `ghl_real_estate_ai/services/` - Service layer
- `ghl_real_estate_ai/streamlit_demo/` - UI components
- `.claude/skills/` - Shared skills (32 production skills)

**File Filtering:**
- Respects `.gitignore` (excludes `venv/`, `__pycache__/`, etc.)
- Respects `.geminiignore` (custom exclusions)
- Recursive file search enabled (discovers nested files)
- Fuzzy search enabled (flexible file matching)

### EnterpriseHub Memory Commands

```bash
# Refresh context from all directories
/memory refresh

# Show combined context (GEMINI.md + CLAUDE.md + included dirs)
/memory show

# Reload project structure
/memory reload
```

---

## Section 4: Real Estate AI Workflow with Gemini CLI

### Lead Scoring Development

```bash
# 1. Explore existing lead scoring implementation (1M context advantage)
gemini -m exploration "analyze all lead scoring code in services/lead_scorer.py and related files"

# 2. Prototype new features (free tier advantage)
gemini -m fast "create prototype for behavioral lead scoring using interaction patterns"

# 3. Implement with precision (switch to Claude Code for production)
claude-yolo "implement production-ready behavioral lead scoring"
```

### Property Matching Optimization

```bash
# 1. Analyze entire property matching system
gemini "review services/property/ directory and identify optimization opportunities"

# 2. Prototype ML model improvements
gemini -m precise "design improved property matching algorithm using TensorFlow"

# 3. Test with large datasets
gemini "simulate property matching with 10,000 properties and analyze performance"
```

### GHL Integration Development

```bash
# 1. Understand GHL API patterns (large context)
gemini "analyze all GHL webhook handlers and API integration code"

# 2. Design new integration
gemini -m precise "design GHL webhook for opportunity.updated event"

# 3. Implement with Claude Code (precision required)
claude-auto "implement GHL opportunity.updated webhook with error handling"
```

### Streamlit Component Creation

```bash
# 1. Review existing components (all 26+)
gemini "analyze streamlit_demo/ components and identify common patterns"

# 2. Prototype new dashboard
gemini -m fast "create streamlit dashboard for churn prediction visualization"

# 3. Refine UI (use frontend-design skill with Claude Code)
claude "invoke frontend-design skill to polish churn dashboard"
```

---

## Section 5: Gemini CLI + EnterpriseHub Hooks

### Configured Hooks

**BeforeTool - Prevent Secret Commits:**
- Blocks bash commands that might commit secrets
- Scans for: API_KEY, SECRET, TOKEN, PASSWORD
- Excludes: .gemini/, .claude/, node_modules/, .git/
- Action: Blocks tool execution if secrets found

**AfterTool - Auto-Format Python:**
- Automatically runs `black` on Python files after write/edit
- Only processes .py files
- Non-blocking (doesn't fail if black not installed)
- Maintains EnterpriseHub code quality standards

### Custom Hook Examples

**Add ML Model Validation Hook:**

```json
{
  "hooks": {
    "AfterTool": [
      {
        "name": "validate-ml-models",
        "command": "python",
        "args": ["scripts/validate_models.py", "${GEMINI_TOOL_OUTPUT_FILE}"],
        "targetTools": ["write"],
        "filePatterns": ["**/learning/models/*.py"]
      }
    ]
  }
}
```

**Add Test Execution Hook:**

```json
{
  "hooks": {
    "AfterTool": [
      {
        "name": "run-relevant-tests",
        "command": "pytest",
        "args": ["-xvs", "tests/test_${GEMINI_MODIFIED_SERVICE}.py"],
        "targetTools": ["write", "edit"],
        "filePatterns": ["ghl_real_estate_ai/services/*.py"]
      }
    ]
  }
}
```

---

## Section 6: Hybrid Workflow Best Practices

### Phase 1: Exploration (Gemini CLI)

**Objective:** Understand problem space, analyze existing code, research solutions

```bash
# Use Gemini's 1M context to analyze everything
gemini -m exploration "analyze entire behavioral learning engine and suggest improvements"

# Cost-effective prototyping
gemini -m fast "prototype lead intelligence dashboard using existing patterns"

# Documentation review
gemini "review all docstrings in services/ and identify missing or outdated docs"
```

**Advantages:**
- Free tier (1,000 requests/day)
- 1M context window (see entire codebase)
- Faster for simple queries
- Great for learning and research

### Phase 2: Implementation (Claude Code)

**Objective:** Production-ready code, complex logic, critical features

```bash
# Switch to Claude for implementation
claude-auto "implement behavioral learning dashboard with production-ready code"

# Use skills system (32 EnterpriseHub skills)
claude "invoke rapid-feature-prototyping for lead-scoring-dashboard"

# Complex refactoring
claude "refactor property matching service to use Strategy Pattern"
```

**Advantages:**
- Superior code quality (Claude Sonnet 3.5/Opus)
- Production-ready skills system
- Better for complex logic
- More autonomous execution

### Phase 3: Testing & Refinement (Both)

**Gemini for exploration:**
```bash
gemini "analyze test coverage for new feature and suggest additional tests"
```

**Claude for implementation:**
```bash
claude-yolo "implement missing tests identified by Gemini"
```

### Phase 4: Documentation (Gemini)

**Leverage 1M context for comprehensive docs:**

```bash
# Full codebase documentation
gemini "generate comprehensive API documentation for all services"

# Architecture diagrams
gemini "create architecture diagram for behavioral learning engine"

# Update README
gemini "update README.md with new features and deployment instructions"
```

---

## Section 7: Session Management

### Gemini CLI Session Commands

```bash
# List all EnterpriseHub sessions
gemini --list-sessions

# Resume most recent work
gemini --resume
gemini --resume latest

# Resume specific session by index
gemini --resume 5

# Resume by UUID (from session browser)
gemini --resume 4e65d8da-41ab-4530-a8e8-23821a8a8deb

# Delete old session
gemini --delete-session 10

# Interactive session browser (in-session)
/resume
```

### Session Retention Policy

**Configured:**
- Maximum age: 30 days (auto-delete older sessions)
- Maximum count: 100 sessions (keep most recent 100)
- Minimum retention: 1 day (safety buffer)

**Session Storage:**
- Location: `~/.gemini/tmp/<project_hash>/chats/`
- Project-specific (switching directories switches history)
- Auto-saved every interaction

---

## Section 8: Performance Optimization

### Context Compression

**Configured thresholds:**
- Compression at 70% context usage (vs default 50%)
- Maximize use of 1M context before compression
- Tool output summarization:
  - bash: 10,000 tokens
  - read: 50,000 tokens
  - grep: 20,000 tokens
  - glob: 10,000 tokens

### JIT Context Loading

**Enabled:** `experimental.jitContext: true`

**Benefits:**
- Load files only when needed (reduce initial token usage)
- Better for large codebases (EnterpriseHub qualifies)
- Faster session startup
- More efficient context management

### Tool Output Truncation

**Configured:**
- Threshold: 4M characters (very large outputs)
- Line limit: 1,000 lines
- Prevents context overflow from large file reads
- Maintains responsiveness

---

## Section 9: MCP Integration (Shared with Claude Code)

### GitHub MCP Server

**Configured tools (allowlist):**
- `create_issue` - Bug reports, feature requests
- `list_repos` - Repository management
- `create_pr` - Pull request automation
- `search_code` - Codebase search
- `get_file_contents` - File retrieval

**Blocked tools:**
- `delete_repo` - Too dangerous
- `force_push` - Risk of data loss

**Authentication:**
- Uses `GITHUB_TOKEN` environment variable
- Shared with Claude Code (same .env file)
- No trust mode (requires confirmation for all actions)

### Adding Custom MCP Servers

**Example: Real Estate API Server**

```bash
# Add MCP server via CLI
gemini mcp add real-estate-api npx -y @custom/real-estate-mcp-server

# Or add to .gemini/settings.json
{
  "mcpServers": {
    "real-estate-api": {
      "command": "npx",
      "args": ["-y", "@custom/real-estate-mcp-server"],
      "env": {
        "REAL_ESTATE_API_KEY": "${REAL_ESTATE_API_KEY}",
        "MLS_INTEGRATION_KEY": "${MLS_INTEGRATION_KEY}"
      },
      "includeTools": ["search_properties", "get_market_data"],
      "trust": false
    }
  }
}
```

---

## Section 10: Telemetry & Observability

### Local Telemetry Enabled

**Configuration:**
- Target: Local file (`/tmp/gemini-enterprisehub-telemetry.json`)
- Protocol: OpenTelemetry (OTLP) gRPC
- Endpoint: `http://localhost:4318`
- Prompts logging: Disabled (privacy)

**Use Cases:**
- Track token usage per session
- Analyze which features use most context
- Optimize model selection based on task type
- Measure performance improvements

**View telemetry:**

```bash
# Real-time monitoring
tail -f /tmp/gemini-enterprisehub-telemetry.json | jq .

# Session analysis
cat /tmp/gemini-enterprisehub-telemetry.json | jq '.sessions[] | select(.projectHash == "enterprisehub")'
```

---

## Section 11: Gemini CLI Keyboard Shortcuts

**During session:**

| Shortcut | Action |
|----------|--------|
| **Ctrl+Y** | Toggle YOLO mode (auto-approve all) |
| **Shift+Tab** | Toggle Auto Edit mode (auto-approve edits) |
| **/** | Open session browser and filter sessions |
| **/memory refresh** | Reload context files |
| **/resume** | Interactive session picker |
| **/hooks panel** | Manage hooks |

---

## Section 12: EnterpriseHub-Specific Commands

### Quick Development Workflows

```bash
# Full feature development cycle
alias hub-explore='gemini -m exploration'
alias hub-prototype='gemini -m fast'
alias hub-implement='claude-auto'
alias hub-test='claude-yolo "run all tests and fix failures"'

# ML-specific workflows
alias ml-explore='gemini -m exploration "analyze ML models and suggest improvements"'
alias ml-implement='gemini -m precise'
alias ml-validate='claude "run ML model validation suite"'

# GHL integration workflows
alias ghl-explore='gemini "analyze GHL integration patterns"'
alias ghl-implement='claude-auto "implement GHL webhook with error handling"'

# Streamlit component workflows
alias ui-explore='gemini "analyze streamlit components"'
alias ui-implement='claude "invoke frontend-design skill"'
```

---

## Section 13: Cost Optimization Strategy

### Free Tier Maximization

**1,000 requests/day Gemini 2.5 Flash:**

**Recommended allocation:**
- 40% (400 requests): Exploration and analysis
- 30% (300 requests): Prototyping and experimentation
- 20% (200 requests): Documentation and review
- 10% (100 requests): Quick utilities and scripts

**Track usage:**

```bash
# Check daily usage
gemini --debug | grep "requests_remaining"

# View telemetry for usage patterns
cat /tmp/gemini-enterprisehub-telemetry.json | jq '.usage'
```

### When to Switch to Claude Code

**Switch triggers:**
1. Free tier exhausted for the day
2. Complex feature requiring high code quality
3. Production-critical bug fix
4. Security-sensitive implementation
5. Need for 32 EnterpriseHub skills

---

## Section 14: Troubleshooting

### Common Issues

**Issue:** Context file not loading

```bash
# Verify file exists
ls .gemini/GEMINI.md

# Force reload
gemini
/memory refresh
```

**Issue:** Hooks not executing

```bash
# Check hooks configuration
cat .gemini/settings.json | jq '.hooks'

# Enable hooks explicitly
gemini --debug  # Shows hook execution logs
```

**Issue:** MCP server connection failed

```bash
# List configured servers
gemini mcp list

# Test connection
gemini --debug  # Shows MCP connection attempts
```

**Issue:** Session not saving

```bash
# Check session directory
ls ~/.gemini/tmp/*/chats/

# Verify retention policy
cat .gemini/settings.json | jq '.general.sessionRetention'
```

---

## Section 15: Integration with Claude Code

### Shared Configuration

**Both CLIs share:**
- ✅ `.env` file (environment variables)
- ✅ MCP server definitions (GitHub integration)
- ✅ Project context (via cross-references)
- ✅ Git repository and history

**Separate configurations:**
- ❌ Sessions (different storage locations)
- ❌ Settings files (.gemini/settings.json vs .claude/settings.json)
- ❌ Context files (GEMINI.md vs CLAUDE.md, but cross-referenced)

### Seamless Workflow

```bash
# Start with Gemini exploration
gemini -m exploration "analyze services/churn_prediction_engine.py"

# Note down findings, then switch to Claude for implementation
claude-auto "refactor churn prediction engine based on Gemini analysis"

# Back to Gemini for documentation
gemini "document churn prediction engine with comprehensive docstrings"
```

---

## Section 16: Summary

**Gemini CLI Configuration for EnterpriseHub:**

✅ **Optimized for large-scale analysis** (1M context window)
✅ **Cost-effective development** (free tier leveraged)
✅ **Secure by default** (secret detection hooks, sandbox enabled)
✅ **Hybrid-ready** (seamless integration with Claude Code)
✅ **EnterpriseHub-aware** (all services, skills, and patterns included)
✅ **Production-quality** (hooks, telemetry, session management)

**Quick Start:**

```bash
# Activate Gemini CLI for EnterpriseHub
cd /Users/cave/enterprisehub
gemini

# First command - verify configuration
/memory show

# Start development
gemini "what can I help you build today?"
```

**Hybrid Development Pattern:**

1. **Explore** with Gemini (free, 1M context)
2. **Implement** with Claude (quality, skills)
3. **Document** with Gemini (comprehensive, cost-effective)
4. **Iterate** as needed

---

**Last Updated**: January 9, 2026 | **Version**: 1.0.0 | **Status**: Production Ready
**Gemini CLI Version**: 0.23.0+ | **EnterpriseHub Skills**: 32 shared | **Context**: 1M tokens
