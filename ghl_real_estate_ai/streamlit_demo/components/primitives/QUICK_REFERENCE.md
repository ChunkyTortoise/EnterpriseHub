# Primitive Component Library - Quick Reference

## Installation

No installation needed - primitives are now part of EnterpriseHub.

## Import

```python
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from components.primitives import render_obsidian_card, CardConfig, icon, ICONS

# Apply theme (includes Font Awesome)
inject_elite_css()
```

## Card Component

### Basic Usage
```python
render_obsidian_card(
    title="Title",
    content="<p>HTML content here</p>",
    icon='fire'  # Optional Font Awesome icon
)
```

### Variants

```python
# Default
render_obsidian_card(title="Title", content="Content")

# Glass
render_obsidian_card(title="Title", content="Content", config=CardConfig(variant='glass'))

# Premium
render_obsidian_card(title="Title", content="Content", config=CardConfig(variant='premium'))

# Alert
render_obsidian_card(title="Title", content="Content",
    config=CardConfig(variant='alert', glow_color='#EF4444'))
```

## Icon System

### Custom Icons
```python
icon('fire', color='#EF4444', size='1.5em')
icon('star', style='regular')
icon('github', style='brands')
```

### Pre-configured Icons
```python
ICONS['hot_lead']()      # 🔥 → Fire (red)
ICONS['warm_lead']()     # 🌡️ → Temperature (amber)
ICONS['cold_lead']()     # ❄️ → Snowflake (blue)
ICONS['property']()      # 🏠 → House
ICONS['analytics']()     # 📊 → Chart
ICONS['conversation']()  # 💬 → Comments
ICONS['phone']()         # 📞 → Phone
ICONS['email']()         # ✉️ → Envelope
ICONS['calendar']()      # 📅 → Calendar
ICONS['dollar']()        # 💰 → Dollar
ICONS['star']()          # ⭐ → Star
ICONS['check']()         # ✅ → Check (green)
ICONS['warning']()       # ⚠️ → Warning (amber)
ICONS['error']()         # ❌ → Error (red)
ICONS['info']()          # ℹ️ → Info (blue)
```

### Helpers
```python
get_lead_temp_icon('hot')      # Auto-select icon
get_status_icon('success')     # Auto-select icon
```

## Theme Tokens

```python
from ghl_real_estate_ai.streamlit_demo.theme_service import Colors, Typography, Spacing

Colors.PRIMARY           # '#6366F1'
Colors.HOT              # '#EF4444'
Colors.WARM             # '#F59E0B'
Colors.COLD             # '#3B82F6'
Typography.HEADING_FAMILY  # 'Space Grotesk, sans-serif'
Typography.BODY_FAMILY     # 'Inter, sans-serif'
Spacing.MD              # '1.5rem'
```

## Common Patterns

### Lead Card
```python
render_obsidian_card(
    title=f"{ICONS['hot_lead']()} Hot Leads",
    content=f"<p><strong>15</strong> leads need attention</p>",
    config=CardConfig(variant='alert', glow_color='#EF4444')
)
```

### Property Card
```python
render_obsidian_card(
    title=f"{ICONS['property']()} Property Match",
    content="<p>AI Confidence: 94%</p>",
    config=CardConfig(variant='glass'),
    icon='sparkles'
)
```

### Analytics Card
```python
render_obsidian_card(
    title=f"{ICONS['analytics']()} Metrics",
    content=f"{ICONS['dollar']()} <strong>$1.2M</strong> Pipeline",
    config=CardConfig(variant='premium')
)
```

## Tips

- **Always use primitives** instead of inline styling
- **4 lines vs 15+ lines** - huge time saver
- **Type-safe** - CardConfig prevents errors
- **Consistent** - Single source of truth for theming
- **Professional** - Font Awesome > emojis

## Resources

- Full docs: `README.md`
- Examples: `USAGE_EXAMPLES.md`
- Demo: `streamlit run test_primitives_demo.py`
- Icons: https://fontawesome.com/icons
