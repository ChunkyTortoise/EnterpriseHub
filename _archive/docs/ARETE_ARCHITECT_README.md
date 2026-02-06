# ARETE-Architect: AI Technical Co-Founder

## Overview

ARETE-Architect is a production-ready AI agent that serves as an autonomous technical co-founder. Built with Claude API, LangGraph, and comprehensive GitHub integration, it can maintain and extend entire software systems through natural language conversation.

## Key Capabilities

### 🗣️ Conversational Interface
- Natural language interaction via web-based chat
- Streaming responses for real-time feedback
- Context-aware conversations across sessions

### 🧠 Persistent Memory
- PostgreSQL-backed conversation history
- Decision logging with reasoning
- Context retrieval from past interactions
- Never loses track of your requests

### 🔧 GitHub Integration
- **Read**: Clone repos, browse files, analyze code
- **Write**: Create/update files, commit changes
- **Manage**: Create branches, pull requests, issues
- **Deploy**: Trigger CI/CD pipelines, manage releases

### 💻 Code Generation
- Writes production-quality code based on requirements
- Generates comprehensive tests (pytest)
- Creates documentation automatically
- Follows best practices and design patterns

### 🚀 Self-Improvement
- Analyzes its own decision log
- Learns from successes and failures
- Updates strategies autonomously
- Requests human review for major changes

## Architecture

```
User Request → Planner → Coder → GitHub Handler → Responder
                ↓          ↓           ↓
             Memory DB   Claude API  Git Operations
```

### Core Components

1. **Planner Node**: Analyzes requests and creates execution plans
2. **Coder Node**: Generates code using Claude API
3. **GitHub Node**: Executes file operations and git commands
4. **Responder Node**: Formats and delivers responses
5. **Memory System**: Persists conversations and decisions
6. **GitHub Tools**: Complete GitHub API integration

## Tech Stack

- **Framework**: LangGraph for agent orchestration
- **LLM**: Claude API (Anthropic)
- **Memory**: JSON-based persistent storage (upgradable to PostgreSQL)
- **Version Control**: GitHub API via PyGithub
- **UI**: Streamlit chat interface
- **Language**: Python 3.9+

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Required packages
pip install anthropic langchain langchain-anthropic langgraph PyGithub gitpython
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_claude_api_key

# Optional (for GitHub integration)
GITHUB_TOKEN=your_github_personal_access_token
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer Settings → Personal Access Tokens
2. Generate new token with permissions:
   - `repo` (full control of private repositories)
   - `workflow` (update GitHub Actions workflows)
3. Add token to environment or enter in UI

## Usage

### Starting the Agent

```bash
# Via Streamlit
streamlit run app.py

# Navigate to ARETE-Architect module
```

### Example Interactions

**Simple Task:**
```
User: "Read the README.md and add a new 'Contributing' section"

ARETE:
📋 Plan:
1. Read current README.md
2. Draft Contributing section
3. Update file on GitHub

✅ Complete. Changes committed to main branch.
```

**Complex Task:**
```
User: "Create a new API endpoint for user authentication"

ARETE:
📋 Plan:
1. Analyze existing API structure
2. Generate authentication endpoint code
3. Write unit tests
4. Update API documentation
5. Create pull request for review

🔨 Generated:
- api/endpoints/auth.py (45 lines)
- tests/test_auth.py (23 lines)
- docs/api/authentication.md (updated)

✅ PR created: #42 "feat: User Authentication Endpoint"
Review at: https://github.com/user/repo/pull/42
```

## Memory System

### Conversation History

All interactions are saved to `.arete_memory_{session_id}.json`:

```json
{
  "session_id": "20250101_143022",
  "conversation_history": [
    {
      "role": "user",
      "content": "Add logging to the main function",
      "timestamp": "2025-01-01T14:30:45"
    },
    {
      "role": "assistant",
      "content": "Logging added. Import statements updated, logger configured.",
      "timestamp": "2025-01-01T14:30:52"
    }
  ],
  "decision_log": [
    {
      "decision": "Add Python logging module",
      "reasoning": "Better debugging and production monitoring",
      "outcome": "success",
      "timestamp": "2025-01-01T14:30:50"
    }
  ]
}
```

### Decision Logging

Every significant action is logged with:
- What decision was made
- Why it was made (reasoning)
- What happened (outcome)
- When it occurred

This enables the agent to learn from past interactions.

## GitHub Tools API

### Available Operations

```python
github_tools = GitHubTools(github_token="your_token")

# Read file
content = github_tools.read_file("owner/repo", "path/to/file.py")

# Write/update file
github_tools.write_file(
    "owner/repo",
    "path/to/file.py",
    content="# New code here",
    commit_message="feat: Add new feature"
)

# Create branch
github_tools.create_branch("owner/repo", "feature/new-feature")

# Create pull request
pr_url = github_tools.create_pull_request(
    "owner/repo",
    title="Add new feature",
    body="Description of changes",
    head_branch="feature/new-feature"
)

# List files
files = github_tools.list_files("owner/repo", path="src/")
```

## Agent Workflow

### 1. Planning Phase
The agent analyzes your request and creates a step-by-step plan:
- Identifies required files
- Determines necessary operations
- Estimates complexity
- Plans validation steps

### 2. Execution Phase
The agent executes each step:
- Reads relevant code/docs
- Generates new code with Claude
- Writes changes to GitHub
- Runs tests (if applicable)

### 3. Validation Phase
The agent verifies the work:
- Checks for errors
- Validates syntax
- Reviews changes
- Updates documentation

### 4. Response Phase
The agent reports back:
- Summarizes what was done
- Shows relevant code snippets
- Provides links to commits/PRs
- Suggests next steps

## Use Cases

### Business Operations
- "Create a business plan outline for Q1"
- "Research top 5 competitors and summarize their pricing"
- "Draft a job posting for a senior engineer"

### Development
- "Fix the bug in user authentication"
- "Refactor the database connection code"
- "Add unit tests for the API endpoints"

### Documentation
- "Update the README with installation instructions"
- "Create API documentation from code comments"
- "Write a tutorial for new users"

### Deployment
- "Deploy the latest changes to staging"
- "Create a release tag for v2.0"
- "Set up a CI/CD pipeline with GitHub Actions"

## Limitations & Safety

### Current Limitations
- Code execution is simulated (not running actual code)
- GitHub operations require valid token
- Complex refactoring may need human review
- No direct database access (by design)

### Safety Features
- All GitHub operations are logged
- Destructive actions require confirmation
- Version control enables easy rollback
- Decision log provides full audit trail

## Future Enhancements

### Planned Features
- [ ] PostgreSQL backend for enterprise scale
- [ ] Code execution sandbox for testing
- [ ] Multi-repository orchestration
- [ ] Automated PR review and approval
- [ ] Cost tracking and optimization
- [ ] Integration with Jira/Linear for project management

### Self-Improvement Capabilities
- [ ] Analyze decision log for patterns
- [ ] A/B test different prompting strategies
- [ ] Auto-update own prompts based on outcomes
- [ ] Request human feedback on edge cases

## Troubleshooting

### "LangGraph not available"
```bash
pip install langgraph langchain langchain-anthropic
```

### "GitHub API rate limit exceeded"
- Use authenticated requests (GitHub token)
- Rate limit: 5,000 requests/hour (authenticated)

### "Conversation history not loading"
- Check file permissions on `.arete_memory_*.json` files
- Ensure session ID is consistent

### "Claude API errors"
- Verify `ANTHROPIC_API_KEY` is set correctly
- Check API usage limits at console.anthropic.com

## Contributing

This module is designed to be extended. To add new capabilities:

1. **Add a new node** to the LangGraph workflow
2. **Create new tools** in the GitHubTools class
3. **Update the state** schema if needed
4. **Test thoroughly** with real interactions

## License

MIT License - Part of EnterpriseHub platform

## Support

For issues or questions:
- GitHub Issues: [EnterpriseHub Issues](https://github.com/ChunkyTortoise/EnterpriseHub/issues)
- Documentation: [Full Docs](https://github.com/ChunkyTortoise/EnterpriseHub/tree/main/docs)

---

**Built with ❤️ as proof that AI agents can truly serve as autonomous technical co-founders.**
