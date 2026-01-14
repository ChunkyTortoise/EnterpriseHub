# Code Style & Conventions

## Python Style Guide
- **Formatting**: Black (line length: 88 characters)
- **Import Sorting**: isort with black-compatible settings
- **Linting**: flake8 with PEP 8 compliance
- **Type Hints**: Required for all public functions (mypy enforced)
- **Docstrings**: Google-style docstrings for public functions

## Naming Conventions
- **Files**: Snake_case (e.g., `lead_intelligence_hub.py`)
- **Functions**: Snake_case (e.g., `render_property_matcher`)
- **Classes**: PascalCase (e.g., `MockService`, `DashboardView`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `ENHANCED_LEAD_SCORER_AVAILABLE`)
- **Variables**: Snake_case (e.g., `selected_market`, `ai_tone`)

## Streamlit Component Patterns
```python
def render_component_name(data, config=None):
    \"\"\"
    Render a specific UI component.
    
    Args:
        data: Component data
        config: Optional configuration dict
    \"\"\"
    # Component implementation
    pass
```

## File Organization
```
ghl_real_estate_ai/
├── streamlit_demo/
│   ├── app.py                    # Main application entry
│   ├── components/               # UI components (26+ files)
│   │   ├── lead_intelligence_hub.py
│   │   ├── property_matcher_ai.py
│   │   └── ui_elements.py
│   ├── services/                 # Business logic
│   └── pages/                    # Additional pages
```

## Component Standards
- **Error Handling**: Use `st.error()`, `st.warning()`, `st.info()` for user feedback
- **Loading States**: Use `st.spinner()` with realistic delays (0.5s-1.5s)
- **State Management**: Use `st.session_state` for persistence
- **Responsiveness**: Test on mobile/tablet viewports

## AI Integration Patterns
- **Claude Assistant**: Use `services/claude_assistant.py` for persistent AI context
- **Prompt Engineering**: Store templates in dedicated prompt files
- **Error Handling**: Graceful degradation for API failures
- **Rate Limiting**: Implement exponential backoff for API calls

## Testing Patterns
- **File Location**: Co-located with source (e.g., `test_lead_scorer.py` near `lead_scorer.py`)
- **Naming**: `test_` prefix for test files and functions
- **Coverage**: Minimum 80% line coverage, 85%+ for critical paths
- **Mocking**: Use `pytest` fixtures for external dependencies

## Git Commit Conventions
```
type: brief description

feat: new feature
fix: bug fix
docs: documentation update
style: formatting/style changes
refactor: code restructuring
test: add/update tests
chore: maintenance tasks
```

## Security Guidelines
- **API Keys**: Never commit to git, use `.env` files
- **Input Validation**: Sanitize all user inputs
- **Error Messages**: Don't expose sensitive information
- **Dependencies**: Regular security audits with `pip-audit`