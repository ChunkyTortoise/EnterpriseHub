# Labs: Production AI Systems

## Overview

Each week has a hands-on lab where you build a component of a production AI system. Labs run in GitHub Codespaces with zero local setup required.

## Lab Environment

All labs share a common development environment:

- **Runtime**: Python 3.11
- **Database**: PostgreSQL 15 with pgvector extension
- **Cache**: Redis 7
- **Container**: Docker + Docker Compose
- **IDE**: VS Code (via Codespace) with Python, Pylance, and Ruff extensions

## Getting Started

### Step 1: Accept the Assignment

Click the GitHub Classroom assignment link provided in Discord. This creates a private repository for your submission.

### Step 2: Launch Codespace

1. Open your assignment repository on GitHub
2. Click the green **Code** button
3. Select the **Codespaces** tab
4. Click **Create codespace on main**
5. Wait for the environment to build (first launch: ~2 minutes, subsequent: ~30 seconds)

### Step 3: Verify Environment

Once the Codespace is ready, open a terminal and run:

```bash
# Verify Python
python --version  # Should show 3.11.x

# Verify PostgreSQL
pg_isready  # Should show "accepting connections"

# Verify Redis
redis-cli ping  # Should show "PONG"

# Verify dependencies
pip list | grep fastapi  # Should show fastapi installed

# Run the starter test suite
pytest tests/ -v  # Should show failing tests (your job to make them pass)
```

### Step 4: Complete the Lab

Follow the instructions in each lab's `README.md`. Your goal is to make all autograder tests pass.

### Step 5: Submit

```bash
git add .
git commit -m "Complete lab N"
git push
```

GitHub Classroom's autograder runs automatically on push. Check the Actions tab for results.

## Lab Schedule

| Week | Lab | Topic | Deadline |
|------|-----|-------|----------|
| 1 | week1-agentforge | Multi-agent customer service bot | End of Week 1 |
| 2 | week2-docqa | Document Q&A with hybrid search | End of Week 2 |
| 3 | week3-mcp | 2 custom MCP servers | End of Week 3 |
| 4 | week4-enterprisehub | Caching + rate limiting | End of Week 4 |
| 5 | week5-insight-engine | Monitoring dashboard + 50 tests | End of Week 5 |
| 6 | week6-deployment | Deploy your project | End of Week 6 |

Late submissions are accepted up to 1 week after the deadline with a 20% score penalty.

## Autograder

Each lab includes autograder tests in the `tests/` directory. The autograder:

1. Runs `pytest tests/ -v` on your submission
2. Reports pass/fail for each test
3. Calculates a score based on passing tests
4. Posts results to #lab-submissions in Discord

**Passing threshold**: 70% of tests must pass to receive credit for the lab.

## Getting Help

1. **#lab-help** in Discord — TA responds within 2 hours during lab weeks
2. **#technical-support** — For environment/setup issues
3. **Office hours** — Thursday after Session B for 30 minutes
4. **Peer support** — Collaborate with classmates (but submit your own work)

## Troubleshooting

**Codespace won't start**: Try deleting and recreating. If the issue persists, post in #technical-support with the error message.

**Tests failing unexpectedly**: Run `pytest tests/ -v --tb=long` for detailed error output. Check that your database migrations have run.

**Database connection errors**: Run `pg_isready` to check PostgreSQL. If it's not running, restart the Codespace.

**Redis connection errors**: Run `redis-cli ping`. If no response, run `redis-server --daemonize yes` to start Redis.
