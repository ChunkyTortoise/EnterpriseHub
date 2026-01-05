# DEMO_PLAN.md - Streamlit Demo Implementation Guide

**Strategy:** Option 1 - Interactive Demo with Mock Services
**Estimated Time:** 2 hours
**Goal:** Deliver client-ready mockup showcasing AI capabilities
**Status:** Ready to implement

---

## 🎯 Overview

Build a Streamlit web app that demonstrates the GHL Real Estate AI without requiring:
- Real API keys (mock Claude responses)
- Backend deployment (runs locally or on Streamlit Cloud)
- Complex setup (just Python + Streamlit)

**What Client Experiences:**
1. Interactive chat interface (SMS-style)
2. Real-time lead scoring visualization
3. Property matching with RAG simulation
4. Tag application demonstration
5. Three pre-loaded scenarios to test

---

## 📁 Project Structure

```
streamlit_demo/
├── app.py                          # Main Streamlit application
├── components/
│   ├── chat_interface.py          # SMS-style chat UI
│   ├── lead_dashboard.py          # Score gauge + tags + insights
│   ├── property_cards.py          # Property matching display
│   └── scenario_selector.py      # Demo scenario dropdown
├── mock_services/
│   ├── mock_claude.py             # Pre-crafted AI responses
│   ├── mock_rag.py                # Property matching logic
│   └── conversation_state.py     # Session state management
├── demo_scenarios/
│   ├── cold_lead.json             # Scenario 1: Cold → Warm
│   ├── warm_lead.json             # Scenario 2: Objection handling
│   └── hot_lead.json              # Scenario 3: Hot lead detection
└── assets/
    └── styles.css                 # Custom CSS for polish
```

---

## ⚡ Implementation Steps

### Phase 1: Setup & Dependencies (10 minutes)

**Step 1.1: Install Streamlit Packages**
```bash
cd /Users/cave/enterprisehub/ghl-real-estate-ai
source venv/bin/activate
pip install streamlit streamlit-chat plotly
```

**Step 1.2: Create Directory Structure**
```bash
mkdir -p streamlit_demo/{components,mock_services,demo_scenarios,assets}
touch streamlit_demo/app.py
touch streamlit_demo/components/{chat_interface,lead_dashboard,property_cards,scenario_selector}.py
touch streamlit_demo/mock_services/{mock_claude,mock_rag,conversation_state}.py
touch streamlit_demo/demo_scenarios/{cold_lead,warm_lead,hot_lead}.json
```

---

### Phase 2: Mock Services (30 minutes)

#### File: `streamlit_demo/mock_services/mock_claude.py`

**Purpose:** Generate realistic AI responses without calling Anthropic API

**Implementation:**
```python
"""
Mock Claude Service - Pre-crafted responses for demo.
"""
import re
from typing import Dict, List, Tuple


class MockClaudeService:
    """Simulates Claude AI responses with pattern matching."""

    def __init__(self):
        self.response_patterns = {
            # Greetings
            r"(hi|hello|hey)": [
                "Hey there! Thanks for reaching out. I'd love to help you find the perfect place in Austin. What's most important to you in your next home?",
                "Hi! Austin's market is moving fast right now. Are you looking to buy soon, or just exploring options?"
            ],

            # Budget mentions
            r"budget.*\$?(\d{3,})k?": [
                "That's helpful to know! With a ${budget} budget, you've got some great options in Austin. Are you pre-approved for a mortgage, or should I connect you with our preferred lender first?"
            ],

            # Objection: Price too high
            r"(price|expensive|too high|cost too much)": [
                "I totally get it—sticker shock is real in Austin right now. Here's some context: median home prices jumped 12% last year, and we're seeing bidding wars on anything under $400k. That said, there ARE hidden gems if you're flexible on location or timing. What's your absolute max budget?"
            ],

            # Pre-approval mention
            r"(pre-approved|preapproved|pre approved)": [
                "That's awesome! Being pre-approved puts you ahead of the game. With your budget and timeline, I've got some properties that would be perfect. What neighborhoods are you most interested in?"
            ],

            # Timeline urgency
            r"(asap|immediately|urgent|this month|next month|soon)": [
                "Got it—you're ready to move fast! That's smart in this market. Let me pull up properties that are move-in ready. Any specific must-haves? Pool, good schools, walkable neighborhood?"
            ],

            # Bedroom requirements
            r"(\d)\s*(bed|bedroom)": [
                "Perfect! {bedrooms}-bedroom homes are popular in Austin. Are you looking in a specific area? Hyde Park, Mueller, and Downtown have great options."
            ],

            # Location mentions
            r"(hyde park|downtown|mueller|south congress|east austin)": [
                "Great choice! {location} is one of my favorite areas—{location_details}. What's your budget looking like?"
            ],

            # Just browsing
            r"(just browsing|looking around|not sure|thinking about)": [
                "No problem at all! Browsing is a great place to start. Is there anything specific I can help you explore? Happy to answer any questions about Austin's market."
            ],

            # Default fallback
            "default": [
                "Thanks for sharing that! To find the best match for you, can you tell me a bit more about what you're looking for? Budget range, preferred neighborhoods, and must-have features help me narrow it down."
            ]
        }

        self.location_details = {
            "hyde park": "great schools, walkable to UT, lots of charm",
            "downtown": "urban living, nightlife, easy commute",
            "mueller": "newer development, family-friendly, parks everywhere",
            "south congress": "trendy, amazing food scene, artistic vibe",
            "east austin": "up-and-coming, diverse, creative community"
        }

    def generate_response(
        self,
        user_message: str,
        conversation_history: List[Dict],
        extracted_data: Dict
    ) -> Tuple[str, Dict]:
        """
        Generate AI response based on user message and context.

        Returns:
            (response_text, updated_extracted_data)
        """
        message_lower = user_message.lower()

        # Extract budget
        if "budget" in message_lower or "$" in user_message:
            budget_match = re.search(r'\$?(\d{3,}),?(\d{3})?k?', user_message)
            if budget_match:
                budget_str = budget_match.group(0).replace("$", "").replace("k", "000").replace(",", "")
                try:
                    extracted_data["budget"] = int(budget_str) if len(budget_str) <= 6 else int(budget_str[:6])
                except:
                    pass

        # Extract timeline
        if any(word in message_lower for word in ["asap", "immediately", "urgent", "soon", "this month", "next month"]):
            extracted_data["timeline"] = "ASAP"
        elif any(word in message_lower for word in ["year", "months", "eventually"]):
            extracted_data["timeline"] = "Flexible"

        # Extract financing
        if any(word in message_lower for word in ["pre-approved", "preapproved", "cash"]):
            extracted_data["financing"] = "pre-approved"

        # Extract location
        for location in ["hyde park", "downtown", "mueller", "south congress", "east austin"]:
            if location in message_lower:
                extracted_data["location"] = location.title()

        # Extract bedrooms
        bed_match = re.search(r'(\d)\s*(bed|bedroom)', message_lower)
        if bed_match:
            extracted_data["bedrooms"] = int(bed_match.group(1))

        # Find matching response pattern
        response = None
        for pattern, responses in self.response_patterns.items():
            if pattern == "default":
                continue
            if re.search(pattern, message_lower):
                response = responses[0]
                break

        if not response:
            response = self.response_patterns["default"][0]

        # Replace placeholders
        response = response.replace("{budget}", f"${extracted_data.get('budget', 0):,}")
        response = response.replace("{bedrooms}", str(extracted_data.get('bedrooms', 3)))

        if "{location}" in response:
            location = extracted_data.get('location', 'Austin').lower()
            response = response.replace("{location}", location.title())
            details = self.location_details.get(location, "a great area")
            response = response.replace("{location_details}", details)

        return response, extracted_data
```

#### File: `streamlit_demo/mock_services/mock_rag.py`

**Purpose:** Simulate property matching based on user preferences

**Implementation:**
```python
"""
Mock RAG Service - Property matching simulation.
"""
import json
from typing import List, Dict


class MockRAGService:
    """Simulates property retrieval and matching."""

    def __init__(self, knowledge_base_path: str = "data/knowledge_base/property_listings.json"):
        # Load actual property data
        with open(knowledge_base_path, 'r') as f:
            data = json.load(f)
            self.properties = data.get('listings', [])

    def search_properties(
        self,
        preferences: Dict,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Find properties matching user preferences.

        Simulates semantic search with scoring.
        """
        results = []

        for prop in self.properties:
            score = self._calculate_match_score(prop, preferences)
            if score > 0:
                results.append({
                    **prop,
                    'match_score': score
                })

        # Sort by score, return top K
        results.sort(key=lambda x: x['match_score'], reverse=True)
        return results[:top_k]

    def _calculate_match_score(self, property: Dict, preferences: Dict) -> float:
        """Calculate how well property matches preferences (0-100)."""
        score = 70  # Base score

        # Budget match
        budget = preferences.get('budget')
        if budget:
            price = property.get('price', 0)
            if price <= budget:
                score += 15
            elif price <= budget * 1.1:  # Within 10%
                score += 8
            else:
                score -= 10

        # Bedroom match
        bedrooms = preferences.get('bedrooms')
        if bedrooms and property.get('bedrooms') == bedrooms:
            score += 10

        # Location match
        location = preferences.get('location', '').lower()
        prop_neighborhood = property.get('address', {}).get('neighborhood', '').lower()
        if location and location in prop_neighborhood:
            score += 15

        return max(0, min(100, score))
```

#### File: `streamlit_demo/mock_services/conversation_state.py`

**Purpose:** Manage conversation state in Streamlit session

**Implementation:**
```python
"""
Conversation State Management for Streamlit.
"""
from typing import List, Dict
import streamlit as st


def init_conversation_state():
    """Initialize session state for conversation."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'extracted_data' not in st.session_state:
        st.session_state.extracted_data = {}

    if 'lead_score' not in st.session_state:
        st.session_state.lead_score = 0

    if 'tags' not in st.session_state:
        st.session_state.tags = []


def add_message(role: str, content: str):
    """Add message to conversation history."""
    st.session_state.messages.append({
        'role': role,
        'content': content
    })


def update_extracted_data(data: Dict):
    """Update extracted preferences."""
    st.session_state.extracted_data.update(data)


def calculate_lead_score() -> int:
    """Calculate lead score from extracted data."""
    # Use the actual lead scorer
    from services.lead_scorer import LeadScorer

    scorer = LeadScorer()
    context = {
        'extracted_preferences': st.session_state.extracted_data,
        'conversation_history': st.session_state.messages
    }

    score = scorer.calculate(context)
    st.session_state.lead_score = score

    # Update tags based on score
    update_tags(score, st.session_state.extracted_data)

    return score


def update_tags(score: int, preferences: Dict):
    """Update tags based on score and preferences."""
    tags = []

    # Lead temperature tag
    if score >= 70:
        tags.append("Hot-Lead")
    elif score >= 40:
        tags.append("Warm-Lead")
    else:
        tags.append("Cold-Lead")

    # Budget tags
    budget = preferences.get('budget')
    if budget:
        if budget < 300000:
            tags.append("Budget-Under-300k")
        elif budget <= 500000:
            tags.append("Budget-300k-500k")
        else:
            tags.append("Budget-500k-Plus")

    # Financing tags
    if preferences.get('financing'):
        tags.append("Pre-Approved")

    # Timeline tags
    if preferences.get('timeline') == "ASAP":
        tags.append("Timeline-Urgent")

    # Location tags
    location = preferences.get('location')
    if location:
        tags.append(f"Location-{location.replace(' ', '-')}")

    st.session_state.tags = tags
```

---

### Phase 3: UI Components (40 minutes)

#### File: `streamlit_demo/components/chat_interface.py`

```python
"""
Chat interface component - SMS-style conversation display.
"""
import streamlit as st
from streamlit_chat import message


def render_chat_interface():
    """Render the chat conversation interface."""
    st.markdown("### 💬 Conversation")

    # Display message history
    messages = st.session_state.get('messages', [])

    for i, msg in enumerate(messages):
        if msg['role'] == 'user':
            message(msg['content'], is_user=True, key=f"user_{i}")
        else:
            message(msg['content'], is_user=False, key=f"ai_{i}")

    # Spacer
    st.markdown("<div style='height: 20px'></div>", unsafe_allow_html=True)
```

#### File: `streamlit_demo/components/lead_dashboard.py`

```python
"""
Lead intelligence dashboard - score, tags, insights.
"""
import streamlit as st
import plotly.graph_objects as go


def render_lead_dashboard():
    """Render lead scoring and intelligence panel."""
    st.markdown("### 📊 Lead Intelligence")

    # Lead score gauge
    score = st.session_state.get('lead_score', 0)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Lead Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': get_score_color(score)},
            'steps': [
                {'range': [0, 40], 'color': "lightgray"},
                {'range': [40, 70], 'color': "lightyellow"},
                {'range': [70, 100], 'color': "lightgreen"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))

    fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
    st.plotly_chart(fig, use_container_width=True)

    # Tags
    st.markdown("#### 🏷️ Tags Applied")
    tags = st.session_state.get('tags', [])
    if tags:
        cols = st.columns(2)
        for i, tag in enumerate(tags):
            with cols[i % 2]:
                st.markdown(f"`{tag}`")
    else:
        st.info("No tags yet - chat to build profile")

    # Extracted data insights
    st.markdown("#### 📋 Extracted Preferences")
    prefs = st.session_state.get('extracted_data', {})
    if prefs:
        for key, value in prefs.items():
            if key == 'budget':
                st.write(f"**Budget:** ${value:,}")
            else:
                st.write(f"**{key.title()}:** {value}")
    else:
        st.info("No preferences extracted yet")


def get_score_color(score: int) -> str:
    """Get color based on score."""
    if score >= 70:
        return "green"
    elif score >= 40:
        return "orange"
    else:
        return "red"
```

#### File: `streamlit_demo/components/property_cards.py`

```python
"""
Property matching cards component.
"""
import streamlit as st


def render_property_matches():
    """Render matched properties."""
    st.markdown("### 🏠 Property Matches")

    # Check if we have preferences to match against
    prefs = st.session_state.get('extracted_data', {})
    if not prefs:
        st.info("Share your preferences in the chat to see property matches!")
        return

    # Get property matches from mock RAG
    from streamlit_demo.mock_services.mock_rag import MockRAGService

    rag = MockRAGService()
    matches = rag.search_properties(prefs, top_k=3)

    if not matches:
        st.warning("No matches found - try adjusting your criteria!")
        return

    # Display properties
    cols = st.columns(3)

    for i, prop in enumerate(matches):
        with cols[i]:
            render_property_card(prop)


def render_property_card(property: dict):
    """Render single property card."""
    addr = property.get('address', {})

    st.markdown(f"""
    <div style='padding: 15px; border: 1px solid #ddd; border-radius: 8px; margin-bottom: 10px;'>
        <h4>{addr.get('neighborhood', 'Unknown')}</h4>
        <p><strong>${property.get('price', 0):,}</strong></p>
        <p>{property.get('bedrooms', 0)} BR | {property.get('bathrooms', 0)} BA</p>
        <p>{property.get('sqft', 0):,} sqft</p>
        <p style='color: green;'><strong>Match: {property.get('match_score', 0):.0f}%</strong></p>
    </div>
    """, unsafe_allow_html=True)
```

---

### Phase 4: Main App (30 minutes)

#### File: `streamlit_demo/app.py`

```python
"""
GHL Real Estate AI - Interactive Demo
Main Streamlit Application
"""
import streamlit as st
from components.chat_interface import render_chat_interface
from components.lead_dashboard import render_lead_dashboard
from components.property_cards import render_property_matches
from mock_services.mock_claude import MockClaudeService
from mock_services.conversation_state import (
    init_conversation_state,
    add_message,
    update_extracted_data,
    calculate_lead_score
)

# Page config
st.set_page_config(
    page_title="GHL Real Estate AI Demo",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize services
if 'claude_service' not in st.session_state:
    st.session_state.claude_service = MockClaudeService()

# Initialize conversation state
init_conversation_state()

# Title
st.title("🏠 GHL Real Estate AI - Interactive Demo")
st.markdown("**Experience AI-powered lead qualification in real-time**")
st.markdown("---")

# Sidebar - Scenario selector
with st.sidebar:
    st.markdown("### 🎯 Demo Controls")

    scenario = st.selectbox(
        "Load Scenario:",
        ["Fresh Conversation", "Cold Lead Example", "Warm Lead Example", "Hot Lead Example"]
    )

    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.session_state.extracted_data = {}
        st.session_state.lead_score = 0
        st.session_state.tags = []
        st.rerun()

    st.markdown("---")
    st.markdown("### 💡 Try These:")
    st.markdown("""
    **Cold Lead:**
    - "Looking for a house in Austin"

    **Objection:**
    - "Your prices are too high"

    **Hot Lead:**
    - "I'm pre-approved for $400k, need to move ASAP, love Hyde Park"
    """)

# Main layout - 2 columns
col1, col2 = st.columns([2, 1])

with col1:
    # Chat interface
    render_chat_interface()

    # User input
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Add user message
        add_message('user', user_input)

        # Generate AI response
        response, updated_data = st.session_state.claude_service.generate_response(
            user_input,
            st.session_state.messages,
            st.session_state.extracted_data
        )

        # Update state
        add_message('assistant', response)
        update_extracted_data(updated_data)
        calculate_lead_score()

        # Rerun to update UI
        st.rerun()

with col2:
    # Lead intelligence dashboard
    render_lead_dashboard()

# Bottom section - Property matches
st.markdown("---")
render_property_matches()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>🤖 Built with Claude Sonnet 4.5 | 📊 Lead Scoring Algorithm | 🏠 RAG-Powered Property Matching</p>
    <p>This is a demo environment - production deployment ready after approval</p>
</div>
""", unsafe_allow_html=True)
```

---

### Phase 5: Polish & Deploy (10 minutes)

**Step 5.1: Test Locally**
```bash
cd /Users/cave/enterprisehub/ghl-real-estate-ai
source venv/bin/activate
streamlit run streamlit_demo/app.py
```

**Step 5.2: Deploy to Streamlit Cloud**
1. Create GitHub repo (if not exists)
2. Push code to GitHub
3. Go to https://share.streamlit.io
4. Connect GitHub repo
5. Select `streamlit_demo/app.py` as main file
6. Deploy!

---

## ✅ Testing Checklist

Before sending to client:

- [ ] All 3 scenarios work correctly
- [ ] Lead score updates in real-time
- [ ] Tags appear correctly
- [ ] Property matches show when preferences exist
- [ ] UI looks professional on desktop
- [ ] UI works on mobile (test in browser dev tools)
- [ ] No errors in console
- [ ] Response time feels instant (<500ms)

---

## 🚀 Next Steps After Demo Build

1. **Record Demo Video** (Session 4)
2. **Create Documentation Package** (Session 4)
3. **Package & Send to Client** (Session 5)

---

**Ready to build? Start with Phase 1!**
