# SKILL: Gemini-Powered Visual Generation for EnterpriseHub

## Overview

This skill enables the use of Google Gemini AI to generate professional visual assets and enhance the EnterpriseHub UI/UX. Leverages Gemini's multimodal capabilities (text + image generation) to create stunning visuals that maximize hiring potential and demonstrate cutting-edge AI integration.

## When to Use This Skill

Use this skill when you need to:
- Generate hero images and banner graphics for the application
- Create chart enhancements and data visualizations
- Design icon sets and UI illustrations
- Build portfolio screenshots and demo assets
- Generate visual documentation and architecture diagrams

## Prerequisites

- **Google AI Studio API Key**: Get from [ai.google.dev](https://ai.google.dev)
- **Gemini Model Access**: `gemini-1.5-pro` or `gemini-1.5-flash`
- **Image Generation**: Imagen 3 (via Vertex AI or AI Studio)

## Core Visual Generation Prompts

### 1. Hero Section Background

**Objective**: Create eye-catching gradient backgrounds for the Overview page

**Example Prompts**:

```
Abstract gradient wave pattern background transitioning from indigo (#4338CA) to purple (#9333EA) to cyan (#0E7490). Modern, smooth, professional aesthetic. 1920x1080px. Suitable for business intelligence platform header. Subtle, not distracting, glassmorphism effects.

Abstract background featuring subtle data visualization elements - floating charts, graphs, and analytics symbols. Minimalist, semi-transparent overlays. Color scheme: deep indigo (#4338CA) with light accents. 4K resolution. Professional fintech aesthetic.

Modern geometric composition with overlapping circles and hexagons. Gradient fills from indigo to cyan. Glass morphism effects with subtle shadows. Clean, corporate, trustworthy feel. 1920x1080px PNG with transparency.
```

### 2. Module Feature Icons (512x512px)

**Objective**: Create consistent, professional icon set for all 7 modules

**Prompt Template**:
```
Minimalist [DESCRIPTION] icon, geometric shapes, color [HEX_COLOR], flat design, professional SaaS style, 512x512px, transparent background PNG
```

**Specific Examples**:

- **Market Pulse**: "candlestick stock chart with 3-5 bars, geometric shapes, color #0E7490 (cyan)"
- **Financial Analyst**: "balance sheet or calculator icon, clean lines, color #4338CA (indigo)"
- **Margin Hunter**: "target bullseye with dollar sign in center, color #9333EA (purple)"
- **Agent Logic**: "AI brain or neural network nodes, color #10B981 (emerald)"
- **Content Engine**: "writing pen on document, color #F59E0B (amber)"
- **Data Detective**: "magnifying glass examining data grid, color #8B5CF6 (violet)"
- **Marketing Analytics**: "growth chart or funnel diagram, color #EC4899 (pink)"

### 3. Portfolio README Banner

**Objective**: Create professional GitHub repository banner

**Prompt**:
```
GitHub repository banner for 'EnterpriseHub - Business Intelligence Platform'. Dimensions 1200x600px. Left side: Bold title 'EnterpriseHub' in Space Grotesk font, tagline 'Unified Business Intelligence Platform - 7 Modules, 220+ Tests, Production-Ready'. Right side: Technology badges arranged in grid (Python, Streamlit, Plotly, Claude AI, Google Gemini). Background: Diagonal gradient from indigo (#4338CA) to purple (#9333EA). Professional, modern, corporate SaaS aesthetic. Include subtle data visualization patterns in background.
```

### 4. Architecture Diagram

**Objective**: Visual system architecture for documentation

**Prompt**:
```
System architecture diagram for Python/Streamlit web application. Four layers stacked vertically:
1. Streamlit Frontend (icons: browser, mobile)
2. Business Logic Layer (Python modules)
3. Data Access Layer (Pandas, NumPy)
4. External APIs (Yahoo Finance, Claude AI, Google Gemini)

Modern cloud architecture style with rounded rectangles. Color scheme: indigo (#4338CA) primary, slate grays (#64748B) for secondary components. Clear arrows showing data flow between layers. Professional, clean, suitable for technical documentation. SVG format or high-res PNG 1920x1080.
```

### 5. Feature Screenshot Frames

**Objective**: Professional mockup frames for embedding screenshots

**Prompt**:
```
Modern browser window mockup frame for embedding application screenshots. Chrome-style UI with rounded top corners. Dimensions: 1600x1000px. Includes realistic browser chrome (address bar with 'localhost:8501', back/forward buttons, tabs) at top. Soft elevated shadow (0 20px 50px rgba(0,0,0,0.15)). Center area transparent or white for screenshot insertion. Background: subtle gradient or transparent PNG.
```

## Implementation Workflow

### Quick Start: Using Generate Image Tool

1. **Generate Hero Background**:
   - Use the hero background prompts above
   - Save to `/assets/hero/background_{theme}.png`
   - Reference in `utils/ui.py` hero_section()

2. **Create Module Icons**:
   - Generate each icon using module-specific prompts
   - Save to `/assets/icons/{module_name}.svg` or `.png`
   - Update module cards to use custom icons instead of emojis

3. **Build README Banner**:
   - Generate using README banner prompt
   - Save to `/assets/marketing/readme_banner.png`
   - Add to top of `README.md`: `![EnterpriseHub]( ../assets/marketing/readme_banner.png)`

### Advanced: Programmatic Generation

Create a helper script for batch generation:

```python
# scripts/generate_assets.py
"""
Generate visual assets using Gemini image generation.
Run with: python scripts/generate_assets.py --asset-type [hero|icons|banner]
"""

PROMPTS = {
    "hero_light": "Abstract gradient wave pattern...",
    "hero_dark":  "Dark mode version with inverted colors...",
    "icon_market_pulse": "Minimalist candlestick chart icon...",
    # ... add all prompts
}

def generate_asset(asset_name: str, output_path: str):
    """Generate single asset using image generation."""
    prompt = PROMPTS.get(asset_name)
    if not prompt:
        print(f"No prompt found for {asset_name}")
        return

    print(f"📝 Prompt: {prompt}")
    print(f"💾 Output: {output_path}")
    print(f"\n🎨 Use your image generation tool to create this asset\n")
    # In future: integrate with Imagen API directly

if __name__ == "__main__":
    import sys
    asset_type = sys.argv[1] if len(sys.argv) > 1 else "hero_light"
    output = f"assets/{asset_type}.png"
    generate_asset(asset_type, output)
```

## Asset Organization

Recommended directory structure:

```
assets/
├── hero/
│   ├── background_light.png      # Light theme hero
│   ├── background_dark.png       # Dark theme hero
│   ├── background_ocean.png      # Ocean theme hero
│   └── background_sunset.png     # Sunset theme hero
├── icons/
│   ├── market_pulse.svg
│   ├── financial_analyst.svg
│   ├── margin_hunter.svg
│   ├── agent_logic.svg
│   ├── content_engine.svg
│   ├── data_detective.svg
│   └── marketing_analytics.svg
├── screenshots/
│   ├── margin_hunter_demo.png    # Actual app screenshots
│   ├── market_pulse_charts.png
│   ├── frame_browser.png          # Reusable mockup frame
│   └── portfolio_collage.png      # Multi-screenshot composition
└── marketing/
    ├── readme_banner.png           # GitHub banner
    ├── linkedin_post.png           # Social media assets
    └── architecture_diagram.svg    # Technical diagrams
```

## Best Practices

### Prompt Engineering for Visuals

1. **Be Specific**: Include dimensions, colors (hex codes), file format, style keywords
2. **Reference Styles**: Use terms like "glassmorphism", "flat design", "isometric", "neumorphism"
3. **Iterate**: Generate 2-3 variations, pick the best
4. **Consistency**: Reuse color palette from `utils/ui.py` theme definitions

### Color Palette Reference

Always use these theme colors:
- **Light**: Primary `#4338CA`, Background `#F8FAFC`
- **Dark**: Primary `#A5B4FC`, Background `#0F172A`
- **Ocean**: Primary `#0E7490`, Background `#F0F9FF`
- **Sunset**: Primary `#9333EA`, Background `#FFF7ED`

### Optimization

- **Compress Images**: Use TinyPNG or ImageOptim before committing
- **SVG When Possible**: Icons should be SVG for scalability
- **Lazy Loading**: Large images should load asynchronously
- **Responsive**: Provide multiple sizes (@1x, @2x, @3x)

## Integration Examples

### Hero Section with Background

```python
# utils/ui.py - Enhanced hero_section()
def hero_section(title: str, subtitle: str, background_image: Optional[str] = None) -> None:
    """Enhanced hero with optional AI-generated background."""
    bg_style = ""
    if background_image:
        bg_style = f"""
            background-image: url('{background_image}');
            background-size: cover;
            background-position: center;
        """

    html = f"""
    <section class="hero-container" style="{bg_style}">
        <div style="backdrop-filter: blur(5px); background: rgba(255,255,255,0.9); padding: 2rem; border-radius: 16px;">
            <h1 class="hero-title">{title}</h1>
            <p class="hero-subtitle">{subtitle}</p>
        </div>
    </section>
    """
    st.markdown(html, unsafe_allow_html=True)

# app.py - Use in overview
hero_section(
    "Unified Enterprise Hub",
    "A production-grade business intelligence platform...",
    background_image="assets/hero/background_light.png"
)
```

### Custom Icon Feature Cards

```python
# app.py - Replace emoji with custom SVG icons
ui.feature_card(
    icon='<img src="assets/icons/market_pulse.svg" alt="Market Pulse" style="width: 60px; height: 60px;">',
    title="Market Pulse",
    description="...",
    status="active"
)
```

## Verification Checklist

Before using generated assets:
- [ ] Resolution matches intended use (hero: 1920x1080, icons: 512x512)
- [ ] Colors align with theme palette
- [ ] File format is optimized (SVG for icons, PNG with compression for images)
- [ ] Transparency/background is correct
- [ ] Accessibility: alt text provided, sufficient contrast
- [ ] File size < 500KB (use compression tools)

## Next Steps for Implementation

1. ✅ **Phase 1 Complete**: Enhanced themes (Ocean, Sunset) and UI components
2. 🔄 **Phase 2 In Progress**: Generate visual assets using prompts above
3. ⏭️ **Phase 3 Next**: Integrate assets into UI, update README with banner
4. ⏭️ **Phase 4 Future**: Automated asset pipeline with Gemini API integration

---

**Created**: 2025-12-25
**Purpose**: Enable AI-powered visual generation to maximize portfolio impact
**Skill Type**: Visual Design & AI Integration
