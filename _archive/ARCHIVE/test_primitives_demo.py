import pytest

@pytest.mark.integration
"""
Demo script to test primitive components.
Run with: streamlit run test_primitives_demo.py
"""

import streamlit as st
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from ghl_real_estate_ai.streamlit_demo.components.primitives import (
    render_obsidian_card,
    CardConfig,
    icon,
    ICONS,
    get_lead_temp_icon,
    get_status_icon
)

# Apply Obsidian theme (includes Font Awesome)
inject_elite_css()

st.title("🎨 Primitive Component Library Demo")

st.markdown("---")

# Card Variants Demo
st.header("Card Variants")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Default Card")
    render_obsidian_card(
        title="Property Insights",
        content="<p>3,247 active properties in database</p>",
        icon='house'
    )

    st.subheader("Glass Card")
    render_obsidian_card(
        title="AI Analysis",
        content="<p>Claude is analyzing lead patterns...</p>",
        config=CardConfig(variant='glass'),
        icon='brain'
    )

with col2:
    st.subheader("Premium Card")
    render_obsidian_card(
        title="Elite Feature",
        content="<p>Advanced property matching AI</p>",
        config=CardConfig(variant='premium'),
        icon='sparkles'
    )

    st.subheader("Alert Card")
    render_obsidian_card(
        title="Urgent Action Required",
        content="<p>5 hot leads need immediate followup</p>",
        config=CardConfig(variant='alert', glow_color='#EF4444'),
        icon='exclamation-triangle'
    )

st.markdown("---")

# Icon System Demo
st.header("Icon System")

st.subheader("Lead Temperature Icons")
st.markdown(f"""
- {ICONS['hot_lead']()} Hot Lead
- {ICONS['warm_lead']()} Warm Lead
- {ICONS['cold_lead']()} Cold Lead
""", unsafe_allow_html=True)

st.subheader("Property Icons")
st.markdown(f"""
- {ICONS['property']()} Single Family Home
- {ICONS['building']()} Commercial Property
- {ICONS['location']()} Location
""", unsafe_allow_html=True)

st.subheader("Analytics Icons")
st.markdown(f"""
- {ICONS['analytics']()} Performance Metrics
- {ICONS['chart']()} Revenue Dashboard
- {ICONS['dashboard']()} Executive Dashboard
""", unsafe_allow_html=True)

st.subheader("Communication Icons")
st.markdown(f"""
- {ICONS['conversation']()} AI Chat
- {ICONS['phone']()} Call Scheduled
- {ICONS['email']()} Email Sent
- {ICONS['calendar']()} Appointment
""", unsafe_allow_html=True)

st.subheader("Status Icons")
st.markdown(f"""
- {ICONS['check']()} Completed
- {ICONS['warning']()} Pending Review
- {ICONS['error']()} Failed
- {ICONS['info']()} Information
""", unsafe_allow_html=True)

st.markdown("---")

# Helper Functions Demo
st.header("Helper Functions")

st.subheader("Lead Temperature Helper")
for temp in ['hot', 'warm', 'cold']:
    temp_icon = get_lead_temp_icon(temp)
    st.markdown(f"{temp_icon} {temp.capitalize()} Lead", unsafe_allow_html=True)

st.subheader("Status Helper")
for status in ['success', 'warning', 'error', 'info']:
    status_icon = get_status_icon(status)
    st.markdown(f"{status_icon} {status.capitalize()} Status", unsafe_allow_html=True)

st.markdown("---")

# Real-World Example
st.header("Real-World Examples")

st.subheader("Lead Dashboard Card")
render_obsidian_card(
    title=f"{ICONS['hot_lead']()} Hot Leads Requiring Attention",
    content=f"""
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <p style="font-size: 2rem; font-weight: 700; margin: 0;">15</p>
                <p style="color: #8B949E; margin: 0;">Leads need immediate followup</p>
            </div>
            <div>
                {ICONS['phone']()} {ICONS['email']()} {ICONS['calendar']()}
            </div>
        </div>
    """,
    config=CardConfig(variant='alert', glow_color='#EF4444')
)

st.subheader("Property Match Card")
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

st.subheader("Analytics Summary Card")
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

st.markdown("---")

# Custom Icon Examples
st.header("Custom Icon Examples")

st.markdown(f"""
### Different Sizes
- {icon('star', size='1em', color='#F59E0B')} Small (1em)
- {icon('star', size='1.5em', color='#F59E0B')} Medium (1.5em)
- {icon('star', size='2em', color='#F59E0B')} Large (2em)

### Different Styles
- {icon('heart', style='solid', color='#EF4444')} Solid
- {icon('heart', style='regular', color='#EF4444')} Regular (outline)

### Different Colors
- {icon('circle', color='#EF4444')} Red
- {icon('circle', color='#F59E0B')} Amber
- {icon('circle', color='#10B981')} Green
- {icon('circle', color='#3B82F6')} Blue
- {icon('circle', color='#8B5CF6')} Purple
""", unsafe_allow_html=True)

st.markdown("---")

st.success("✅ All primitive components are working correctly!")
