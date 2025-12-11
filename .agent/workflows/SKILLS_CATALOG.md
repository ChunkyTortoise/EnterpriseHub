# Claude Skills - Consolidated Catalog

**Last Updated**: 2025-12-10

## Summary

- **Total Skills**: 62 across 3 repositories
- **Unique Skills**: 50 (12 are duplicates)
- **Repositories**:
  - `anthropics/skills` (Official) - 16 skills
  - `ComposioHQ/awesome-claude-skills` (Community) - 27 skills
  - `obra/superpowers` (Development Workflow) - 19 skills

## Duplicate Skills

These 12 skills appear in both `anthropics/skills` and `awesome-claude-skills`. Use the version from `anthropics/skills` (official):

- brand-guidelines
- canvas-design
- docx
- internal-comms
- mcp-builder
- pdf
- pptx
- skill-creator
- slack-gif-creator
- theme-factory
- webapp-testing
- xlsx

## Skills by Category

### 🔥 Essential Development Workflow (obra/superpowers)

**Use these daily for software development**

| Skill | Description | When to Use |
|-------|-------------|-------------|
| `test-driven-development` | RED-GREEN-REFACTOR cycle | Implementing any feature or bugfix |
| `systematic-debugging` | 4-phase root cause analysis | Any bug, test failure, unexpected behavior |
| `brainstorming` | Socratic design refinement | Before writing code or implementation plans |
| `writing-plans` | Create detailed implementation tasks | When design is complete |
| `executing-plans` | Execute plans in controlled batches | When you have a complete implementation plan |
| `requesting-code-review` | Pre-review checklist | Before merging, completing major features |
| `receiving-code-review` | Guide feedback response | When receiving code review feedback |
| `finishing-a-development-branch` | Merge/PR decision workflow | Implementation complete, all tests pass |
| `verification-before-completion` | Validate work before claiming done | Before committing or creating PRs |

### 🧪 Testing & Quality (obra/superpowers)

| Skill | Description | Priority |
|-------|-------------|----------|
| `condition-based-waiting` | Fix race conditions in tests | High |
| `testing-anti-patterns` | Avoid common test pitfalls | High |
| `defense-in-depth` | Multi-layer validation | Medium |
| `testing-skills-with-subagents` | Verify skill quality | Low |

### 🐛 Debugging & Analysis (obra/superpowers)

| Skill | Description | Priority |
|-------|-------------|----------|
| `root-cause-tracing` | Trace errors to original trigger | High |
| `systematic-debugging` | 4-phase debugging process | High |

### 🤖 Advanced Workflows (obra/superpowers)

| Skill | Description | Priority |
|-------|-------------|----------|
| `subagent-driven-development` | Fast iteration with quality gates | High |
| `dispatching-parallel-agents` | Coordinate concurrent workflows | Medium |
| `writing-skills` | Create new skills | Low |
| `sharing-skills` | Contribute skills upstream | Low |
| `using-superpowers` | Establishes skill workflows | Low |

### 📄 Document Processing (anthropics/skills)

**Professional document manipulation**

| Skill | Format | Use Case |
|-------|--------|----------|
| `docx` | Word | Create/edit with tracked changes, comments |
| `pdf` | PDF | Extract text/tables, merge, annotate |
| `pptx` | PowerPoint | Create/edit presentations |
| `xlsx` | Excel | Spreadsheet manipulation, formulas, charts |
| `doc-coauthoring` | Any | Collaborative document writing workflow |

### ✍️ Content & Writing (awesome-claude-skills + anthropics/skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `content-research-writer` | Research, citations, section feedback | High |
| `internal-comms` | Company communications (3P updates, newsletters) | Medium |
| `changelog-generator` | Auto-create changelogs from git commits | Medium |
| `meeting-insights-analyzer` | Analyze transcripts for behavioral patterns | Low |

### 🎨 Creative & Design (anthropics/skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `canvas-design` | Visual art in PNG/PDF | Medium |
| `frontend-design` | Production-grade UI interfaces | High |
| `algorithmic-art` | p5.js generative art | Low |
| `theme-factory` | Style artifacts with professional themes | Medium |
| `brand-guidelines` | Apply Anthropic brand standards | Low |
| `slack-gif-creator` | Animated GIFs for Slack | Low |

### 🌐 Web Development (anthropics/skills + awesome-claude-skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `web-artifacts-builder` | Multi-component HTML artifacts (React, Tailwind) | High |
| `webapp-testing` | Playwright testing for web apps | High |
| `image-enhancer` | Enhance screenshots/images | Low |
| `video-downloader` | Download videos from platforms | Low |

### 💼 Business & Marketing (awesome-claude-skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `lead-research-assistant` | Identify & qualify leads | Medium |
| `competitive-ads-extractor` | Analyze competitor ads | Medium |
| `domain-name-brainstormer` | Generate domain ideas + check availability | Low |
| `developer-growth-analysis` | Analyze coding patterns from chat history | Low |

### 🛠️ Productivity & Organization (awesome-claude-skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `file-organizer` | Intelligently organize files/folders | Medium |
| `invoice-organizer` | Organize invoices/receipts for taxes | Low |
| `raffle-winner-picker` | Random winner selection | Low |

### 🏗️ Development Tools (anthropics/skills + awesome-claude-skills)

| Skill | Description | Priority |
|-------|-------------|----------|
| `mcp-builder` | Create MCP servers for LLM integrations | Medium |
| `skill-creator` | Guide for creating new skills | High |
| `skill-share` | Auto-share skills on Slack | Low |

## Recommended Minimal Setup

For most developers, start with these 15 core skills:

### From obra/superpowers (8)
1. test-driven-development
2. systematic-debugging
3. brainstorming
4. writing-plans
5. executing-plans
6. requesting-code-review
7. finishing-a-development-branch
8. verification-before-completion

### From anthropics/skills (5)
1. docx
2. pdf
3. pptx
4. xlsx
5. doc-coauthoring

### From awesome-claude-skills (2)
1. content-research-writer
2. skill-creator

## How to Enable Skills

Skills are auto-discovered from these locations:
- **Personal**: `~/.claude/skills/`
- **Project**: `.claude/skills/`
- **Plugin commands**: Loaded dynamically

## Next Steps

1. **Remove duplicates** - Delete 12 duplicate skills from `awesome-claude-skills`
2. **Symlink core skills** - Create symlinks to essential skills in `.claude/skills/`
3. **Test workflow** - Verify obra/superpowers skills work correctly
4. **Create custom skills** - Use skill-creator for project-specific needs

## Repository Locations

```
.agent/workflows/
├── anthropics/skills/           # Official Anthropic skills
├── awesome-claude-skills/       # Community collection (has duplicates)
└── obra/superpowers/            # Development workflow skills
```
