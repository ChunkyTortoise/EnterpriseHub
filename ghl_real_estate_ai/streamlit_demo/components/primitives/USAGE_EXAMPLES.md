# Primitive Component Library - Usage Examples

## Overview

The primitive component library provides reusable, Obsidian-themed UI components that replace inline styling across the EnterpriseHub platform. This results in:

- **75% reduction in component code** (15+ lines → 4 lines)
- **Consistent theming** across all components
- **Type-safe configuration** with dataclasses
- **Better maintainability** with centralized styling

---

## Components

### 1. Card Component

#### Before (Inline Styling - 15+ lines)

```python
import streamlit as st

st.markdown(f"""
<div style="
    background: rgba(22, 27, 34, 1);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
">
    <h3 style="
        color: #FFFFFF;
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
    ">Hot Leads</h3>
    <p style="color: #E6EDF3;">15 leads need attention</p>
</div>
""", unsafe_allow_html=True)
```

#### After (Using Primitive - 4 lines)

```python
from components.primitives import render_obsidian_card, CardConfig

render_obsidian_card(
    title="Hot Leads",
    content="<p>15 leads need attention</p>",
    config=CardConfig(variant='alert', glow_color='#EF4444'),
    icon='fire'
)
```

**Result**: 75% code reduction, type-safe configuration, consistent theming

---

## Card Variants

### Default Variant
```python
render_obsidian_card(
    title="Property Insights",
    content="<p>3,247 active properties in database</p>",
    icon='house'
)
```
- Standard Obsidian card
- Subtle shadow
- Dark background

### Glass Variant
```python
render_obsidian_card(
    title="AI Analysis",
    content="<p>Claude is analyzing lead patterns...</p>",
    config=CardConfig(variant='glass'),
    icon='brain'
)
```
- Glassmorphism effect
- Backdrop blur
- Semi-transparent

### Premium Variant
```python
render_obsidian_card(
    title="Elite Feature",
    content="<p>Advanced property matching AI</p>",
    config=CardConfig(variant='premium'),
    icon='sparkles'
)
```
- Gradient background
- Indigo accent glow
- Premium appearance

### Alert Variant
```python
render_obsidian_card(
    title="Urgent Action Required",
    content="<p>5 hot leads need immediate followup</p>",
    config=CardConfig(variant='alert', glow_color='#EF4444'),
    icon='exclamation-triangle'
)
```
- Colored border
- Custom glow color
- Attention-grabbing

---

## Icon System

### Basic Icon Usage

#### Before (Inline Emoji)
```python
st.markdown("🔥 Hot Leads")
```

#### After (Font Awesome Icon)
```python
from components.primitives import icon

st.markdown(f"{icon('fire', color='#EF4444')} Hot Leads", unsafe_allow_html=True)
```

### Using Pre-configured Icons

```python
from components.primitives import ICONS

# Lead temperature icons
st.markdown(f"{ICONS['hot_lead']()} Hot Lead", unsafe_allow_html=True)
st.markdown(f"{ICONS['warm_lead']()} Warm Lead", unsafe_allow_html=True)
st.markdown(f"{ICONS['cold_lead']()} Cold Lead", unsafe_allow_html=True)

# Property icons
st.markdown(f"{ICONS['property']()} Single Family Home", unsafe_allow_html=True)
st.markdown(f"{ICONS['building']()} Commercial Property", unsafe_allow_html=True)

# Analytics icons
st.markdown(f"{ICONS['analytics']()} Performance Metrics", unsafe_allow_html=True)
st.markdown(f"{ICONS['chart']()} Revenue Dashboard", unsafe_allow_html=True)

# Communication icons
st.markdown(f"{ICONS['conversation']()} AI Chat", unsafe_allow_html=True)
st.markdown(f"{ICONS['phone']()} Call Scheduled", unsafe_allow_html=True)
st.markdown(f"{ICONS['email']()} Email Sent", unsafe_allow_html=True)

# Status icons
st.markdown(f"{ICONS['check']()} Completed", unsafe_allow_html=True)
st.markdown(f"{ICONS['warning']()} Pending Review", unsafe_allow_html=True)
st.markdown(f"{ICONS['error']()} Failed", unsafe_allow_html=True)
```

### Helper Functions

```python
from components.primitives import get_lead_temp_icon, get_status_icon

# Automatically get icon for lead temperature
lead_temp = "hot"  # from data
temp_icon = get_lead_temp_icon(lead_temp)
st.markdown(f"{temp_icon} Priority Lead", unsafe_allow_html=True)

# Automatically get icon for status
status = "success"  # from operation
status_icon = get_status_icon(status)
st.markdown(f"{status_icon} Operation completed", unsafe_allow_html=True)
```

### Custom Icons

```python
from components.primitives import icon

# Large icon
st.markdown(icon('star', size='2rem', color='#F59E0B'), unsafe_allow_html=True)

# Regular style (outline)
st.markdown(icon('heart', style='regular', color='#EF4444'), unsafe_allow_html=True)

# Brand icon
st.markdown(icon('github', style='brands', color='#FFFFFF'), unsafe_allow_html=True)
```

---

## Real-World Component Examples

### Lead Dashboard Card

```python
from components.primitives import render_obsidian_card, CardConfig, ICONS

lead_count = 15
lead_temp = "hot"

render_obsidian_card(
    title=f"{ICONS['hot_lead']()} Hot Leads Requiring Attention",
    content=f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="font-size: 2rem; font-weight: 700; margin: 0;">{lead_count}</p>
                <p style="color: #8B949E; margin: 0;">Leads need immediate followup</p>
            </div>
            <div>
                {ICONS['phone']()} {ICONS['email']()} {ICONS['calendar']()}
            </div>
        </div>
    """,
    config=CardConfig(variant='alert', glow_color='#EF4444')
)
```

### Property Match Card

```python
render_obsidian_card(
    title=f"{ICONS['property']()} Property Match Insights",
    content="""
        <p><strong>AI Confidence:</strong> 94%</p>
        <p><strong>Price Range:</strong> $450K - $520K</p>
        <p><strong>Location:</strong> Preferred neighborhood</p>
        <p style="margin-top: 1rem; color: #8B949E;">
            Claude recommends scheduling a showing based on buyer preferences.
        </p>
    """,
    config=CardConfig(variant='glass'),
    icon='sparkles'
)
```

### Analytics Summary Card

```python
render_obsidian_card(
    title=f"{ICONS['analytics']()} Performance Metrics",
    content=f"""
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <p>{ICONS['conversation']()} <strong>47</strong> AI Conversations</p>
                <p>{ICONS['check']()} <strong>23</strong> Qualified Leads</p>
            </div>
            <div>
                <p>{ICONS['dollar']()} <strong>$1.2M</strong> Pipeline Value</p>
                <p>{ICONS['star']()} <strong>4.8</strong> Lead Quality Score</p>
            </div>
        </div>
    """,
    config=CardConfig(variant='premium')
)
```

---

## Theme Service Usage

For advanced customization, you can access the theme service directly:

```python
from ghl_real_estate_ai.streamlit_demo.theme_service import (
    ObsidianThemeService, Colors, Typography, Spacing
)

theme = ObsidianThemeService()

# Access tokens via dot notation
primary_color = theme.get_token('colors.brand.primary')  # '#6366F1'
heading_font = theme.get_token('typography.family.heading')  # 'Space Grotesk, sans-serif'

# Or use convenience classes
st.markdown(f'<h1 style="color: {Colors.PRIMARY};">Dashboard</h1>', unsafe_allow_html=True)
st.markdown(f'<p style="font-family: {Typography.BODY_FAMILY};">Content</p>', unsafe_allow_html=True)
```

---

## Migration Guide

### Step 1: Import Primitives

Replace inline styling imports with primitive imports:

```python
# Old
import streamlit as st

# New
import streamlit as st
from components.primitives import render_obsidian_card, CardConfig, icon, ICONS
```

### Step 2: Replace Inline Cards

Find all inline card implementations (search for `st.markdown` with style attributes):

```python
# Find these patterns
st.markdown(f"""<div style="background:...">...</div>""", unsafe_allow_html=True)
```

Replace with:

```python
render_obsidian_card(title="...", content="...", config=CardConfig(variant='...'))
```

### Step 3: Replace Emojis with Icons

Find emoji usage:

```python
# Old
"🔥 Hot Leads"
"📊 Analytics"
"🏠 Properties"
```

Replace with Font Awesome:

```python
# New
f"{ICONS['hot_lead']()} Hot Leads"
f"{ICONS['analytics']()} Analytics"
f"{ICONS['property']()} Properties"
```

---

## Benefits Summary

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Lines of Code** | 15+ lines/card | 4 lines/card | 75% reduction |
| **Type Safety** | None | Full dataclass validation | 100% type-safe |
| **Theming Consistency** | Manual per component | Centralized tokens | Single source of truth |
| **Maintenance** | 132+ inline implementations | 1 primitive component | 99% easier updates |
| **Icon System** | Emojis (inconsistent) | Font Awesome (professional) | Better accessibility |

---

## Available Icons Reference

### Lead Temperature
- `hot_lead` - Fire icon (red)
- `warm_lead` - Temperature icon (amber)
- `cold_lead` - Snowflake icon (blue)

### Properties
- `property` - House icon
- `building` - Building icon
- `location` - Location pin icon

### Analytics
- `analytics` - Line chart icon
- `chart` - Bar chart icon
- `dashboard` - Gauge icon

### Communication
- `conversation` - Comments icon
- `phone` - Phone icon
- `email` - Envelope icon
- `calendar` - Calendar icon

### Status
- `check` / `circle_check` - Success icons (green)
- `warning` - Warning triangle (amber)
- `error` - Error circle (red)
- `info` - Info circle (blue)

### Financial
- `dollar` - Dollar sign icon
- `money` - Money bill icon

### Actions
- `search` - Magnifying glass
- `filter` - Filter icon
- `download` - Download icon
- `upload` - Upload icon
- `settings` - Gear icon

### AI/Special
- `ai` / `brain` - AI brain icon (purple)
- `robot` - Robot icon (purple)
- `sparkles` - Sparkles icon (amber)
- `star` / `star_outline` - Star icons

### User
- `user` - Single user icon
- `users` - Multiple users icon

Find more icons at: https://fontawesome.com/icons

---

## Next Steps

1. **Migrate Existing Components**: Start with high-traffic components (lead dashboard, property cards)
2. **Add More Primitives**: Implement button, metric, and badge components
3. **Create Patterns**: Build composed components from primitives (lead_card, property_card)
4. **Document Customizations**: Add project-specific variants as needed

---

**Version**: 1.0.0
**Last Updated**: January 2026
**Maintainer**: EnterpriseHub Team
