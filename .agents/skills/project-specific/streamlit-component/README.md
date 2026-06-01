# Streamlit Component Development

**Skill**: Streamlit Component Creation
**Category**: Real Estate AI - Frontend
**Version**: 1.0.0
**Last Updated**: 2026-01-14

## Purpose

Standardize the creation of reusable, performant, and consistent Streamlit components for the EnterpriseHub real estate AI platform. Ensures proper caching, error handling, and integration with backend services.

## When to Use This Skill

Invoke this skill when:
- Creating new dashboard components
- Building interactive property visualizations
- Developing lead intelligence interfaces
- Adding AI-powered UI elements
- Refactoring existing components for reusability

## Prerequisites

- Understanding of Streamlit session state
- Knowledge of caching strategies
- Backend service integration patterns
- UI/UX design system familiarity

## Component Development Workflow

### 1. Component Planning

**Key Questions:**
- What is the component's single responsibility?
- What data does it need from backend services?
- What user interactions should it support?
- Should it maintain state across reruns?
- What are the performance requirements?

**Component Classification:**
```python
# Display Component: Read-only, shows data
# Example: PropertyCard, LeadScoreDisplay, AnalyticsChart

# Interactive Component: User input, triggers actions
# Example: PropertySearchFilter, LeadScoreEditor, ChatInterface

# Composite Component: Combines multiple sub-components
# Example: LeadDashboard, PropertyMatcher, ExecutiveHub
```

### 2. File Structure

```
ghl_real_estate_ai/streamlit_demo/components/
├── [component_name].py          # Component implementation
└── tests/
    └── test_[component_name].py # Component tests
```

### 3. Component Template

**Basic Component Structure:**
```python
"""
[Component Name] Component
[Brief description of what this component does]
"""
import streamlit as st
from typing import Optional, Dict, Any, List
from ..services.cache_service import CacheService
from ..services.[relevant_service] import [Service]
import logging

logger = logging.getLogger(__name__)


def render_[component_name](
    data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    key: Optional[str] = None
) -> None:
    """
    Render [component name] with given data.

    Args:
        data: Component data (from backend service)
        config: Component configuration options
        key: Unique key for component instance

    Usage:
        ```python
        render_[component_name](
            data={"title": "Dashboard"},
            config={"theme": "dark"},
            key="main_component"
        )
        ```
    """
    # Generate unique key if not provided
    component_key = key or "component_default"

    # Initialize session state
    if f"{component_key}_initialized" not in st.session_state:
        st.session_state[f"{component_key}_initialized"] = True
        st.session_state[f"{component_key}_data"] = None

    # Component container
    with st.container():
        # Component logic here
        _render_component_content(data, config, component_key)


def _render_component_content(
    data: Optional[Dict[str, Any]],
    config: Optional[Dict[str, Any]],
    key: str
) -> None:
    """Internal rendering logic (private function)"""
    try:
        # Validation
        if data is None:
            st.warning("No data provided to component")
            return

        # Render component UI
        st.markdown(f"### {data.get('title', 'Component')}")

        # Add interactive elements
        # ...

    except Exception as e:
        logger.error(f"Error rendering {key}: {str(e)}")
        st.error(f"Failed to render component: {str(e)}")


# Optional: Data fetching with caching
@st.cache_data(ttl=300)
def _fetch_component_data(
    param1: str,
    param2: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch data for component with caching.

    Args:
        param1: Primary data identifier
        param2: Optional secondary parameter

    Returns:
        Dictionary with component data
    """
    # Fetch from backend service
    # This will be cached for 5 minutes
    try:
        # service = SomeService()
        # data = service.get_data(param1, param2)
        return {"title": "Sample Data"}
    except Exception as e:
        logger.error(f"Error fetching data: {str(e)}")
        return {}


# Optional: Resource caching (for connections, clients)
@st.cache_resource
def _get_service_client() -> Any:
    """
    Get cached service client instance.

    Returns:
        Initialized service client
    """
    # Initialize expensive resources once
    # Example: database connections, API clients
    return None  # Replace with actual client
```

### 4. Caching Strategies

**st.cache_data (for data):**
```python
# Use for: API responses, database queries, computed results
@st.cache_data(ttl=300)  # 5 minutes
def fetch_lead_data(lead_id: str) -> Dict:
    # Expensive data fetching
    return service.get_lead(lead_id)

# With show_spinner
@st.cache_data(ttl=600, show_spinner="Loading properties...")
def fetch_properties(filters: Dict) -> List[Dict]:
    return service.search_properties(filters)

# With hash_funcs for custom objects
@st.cache_data(
    ttl=300,
    hash_funcs={CustomClass: lambda x: x.id}
)
def process_custom_data(obj: CustomClass) -> Dict:
    return obj.process()
```

**st.cache_resource (for connections):**
```python
# Use for: Database connections, API clients, ML models
@st.cache_resource
def get_redis_client():
    import redis
    return redis.Redis(host='localhost', port=6379)

@st.cache_resource
def get_claude_client():
    from anthropic import Anthropic
    return Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
```

### 5. Session State Management

**Initialization Pattern:**
```python
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "current_lead_id": None,
        "filter_state": {},
        "conversation_history": [],
        "ui_preferences": {"theme": "dark"}
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# Call at component start
init_session_state()
```

**State Update Pattern:**
```python
# Reading state
current_lead = st.session_state.get("current_lead_id")

# Updating state
if st.button("Select Lead"):
    st.session_state.current_lead_id = lead_id
    st.rerun()  # Trigger rerun to show changes

# Callback pattern
def on_filter_change():
    st.session_state.filter_applied = True

st.selectbox(
    "Filter",
    options=["All", "Hot", "Warm"],
    key="filter_value",
    on_change=on_filter_change
)
```

### 6. Error Handling

**Graceful Degradation:**
```python
def render_component_with_error_handling(data: Dict) -> None:
    """Component with comprehensive error handling"""
    try:
        # Validate input
        if not data or "required_field" not in data:
            st.warning("⚠️ Missing required data. Showing defaults.")
            data = get_default_data()

        # Render main content
        render_content(data)

    except Exception as e:
        # Log error
        logger.error(f"Component error: {str(e)}", exc_info=True)

        # Show user-friendly message
        st.error("❌ Unable to load component. Please try again.")

        # Optional: Show error details in expander
        with st.expander("🔍 Error Details"):
            st.code(str(e))

        # Provide recovery action
        if st.button("🔄 Retry"):
            st.rerun()
```

**Service Integration Error Handling:**
```python
@st.cache_data(ttl=300)
def fetch_from_service(service_name: str, params: Dict) -> Optional[Dict]:
    """Fetch data with fallback on error"""
    try:
        service = get_service(service_name)
        return service.get_data(params)
    except TimeoutError:
        st.warning("⏱️ Request timed out. Using cached data.")
        return get_cached_data(params)
    except ConnectionError:
        st.error("🔌 Service unavailable. Please check your connection.")
        return None
    except Exception as e:
        logger.error(f"Service error: {str(e)}")
        st.error(f"❌ Error: {str(e)}")
        return None
```

### 7. Performance Optimization

**Lazy Loading:**
```python
# Only load expensive components when needed
if st.session_state.get("show_analytics"):
    with st.spinner("Loading analytics..."):
        render_analytics_dashboard()
```

**Pagination:**
```python
def render_paginated_list(items: List[Dict], page_size: int = 10):
    """Render large lists with pagination"""
    if "current_page" not in st.session_state:
        st.session_state.current_page = 0

    total_pages = len(items) // page_size
    start_idx = st.session_state.current_page * page_size
    end_idx = start_idx + page_size

    # Show current page items
    for item in items[start_idx:end_idx]:
        render_item(item)

    # Pagination controls
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("◀ Previous") and st.session_state.current_page > 0:
            st.session_state.current_page -= 1
            st.rerun()
    with col2:
        st.write(f"Page {st.session_state.current_page + 1} of {total_pages + 1}")
    with col3:
        if st.button("Next ▶") and st.session_state.current_page < total_pages:
            st.session_state.current_page += 1
            st.rerun()
```

**Debouncing User Input:**
```python
import time

def debounced_input(label: str, debounce_ms: int = 500) -> Optional[str]:
    """Input with debouncing to avoid excessive reruns"""
    key = f"debounced_{label}"

    if f"{key}_last_update" not in st.session_state:
        st.session_state[f"{key}_last_update"] = 0
        st.session_state[f"{key}_value"] = ""

    user_input = st.text_input(label, key=key)

    current_time = time.time() * 1000
    if current_time - st.session_state[f"{key}_last_update"] > debounce_ms:
        st.session_state[f"{key}_value"] = user_input
        st.session_state[f"{key}_last_update"] = current_time

    return st.session_state[f"{key}_value"]
```

### 8. Testing Pattern

**Component Test Template:**
```python
"""
Tests for [Component Name]
"""
import pytest
from streamlit.testing.v1 import AppTest


def test_component_renders_with_data():
    """Test component renders correctly with valid data"""
    at = AppTest.from_file("components/[component_name].py")
    at.run()

    # Check component exists
    assert not at.exception

    # Check expected elements present
    assert len(at.markdown) > 0
    assert len(at.button) > 0


def test_component_handles_missing_data():
    """Test component gracefully handles missing data"""
    at = AppTest.from_file("components/[component_name].py")
    at.run()

    # Should show warning, not crash
    assert len(at.warning) > 0
    assert not at.exception


def test_component_state_management():
    """Test session state is properly managed"""
    at = AppTest.from_file("components/[component_name].py")
    at.run()

    # Check initial state
    assert "component_initialized" in at.session_state

    # Simulate interaction
    at.button[0].click().run()

    # Check state updated
    assert at.session_state["component_initialized"] is True


def test_component_caching():
    """Test data caching works correctly"""
    # Test cache behavior
    pass
```

## Design System Integration

**UI Elements Library:**
```python
# Use existing UI elements
from .ui_elements import (
    render_card,
    render_metric_card,
    render_stat_box,
    create_styled_button
)

def render_my_component(data: Dict):
    """Component using design system"""
    with render_card(title="Lead Details"):
        render_metric_card(
            label="Lead Score",
            value=data.get("score", 0),
            delta=data.get("score_change", 0)
        )
```

**Consistent Styling:**
```python
# Apply project CSS
def apply_component_styles():
    """Apply consistent styling to component"""
    st.markdown("""
        <style>
        .component-container {
            padding: 1rem;
            border-radius: 0.5rem;
            background: var(--background-color);
        }
        </style>
    """, unsafe_allow_html=True)
```

## Quality Checklist

Before considering the component complete:

- [ ] Component has single, clear responsibility
- [ ] Properly uses st.cache_data or st.cache_resource
- [ ] Session state initialized and managed correctly
- [ ] Error handling covers edge cases
- [ ] User-friendly error messages displayed
- [ ] Performance optimized (lazy loading, pagination)
- [ ] Consistent with design system
- [ ] Responsive to different screen sizes
- [ ] Documented with docstrings
- [ ] Unit tests cover main functionality
- [ ] Integration test with backend services (if applicable)
- [ ] No memory leaks in session state
- [ ] Logging added for debugging

## Common Patterns

**AI-Powered Component:**
```python
def render_ai_insights(lead_data: Dict):
    """Component with Claude AI integration"""
    with st.spinner("🤖 Analyzing with Claude AI..."):
        insights = st.cache_data(ttl=600)(
            get_claude_insights
        )(lead_data)

    st.markdown("### 🧠 AI Insights")
    st.write(insights)
```

**Real-Time Updates:**
```python
import asyncio

def render_realtime_dashboard():
    """Component with real-time updates"""
    placeholder = st.empty()

    while True:
        data = fetch_latest_data()
        with placeholder.container():
            render_dashboard_content(data)
        time.sleep(5)  # Update every 5 seconds
```

## Related Skills

- `frontend-design` - UI/UX consistency
- `web-artifacts-builder` - Interactive component generation
- `theme-factory` - Styling and theming
- `testing-anti-patterns` - Test quality
- `condition-based-waiting` - Async testing

## References

- [Streamlit Documentation](https://docs.streamlit.io)
- Existing components: `ghl_real_estate_ai/streamlit_demo/components/`
- UI elements: `ghl_real_estate_ai/streamlit_demo/components/ui_elements.py`
- Config: `ghl_real_estate_ai/.streamlit/config.toml`
