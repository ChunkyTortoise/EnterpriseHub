"""
Agent Coaching Dashboard - Real-Time Coaching Interface
"""
import streamlit as st
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.agent_coaching import AgentCoachingService

st.set_page_config(page_title="Agent Coaching", page_icon="🎓", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .coaching-tip {
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .urgency-1 { border-left-color: #EF4444; }
    .urgency-2 { border-left-color: #F59E0B; }
    .urgency-3 { border-left-color: #3B82F6; }
    
    .example-box {
        background: #F9FAFB;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-family: 'Courier New', monospace;
    }
    
    .agent-score {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎓 Agent Coaching Dashboard")
st.markdown("**Real-Time Conversation Intelligence**")

# Initialize service
coaching_service = AgentCoachingService()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Live Coaching", "📊 Agent Performance", "📚 Jorge's Templates", "🏆 Best Practices"])

with tab1:
    st.subheader("Real-Time Conversation Coaching")
    
    # Demo conversation simulator
    st.markdown("### Simulate Live Conversation")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("**Current Conversation:**")
        
        # Sample conversation
        conversation = [
            {'sender': 'agent', 'message': 'Hey! Looking to buy or sell?', 'timestamp': '2026-01-05T14:00:00'},
            {'sender': 'lead', 'message': 'Selling. House is old though, needs work', 'timestamp': '2026-01-05T14:02:00'},
            {'sender': 'agent', 'message': 'No problem! We buy as-is. What area?', 'timestamp': '2026-01-05T14:03:00'},
            {'sender': 'lead', 'message': 'Kendall. But it\'s expensive to fix up', 'timestamp': '2026-01-05T14:05:00'},
        ]
        
        for msg in conversation:
            if msg['sender'] == 'agent':
                st.info(f"**Agent:** {msg['message']}")
            else:
                st.success(f"**Lead:** {msg['message']}")
        
        # Input for next message
        next_message = st.text_area("Lead's Next Message:", "I'm also talking to another agent who says they can get me more...")
        
        if st.button("Get Coaching Tips", type="primary"):
            # Add new message to conversation
            conversation.append({'sender': 'lead', 'message': next_message, 'timestamp': datetime.now().isoformat()})
            
            # Get coaching
            context = {'score': 7.2, 'location': 'Kendall', 'name': 'Maria'}
            tips = coaching_service.analyze_conversation_live(conversation, context)
            
            st.markdown("---")
            st.markdown("### 🎯 AI Coaching Suggestions:")
            
            for tip in tips[:3]:  # Top 3 tips
                urgency_class = f"urgency-{tip.urgency}"
                urgency_icon = "🔥" if tip.urgency == 1 else "⚠️" if tip.urgency == 2 else "💡"
                
                st.markdown(f"""
                <div class='coaching-tip {urgency_class}'>
                    <h3>{urgency_icon} {tip.title}</h3>
                    <p><strong>Suggestion:</strong> {tip.suggestion}</p>
                    <div class='example-box'>
                        <strong>💬 Say This:</strong><br>
                        "{tip.example}"
                    </div>
                    <p><small><strong>✨ Why It Works:</strong> {tip.why_it_works}</small></p>
                    <p><small>Confidence: {tip.confidence*100:.0f}% | Show: {'Immediately' if tip.urgency == 1 else 'Soon' if tip.urgency == 2 else 'When Idle'}</small></p>
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("**Quick Stats:**")
        st.metric("Lead Score", "7.2", "+0.3")
        st.metric("Messages", len(conversation), "+1")
        st.metric("Response Time", "2 min", "-1 min")
        
        st.markdown("---")
        st.markdown("**⚡ Quick Actions:**")
        if st.button("🎯 Close for Appointment"):
            st.success("Suggested: 'Perfect! Would today around 2pm or 4:30pm work better for you?'")
        if st.button("💰 Handle Price Objection"):
            st.success("Suggested: 'I hear you. That's why we offer cash (fast) OR listing (top dollar). Which matters more?'")
        if st.button("📞 Request Phone Call"):
            st.success("Suggested: 'Let's hop on a quick call. I have 10 min now or 4pm. Which works?'")

with tab2:
    st.subheader("Agent Performance Analytics")
    
    # Select agent
    agent_name = st.selectbox("Select Agent", ["Maria Johnson", "Carlos Rodriguez", "Jennifer Smith", "Mike Chen"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class='agent-score'>
            <h2>85%</h2>
            <p>Coaching Adoption Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='agent-score'>
            <h2>92%</h2>
            <p>Jorge-Style Usage</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class='agent-score'>
            <h2>28%</h2>
            <p>Appointment Rate</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance report
    st.markdown("### 📊 Performance Report")
    
    # Mock report data
    report = {
        'agent_id': 'MA001',
        'metrics': {
            'total_conversations': 45,
            'appointment_rate': '28.9%',
            'avg_questions_per_convo': 3.2,
            'jorge_style_adoption': '92.0%'
        },
        'strengths': [
            "High appointment conversion rate",
            "Strong adoption of Jorge's communication style",
            "Excellent use of either/or closing questions"
        ],
        'improvements': [
            "Could reduce average response time (currently 8 min)",
            "Consider using break-up texts more frequently"
        ],
        'coaching_focus': [
            "Practice handling price objections",
            "Master the competitive differentiation script"
        ]
    }
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**💪 Strengths:**")
        for strength in report['strengths']:
            st.success(f"✅ {strength}")
    
    with col_b:
        st.markdown("**🎯 Areas for Improvement:**")
        for improvement in report['improvements']:
            st.warning(f"⚠️ {improvement}")
    
    st.markdown("**🎓 Recommended Coaching Focus:**")
    for focus in report['coaching_focus']:
        st.info(f"📚 {focus}")

with tab3:
    st.subheader("Jorge's Proven Templates")
    
    template_category = st.selectbox(
        "Select Category",
        ["Opening", "Timeline", "Budget", "Closing", "Re-engagement", "Objection Handlers"]
    )
    
    templates = {
        'Opening': [
            "Hey {name}! Quick question - looking to buy or sell?",
            "Hey {name}, are you wanting a cash offer or to list for top dollar?",
            "Hey! Saw you were interested in {location}. Buy or sell?"
        ],
        'Timeline': [
            "When are you hoping to move? Next few months or just exploring?",
            "What's your timeline looking like - urgent or flexible?",
            "Are we talking next 30 days or more like 60-90 days?"
        ],
        'Budget': [
            "What price range are you comfortable with? Ballpark is fine.",
            "What's your budget looking like? Just helps me narrow it down.",
            "Got it. What were you thinking price-wise?"
        ],
        'Closing': [
            "Perfect! Would today around 2pm or closer to 4:30pm work better?",
            "Sounds good. I have slots at 11am or 3pm tomorrow. Which works?",
            "Let's lock it in. Morning person or afternoon person?"
        ],
        'Re-engagement': [
            "Hey {name}, just checking in. Still thinking about {location} or should we close your file?",
            "{name} - real talk. Is this still a priority or have you given up? No judgment!",
            "Hey {name}, last check. Still interested or we good to close this out?"
        ],
        'Objection Handlers': [
            "I hear you. That's why we offer two routes - cash (quick, as-is) or listing (top dollar). Which matters more?",
            "Fair concern. Most people in {location} face the same thing. Let me ask - speed or maximum price?",
            "I get it. That's actually why we're different - we can buy it cash OR list it. What's your priority?"
        ]
    }
    
    st.markdown(f"**{template_category} Templates:**")
    
    for i, template in enumerate(templates.get(template_category, []), 1):
        st.markdown(f"""
        <div class='example-box'>
            <strong>Template {i}:</strong><br>
            "{template}"
        </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"Copy Template {i}", key=f"copy_{template_category}_{i}"):
            st.success("✅ Copied to clipboard!")
    
    st.markdown("---")
    st.info("💡 **Pro Tip:** Use {name} and {location} as placeholders. The system will automatically fill them in.")

with tab4:
    st.subheader("🏆 Best Practices from Top Performers")
    
    st.markdown("""
    ### Jorge's Golden Rules
    
    #### 1. **Always Offer Two Paths**
    - Cash offer (speed, convenience)
    - List for top dollar (maximum value)
    - Let THEM choose based on their priorities
    
    #### 2. **Use Either/Or Questions**
    ❌ "When do you want to meet?"  
    ✅ "Would 2pm or 4:30pm work better?"
    
    Why? Easier to answer, feels less committal
    
    #### 3. **Break-Up Texts Work**
    - After 48h no response: "Still interested or should we close your file?"
    - Gets 42% response rate
    - Creates urgency without being pushy
    
    #### 4. **Match Their Energy**
    - Urgent lead? → Call immediately, offer same-day viewing
    - Casual lead? → Text, build rapport, educate
    
    #### 5. **Real Talk = Trust**
    - "Real talk..."
    - "No judgment..."
    - "Just being honest..."
    
    These phrases build rapport and show authenticity
    
    #### 6. **Never Ask What They Already Told You**
    - AI tracks everything they've said
    - Review conversation history before responding
    - Build on previous context
    
    #### 7. **When They Mention Competition**
    - Don't badmouth
    - Differentiate: "Most agents only list. We can buy cash OR list."
    - Move fast: "Let's schedule today"
    
    #### 8. **Hot Lead = Phone Call**
    - Score 7.5+? Stop texting
    - "Let's hop on a quick call. 10 min now or 4pm?"
    - Voice closes better than text
    
    #### 9. **Keep It Under 160 Characters**
    - SMS limit
    - Forces clarity
    - Easier to read on mobile
    
    #### 10. **End With Questions**
    - Keeps conversation going
    - Shows engagement
    - Makes them think about next steps
    """)
    
    st.markdown("---")
    
    col_tip1, col_tip2 = st.columns(2)
    
    with col_tip1:
        st.markdown("""
        ### 📱 Text Examples (Under 160 chars)
        
        ✅ "Hey Maria! Quick Q - cash offer or list for top dollar? Just wanna help you the right way."
        
        ✅ "Got it. 3 beds, Doral, next 60 days. What's your budget looking like?"
        
        ✅ "Perfect! Would 2pm or 4:30pm work better for you?"
        """)
    
    with col_tip2:
        st.markdown("""
        ### ❌ What NOT to Do
        
        ❌ Long paragraphs
        
        ❌ "Let me tell you about all our services..."
        
        ❌ Asking questions they already answered
        
        ❌ Being pushy or desperate
        """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6B7280; padding: 2rem;'>
    <p><strong>🎓 Agent Coaching System</strong> | Powered by Jorge's Proven Methods</p>
    <p style='font-size: 0.875rem;'>Real-time coaching that turns rookies into closers</p>
</div>
""", unsafe_allow_html=True)
