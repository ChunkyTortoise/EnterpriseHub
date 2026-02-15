# Insight Engine

**Obsidian-themed Streamlit BI dashboard components with glassmorphism, design tokens, and type-safe primitives.**

## Installation

```bash
pip install insight-engine
```

## Quick Start

```python
import streamlit as st
from insight_engine import inject_elite_css, style_obsidian_chart
from insight_engine.primitives import (
    render_obsidian_card, CardConfig,
    render_obsidian_metric, MetricConfig,
    render_obsidian_badge, BadgeConfig,
    lead_temperature_badge, status_badge,
    icon, ICONS,
)

# Apply the Obsidian Command theme
inject_elite_css()

# Render a premium card
render_obsidian_card(
    title="Hot Leads",
    content="<p>15 leads need attention</p>",
    config=CardConfig(variant='alert', glow_color='#EF4444'),
    icon='fire'
)

# Render a metric with trend
render_obsidian_metric(
    value="$2.4M",
    label="Revenue This Quarter",
    config=MetricConfig(variant='success', trend='up', show_comparison=True),
    comparison_value="+18% vs Q3",
    metric_icon='dollar-sign'
)

# Render badges
lead_temperature_badge("hot")
status_badge("success", "Deployed")

# Style Plotly charts
import plotly.graph_objects as go
fig = go.Figure(data=go.Scatter(x=[1,2,3], y=[4,5,6]))
fig = style_obsidian_chart(fig)
st.plotly_chart(fig)
```

## Components

### Theme System

- **`inject_elite_css()`** - Inject the full Obsidian Command CSS theme
- **`style_obsidian_chart(fig)`** - Apply dark theme to Plotly figures
- **`ObsidianThemeService`** - Design token access via dot-notation
- **`Colors`**, **`Typography`**, **`Spacing`** - Quick access to tokens

### Primitives

| Component | Description |
|-----------|-------------|
| `render_obsidian_card` | Card with default/glass/premium/alert variants |
| `render_obsidian_metric` | Metric display with trend indicators |
| `render_obsidian_badge` | Status badges (16 variants) |
| `icon` | Font Awesome icon wrapper |

### Visual Effects

| Function | Description |
|----------|-------------|
| `render_dossier_block` | Glassmorphism content block |
| `render_neural_progress` | Glowing progress bar |
| `render_terminal_log` | Terminal-style log display |
| `render_journey_line` | Temperature-based journey indicator |
| `render_biometric_heartbeat` | EKG-style pulse animation |
| `render_countdown_gauge` | Circular countdown timer |
| `render_decision_stream` | Decision audit log |

## Design Tokens

Access tokens programmatically:

```python
from insight_engine import ObsidianThemeService, Colors

# Dot-notation access
primary = ObsidianThemeService.get_token('colors.brand.primary')  # '#6366F1'

# Quick access
bg = Colors.BACKGROUND_DEEP  # '#05070A'
hot = Colors.HOT  # '#EF4444'
```

## License

MIT License - See [LICENSE](LICENSE) for details.
