# Figma-to-Component Templates

## Template: Basic Streamlit Component from Figma

```python
"""
Basic component template for Figma-generated Streamlit components.

This template provides a foundation for converting Figma designs into
production-ready Streamlit components with type safety, caching, and testing.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import streamlit as st
from enum import Enum


# ============================================================================
# SECTION 1: Type Definitions
# ============================================================================

class ComponentVariant(Enum):
    """Component style variants (map from Figma variants)."""
    DEFAULT = "default"
    COMPACT = "compact"
    EXPANDED = "expanded"


@dataclass
class ComponentProps:
    """
    Type-safe props for component.

    Attributes:
        title: Component title
        variant: Visual variant
        data: Component data payload
        key: Optional unique key for Streamlit
        on_click: Optional callback function
    """
    title: str
    variant: ComponentVariant = ComponentVariant.DEFAULT
    data: Optional[Dict[str, Any]] = None
    key: Optional[str] = None
    on_click: Optional[callable] = None


# ============================================================================
# SECTION 2: Design System Integration
# ============================================================================

@st.cache_resource
def get_design_system():
    """
    Initialize and cache design system (singleton pattern).

    Returns:
        DesignSystem: Cached design system instance
    """
    from ghl_real_estate_ai.streamlit_demo.components.ui_elements import (
        DesignSystem,
        ColorScheme
    )
    return DesignSystem(ColorScheme.PROFESSIONAL)


# ============================================================================
# SECTION 3: Component Rendering
# ============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def render_component(props: ComponentProps) -> None:
    """
    Render component matching Figma design specifications.

    This function generates HTML that matches the Figma design with 1:1 fidelity,
    using design system tokens for consistency.

    Args:
        props: Component properties

    Returns:
        None (renders directly to Streamlit)

    Design Source: [Figma URL]
    Generated: [timestamp]
    """

    # Initialize design system
    design = get_design_system()
    tokens = design.tokens

    # Variant-specific styling
    variant_styles = {
        ComponentVariant.DEFAULT: {
            'padding': tokens.spacing_lg,
            'min_height': '200px',
        },
        ComponentVariant.COMPACT: {
            'padding': tokens.spacing_md,
            'min_height': '100px',
        },
        ComponentVariant.EXPANDED: {
            'padding': tokens.spacing_xl,
            'min_height': '300px',
        }
    }

    style = variant_styles.get(props.variant, variant_styles[ComponentVariant.DEFAULT])

    # Generate component HTML
    component_html = f"""
    <div class="figma-component {props.variant.value}" style="
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_medium};
        padding: {style['padding']};
        min-height: {style['min_height']};
        box-shadow: {tokens.shadow_medium};
        transition: {tokens.transition_medium};
        font-family: {tokens.font_family};
    ">
        <!-- Component Header -->
        <div class="component-header" style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: {tokens.spacing_md};
            border-bottom: 1px solid {tokens.border_light};
            padding-bottom: {tokens.spacing_sm};
        ">
            <div class="component-title" style="
                font-size: {tokens.font_size_large};
                font-weight: {tokens.font_weight_bold};
                color: {tokens.text_primary};
            ">
                {props.title}
            </div>
        </div>

        <!-- Component Body -->
        <div class="component-body" style="
            color: {tokens.text_primary};
            font-size: {tokens.font_size_base};
            line-height: 1.6;
        ">
            <!-- Content goes here -->
            {_render_component_content(props.data, tokens) if props.data else ''}
        </div>

        <!-- Component Footer (optional) -->
        <div class="component-footer" style="
            margin-top: {tokens.spacing_md};
            padding-top: {tokens.spacing_sm};
            border-top: 1px solid {tokens.border_light};
            font-size: {tokens.font_size_small};
            color: {tokens.text_muted};
            text-align: right;
        ">
            <!-- Footer content -->
        </div>
    </div>
    """

    st.markdown(component_html, unsafe_allow_html=True)

    # Handle interactions (if callback provided)
    if props.on_click:
        if st.button("Action", key=props.key or f"btn_{hash(props.title)}"):
            props.on_click()


def _render_component_content(data: Dict[str, Any], tokens) -> str:
    """
    Render component content based on data.

    Args:
        data: Component data
        tokens: Design system tokens

    Returns:
        str: HTML content
    """
    if not data:
        return ""

    # Example content rendering
    content_html = ""
    for key, value in data.items():
        content_html += f"""
        <div style="margin-bottom: {tokens.spacing_sm};">
            <span style="
                font-weight: {tokens.font_weight_medium};
                color: {tokens.text_secondary};
            ">{key}:</span>
            <span style="
                margin-left: {tokens.spacing_xs};
                color: {tokens.text_primary};
            ">{value}</span>
        </div>
        """

    return content_html


# ============================================================================
# SECTION 4: Accessibility Helpers
# ============================================================================

def add_aria_attributes(element_id: str, role: str, label: str) -> str:
    """
    Generate ARIA attributes for accessibility.

    Args:
        element_id: Unique element identifier
        role: ARIA role (button, link, etc.)
        label: Accessible label

    Returns:
        str: ARIA attribute string
    """
    return f'id="{element_id}" role="{role}" aria-label="{label}"'


# ============================================================================
# SECTION 5: Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example component usage
    st.title("Component Showcase")

    # Default variant
    props_default = ComponentProps(
        title="Default Component",
        variant=ComponentVariant.DEFAULT,
        data={"Status": "Active", "Count": 42}
    )
    render_component(props_default)

    st.markdown("---")

    # Compact variant
    props_compact = ComponentProps(
        title="Compact Component",
        variant=ComponentVariant.COMPACT,
        data={"Score": 85}
    )
    render_component(props_compact)

    st.markdown("---")

    # Expanded variant with callback
    def handle_click():
        st.success("Button clicked!")

    props_expanded = ComponentProps(
        title="Expanded Component",
        variant=ComponentVariant.EXPANDED,
        data={"Details": "Full information display"},
        on_click=handle_click
    )
    render_component(props_expanded)
```

## Template: Complex Component with Sub-components

```python
"""
Complex component template with nested sub-components.
Use this for components with multiple sections and interactive elements.
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import streamlit as st


@dataclass
class SubComponentProps:
    """Props for nested sub-component."""
    label: str
    value: Any
    icon: Optional[str] = None


@dataclass
class ComplexComponentProps:
    """Props for complex component with sub-components."""
    title: str
    sections: List[SubComponentProps]
    show_actions: bool = True
    key: Optional[str] = None


@st.cache_data(ttl=300)
def render_complex_component(props: ComplexComponentProps) -> None:
    """
    Render complex component with multiple sections.

    Args:
        props: Complex component properties
    """

    design = get_design_system()
    tokens = design.tokens

    # Main container
    st.markdown(f"""
    <div class="complex-component" style="
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_medium};
        overflow: hidden;
        box-shadow: {tokens.shadow_large};
    ">
        <!-- Component Header -->
        <div style="
            background: {tokens.primary};
            color: white;
            padding: {tokens.spacing_lg};
            font-size: {tokens.font_size_large};
            font-weight: {tokens.font_weight_bold};
        ">
            {props.title}
        </div>

        <!-- Sections Container -->
        <div style="padding: {tokens.spacing_lg};">
            {_render_sections(props.sections, tokens)}
        </div>

        <!-- Actions (if enabled) -->
        {_render_actions(tokens) if props.show_actions else ''}
    </div>
    """, unsafe_allow_html=True)

    # Interactive elements (buttons) rendered separately
    if props.show_actions:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Primary Action", key=f"{props.key}_primary"):
                st.success("Primary action executed")
        with col2:
            if st.button("Secondary Action", key=f"{props.key}_secondary"):
                st.info("Secondary action executed")
        with col3:
            if st.button("Tertiary Action", key=f"{props.key}_tertiary"):
                st.warning("Tertiary action executed")


def _render_sections(sections: List[SubComponentProps], tokens) -> str:
    """Render individual sections of complex component."""
    sections_html = ""

    for section in sections:
        icon_html = f'<span style="margin-right: {tokens.spacing_sm};">{section.icon}</span>' if section.icon else ''

        sections_html += f"""
        <div style="
            margin-bottom: {tokens.spacing_md};
            padding: {tokens.spacing_md};
            background: {tokens.background};
            border-radius: {tokens.radius_small};
            border-left: 3px solid {tokens.accent};
        ">
            <div style="
                font-weight: {tokens.font_weight_medium};
                color: {tokens.text_secondary};
                margin-bottom: {tokens.spacing_xs};
                font-size: {tokens.font_size_small};
            ">
                {icon_html}{section.label}
            </div>
            <div style="
                font-size: {tokens.font_size_large};
                font-weight: {tokens.font_weight_bold};
                color: {tokens.text_primary};
            ">
                {section.value}
            </div>
        </div>
        """

    return sections_html


def _render_actions(tokens) -> str:
    """Render action buttons placeholder."""
    return f"""
    <div style="
        border-top: 1px solid {tokens.border_light};
        padding: {tokens.spacing_md} {tokens.spacing_lg};
        background: {tokens.surface};
    ">
        <!-- Streamlit buttons will be rendered here -->
    </div>
    """
```

## Template: Responsive Grid Layout

```python
"""
Responsive grid layout template for displaying multiple components.
"""

from typing import List, Dict, Any
import streamlit as st


@st.cache_data(ttl=300)
def render_responsive_grid(
    items: List[Dict[str, Any]],
    columns_desktop: int = 3,
    columns_tablet: int = 2,
    columns_mobile: int = 1
) -> None:
    """
    Render responsive grid layout from Figma design.

    Args:
        items: List of items to display in grid
        columns_desktop: Number of columns on desktop (>=1200px)
        columns_tablet: Number of columns on tablet (>=768px)
        columns_mobile: Number of columns on mobile (<768px)
    """

    design = get_design_system()
    tokens = design.tokens

    # Generate responsive CSS
    st.markdown(f"""
    <style>
    .responsive-grid {{
        display: grid;
        gap: {tokens.spacing_lg};
        grid-template-columns: repeat({columns_desktop}, 1fr);
    }}

    @media (max-width: 1200px) {{
        .responsive-grid {{
            grid-template-columns: repeat({columns_tablet}, 1fr);
        }}
    }}

    @media (max-width: 768px) {{
        .responsive-grid {{
            grid-template-columns: repeat({columns_mobile}, 1fr);
        }}
    }}

    .grid-item {{
        background: {tokens.surface};
        border: 1px solid {tokens.border};
        border-radius: {tokens.radius_medium};
        padding: {tokens.spacing_lg};
        box-shadow: {tokens.shadow_small};
        transition: {tokens.transition_medium};
    }}

    .grid-item:hover {{
        box-shadow: {tokens.shadow_large};
        transform: translateY(-2px);
    }}
    </style>
    """, unsafe_allow_html=True)

    # Render grid items
    grid_html = '<div class="responsive-grid">'

    for item in items:
        grid_html += f"""
        <div class="grid-item">
            <div style="
                font-size: {tokens.font_size_large};
                font-weight: {tokens.font_weight_bold};
                color: {tokens.text_primary};
                margin-bottom: {tokens.spacing_sm};
            ">
                {item.get('title', 'Item')}
            </div>
            <div style="
                font-size: {tokens.font_size_base};
                color: {tokens.text_secondary};
            ">
                {item.get('description', '')}
            </div>
        </div>
        """

    grid_html += '</div>'

    st.markdown(grid_html, unsafe_allow_html=True)
```

## Best Practices for Using Templates

1. **Start with Basic Template**: Use for simple components without complex interactions
2. **Complex Template**: Use when component has multiple sections or nested elements
3. **Grid Layout**: Use for displaying multiple similar items
4. **Customize Tokens**: Always use design system tokens, never hardcode values
5. **Add Type Hints**: Ensure all props have proper type annotations
6. **Document Source**: Always include Figma URL in component docstring
7. **Test Thoroughly**: Create visual regression tests for all variants

## Template Customization Guide

### Step 1: Replace Placeholder Content
```python
# Before (placeholder)
<div>{props.title}</div>

# After (with actual Figma content)
<div style="
    font-size: 24px;
    font-weight: 600;
    color: #1f2937;
    letter-spacing: -0.02em;
">{props.title}</div>
```

### Step 2: Map Figma Variants to Enums
```python
# Extract variants from Figma
class ComponentVariant(Enum):
    DEFAULT = "default"           # From Figma: Default state
    HOVER = "hover"               # From Figma: Hover state
    ACTIVE = "active"             # From Figma: Active state
    DISABLED = "disabled"         # From Figma: Disabled state
```

### Step 3: Add Interactive States
```python
# Add CSS for interactive states
"""
<style>
.component-button {{
    transition: all 0.3s ease;
}}

.component-button:hover {{
    background: {tokens.accent};
    transform: scale(1.05);
}}

.component-button:active {{
    transform: scale(0.98);
}}

.component-button:disabled {{
    opacity: 0.5;
    cursor: not-allowed;
}}
</style>
"""
```

### Step 4: Implement Accessibility
```python
# Add ARIA attributes and semantic HTML
component_html = f"""
<section role="region" aria-labelledby="component-title">
    <h2 id="component-title" style="...">
        {props.title}
    </h2>
    <button
        role="button"
        aria-label="Primary action button"
        tabindex="0"
    >
        Action
    </button>
</section>
"""
```

## Common Figma-to-Code Patterns

### Pattern: Auto Layout → Flexbox
```python
# Figma: Auto Layout (Horizontal, spacing: 16px)
# Code:
"""
<div style="
    display: flex;
    flex-direction: row;
    gap: 16px;
    align-items: center;
">
    <!-- Child elements -->
</div>
"""
```

### Pattern: Constraints → CSS Positioning
```python
# Figma: Left & Right constraints
# Code:
"""
<div style="
    position: absolute;
    left: 0;
    right: 0;
">
    <!-- Content -->
</div>
"""
```

### Pattern: Effects → Box Shadow
```python
# Figma: Drop Shadow (x:0, y:4, blur:6, spread:0, color:rgba(0,0,0,0.1))
# Code:
"""
<div style="
    box-shadow: 0 4px 6px 0 rgba(0, 0, 0, 0.1);
">
    <!-- Content -->
</div>
"""
```

---

**Last Updated**: January 2026
**For More Examples**: See `.claude/skills/design/figma-to-component/examples/`
