# Cayman Roden - Freelance AI Engineer

Python: FastAPI and Streamlit. TypeScript: Next.js. EnterpriseHub is one of the portfolio repos under `~/Projects/`.

## Workflow

- Explore, plan, build, verify.
- Read relevant files before editing.
- Ask before architecture changes, DB schema changes, deployments, file deletion, force-pushes, dropping tables, deleting branches, or security workflow changes.
- Prefer targeted reads and `rg`/`fd` over broad scans.
- Use `just <recipe>` when a Justfile exists.

## Standards

- FastAPI endpoints should use `response_model`, explicit `status_code`, and typed dependencies.
- Async service code should use explicit error handling; avoid bare `except`.
- Next.js should use server components for data fetches and client components only for interactivity.
- New code should include at least one happy-path test.

## Error Recovery

- On test failure, read the failing test and code under test before fixing.
- On build error, check dependency versions and lock files before changing code.
- After 3 failed attempts on the same issue, stop, summarize what was tried, and ask for guidance.
- When adding async service code, propagate exceptions with explicit types and log before re-raising.

## Context

- Prefer small, specific file reads over dumping large directories.
- Summarize long test output instead of pasting everything.
- For long tasks, write checkpoints to `claude-progress.txt` or a task-specific progress file if continuity is at risk.
- When resuming, check `git status`, recent commits, and any progress file before continuing.

## Done When

- Relevant test suite passes.
- Linter is clean: ruff for Python, eslint for JS/TS.
- Changes are minimal; do not refactor unrelated code.

## Do Not

- Modify `.env` files or secrets.
- Install packages without asking.
- Auto-commit unless explicitly asked.
- Use destructive git or filesystem commands unless explicitly requested.
