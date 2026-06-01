# Figma-to-Component Usage Guide

## Quick Start

### 1. Verify Figma MCP Setup

Check that Figma MCP is enabled in your streamlit-dev profile:

```bash
# View active MCP profile
cat .claude/mcp-profiles/streamlit-dev.json | grep -A 10 figma
```

Expected output:
```json
"figma": {
  "enabled": true,
  "config": {
    "transport": "http",
    "url": "https://mcp.figma.com/mcp"
  }
}
```

### 2. Activate Streamlit-Dev Profile

```bash
# Set environment variable
export CLAUDE_PROFILE=streamlit-dev

# Or add to your shell config
echo 'export CLAUDE_PROFILE=streamlit-dev' >> ~/.zshrc
```

### 3. Generate Component from Figma

**Simple Command**:
```
Generate a lead score card component from this Figma design:
https://www.figma.com/file/ABC123/EnterpriseHub?node-id=1:234
```

**Detailed Command**:
```
Import the property listing card from Figma (https://www.figma.com/file/XYZ789/PropertyCards?node-id=5:678)
as a Streamlit component with:
- Type-safe props using dataclass
- Caching with 5-minute TTL
- Responsive design (mobile, tablet, desktop)
- Visual regression tests
- Accessibility validation
```

## Common Use Cases

### Use Case 1: Generate Single Component

**Scenario**: Designer creates new lead score card in Figma

**Steps**:
1. Get Figma URL from designer
2. Request component generation
3. Review generated code
4. Run visual tests
5. Integrate into application

**Example**:
```
User: "Generate lead score card component from:
      https://www.figma.com/file/ABC123/EnterpriseHub?node-id=1:234"

Claude:
1. ✅ Extracted design from Figma MCP
2. ✅ Mapped colors to design tokens
3. ✅ Generated LeadScoreCard component
4. ✅ Created visual regression tests
5. ✅ Validated accessibility (WCAG AA)

Files created:
- ghl_real_estate_ai/streamlit_demo/components/primitives/lead_score_card.py
- tests/visual/test_lead_score_card_snapshot.py
- Component documentation

Usage:
```python
from components.primitives.lead_score_card import LeadScoreCardProps, render_lead_score_card

props = LeadScoreCardProps(
    lead_name="John Doe",
    score=87.5,
    status="hot",
    last_interaction="2 hours ago",
    confidence=0.92
)
render_lead_score_card(props)
```
```

### Use Case 2: Extract Design System Tokens

**Scenario**: Update design system to match Figma styles

**Steps**:
1. Identify Figma file with design system
2. Request token extraction
3. Review mapping to existing tokens
4. Update DesignTokens dataclass
5. Validate across components

**Example**:
```
User: "Extract design tokens from our Figma design system:
      https://www.figma.com/file/DEF456/DesignSystem"

Claude:
1. ✅ Analyzed Figma styles and variables
2. ✅ Extracted color palette (12 colors)
3. ✅ Extracted typography scale (6 sizes, 3 weights)
4. ✅ Extracted spacing system (8px grid)
5. ✅ Created token mapping

Proposed updates to ui_elements.py:

@dataclass
class DesignTokens:
    # Updated from Figma
    primary: str = "#0f172a"        # Slate-900
    secondary: str = "#1e293b"      # Slate-800
    accent: str = "#3b82f6"         # Blue-500
    # ... (full token list)
```

### Use Case 3: Generate Complete Page Layout

**Scenario**: Implement multi-section dashboard from Figma

**Steps**:
1. Identify all sections in Figma page
2. Request component generation for each section
3. Generate layout container
4. Wire up data flow
5. Test responsiveness

**Example**:
```
User: "Generate the executive dashboard page from Figma:
      https://www.figma.com/file/GHI789/Dashboard?node-id=10:100

      Include all sections:
      - Header with metrics
      - Lead activity chart
      - Property recommendations grid
      - Recent conversations list"

Claude:
1. ✅ Analyzed page structure (4 main sections)
2. ✅ Generated 4 components:
   - DashboardHeader
   - LeadActivityChart
   - PropertyRecommendationsGrid
   - RecentConversationsList
3. ✅ Generated page layout component
4. ✅ Created integration tests
5. ✅ Validated responsive behavior

Main page component:
ghl_real_estate_ai/streamlit_demo/pages/executive_dashboard.py

Run: streamlit run ghl_real_estate_ai/streamlit_demo/pages/executive_dashboard.py
```

### Use Case 4: Update Existing Component

**Scenario**: Designer updates component in Figma, need to sync code

**Steps**:
1. Identify changed component
2. Request regeneration
3. Compare with existing code
4. Review visual diff
5. Update and commit

**Example**:
```
User: "The lead score card design was updated in Figma.
      Re-generate from: https://www.figma.com/file/ABC123/EnterpriseHub?node-id=1:234
      Compare with existing implementation."

Claude:
1. ✅ Extracted updated design
2. ✅ Compared with existing code
3. ✅ Identified changes:
   - Badge styling updated (rounded corners: 4px → 8px)
   - Score circle size increased (120px → 140px)
   - Footer alignment changed (space-between → center)
4. ✅ Generated updated component
5. ✅ Updated visual tests
6. ✅ Visual diff report available

Changes preview:
- Old: tokens.radius_small (4px)
- New: tokens.radius_medium (8px)

Ready to commit? (Review visual diff first)
```

## Advanced Workflows

### Workflow 1: Component Variants from Figma

**Figma Setup**:
- Create component with variants (Default, Compact, Expanded)
- Use Figma variant properties

**Generation**:
```
User: "Generate component with all variants from:
      https://www.figma.com/file/JKL012/Components?node-id=15:200"

Claude:
Detected 3 variants in Figma:
- Default (360x240px)
- Compact (360x120px)
- Expanded (360x360px)

Generated ComponentVariant enum:
```python
class LeadScoreCardVariant(Enum):
    DEFAULT = "default"
    COMPACT = "compact"
    EXPANDED = "expanded"
```

All variants supported in single component.
```

### Workflow 2: Design System Migration

**Scenario**: Migrate entire design system from old tokens to Figma

**Steps**:
```
User: "Analyze our Figma design system and create migration plan:
      https://www.figma.com/file/MNO345/DesignSystemV2"

Claude:
Design System Analysis:

Figma Styles:
- 16 color variables
- 6 typography styles
- 5 spacing tokens
- 4 shadow effects
- 3 border radius values

Current EnterpriseHub:
- 15 color tokens (1 missing: accent-secondary)
- 11 typography tokens (5 unused)
- 5 spacing tokens (matches)
- 3 shadow tokens (2 missing)
- 3 border radius tokens (matches)

Migration Plan:
1. Add accent-secondary: #8b5cf6 (Violet-500)
2. Update shadow tokens:
   - shadow_xl: "0 20px 25px -5px rgba(0, 0, 0, 0.1)"
   - shadow_inner: "inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)"
3. Clean up unused typography tokens
4. Update 18 existing components

Affected components:
- lead_score_card.py
- property_card.py
- ... (16 more)

Ready to proceed?
```

### Workflow 3: Batch Component Generation

**Scenario**: Generate multiple related components

**Example**:
```
User: "Generate all property-related components from Figma:
      - Property Card: node-id=20:100
      - Property Details: node-id=20:200
      - Property Gallery: node-id=20:300
      - Property Map: node-id=20:400

      Base file: https://www.figma.com/file/PQR678/PropertyComponents"

Claude:
Batch Generation Progress:

1/4: PropertyCard ✅
   - File: components/primitives/property_card.py
   - Tests: tests/visual/test_property_card_snapshot.py

2/4: PropertyDetails ✅
   - File: components/primitives/property_details.py
   - Tests: tests/visual/test_property_details_snapshot.py

3/4: PropertyGallery ✅
   - File: components/primitives/property_gallery.py
   - Tests: tests/visual/test_property_gallery_snapshot.py

4/4: PropertyMap ✅
   - File: components/primitives/property_map.py
   - Tests: tests/visual/test_property_map_snapshot.py

All components generated successfully!
Total time: 12 minutes (vs 6-8 hours manual implementation)
```

## Troubleshooting

### Issue 1: Figma URL Not Accessible

**Symptom**: `Error: Unable to access Figma file`

**Solutions**:
1. Verify Figma file permissions (must have read access)
2. Check Figma URL format: `https://www.figma.com/file/FILE_ID/FILENAME?node-id=NODE_ID`
3. Ensure Figma MCP server is running
4. Try sharing Figma file publicly (if permissions allow)

### Issue 2: Design Tokens Don't Match

**Symptom**: Generated component uses wrong colors/spacing

**Solutions**:
1. Re-run `create-design-system-rules` to sync tokens
2. Manually map Figma variables to design tokens
3. Update DesignTokens dataclass with new values
4. Regenerate component with updated tokens

### Issue 3: Visual Tests Failing

**Symptom**: Snapshot comparison shows differences

**Solutions**:
1. Review visual diff to identify changes
2. If changes are intentional, update baseline:
   ```bash
   pytest tests/visual/test_component.py --update-snapshots
   ```
3. If changes are not intentional:
   - Check Streamlit version compatibility
   - Verify design system token values
   - Review CSS injection order

### Issue 4: Component Not Rendering

**Symptom**: Component doesn't display in Streamlit

**Solutions**:
1. Check browser console for errors
2. Verify `unsafe_allow_html=True` in `st.markdown()`
3. Validate HTML structure (balanced tags)
4. Test CSS injection (view page source)
5. Clear Streamlit cache:
   ```python
   st.cache_data.clear()
   st.cache_resource.clear()
   ```

### Issue 5: Responsive Layout Broken

**Symptom**: Component doesn't adapt to viewport sizes

**Solutions**:
1. Add CSS media queries:
   ```css
   @media (max-width: 768px) {
       .component { /* mobile styles */ }
   }
   ```
2. Test at different viewport sizes:
   ```bash
   pytest tests/visual/test_component_responsive.py
   ```
3. Use Figma's responsive constraints correctly
4. Review Streamlit's column layout behavior

## Best Practices

### 1. Figma File Organization

**Recommended Structure**:
```
Figma File: EnterpriseHub Components
├── 📁 Design System
│   ├── Colors
│   ├── Typography
│   ├── Spacing
│   └── Effects
├── 📁 Primitives
│   ├── Buttons
│   ├── Inputs
│   ├── Cards
│   └── Badges
├── 📁 Composite Components
│   ├── Lead Score Card
│   ├── Property Card
│   └── Dashboard Header
└── 📁 Pages
    ├── Executive Dashboard
    ├── Lead Intelligence Hub
    └── Property Matcher
```

### 2. Naming Conventions

**Figma Layer Names → Code Names**:
- PascalCase in Figma → PascalCase in code
- Use descriptive names (not "Frame 1")
- Include variant names ("LeadScoreCard/Default")
- Avoid special characters

**Examples**:
- ✅ `LeadScoreCard` → `LeadScoreCard`
- ✅ `PropertyCard/Compact` → `PropertyCardVariant.COMPACT`
- ❌ `Frame 234` → (unclear, rename in Figma)
- ❌ `card-v2-final` → (inconsistent, use PascalCase)

### 3. Component Prop Design

**Follow EnterpriseHub Patterns**:
```python
# ✅ Good: Type-safe dataclass
@dataclass
class ComponentProps:
    required_field: str
    optional_field: Optional[int] = None
    variant: ComponentVariant = ComponentVariant.DEFAULT

# ❌ Bad: Untyped dictionary
def render_component(props: dict):
    pass
```

### 4. Caching Strategy

**Cache Levels**:
```python
# Level 1: Design system (singleton, never expires)
@st.cache_resource
def get_design_system():
    return DesignSystem()

# Level 2: Component rendering (5-10 min TTL)
@st.cache_data(ttl=300)
def render_component(props):
    pass

# Level 3: Data fetching (1-5 min TTL)
@st.cache_data(ttl=60)
def fetch_component_data(lead_id):
    pass
```

### 5. Testing Pyramid

**Test Coverage**:
- Unit tests (props validation, logic): 60%
- Visual regression tests (snapshots): 30%
- Accessibility tests (axe-core): 10%

**Example**:
```python
# Unit test
def test_lead_score_card_props_validation():
    with pytest.raises(ValueError):
        LeadScoreCardProps(score=150)  # Invalid: score > 100

# Visual test
def test_lead_score_card_snapshot(page):
    expect(page.locator(".card")).to_have_screenshot()

# Accessibility test
def test_lead_score_card_accessibility(page):
    results = page.accessibility.snapshot()
    assert len(results['violations']) == 0
```

## Performance Optimization

### 1. Minimize HTML Generation

**Before** (inefficient):
```python
for item in items:
    st.markdown(f"<div>{item}</div>", unsafe_allow_html=True)  # N renders
```

**After** (efficient):
```python
html = "".join([f"<div>{item}</div>" for item in items])
st.markdown(html, unsafe_allow_html=True)  # 1 render
```

### 2. CSS Injection Optimization

**Before** (repeated injection):
```python
def render_component(props):
    st.markdown("<style>...</style>", unsafe_allow_html=True)  # Every call
    # component HTML
```

**After** (singleton injection):
```python
@st.cache_resource
def inject_component_styles():
    st.markdown("<style>...</style>", unsafe_allow_html=True)

def render_component(props):
    inject_component_styles()  # Only once per session
    # component HTML
```

### 3. Image Optimization

**Best Practices**:
- Use CDN for images
- Lazy load off-screen images
- Responsive images with `srcset`
- WebP format for better compression

```html
<img
    src="image-800w.webp"
    srcset="image-400w.webp 400w, image-800w.webp 800w, image-1200w.webp 1200w"
    sizes="(max-width: 768px) 100vw, 50vw"
    loading="lazy"
    alt="Property image"
/>
```

## Integration Checklist

After generating component from Figma:

- [ ] Code generated successfully
- [ ] Component renders without errors
- [ ] Design tokens match Figma styles
- [ ] Visual tests pass
- [ ] Responsive at all viewport sizes
- [ ] Accessibility score 100% (axe-core)
- [ ] Documentation added to README
- [ ] Component added to gallery/showcase
- [ ] Type hints validated (mypy)
- [ ] Cached appropriately (TTL set)
- [ ] Error handling implemented
- [ ] Integration tests written
- [ ] Code review completed
- [ ] Merged to main branch

## FAQ

**Q: How accurate is the Figma-to-code conversion?**
A: 95-98% pixel-perfect. Minor adjustments may be needed for complex interactions.

**Q: Can I update generated code manually?**
A: Yes, but add comments to mark manual changes. Re-generation will prompt you.

**Q: How do I handle Figma components with animations?**
A: Use CSS transitions/animations. Complex animations may need custom implementation.

**Q: What if Figma design uses custom fonts not in our system?**
A: Map to closest design system font or add custom font to project.

**Q: Can I generate components from Figma prototypes?**
A: Yes, but interactive flows need manual implementation (use Figma as visual reference).

**Q: How do I sync design changes from Figma?**
A: Re-run generation with same URL. Tool will show diff and prompt for update.

---

**Need Help?**
- Read full skill documentation: `.claude/skills/design/figma-to-component/SKILL.md`
- View examples: `.claude/skills/design/figma-to-component/examples/`
- Check templates: `.claude/skills/design/figma-to-component/reference/`
