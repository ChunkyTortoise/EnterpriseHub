# Enterprise Design System - Quick Reference

## Installation & Setup

```python
# In your Streamlit app
from ghl_real_estate_ai.design_system import inject_enterprise_theme

# Call at the top of your app (after st.set_page_config)
inject_enterprise_theme()
```

---

## Color Palette Quick Reference

### Primary Colors
| Name | Hex | Usage |
|------|-----|-------|
| Navy 600 | `#1e3a8a` | Primary brand, headers |
| Navy 500 | `#2563eb` | Interactive elements |
| Gold 500 | `#d4af37` | Premium accents, CTAs |
| Bronze 500 | `#cd7f32` | Secondary accents |

### Status Colors
| Status | Hex | Usage |
|--------|-----|-------|
| Success | `#059669` | Positive states, confirmations |
| Warning | `#f59e0b` | Attention needed |
| Danger | `#ef4444` | Errors, critical alerts |
| Info | `#0ea5e9` | Informational |

### CSS Variables
```css
var(--enterprise-navy-600)
var(--enterprise-gold-500)
var(--status-success-500)
var(--status-warning-500)
var(--status-danger-500)
var(--neutral-800)  /* Headings */
var(--neutral-600)  /* Body text */
```

---

## Typography Quick Reference

### Font Families
```css
--font-display: 'Playfair Display'  /* Headlines, metrics */
--font-heading: 'Inter'             /* Subheadings */
--font-body: 'Inter'                /* Body text */
--font-mono: 'JetBrains Mono'       /* Code, numbers */
```

### Type Scale
| Class | Size | Usage |
|-------|------|-------|
| `--text-xs` | 12px | Captions, labels |
| `--text-sm` | 14px | Secondary text |
| `--text-base` | 16px | Body text |
| `--text-lg` | 18px | Lead text |
| `--text-xl` | 20px | H5 |
| `--text-2xl` | 24px | H4 |
| `--text-3xl` | 30px | H3 |
| `--text-4xl` | 36px | H2 |
| `--text-5xl` | 48px | H1 |

---

## Spacing Scale

```
4px   --space-1
8px   --space-2
12px  --space-3
16px  --space-4
24px  --space-6
32px  --space-8
48px  --space-12
64px  --space-16
```

---

## Component Usage

### Metric Cards
```python
from ghl_real_estate_ai.design_system import enterprise_metric

enterprise_metric(
    label="Total Revenue",
    value="$125,000",
    delta="+12.5%",
    delta_type="positive",
    icon=""
)
```

### Cards
```python
from ghl_real_estate_ai.design_system import enterprise_card

enterprise_card(
    content="<p>Your content here</p>",
    title="Card Title",
    variant="gold",  # default, gold, success, warning, danger, glass, premium
    footer="Optional footer"
)
```

### Badges
```python
from ghl_real_estate_ai.design_system import enterprise_badge

badge_html = enterprise_badge(
    text="HOT LEAD",
    variant="danger",  # default, primary, gold, success, warning, danger, info, live
    icon=""
)
st.markdown(badge_html, unsafe_allow_html=True)
```

### Progress Ring
```python
from ghl_real_estate_ai.design_system import enterprise_progress_ring

enterprise_progress_ring(
    value=75,
    label="Qualification Progress",
    size=80,
    stroke_width=8
)
```

### KPI Grid
```python
from ghl_real_estate_ai.design_system import enterprise_kpi_grid

metrics = [
    {"label": "Revenue", "value": "$125K", "delta": "+12%", "delta_type": "positive"},
    {"label": "Leads", "value": "847", "delta": "+8%", "delta_type": "positive"},
    {"label": "Conversion", "value": "12.5%", "delta": "-2%", "delta_type": "negative"},
    {"label": "Avg Deal", "value": "$45K", "delta_type": "neutral"},
]

enterprise_kpi_grid(metrics, columns=4)
```

### Section Headers
```python
from ghl_real_estate_ai.design_system import enterprise_section_header

enterprise_section_header(
    title="Lead Analytics",
    subtitle="Real-time performance metrics",
    icon=""
)
```

### Status Indicators
```python
from ghl_real_estate_ai.design_system import enterprise_status_indicator

enterprise_status_indicator(
    status="active",  # active, warning, danger, inactive
    label="System Online",
    description="All services operational"
)
```

---

## CSS Classes

### Cards
```css
.enterprise-card              /* Base card */
.enterprise-card--gold        /* Gold accent top border */
.enterprise-card--success     /* Green left border */
.enterprise-card--warning     /* Amber left border */
.enterprise-card--danger      /* Red left border */
.enterprise-card--glass       /* Glassmorphism effect */
.enterprise-card--premium     /* Luxury styling with glow */
```

### Buttons
```css
.enterprise-btn               /* Base button */
.enterprise-btn--primary      /* Navy gradient */
.enterprise-btn--secondary    /* Outlined */
.enterprise-btn--gold         /* Gold gradient */
.enterprise-btn--ghost        /* Transparent */
.enterprise-btn--danger       /* Red */
```

### Badges
```css
.enterprise-badge             /* Base badge */
.enterprise-badge--primary    /* Navy */
.enterprise-badge--gold       /* Gold */
.enterprise-badge--success    /* Green */
.enterprise-badge--warning    /* Amber */
.enterprise-badge--danger     /* Red */
.enterprise-badge--live       /* Pulsing green */
```

### Text Utilities
```css
.enterprise-gradient-text     /* Navy to gold gradient text */
.enterprise-display           /* Large display text */
.enterprise-mono              /* Monospace text */
.enterprise-caption           /* Uppercase caption */
```

### Animation Classes
```css
.enterprise-fade-in           /* Fade in */
.enterprise-fade-in-up        /* Fade in with upward motion */
.enterprise-slide-in-left     /* Slide from left */
.enterprise-slide-in-right    /* Slide from right */
.enterprise-pulse             /* Gentle pulse */
.enterprise-luxury-pulse      /* Pulse with gold glow */
```

---

## Plotly Charts

```python
from ghl_real_estate_ai.design_system import apply_plotly_theme
import plotly.express as px

fig = px.bar(df, x='category', y='value')
apply_plotly_theme(fig)
st.plotly_chart(fig)
```

---

## Accessibility

- All text meets WCAG 2.1 AA contrast requirements
- Focus states use gold outline for visibility
- Supports `prefers-reduced-motion` for users sensitive to animations
- Supports `prefers-contrast: high` for high contrast mode

---

## Dark Mode

The design system includes automatic dark mode support via `prefers-color-scheme: dark`.
All color variables are inverted appropriately.

---

## Support

For questions or issues, contact the EnterpriseHub Design Team.

**Version**: 2.0.0
**Last Updated**: January 10, 2026
