# Claude Code Usage Guide - EnterpriseHub

Complete guide for using Claude Code with the EnterpriseHub GHL Real Estate AI project.

## 🎯 Quick Reference

### Common Commands

```bash
# Set development context
export CLAUDE_PROFILE=backend-services  # or streamlit-dev, testing-qa

# Run pre-commit checks
./.claude/scripts/pre-commit-validation.sh

# Test Python syntax
python3 -m py_compile file.py

# Run tests
pytest tests/ -v --cov=ghl_real_estate_ai

# Lint and format
ruff check --fix .
ruff format .

# Type check
mypy ghl_real_estate_ai/services/ --ignore-missing-imports
```

### Profile Selection Guide

| Task | Profile | Why |
|------|---------|-----|
| Building Streamlit UI | `streamlit-dev` | Playwright, UI tools, frontend skills |
| Creating API service | `backend-services` | Serena, Context7, API docs |
| Writing tests | `testing-qa` | Test tools, coverage, E2E |
| Debugging issues | `backend-services` | Code navigation, symbol search |
| Refactoring code | Profile based on code type | Full tool access for refactoring |

## 📋 Detailed Workflows

### Workflow 1: Adding a New GHL API Integration

**Goal**: Integrate a new GoHighLevel API endpoint (e.g., create calendar appointment)

**Steps:**

1. **Set Backend Profile**
   ```bash
   export CLAUDE_PROFILE=backend-services
   ```

2. **Invoke GHL Integration Skill**
   - Claude automatically loads skill documentation
   - Review patterns in `.claude/skills/project-specific/ghl-integration/README.md`

3. **Research API Endpoint**
   ```bash
   # Use Context7 MCP to lookup GHL docs
   # Search: "GHL calendar appointment API"
   ```

4. **Follow TDD Workflow**

   **RED Phase** - Write failing test:
   ```python
   # tests/unit/test_ghl_calendar_service.py
   import pytest
   from ghl_real_estate_ai.services.ghl_calendar_service import (
       GHLCalendarService,
       CreateAppointmentRequest
   )

   @pytest.mark.asyncio
   async def test_create_appointment_success():
       service = GHLCalendarService(
           ghl_api_key="test_key",
           location_id="test_location"
       )
       request = CreateAppointmentRequest(
           title="Property Tour",
           start_time="2024-01-15T10:00:00Z",
           contact_id="contact_123"
       )

       response = await service.create_appointment(request)

       assert response.success is True
       assert response.appointment_id is not None
   ```

   Run test (should fail):
   ```bash
   pytest tests/unit/test_ghl_calendar_service.py -v
   ```

   **GREEN Phase** - Implement service:
   ```python
   # ghl_real_estate_ai/services/ghl_calendar_service.py
   import httpx
   from pydantic import BaseModel
   from typing import Optional

   class CreateAppointmentRequest(BaseModel):
       title: str
       start_time: str
       contact_id: str

   class CreateAppointmentResponse(BaseModel):
       success: bool
       appointment_id: Optional[str] = None
       error: Optional[str] = None

   class GHLCalendarService:
       def __init__(self, ghl_api_key: str, location_id: str):
           self.ghl_api_key = ghl_api_key
           self.location_id = location_id
           self.base_url = "https://services.leadconnectorhq.com"

       async def create_appointment(
           self,
           request: CreateAppointmentRequest
       ) -> CreateAppointmentResponse:
           headers = {
               "Authorization": f"Bearer {self.ghl_api_key}",
               "Version": "2021-07-28"
           }

           async with httpx.AsyncClient() as client:
               try:
                   response = await client.post(
                       f"{self.base_url}/calendars/appointments",
                       headers=headers,
                       json={
                           "title": request.title,
                           "startTime": request.start_time,
                           "contactId": request.contact_id,
                           "locationId": self.location_id
                       }
                   )
                   response.raise_for_status()
                   data = response.json()

                   return CreateAppointmentResponse(
                       success=True,
                       appointment_id=data.get("id")
                   )
               except Exception as e:
                   return CreateAppointmentResponse(
                       success=False,
                       error=str(e)
                   )
   ```

   Run test (should pass):
   ```bash
   pytest tests/unit/test_ghl_calendar_service.py -v
   ```

   **REFACTOR Phase** - Improve code:
   - Extract common HTTP logic
   - Add caching if appropriate
   - Add logging
   - Improve error handling

5. **Pre-Commit Validation**
   ```bash
   ./.claude/scripts/pre-commit-validation.sh
   ```

6. **Commit Changes**
   ```bash
   git add ghl_real_estate_ai/services/ghl_calendar_service.py
   git add tests/unit/test_ghl_calendar_service.py
   git commit -m "feat: add GHL calendar appointment creation service

   - Implements create_appointment method
   - Adds proper error handling and typing
   - Includes comprehensive unit tests
   - Follows existing GHL integration patterns"
   ```

### Workflow 2: Creating a New Streamlit Component

**Goal**: Build a new "Lead Priority Badge" component

**Steps:**

1. **Set Frontend Profile**
   ```bash
   export CLAUDE_PROFILE=streamlit-dev
   ```

2. **Invoke Streamlit Component Skill**
   - Review patterns in `.claude/skills/project-specific/streamlit-component/README.md`

3. **Create Component File**
   ```python
   # ghl_real_estate_ai/streamlit_demo/components/lead_priority_badge.py
   """
   Lead Priority Badge Component
   Displays lead priority with color-coded badge and icon
   """
   import streamlit as st
   from typing import Literal, Optional

   LeadPriority = Literal["hot", "warm", "cold", "new"]

   def render_lead_priority_badge(
       priority: LeadPriority,
       show_label: bool = True,
       size: Literal["sm", "md", "lg"] = "md"
   ) -> None:
       """
       Render lead priority badge with color coding.

       Args:
           priority: Lead priority level
           show_label: Whether to show text label
           size: Badge size (sm, md, lg)

       Usage:
           ```python
           render_lead_priority_badge(priority="hot", size="lg")
           ```
       """
       # Color and icon mapping
       config = {
           "hot": {"color": "#FF4444", "icon": "🔥", "label": "Hot Lead"},
           "warm": {"color": "#FFA500", "icon": "⚡", "label": "Warm Lead"},
           "cold": {"color": "#4A90E2", "icon": "❄️", "label": "Cold Lead"},
           "new": {"color": "#9B59B6", "icon": "✨", "label": "New Lead"}
       }

       # Size mapping
       sizes = {
           "sm": {"padding": "0.25rem 0.5rem", "font": "0.875rem"},
           "md": {"padding": "0.5rem 1rem", "font": "1rem"},
           "lg": {"padding": "0.75rem 1.5rem", "font": "1.25rem"}
       }

       badge_config = config.get(priority, config["new"])
       size_config = sizes[size]

       # Render badge
       st.markdown(
           f"""
           <div style="
               display: inline-block;
               background-color: {badge_config['color']};
               color: white;
               padding: {size_config['padding']};
               border-radius: 9999px;
               font-size: {size_config['font']};
               font-weight: 600;
               text-align: center;
           ">
               {badge_config['icon']} {badge_config['label'] if show_label else ''}
           </div>
           """,
           unsafe_allow_html=True
       )
   ```

4. **Test Component**
   ```python
   # tests/streamlit/test_lead_priority_badge.py
   from streamlit.testing.v1 import AppTest
   import pytest

   def test_badge_renders_all_priorities():
       """Test badge renders for all priority levels"""
       priorities = ["hot", "warm", "cold", "new"]

       for priority in priorities:
           # Test would go here
           pass

   def test_badge_respects_size_parameter():
       """Test badge renders different sizes"""
       pass

   def test_badge_shows_hides_label():
       """Test show_label parameter works"""
       pass
   ```

5. **Integrate into Dashboard**
   ```python
   # In your dashboard component
   from .lead_priority_badge import render_lead_priority_badge

   def render_lead_card(lead: Dict):
       with st.container():
           col1, col2 = st.columns([3, 1])
           with col1:
               st.write(f"**{lead['name']}**")
           with col2:
               render_lead_priority_badge(
                   priority=lead['priority'],
                   size="sm"
               )
   ```

6. **Pre-Commit Validation**
   ```bash
   ./.claude/scripts/pre-commit-validation.sh
   ```

7. **Manual Testing**
   ```bash
   streamlit run ghl_real_estate_ai/streamlit_demo/app.py
   # Navigate to component in UI
   ```

### Workflow 3: Debugging a Production Issue

**Goal**: Fix "Redis connection timeout in lead scoring service"

**Steps:**

1. **Set Backend Profile**
   ```bash
   export CLAUDE_PROFILE=backend-services
   ```

2. **Use Systematic Debugging Skill**

   **REPRODUCE Phase**:
   ```bash
   # Try to reproduce locally
   pytest tests/unit/test_predictive_lead_scorer.py -v

   # Check logs
   grep -r "Redis timeout" logs/

   # Check Redis connection
   redis-cli ping
   ```

   **GATHER Phase**:
   ```bash
   # Use Serena MCP to find all Redis usage
   # Search for: "redis" in services/

   # Find service definition
   # Read: ghl_real_estate_ai/services/predictive_lead_scorer.py
   # Read: ghl_real_estate_ai/services/cache_service.py
   ```

   **HYPOTHESIZE Phase**:
   - Theory 1: Redis connection pool exhausted
   - Theory 2: Network timeout too short
   - Theory 3: Redis not running in production
   - Theory 4: Missing connection retry logic

   **TEST Phase**:
   ```python
   # Add connection pooling and retries
   # In cache_service.py
   import redis
   from redis.exceptions import ConnectionError
   import time

   class CacheService:
       def __init__(self, redis_url: str, max_retries: int = 3):
           self.redis_url = redis_url
           self.max_retries = max_retries
           self.client = self._create_client()

       def _create_client(self):
           return redis.from_url(
               self.redis_url,
               decode_responses=True,
               max_connections=50,  # Connection pool
               socket_timeout=5.0,
               socket_connect_timeout=5.0
           )

       async def get(self, key: str) -> Optional[str]:
           for attempt in range(self.max_retries):
               try:
                   return self.client.get(key)
               except ConnectionError as e:
                   if attempt == self.max_retries - 1:
                       logger.error(f"Redis connection failed: {e}")
                       return None  # Fallback gracefully
                   time.sleep(0.1 * (attempt + 1))  # Backoff
   ```

3. **Add Tests for Fix**
   ```python
   # tests/unit/test_cache_service.py
   @pytest.mark.asyncio
   async def test_redis_connection_retry():
       """Test cache service retries on connection failure"""
       pass

   @pytest.mark.asyncio
   async def test_redis_graceful_fallback():
       """Test graceful fallback when Redis unavailable"""
       pass
   ```

4. **Validate Fix**
   ```bash
   pytest tests/unit/test_cache_service.py -v
   pytest tests/integration/ -k redis -v
   ```

5. **Document Solution**
   - PostToolUse hook captures the fix pattern
   - Update troubleshooting docs

### Workflow 4: Code Review Preparation

**Goal**: Prepare code for PR review

**Steps:**

1. **Run Pre-Commit Checks**
   ```bash
   ./.claude/scripts/pre-commit-validation.sh
   ```

2. **Check Test Coverage**
   ```bash
   pytest tests/ --cov=ghl_real_estate_ai --cov-report=html
   open htmlcov/index.html

   # Ensure >= 80% coverage
   ```

3. **Run Type Checking**
   ```bash
   mypy ghl_real_estate_ai/ --ignore-missing-imports
   ```

4. **Check for Security Issues**
   ```bash
   bandit -r ghl_real_estate_ai/ -ll
   ```

5. **Review with Greptile MCP**
   ```bash
   # Use Greptile to analyze PR
   # Check for:
   # - Similar patterns in codebase
   # - Test coverage
   # - Code quality issues
   ```

6. **Generate PR Description**
   ```markdown
   ## Summary
   [Brief description of changes]

   ## Changes Made
   - Added GHL calendar appointment service
   - Implemented error handling and retry logic
   - Added comprehensive unit tests
   - Updated documentation

   ## Testing
   - [x] Unit tests pass (coverage: 92%)
   - [x] Integration tests pass
   - [x] Manual testing completed
   - [x] Pre-commit checks pass

   ## Screenshots
   [If UI changes]

   ## Checklist
   - [x] Code follows project style guide
   - [x] Tests added for new functionality
   - [x] Documentation updated
   - [x] No secrets committed
   - [x] Breaking changes documented
   ```

## 🔍 Advanced Usage

### Using Serena MCP for Code Navigation

**Find all Redis usage:**
```bash
# Serena automatically indexes codebase
# Search for pattern: "redis"
# Returns: Symbol definitions, references, usage patterns
```

**Refactor service method:**
```bash
# Use Serena to:
# 1. Find symbol: find_symbol "LeadScorer/calculate_score"
# 2. Find references: find_referencing_symbols
# 3. Replace symbol body: replace_symbol_body
# 4. Validate with tests
```

### Using Context7 for API Documentation

**Lookup API patterns:**
```bash
# Query FastAPI documentation
# Query: "FastAPI dependency injection patterns"

# Query Anthropic Claude API
# Query: "Claude streaming response handling"

# Query Redis Python client
# Query: "Redis connection pooling best practices"
```

### Using Playwright for E2E Testing

**Test Streamlit component:**
```python
# With testing-qa profile active
# Playwright automatically available

# Navigate to app
browser.navigate("http://localhost:8501")

# Take snapshot
browser.snapshot()

# Interact with component
browser.click(element="button[data-testid='lead-score-filter']")

# Validate state
assert "Hot Leads" in browser.snapshot()
```

### Using Greptile for Code Intelligence

**Search codebase patterns:**
```bash
# Find similar implementations
# Query: "GHL API error handling patterns"

# Analyze PR quality
# Check: Test coverage, code patterns, best practices

# Track code review comments
# View: Historical feedback on similar code
```

## 🎓 Best Practices

### Context Management

**Do:**
- Use appropriate MCP profile for task
- Load only necessary files into context
- Reference priority files explicitly
- Clear context when switching tasks

**Don't:**
- Load entire codebase into context
- Access forbidden paths (.env, secrets)
- Mix profiles (frontend + backend simultaneously)
- Ignore performance warnings

### Security

**Do:**
- Use .env.example for documentation
- Let hooks validate before operations
- Run pre-commit checks before pushing
- Review changes for accidental secrets

**Don't:**
- Disable security hooks
- Commit .env files
- Hardcode credentials
- Override security warnings

### Testing

**Do:**
- Follow TDD workflow (RED-GREEN-REFACTOR)
- Use condition-based waiting (not sleep)
- Mock external dependencies
- Maintain 80%+ coverage

**Don't:**
- Skip tests for "simple" changes
- Use arbitrary timeouts
- Test implementation details
- Create flaky tests

### Performance

**Do:**
- Cache expensive operations
- Use async/await consistently
- Paginate large datasets
- Profile before optimizing

**Don't:**
- Premature optimization
- Blocking synchronous calls
- Unbounded data loading
- Ignore N+1 queries

## 🐛 Troubleshooting

### Issue: Hook Not Executing

**Symptoms**: PreToolUse or PostToolUse not running

**Solutions:**
```bash
# Check hooks enabled in settings.json
grep -A 3 '"hooks"' .claude/settings.json

# Verify hook files exist
ls -l .claude/hooks/

# Check file permissions
chmod +x .claude/hooks/*.md
```

### Issue: MCP Server Connection Failed

**Symptoms**: Serena/Context7/Playwright not available

**Solutions:**
```bash
# Check profile is active
echo $CLAUDE_PROFILE

# Verify MCP server installed
which uvx  # For Serena
which npx  # For Context7/Playwright

# Check network connectivity
# MCP servers may require internet access
```

### Issue: Pre-Commit Validation Failing

**Symptoms**: Commit blocked by validation script

**Solutions:**
```bash
# Run manually to see specific errors
./.claude/scripts/pre-commit-validation.sh

# Fix syntax errors
python3 -m py_compile problematic_file.py

# Fix linting
ruff check --fix .

# Fix type errors
mypy --ignore-missing-imports file.py

# Check for secrets
grep -r "ANTHROPIC_API_KEY\|GHL.*API" .
```

### Issue: Tests Failing After Changes

**Symptoms**: Previously passing tests now fail

**Solutions:**
```bash
# Run specific test file
pytest tests/unit/test_specific.py -v

# Run with debugging
pytest tests/unit/test_specific.py -v -s --pdb

# Check for race conditions
# Use condition-based-waiting skill

# Verify mocks are correct
# Check fixture setup/teardown
```

## 📚 Additional Resources

### Documentation
- Main Project Guide: `/CLAUDE.md`
- Claude Directory: `.claude/README.md`
- Quick Start: `/QUICK_START_GUIDE.md`

### Skills
- All Skills: `.claude/skills/*/README.md`
- GHL Integration: `.claude/skills/project-specific/ghl-integration/README.md`
- Streamlit Components: `.claude/skills/project-specific/streamlit-component/README.md`

### Agents
- TDD Guardian: `.claude/agents/tdd-guardian.md`
- Architecture Sentinel: `.claude/agents/architecture-sentinel.md`
- Integration Testing: `.claude/agents/integration-test-workflow.md`

### External Resources
- [Claude Code Documentation](https://docs.anthropic.com/claude-code)
- [Streamlit Documentation](https://docs.streamlit.io)
- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [GHL API Documentation](https://highlevel.stoplight.io/docs/integrations/)

---

**Version**: 1.0.0
**Last Updated**: January 14, 2026
**Status**: Production-Ready
