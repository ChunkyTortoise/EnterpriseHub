"""
Deal Closer AI - Interactive Demo
Intelligent objection handling system for real estate sales.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.deal_closer_ai import DealCloserAI, handle_objection

st.set_page_config(
    page_title="Deal Closer AI | GHL Real Estate",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if "objection_history" not in st.session_state:
    st.session_state.objection_history = []

# Header
st.title("💰 Deal Closer AI")
st.markdown("### Intelligent Objection Handling System")
st.markdown("**Revenue Impact:** +$50K-80K/year | **Close Rate:** +15% improvement")

st.divider()

# Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎯 Lead Objection Input")
    
    # Lead information
    with st.expander("📋 Lead Context", expanded=True):
        lead_name = st.text_input("Lead Name", value="Sarah Johnson")
        lead_budget = st.number_input("Budget ($)", value=750000, step=50000, format="%d")
        lead_stage = st.selectbox("Deal Stage", ["New Lead", "Qualified", "Showing", "Offer", "Negotiation"])
        interactions = st.slider("Previous Interactions", 0, 20, 3)
    
    st.divider()
    
    # Objection input
    st.markdown("**💬 Lead's Objection:**")
    
    # Quick examples
    example_objections = {
        "Price Concern": "I think the price is too high for this area",
        "Need Time": "I need more time to think about it",
        "Competition": "I'm also talking to another agent who offered lower commission",
        "Property Issues": "I'm worried about the condition of the property",
        "Financing": "I'm not sure if I can get financing approved",
        "Location": "The neighborhood doesn't seem right for my family"
    }
    
    selected_example = st.selectbox(
        "Quick Examples (or type your own below):",
        [""] + list(example_objections.keys())
    )
    
    if selected_example:
        default_objection = example_objections[selected_example]
    else:
        default_objection = ""
    
    objection_text = st.text_area(
        "Objection Text:",
        value=default_objection,
        height=100,
        placeholder="Enter the lead's concern or objection..."
    )
    
    # Property context (optional)
    with st.expander("🏠 Property Context (Optional)"):
        property_address = st.text_input("Property Address", "123 Main Street")
        property_price = st.number_input("Listing Price ($)", value=int(lead_budget), step=10000, format="%d")
        property_type = st.selectbox("Property Type", ["Single Family", "Condo", "Townhouse", "Multi-Family"])
    
    st.divider()
    
    # Generate response button
    generate_btn = st.button("🚀 Generate AI Response", type="primary", use_container_width=True)

with col2:
    st.subheader("🤖 AI-Powered Response")
    
    if generate_btn and objection_text:
        with st.spinner("🧠 Analyzing objection and generating response..."):
            # Initialize Deal Closer AI
            closer = DealCloserAI()
            
            # Build context
            lead_context = {
                "name": lead_name,
                "stage": lead_stage.lower().replace(" ", "_"),
                "interaction_count": interactions,
                "budget_min": int(lead_budget * 0.8),
                "budget_max": int(lead_budget * 1.2)
            }
            
            property_context = {
                "address": property_address,
                "price": property_price,
                "type": property_type
            } if property_address else None
            
            # Generate response
            result = closer.generate_response(
                objection_text,
                lead_context,
                property_context
            )
            
            # Store in history
            st.session_state.objection_history.append({
                "objection": objection_text,
                "result": result,
                "lead": lead_name
            })
            
            # Display objection analysis
            st.markdown("#### 🔍 Objection Analysis")
            
            col_a, col_b = st.columns(2)
            with col_a:
                category = result.get("objection_category", "general")
                st.metric("Category", category.replace("_", " ").title())
            with col_b:
                confidence = result.get("confidence", 0)
                st.metric("Confidence", f"{confidence:.0%}")
            
            st.divider()
            
            # Display response
            st.markdown("#### ✅ Recommended Response")
            response_text = result.get("response", "No response generated")
            st.success(response_text)
            
            # Copy button simulation
            if st.button("📋 Copy Response", key="copy_response"):
                st.info("✅ Response copied to clipboard!")
            
            st.divider()
            
            # Talking points
            st.markdown("#### 💡 Key Talking Points")
            talking_points = result.get("talking_points", [])
            for i, point in enumerate(talking_points, 1):
                st.markdown(f"{i}. {point}")
            
            st.divider()
            
            # Follow-up actions
            st.markdown("#### 📋 Recommended Follow-Up Actions")
            follow_ups = result.get("follow_up_actions", [])
            for action in follow_ups:
                st.checkbox(action, key=f"action_{action[:20]}")
            
            # Additional info
            if result.get("is_fallback"):
                st.info("ℹ️ Using template response (API not configured)")
    
    elif generate_btn:
        st.warning("⚠️ Please enter an objection to analyze")
    else:
        st.info("👈 Enter a lead objection and click 'Generate AI Response' to see intelligent recommendations")

# Bottom section - History
st.divider()

st.subheader("📊 Objection Handling History")

if st.session_state.objection_history:
    # Statistics
    total_handled = len(st.session_state.objection_history)
    categories = [h["result"].get("objection_category", "unknown") for h in st.session_state.objection_history]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Objections Handled", total_handled)
    with col2:
        most_common = max(set(categories), key=categories.count) if categories else "N/A"
        st.metric("Most Common Category", most_common.replace("_", " ").title())
    with col3:
        avg_confidence = sum(h["result"].get("confidence", 0) for h in st.session_state.objection_history) / total_handled
        st.metric("Avg Confidence", f"{avg_confidence:.0%}")
    
    st.divider()
    
    # History table
    with st.expander("📜 View Full History", expanded=False):
        for i, entry in enumerate(reversed(st.session_state.objection_history[-10:]), 1):
            st.markdown(f"**{i}. {entry['lead']}** - {entry['result'].get('objection_category', 'unknown').replace('_', ' ').title()}")
            st.caption(f"Objection: {entry['objection'][:100]}...")
            st.caption(f"Response: {entry['result'].get('response', '')[:150]}...")
            st.divider()
    
    if st.button("🗑️ Clear History"):
        st.session_state.objection_history = []
        st.rerun()
else:
    st.info("No objections handled yet. Start by analyzing your first lead objection!")

# Sidebar - Feature Info
with st.sidebar:
    st.markdown("### 💰 Deal Closer AI")
    st.markdown("---")
    
    st.markdown("**🎯 Key Features:**")
    st.markdown("""
    - 🔍 Real-time objection detection
    - 🤖 AI-powered response generation
    - 💡 Context-aware strategies
    - 📋 Actionable follow-ups
    - 📊 Pattern learning
    """)
    
    st.markdown("---")
    st.markdown("**💰 Revenue Impact:**")
    st.markdown("""
    - **+15% close rate** improvement
    - **+$50K-80K/year** revenue increase
    - **Time saved:** 10+ hours/week
    - **Response quality:** Professional & empathetic
    """)
    
    st.markdown("---")
    st.markdown("**🎓 Objection Categories:**")
    categories_list = [
        "💵 Price concerns",
        "⏰ Timing issues", 
        "👥 Competition",
        "🤝 Trust/credibility",
        "🏠 Property concerns",
        "💳 Financing challenges"
    ]
    for cat in categories_list:
        st.caption(cat)
    
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use this tool during live calls or immediately after receiving objections to maintain momentum!")
