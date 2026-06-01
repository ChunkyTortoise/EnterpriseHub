---
name: Caching Decorator Enforcer
type: PreToolUse
enabled: true
priority: 50
---

# Caching Decorator Enforcement

Enforce Streamlit caching best practices to ensure optimal component performance.

## Trigger Conditions

```yaml
triggers:
  - tool: Write
    path_pattern: "ghl_real_estate_ai/streamlit_demo/components/*.py"
  - tool: Edit
    path_pattern: "ghl_real_estate_ai/streamlit_demo/components/*.py"
```

## Validation Logic

When a component file is being written or edited:

1. **Parse the file content** for function definitions
2. **Identify cacheable functions** based on naming patterns
3. **Check for caching decorators** (`@st.cache_data`, `@st.cache_resource`)
4. **Warn if missing**, unless bypass comment present

## Function Classification

### Data Functions (Require @st.cache_data)

Functions that transform or fetch data should use `@st.cache_data(ttl=<seconds>)`:

**Naming Patterns**:
- `load_*` - Load data from sources
- `fetch_*` - Fetch data from APIs
- `get_*_data` - Retrieve data
- `calculate_*` - Perform calculations
- `aggregate_*` - Aggregate data
- `transform_*` - Transform data
- `generate_*_data` - Generate data

**Example**:
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_lead_analytics(lead_id: str) -> dict:
    # Expensive data transformation
    return analytics_data
```

### Resource Functions (Require @st.cache_resource)

Functions that create connections or expensive objects should use `@st.cache_resource`:

**Naming Patterns**:
- `get_*_client` - Get API/database clients
- `init_*` - Initialize resources
- `create_connection` - Create connections
- `get_*_service` - Get service instances

**Example**:
```python
@st.cache_resource
def get_redis_client():
    return redis.Redis(host='localhost', port=6379)
```

### Event Handlers (Never Cache)

Functions that handle user interactions should NOT be cached:

**Naming Patterns**:
- `handle_*` - Event handlers
- `on_*` - Event callbacks
- `render_*` - Render functions (may have internal cacheable helpers)

## Bypass Mechanism

Add a comment to skip caching enforcement:

```python
# @cache-skip: Event handler, must run every time
def handle_button_click():
    st.session_state.clicked = True
```

Or:

```python
# @cache-skip: Intentionally uncached for real-time updates
def get_live_market_data():
    return fetch_latest_prices()
```

## Warning Message Template

When a cacheable function is detected without a decorator:

```
⚠️  CACHING DECORATOR MISSING

Function: `{function_name}` in `{file_path}`
Pattern: {matched_pattern}

Recommendation:
{recommendation}

Performance Impact:
- Without caching: Function runs on every Streamlit rerun
- With caching: 40-60% load time improvement
- TTL suggestion: 300 seconds (5 minutes) for frequently changing data

Add bypass comment if intentional:
# @cache-skip: <reason>

Reference: CLAUDE.md (Streamlit Component Patterns)
```

## Recommendation Logic

```python
def get_recommendation(function_name: str) -> str:
    if any(function_name.startswith(p) for p in ['load_', 'fetch_', 'get_', 'calculate_', 'aggregate_', 'transform_', 'generate_']):
        return """
Add data caching:
    @st.cache_data(ttl=300)
    def {function_name}(...):
        pass

Choose TTL based on data freshness:
- Real-time data: ttl=60 (1 minute)
- Frequently changing: ttl=300 (5 minutes)
- Stable data: ttl=3600 (1 hour)
- Static data: no ttl parameter
"""
    elif any(function_name.startswith(p) for p in ['get_client', 'init_', 'create_connection', 'get_service']):
        return """
Add resource caching:
    @st.cache_resource
    def {function_name}(...):
        pass

Use for:
- Database connections
- API clients
- Expensive object initialization
- Singleton instances
"""
    else:
        return """
Consider caching if function:
- Performs expensive computations
- Fetches data from external sources
- Returns immutable data structures

Use @st.cache_data for data transformations
Use @st.cache_resource for client connections
"""
```

## Implementation Notes

### Detection Strategy

1. **Parse Python AST** to find function definitions
2. **Check decorator list** for existing cache decorators
3. **Match function name** against patterns
4. **Look for bypass comments** in docstring or preceding line
5. **Generate warning** if cacheable but not cached

### Edge Cases

- **Already decorated**: Skip validation
- **Bypass comment present**: Skip validation
- **Inside class**: Check for `self` parameter, may be method
- **Async functions**: Support `@st.cache_data` on async functions
- **Multiple decorators**: Check entire decorator list

### Performance Targets

Based on EnterpriseHub benchmarks:

- **Without caching**: 2-4 second component load times
- **With caching**: 0.8-1.2 second load times
- **Improvement**: 40-60% faster
- **User experience**: Smoother interactions, less waiting

## Severity Levels

### Error (Block commit)
- Never used - this is a warning-only hook

### Warning (Allow but notify)
- Missing `@st.cache_data` on data functions
- Missing `@st.cache_resource` on resource functions

### Info (FYI)
- Function could potentially benefit from caching
- Unclear if function is cacheable

## Integration

### Pre-commit Hook
This validation runs automatically before commits via `.claude/scripts/pre-commit-validation.sh`

### Manual Validation
```bash
# Check specific component
python .claude/scripts/validate-caching.py ghl_real_estate_ai/streamlit_demo/components/lead_intelligence_hub.py

# Check all components
python .claude/scripts/validate-caching.py ghl_real_estate_ai/streamlit_demo/components/
```

### Auto-fix
```bash
# Automatically add decorators
python .claude/scripts/add-caching-decorators.py ghl_real_estate_ai/streamlit_demo/components/lead_intelligence_hub.py
```

## References

- [Streamlit Caching Documentation](https://docs.streamlit.io/library/advanced-features/caching)
- EnterpriseHub CLAUDE.md (Streamlit Component Patterns)
- `.claude/FRONTEND_EXCELLENCE_SYNTHESIS.md` (lines 421-563)

## Changelog

- **v1.0.0** (2026-01-16): Initial implementation
  - Data function detection
  - Resource function detection
  - Bypass mechanism
  - Warning message template
