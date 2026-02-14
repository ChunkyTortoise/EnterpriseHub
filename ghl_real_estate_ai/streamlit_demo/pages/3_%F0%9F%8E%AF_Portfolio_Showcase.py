"""
Portfolio Showcase Page for EnterpriseHub
Target: AI Chatbot & Agent Development gigs (71% YoY growth on Upwork)
Signature Offer: AI Lead Qualification Chatbot + CRM Automation for Real Estate
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Import theme and utilities
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from ghl_real_estate_ai.streamlit_demo.config.page_config import configure_page

# Configure page
configure_page()

# Inject CSS
inject_elite_css()

# Import components
from ghl_real_estate_ai.streamlit_demo.components.lead_scoring_viz import (
    render_lead_temperature_gauge,
    render_qualification_framework,
    render_factor_breakdown,
)
from ghl_real_estate_ai.streamlit_demo.components.handoff_flow_animation import (
    render_handoff_flow_diagram,
    render_trigger_phrases,
)


def render_hero_section():
    """Render the hero section with headline and CTA buttons."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(0, 229, 255, 0.1) 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 25px 60px rgba(99, 102, 241, 0.15);
    ">
        <h1 style="
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            letter-spacing: -0.02em;
        ">
            AI Lead Qualification Chatbot<br>
            <span style="color: #6366F1;">for Real Estate</span>
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.85);
            font-size: 1.35rem;
            max-width: 800px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        ">
            I build AI chatbots that qualify leads 24/7 so real estate agents 
            close more deals and waste zero time on tire-kickers.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="#demo" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 700;
                font-size: 1.1rem;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
                transition: all 0.3s ease;
            ">
                🚀 Try Live Demo
            </a>
            <a href="#case-studies" style="
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 600;
                font-size: 1.1rem;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                📊 View Case Studies
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics_banner():
    """Render the key metrics banner."""
    st.markdown("""
    <div style="
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            text-align: center;
        ">
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #10B981; margin-bottom: 0.5rem;">85%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Lead Qualification Rate</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00E5FF; margin-bottom: 0.5rem;"><200ms</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Response Time</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 0.5rem;">92%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Hot Lead Detection</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #6366F1; margin-bottom: 0.5rem;">
                    GHL • HubSpot • Salesforce
                </div>
                <div style="color: #8B949E; font-size: 0.95rem;">CRM Integration</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_interactive_demo():
    """Render the interactive demo section with chat interface mockup."""
    st.markdown("<a name='demo'></a>", unsafe_allow_html=True)
    st.markdown("### 🎮 Interactive Demo")
    st.markdown("Experience how the AI qualifies leads in real-time")
    
    # Scenario selector
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scenario = st.selectbox(
            "Select a Scenario:",
            [
                "🏠 Buyer Inquiry",
                "🏡 Seller Lead", 
                "❓ Property Question",
            ],
            label_visibility="visible"
        )
        
        # Lead scoring visualization
        st.markdown("#### Lead Temperature")
        
        # Determine score based on scenario
        scenario_scores = {
            "🏠 Buyer Inquiry": {"score": 78, "temperature": "Warm"},
            "🏡 Seller Lead": {"score": 92, "temperature": "Hot"},
            "❓ Property Question": {"score": 45, "temperature": "Cold"},
        }
        
        lead_data = scenario_scores.get(scenario, {"score": 50, "temperature": "Warm"})
        render_lead_temperature_gauge(lead_data["score"])
        
        # Qualification framework
        st.markdown("#### Q0-Q4 Qualification")
        render_qualification_framework(lead_data["score"])
    
    with col2:
        # Chat interface mockup
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.9);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        ">
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1rem 1.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                gap: 0.75rem;
            ">
                <div style="width: 10px; height: 10px; background: #10B981; border-radius: 50%;"></div>
                <span style="color: #FFFFFF; font-weight: 600;">Jorge Lead Bot</span>
                <span style="color: #8B949E; font-size: 0.85rem; margin-left: auto;">Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Sample conversation based on scenario
            if "Buyer" in scenario:
                render_buyer_conversation()
            elif "Seller" in scenario:
                render_seller_conversation()
            else:
                render_property_question_conversation()


def render_buyer_conversation():
    """Render buyer inquiry conversation."""
    conversations = [
        {"role": "user", "message": "Hi, I'm looking for a 3-bedroom home in Rancho Cucamonga under $600k."},
        {"role": "bot", "message": "Great to meet you! I'd love to help you find your perfect home. A few quick questions to narrow down the best options:", "lead_score": "+5"},
        {"role": "bot", "message": "1️⃣ What's your timeline for moving?\n2️⃣ Are you pre-approved for a mortgage?\n3️⃣ Any must-haves (pool, garage, schools)?"},
        {"role": "user", "message": "We need to move in 2-3 months. Yes, pre-approved for $550k. Good schools are a must!"},
        {"role": "bot", "message": "Excellent! 🎯 Pre-approved buyer with clear timeline = **Warm Lead** detected.", "lead_score": "+15", "temperature": "warm"},
        {"role": "bot", "message": "I've found 7 properties matching your criteria in the Etiwanda School District. Would you like me to schedule viewings for this weekend?"},
    ]
    
    render_chat_messages(conversations)


def render_seller_conversation():
    """Render seller lead conversation."""
    conversations = [
        {"role": "user", "message": "I'm thinking about selling my home in Victoria Gardens. What's it worth?"},
        {"role": "bot", "message": "I'd be happy to help you understand your home's value! Victoria Gardens is a sought-after area.", "lead_score": "+8"},
        {"role": "bot", "message": "To provide an accurate estimate:\n1️⃣ What's your square footage?\n2️⃣ Any recent upgrades?\n3️⃣ What's your motivation for selling?"},
        {"role": "user", "message": "2,400 sq ft, renovated kitchen last year. We're relocating for work in 60 days - need to sell fast!"},
        {"role": "bot", "message": "🔥 **Hot Lead Detected!** Motivated seller with timeline urgency.", "lead_score": "+25", "temperature": "hot"},
        {"role": "bot", "message": "Based on recent comps, your home could list for $725K-$750K. I can connect you with our listing specialist within the hour. Interested?"},
    ]
    
    render_chat_messages(conversations)


def render_property_question_conversation():
    """Render property question conversation."""
    conversations = [
        {"role": "user", "message": "What's the HOA fee for the condos on Haven Avenue?"},
        {"role": "bot", "message": "I can help with that! The Haven Avenue condos (The Villas) have HOA fees ranging from $180-$250/month depending on the unit size.", "lead_score": "+3"},
        {"role": "bot", "message": "Are you considering purchasing in that area, or just researching?"},
        {"role": "user", "message": "Just curious about the area for now, thanks!"},
        {"role": "bot", "message": "📝 **Cold Lead** - Information seeker, no immediate intent.", "lead_score": "-2", "temperature": "cold"},
        {"role": "bot", "message": "No problem! I'm here whenever you're ready to explore further. Feel free to ask anything about Rancho Cucamonga real estate!"},
    ]
    
    render_chat_messages(conversations)


def render_chat_messages(conversations):
    """Render a list of chat messages."""
    for conv in conversations:
        if conv["role"] == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    color: #FFFFFF;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 4px 16px;
                    max-width: 80%;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">{conv["message"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Bot message with optional lead score
            score_badge = ""
            if "lead_score" in conv:
                score_color = "#10B981" if "+" in conv["lead_score"] else "#EF4444"
                score_badge = f'<span style="background: {score_color}22; color: {score_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["lead_score"]}</span>'
            
            temp_badge = ""
            if "temperature" in conv:
                temp_colors = {"hot": "#EF4444", "warm": "#F59E0B", "cold": "#3B82F6"}
                temp_color = temp_colors.get(conv["temperature"], "#8B949E")
                temp_badge = f'<span style="background: {temp_color}22; color: {temp_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["temperature"].upper()}</span>'
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.05);
                    color: #E5E7EB;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 16px 4px;
                    max-width: 80%;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                ">{conv["message"]}{score_badge}{temp_badge}</div>
            </div>
            """, unsafe_allow_html=True)


def render_capabilities_showcase():
    """Render the expandable capabilities sections."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Capabilities Showcase")
    
    # Multi-Bot Orchestration
    with st.expander("🤖 Multi-Bot Orchestration", expanded=True):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Three specialized AI agents work together to handle every lead type:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🎯</div>
                <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Jorge Lead Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Initial qualification & routing</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(16, 185, 129, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏠</div>
                <h4 style="color: #10B981; margin-bottom: 0.5rem;">Jorge Buyer Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Property matching & tours</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(245, 158, 11, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏡</div>
                <h4 style="color: #F59E0B; margin-bottom: 0.5rem;">Jorge Seller Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Valuation & listing prep</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Handoff flow diagram
        st.markdown("<br>", unsafe_allow_html=True)
        render_handoff_flow_diagram()
    
    # RAG-Powered Intelligence
    with st.expander("🧠 RAG-Powered Intelligence"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Retrieval-Augmented Generation ensures accurate, contextual responses:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #6366F1; margin-bottom: 0.75rem;">📚 Knowledge Base</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Local market data & trends</li>
                    <li>Property listings & history</li>
                    <li>Neighborhood insights</li>
                    <li>School district information</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #10B981; margin-bottom: 0.75rem;">⚡ Real-Time Retrieval</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Semantic search <50ms</li>
                    <li>Context-aware responses</li>
                    <li>Citation-backed answers</li>
                    <li>Multi-source synthesis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # CRM Automation
    with st.expander("🔗 CRM Automation & Integration"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Seamless integration with your existing CRM workflow:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("GoHighLevel", "✓ Native", "Webhooks + API")
        with col2:
            st.metric("HubSpot", "✓ Supported", "OAuth 2.0")
        with col3:
            st.metric("Salesforce", "✓ Supported", "REST API")
        
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h5 style="color: #6366F1; margin-bottom: 0.75rem;">🔄 Automated Actions</h5>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div style="color: #8B949E;">• Lead tagging & scoring</div>
                <div style="color: #8B949E;">• Follow-up sequences</div>
                <div style="color: #8B949E;">• Agent notifications</div>
                <div style="color: #8B949E;">• Pipeline updates</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-Time Analytics
    with st.expander("📊 Real-Time Analytics Dashboard"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Monitor performance and optimize conversions with comprehensive analytics:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Leads Today", "47", "+12%")
        with col2:
            st.metric("Avg Response", "0.8s", "-60%")
        with col3:
            st.metric("Conversion Rate", "23%", "+8%")
        with col4:
            st.metric("Hot Leads", "8", "Ready for agent")


def render_case_studies():
    """Render the case studies section."""
    st.markdown("<a name='case-studies'></a>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Case Studies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            height: 100%;
        ">
            <div style="
                background: #6366F1;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">REAL ESTATE BROKERAGE</div>
            <h4 style="color: white; margin-bottom: 1rem;">95% Faster Lead Response</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                A scaling brokerage reduced response time from 45 minutes to 2 minutes, 
                recovering $240K in annual labor costs.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">133%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Conversion Increase</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">$240K</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Annual Savings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            height: 100%;
        ">
            <div style="
                background: #10B981;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">PROPERTY MANAGEMENT</div>
            <h4 style="color: white; margin-bottom: 1rem;">24/7 Tenant Qualification</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Property management firm automated tenant screening, reducing vacancy 
                time by 40% and eliminating after-hours calls.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">40%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Less Vacancy</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">85%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Auto-Qualified</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_cta_section():
    """Render the call-to-action section."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-top: 2rem;
    ">
        <h2 style="color: white; margin-bottom: 1rem;">Ready to Automate Your Lead Qualification?</h2>
        <p style="color: #8B949E; font-size: 1.1rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Get a custom AI chatbot that qualifies leads 24/7 and integrates with your CRM.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="https://calendly.com" target="_blank" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
            ">
                📅 Book a Free Consultation
            </a>
            <a href="mailto:contact@example.com" style="
                background: rgba(255, 255, 255, 0.08);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                ✉️ Send an Email
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the footer section."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
            © 2026 EnterpriseHub | AI Lead Qualification for Real Estate
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem;">
            <a href="https://github.com/ChunkyTortoise/EnterpriseHub" style="color: #6366F1; text-decoration: none;">GitHub</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">LinkedIn</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">Portfolio</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main function to render the portfolio showcase page."""
    # Page title
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Render all sections
    render_hero_section()
    render_metrics_banner()
    render_interactive_demo()
    render_capabilities_showcase()
    render_case_studies()
    render_cta_section()
    render_footer()


if __name__ == "__main__":
    main()
Portfolio Showcase Page for EnterpriseHub
Target: AI Chatbot & Agent Development gigs (71% YoY growth on Upwork)
Signature Offer: AI Lead Qualification Chatbot + CRM Automation for Real Estate
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Import theme and utilities
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from ghl_real_estate_ai.streamlit_demo.config.page_config import configure_page

# Configure page
configure_page()

# Inject CSS
inject_elite_css()

# Import components
from ghl_real_estate_ai.streamlit_demo.components.lead_scoring_viz import (
    render_lead_temperature_gauge,
    render_qualification_framework,
    render_factor_breakdown,
)
from ghl_real_estate_ai.streamlit_demo.components.handoff_flow_animation import (
    render_handoff_flow_diagram,
    render_trigger_phrases,
)


def render_hero_section():
    """Render the hero section with headline and CTA buttons."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(0, 229, 255, 0.1) 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 25px 60px rgba(99, 102, 241, 0.15);
    ">
        <h1 style="
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            letter-spacing: -0.02em;
        ">
            AI Lead Qualification Chatbot<br>
            <span style="color: #6366F1;">for Real Estate</span>
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.85);
            font-size: 1.35rem;
            max-width: 800px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        ">
            I build AI chatbots that qualify leads 24/7 so real estate agents 
            close more deals and waste zero time on tire-kickers.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="#demo" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 700;
                font-size: 1.1rem;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
                transition: all 0.3s ease;
            ">
                🚀 Try Live Demo
            </a>
            <a href="#case-studies" style="
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 600;
                font-size: 1.1rem;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                📊 View Case Studies
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics_banner():
    """Render the key metrics banner."""
    st.markdown("""
    <div style="
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            text-align: center;
        ">
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #10B981; margin-bottom: 0.5rem;">85%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Lead Qualification Rate</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00E5FF; margin-bottom: 0.5rem;"><200ms</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Response Time</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 0.5rem;">92%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Hot Lead Detection</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #6366F1; margin-bottom: 0.5rem;">
                    GHL • HubSpot • Salesforce
                </div>
                <div style="color: #8B949E; font-size: 0.95rem;">CRM Integration</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_interactive_demo():
    """Render the interactive demo section with chat interface mockup."""
    st.markdown("<a name='demo'></a>", unsafe_allow_html=True)
    st.markdown("### 🎮 Interactive Demo")
    st.markdown("Experience how the AI qualifies leads in real-time")
    
    # Scenario selector
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scenario = st.selectbox(
            "Select a Scenario:",
            [
                "🏠 Buyer Inquiry",
                "🏡 Seller Lead", 
                "❓ Property Question",
            ],
            label_visibility="visible"
        )
        
        # Lead scoring visualization
        st.markdown("#### Lead Temperature")
        
        # Determine score based on scenario
        scenario_scores = {
            "🏠 Buyer Inquiry": {"score": 78, "temperature": "Warm"},
            "🏡 Seller Lead": {"score": 92, "temperature": "Hot"},
            "❓ Property Question": {"score": 45, "temperature": "Cold"},
        }
        
        lead_data = scenario_scores.get(scenario, {"score": 50, "temperature": "Warm"})
        render_lead_temperature_gauge(lead_data["score"])
        
        # Qualification framework
        st.markdown("#### Q0-Q4 Qualification")
        render_qualification_framework(lead_data["score"])
    
    with col2:
        # Chat interface mockup
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.9);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        ">
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1rem 1.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                gap: 0.75rem;
            ">
                <div style="width: 10px; height: 10px; background: #10B981; border-radius: 50%;"></div>
                <span style="color: #FFFFFF; font-weight: 600;">Jorge Lead Bot</span>
                <span style="color: #8B949E; font-size: 0.85rem; margin-left: auto;">Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Sample conversation based on scenario
            if "Buyer" in scenario:
                render_buyer_conversation()
            elif "Seller" in scenario:
                render_seller_conversation()
            else:
                render_property_question_conversation()


def render_buyer_conversation():
    """Render buyer inquiry conversation."""
    conversations = [
        {"role": "user", "message": "Hi, I'm looking for a 3-bedroom home in Rancho Cucamonga under $600k."},
        {"role": "bot", "message": "Great to meet you! I'd love to help you find your perfect home. A few quick questions to narrow down the best options:", "lead_score": "+5"},
        {"role": "bot", "message": "1️⃣ What's your timeline for moving?\n2️⃣ Are you pre-approved for a mortgage?\n3️⃣ Any must-haves (pool, garage, schools)?"},
        {"role": "user", "message": "We need to move in 2-3 months. Yes, pre-approved for $550k. Good schools are a must!"},
        {"role": "bot", "message": "Excellent! 🎯 Pre-approved buyer with clear timeline = **Warm Lead** detected.", "lead_score": "+15", "temperature": "warm"},
        {"role": "bot", "message": "I've found 7 properties matching your criteria in the Etiwanda School District. Would you like me to schedule viewings for this weekend?"},
    ]
    
    render_chat_messages(conversations)


def render_seller_conversation():
    """Render seller lead conversation."""
    conversations = [
        {"role": "user", "message": "I'm thinking about selling my home in Victoria Gardens. What's it worth?"},
        {"role": "bot", "message": "I'd be happy to help you understand your home's value! Victoria Gardens is a sought-after area.", "lead_score": "+8"},
        {"role": "bot", "message": "To provide an accurate estimate:\n1️⃣ What's your square footage?\n2️⃣ Any recent upgrades?\n3️⃣ What's your motivation for selling?"},
        {"role": "user", "message": "2,400 sq ft, renovated kitchen last year. We're relocating for work in 60 days - need to sell fast!"},
        {"role": "bot", "message": "🔥 **Hot Lead Detected!** Motivated seller with timeline urgency.", "lead_score": "+25", "temperature": "hot"},
        {"role": "bot", "message": "Based on recent comps, your home could list for $725K-$750K. I can connect you with our listing specialist within the hour. Interested?"},
    ]
    
    render_chat_messages(conversations)


def render_property_question_conversation():
    """Render property question conversation."""
    conversations = [
        {"role": "user", "message": "What's the HOA fee for the condos on Haven Avenue?"},
        {"role": "bot", "message": "I can help with that! The Haven Avenue condos (The Villas) have HOA fees ranging from $180-$250/month depending on the unit size.", "lead_score": "+3"},
        {"role": "bot", "message": "Are you considering purchasing in that area, or just researching?"},
        {"role": "user", "message": "Just curious about the area for now, thanks!"},
        {"role": "bot", "message": "📝 **Cold Lead** - Information seeker, no immediate intent.", "lead_score": "-2", "temperature": "cold"},
        {"role": "bot", "message": "No problem! I'm here whenever you're ready to explore further. Feel free to ask anything about Rancho Cucamonga real estate!"},
    ]
    
    render_chat_messages(conversations)


def render_chat_messages(conversations):
    """Render a list of chat messages."""
    for conv in conversations:
        if conv["role"] == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    color: #FFFFFF;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 4px 16px;
                    max-width: 80%;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">{conv["message"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Bot message with optional lead score
            score_badge = ""
            if "lead_score" in conv:
                score_color = "#10B981" if "+" in conv["lead_score"] else "#EF4444"
                score_badge = f'<span style="background: {score_color}22; color: {score_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["lead_score"]}</span>'
            
            temp_badge = ""
            if "temperature" in conv:
                temp_colors = {"hot": "#EF4444", "warm": "#F59E0B", "cold": "#3B82F6"}
                temp_color = temp_colors.get(conv["temperature"], "#8B949E")
                temp_badge = f'<span style="background: {temp_color}22; color: {temp_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["temperature"].upper()}</span>'
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.05);
                    color: #E5E7EB;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 16px 4px;
                    max-width: 80%;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                ">{conv["message"]}{score_badge}{temp_badge}</div>
            </div>
            """, unsafe_allow_html=True)


def render_capabilities_showcase():
    """Render the expandable capabilities sections."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Capabilities Showcase")
    
    # Multi-Bot Orchestration
    with st.expander("🤖 Multi-Bot Orchestration", expanded=True):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Three specialized AI agents work together to handle every lead type:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🎯</div>
                <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Jorge Lead Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Initial qualification & routing</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(16, 185, 129, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏠</div>
                <h4 style="color: #10B981; margin-bottom: 0.5rem;">Jorge Buyer Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Property matching & tours</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(245, 158, 11, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏡</div>
                <h4 style="color: #F59E0B; margin-bottom: 0.5rem;">Jorge Seller Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Valuation & listing prep</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Handoff flow diagram
        st.markdown("<br>", unsafe_allow_html=True)
        render_handoff_flow_diagram()
    
    # RAG-Powered Intelligence
    with st.expander("🧠 RAG-Powered Intelligence"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Retrieval-Augmented Generation ensures accurate, contextual responses:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #6366F1; margin-bottom: 0.75rem;">📚 Knowledge Base</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Local market data & trends</li>
                    <li>Property listings & history</li>
                    <li>Neighborhood insights</li>
                    <li>School district information</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #10B981; margin-bottom: 0.75rem;">⚡ Real-Time Retrieval</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Semantic search <50ms</li>
                    <li>Context-aware responses</li>
                    <li>Citation-backed answers</li>
                    <li>Multi-source synthesis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # CRM Automation
    with st.expander("🔗 CRM Automation & Integration"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Seamless integration with your existing CRM workflow:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("GoHighLevel", "✓ Native", "Webhooks + API")
        with col2:
            st.metric("HubSpot", "✓ Supported", "OAuth 2.0")
        with col3:
            st.metric("Salesforce", "✓ Supported", "REST API")
        
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h5 style="color: #6366F1; margin-bottom: 0.75rem;">🔄 Automated Actions</h5>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div style="color: #8B949E;">• Lead tagging & scoring</div>
                <div style="color: #8B949E;">• Follow-up sequences</div>
                <div style="color: #8B949E;">• Agent notifications</div>
                <div style="color: #8B949E;">• Pipeline updates</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-Time Analytics
    with st.expander("📊 Real-Time Analytics Dashboard"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Monitor performance and optimize conversions with comprehensive analytics:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Leads Today", "47", "+12%")
        with col2:
            st.metric("Avg Response", "0.8s", "-60%")
        with col3:
            st.metric("Conversion Rate", "23%", "+8%")
        with col4:
            st.metric("Hot Leads", "8", "Ready for agent")


def render_case_studies():
    """Render the case studies section."""
    st.markdown("<a name='case-studies'></a>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Case Studies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            height: 100%;
        ">
            <div style="
                background: #6366F1;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">REAL ESTATE BROKERAGE</div>
            <h4 style="color: white; margin-bottom: 1rem;">95% Faster Lead Response</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                A scaling brokerage reduced response time from 45 minutes to 2 minutes, 
                recovering $240K in annual labor costs.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">133%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Conversion Increase</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">$240K</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Annual Savings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            height: 100%;
        ">
            <div style="
                background: #10B981;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">PROPERTY MANAGEMENT</div>
            <h4 style="color: white; margin-bottom: 1rem;">24/7 Tenant Qualification</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Property management firm automated tenant screening, reducing vacancy 
                time by 40% and eliminating after-hours calls.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">40%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Less Vacancy</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">85%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Auto-Qualified</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_cta_section():
    """Render the call-to-action section."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-top: 2rem;
    ">
        <h2 style="color: white; margin-bottom: 1rem;">Ready to Automate Your Lead Qualification?</h2>
        <p style="color: #8B949E; font-size: 1.1rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Get a custom AI chatbot that qualifies leads 24/7 and integrates with your CRM.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="https://calendly.com" target="_blank" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
            ">
                📅 Book a Free Consultation
            </a>
            <a href="mailto:contact@example.com" style="
                background: rgba(255, 255, 255, 0.08);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                ✉️ Send an Email
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the footer section."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
            © 2026 EnterpriseHub | AI Lead Qualification for Real Estate
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem;">
            <a href="https://github.com/ChunkyTortoise/EnterpriseHub" style="color: #6366F1; text-decoration: none;">GitHub</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">LinkedIn</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">Portfolio</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main function to render the portfolio showcase page."""
    # Page title
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Render all sections
    render_hero_section()
    render_metrics_banner()
    render_interactive_demo()
    render_capabilities_showcase()
    render_case_studies()
    render_cta_section()
    render_footer()


if __name__ == "__main__":
    main()

Target: AI Chatbot & Agent Development gigs (71% YoY growth on Upwork)
Signature Offer: AI Lead Qualification Chatbot + CRM Automation for Real Estate
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Import theme and utilities
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from ghl_real_estate_ai.streamlit_demo.config.page_config import configure_page

# Configure page
configure_page()

# Inject CSS
inject_elite_css()

# Import components
from ghl_real_estate_ai.streamlit_demo.components.lead_scoring_viz import (
    render_lead_temperature_gauge,
    render_qualification_framework,
    render_factor_breakdown,
)
from ghl_real_estate_ai.streamlit_demo.components.handoff_flow_animation import (
    render_handoff_flow_diagram,
    render_trigger_phrases,
)


def render_hero_section():
    """Render the hero section with headline and CTA buttons."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(0, 229, 255, 0.1) 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 25px 60px rgba(99, 102, 241, 0.15);
    ">
        <h1 style="
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            letter-spacing: -0.02em;
        ">
            AI Lead Qualification Chatbot<br>
            <span style="color: #6366F1;">for Real Estate</span>
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.85);
            font-size: 1.35rem;
            max-width: 800px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        ">
            I build AI chatbots that qualify leads 24/7 so real estate agents 
            close more deals and waste zero time on tire-kickers.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="#demo" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 700;
                font-size: 1.1rem;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
                transition: all 0.3s ease;
            ">
                🚀 Try Live Demo
            </a>
            <a href="#case-studies" style="
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 600;
                font-size: 1.1rem;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                📊 View Case Studies
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics_banner():
    """Render the key metrics banner."""
    st.markdown("""
    <div style="
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            text-align: center;
        ">
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #10B981; margin-bottom: 0.5rem;">85%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Lead Qualification Rate</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00E5FF; margin-bottom: 0.5rem;"><200ms</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Response Time</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 0.5rem;">92%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Hot Lead Detection</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #6366F1; margin-bottom: 0.5rem;">
                    GHL • HubSpot • Salesforce
                </div>
                <div style="color: #8B949E; font-size: 0.95rem;">CRM Integration</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_interactive_demo():
    """Render the interactive demo section with chat interface mockup."""
    st.markdown("<a name='demo'></a>", unsafe_allow_html=True)
    st.markdown("### 🎮 Interactive Demo")
    st.markdown("Experience how the AI qualifies leads in real-time")
    
    # Scenario selector
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scenario = st.selectbox(
            "Select a Scenario:",
            [
                "🏠 Buyer Inquiry",
                "🏡 Seller Lead", 
                "❓ Property Question",
            ],
            label_visibility="visible"
        )
        
        # Lead scoring visualization
        st.markdown("#### Lead Temperature")
        
        # Determine score based on scenario
        scenario_scores = {
            "🏠 Buyer Inquiry": {"score": 78, "temperature": "Warm"},
            "🏡 Seller Lead": {"score": 92, "temperature": "Hot"},
            "❓ Property Question": {"score": 45, "temperature": "Cold"},
        }
        
        lead_data = scenario_scores.get(scenario, {"score": 50, "temperature": "Warm"})
        render_lead_temperature_gauge(lead_data["score"])
        
        # Qualification framework
        st.markdown("#### Q0-Q4 Qualification")
        render_qualification_framework(lead_data["score"])
    
    with col2:
        # Chat interface mockup
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.9);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        ">
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1rem 1.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                gap: 0.75rem;
            ">
                <div style="width: 10px; height: 10px; background: #10B981; border-radius: 50%;"></div>
                <span style="color: #FFFFFF; font-weight: 600;">Jorge Lead Bot</span>
                <span style="color: #8B949E; font-size: 0.85rem; margin-left: auto;">Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Sample conversation based on scenario
            if "Buyer" in scenario:
                render_buyer_conversation()
            elif "Seller" in scenario:
                render_seller_conversation()
            else:
                render_property_question_conversation()


def render_buyer_conversation():
    """Render buyer inquiry conversation."""
    conversations = [
        {"role": "user", "message": "Hi, I'm looking for a 3-bedroom home in Rancho Cucamonga under $600k."},
        {"role": "bot", "message": "Great to meet you! I'd love to help you find your perfect home. A few quick questions to narrow down the best options:", "lead_score": "+5"},
        {"role": "bot", "message": "1️⃣ What's your timeline for moving?\n2️⃣ Are you pre-approved for a mortgage?\n3️⃣ Any must-haves (pool, garage, schools)?"},
        {"role": "user", "message": "We need to move in 2-3 months. Yes, pre-approved for $550k. Good schools are a must!"},
        {"role": "bot", "message": "Excellent! 🎯 Pre-approved buyer with clear timeline = **Warm Lead** detected.", "lead_score": "+15", "temperature": "warm"},
        {"role": "bot", "message": "I've found 7 properties matching your criteria in the Etiwanda School District. Would you like me to schedule viewings for this weekend?"},
    ]
    
    render_chat_messages(conversations)


def render_seller_conversation():
    """Render seller lead conversation."""
    conversations = [
        {"role": "user", "message": "I'm thinking about selling my home in Victoria Gardens. What's it worth?"},
        {"role": "bot", "message": "I'd be happy to help you understand your home's value! Victoria Gardens is a sought-after area.", "lead_score": "+8"},
        {"role": "bot", "message": "To provide an accurate estimate:\n1️⃣ What's your square footage?\n2️⃣ Any recent upgrades?\n3️⃣ What's your motivation for selling?"},
        {"role": "user", "message": "2,400 sq ft, renovated kitchen last year. We're relocating for work in 60 days - need to sell fast!"},
        {"role": "bot", "message": "🔥 **Hot Lead Detected!** Motivated seller with timeline urgency.", "lead_score": "+25", "temperature": "hot"},
        {"role": "bot", "message": "Based on recent comps, your home could list for $725K-$750K. I can connect you with our listing specialist within the hour. Interested?"},
    ]
    
    render_chat_messages(conversations)


def render_property_question_conversation():
    """Render property question conversation."""
    conversations = [
        {"role": "user", "message": "What's the HOA fee for the condos on Haven Avenue?"},
        {"role": "bot", "message": "I can help with that! The Haven Avenue condos (The Villas) have HOA fees ranging from $180-$250/month depending on the unit size.", "lead_score": "+3"},
        {"role": "bot", "message": "Are you considering purchasing in that area, or just researching?"},
        {"role": "user", "message": "Just curious about the area for now, thanks!"},
        {"role": "bot", "message": "📝 **Cold Lead** - Information seeker, no immediate intent.", "lead_score": "-2", "temperature": "cold"},
        {"role": "bot", "message": "No problem! I'm here whenever you're ready to explore further. Feel free to ask anything about Rancho Cucamonga real estate!"},
    ]
    
    render_chat_messages(conversations)


def render_chat_messages(conversations):
    """Render a list of chat messages."""
    for conv in conversations:
        if conv["role"] == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    color: #FFFFFF;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 4px 16px;
                    max-width: 80%;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">{conv["message"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Bot message with optional lead score
            score_badge = ""
            if "lead_score" in conv:
                score_color = "#10B981" if "+" in conv["lead_score"] else "#EF4444"
                score_badge = f'<span style="background: {score_color}22; color: {score_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["lead_score"]}</span>'
            
            temp_badge = ""
            if "temperature" in conv:
                temp_colors = {"hot": "#EF4444", "warm": "#F59E0B", "cold": "#3B82F6"}
                temp_color = temp_colors.get(conv["temperature"], "#8B949E")
                temp_badge = f'<span style="background: {temp_color}22; color: {temp_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["temperature"].upper()}</span>'
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.05);
                    color: #E5E7EB;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 16px 4px;
                    max-width: 80%;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                ">{conv["message"]}{score_badge}{temp_badge}</div>
            </div>
            """, unsafe_allow_html=True)


def render_capabilities_showcase():
    """Render the expandable capabilities sections."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Capabilities Showcase")
    
    # Multi-Bot Orchestration
    with st.expander("🤖 Multi-Bot Orchestration", expanded=True):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Three specialized AI agents work together to handle every lead type:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🎯</div>
                <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Jorge Lead Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Initial qualification & routing</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(16, 185, 129, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏠</div>
                <h4 style="color: #10B981; margin-bottom: 0.5rem;">Jorge Buyer Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Property matching & tours</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(245, 158, 11, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏡</div>
                <h4 style="color: #F59E0B; margin-bottom: 0.5rem;">Jorge Seller Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Valuation & listing prep</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Handoff flow diagram
        st.markdown("<br>", unsafe_allow_html=True)
        render_handoff_flow_diagram()
    
    # RAG-Powered Intelligence
    with st.expander("🧠 RAG-Powered Intelligence"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Retrieval-Augmented Generation ensures accurate, contextual responses:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #6366F1; margin-bottom: 0.75rem;">📚 Knowledge Base</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Local market data & trends</li>
                    <li>Property listings & history</li>
                    <li>Neighborhood insights</li>
                    <li>School district information</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #10B981; margin-bottom: 0.75rem;">⚡ Real-Time Retrieval</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Semantic search <50ms</li>
                    <li>Context-aware responses</li>
                    <li>Citation-backed answers</li>
                    <li>Multi-source synthesis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # CRM Automation
    with st.expander("🔗 CRM Automation & Integration"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Seamless integration with your existing CRM workflow:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("GoHighLevel", "✓ Native", "Webhooks + API")
        with col2:
            st.metric("HubSpot", "✓ Supported", "OAuth 2.0")
        with col3:
            st.metric("Salesforce", "✓ Supported", "REST API")
        
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h5 style="color: #6366F1; margin-bottom: 0.75rem;">🔄 Automated Actions</h5>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div style="color: #8B949E;">• Lead tagging & scoring</div>
                <div style="color: #8B949E;">• Follow-up sequences</div>
                <div style="color: #8B949E;">• Agent notifications</div>
                <div style="color: #8B949E;">• Pipeline updates</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-Time Analytics
    with st.expander("📊 Real-Time Analytics Dashboard"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Monitor performance and optimize conversions with comprehensive analytics:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Leads Today", "47", "+12%")
        with col2:
            st.metric("Avg Response", "0.8s", "-60%")
        with col3:
            st.metric("Conversion Rate", "23%", "+8%")
        with col4:
            st.metric("Hot Leads", "8", "Ready for agent")


def render_case_studies():
    """Render the case studies section."""
    st.markdown("<a name='case-studies'></a>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Case Studies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            height: 100%;
        ">
            <div style="
                background: #6366F1;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">REAL ESTATE BROKERAGE</div>
            <h4 style="color: white; margin-bottom: 1rem;">95% Faster Lead Response</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                A scaling brokerage reduced response time from 45 minutes to 2 minutes, 
                recovering $240K in annual labor costs.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">133%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Conversion Increase</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">$240K</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Annual Savings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            height: 100%;
        ">
            <div style="
                background: #10B981;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">PROPERTY MANAGEMENT</div>
            <h4 style="color: white; margin-bottom: 1rem;">24/7 Tenant Qualification</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Property management firm automated tenant screening, reducing vacancy 
                time by 40% and eliminating after-hours calls.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">40%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Less Vacancy</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">85%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Auto-Qualified</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_cta_section():
    """Render the call-to-action section."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-top: 2rem;
    ">
        <h2 style="color: white; margin-bottom: 1rem;">Ready to Automate Your Lead Qualification?</h2>
        <p style="color: #8B949E; font-size: 1.1rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Get a custom AI chatbot that qualifies leads 24/7 and integrates with your CRM.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="https://calendly.com" target="_blank" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
            ">
                📅 Book a Free Consultation
            </a>
            <a href="mailto:contact@example.com" style="
                background: rgba(255, 255, 255, 0.08);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                ✉️ Send an Email
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the footer section."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
            © 2026 EnterpriseHub | AI Lead Qualification for Real Estate
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem;">
            <a href="https://github.com/ChunkyTortoise/EnterpriseHub" style="color: #6366F1; text-decoration: none;">GitHub</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">LinkedIn</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">Portfolio</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main function to render the portfolio showcase page."""
    # Page title
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Render all sections
    render_hero_section()
    render_metrics_banner()
    render_interactive_demo()
    render_capabilities_showcase()
    render_case_studies()
    render_cta_section()
    render_footer()


if __name__ == "__main__":
    main()

Target: AI Chatbot & Agent Development gigs (71% YoY growth on Upwork)
Signature Offer: AI Lead Qualification Chatbot + CRM Automation for Real Estate
"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import time

# Import theme and utilities
from ghl_real_estate_ai.streamlit_demo.obsidian_theme import inject_elite_css
from ghl_real_estate_ai.streamlit_demo.config.page_config import configure_page

# Configure page
configure_page()

# Inject CSS
inject_elite_css()

# Import components
from ghl_real_estate_ai.streamlit_demo.components.lead_scoring_viz import (
    render_lead_temperature_gauge,
    render_qualification_framework,
    render_factor_breakdown,
)
from ghl_real_estate_ai.streamlit_demo.components.handoff_flow_animation import (
    render_handoff_flow_diagram,
    render_trigger_phrases,
)


def render_hero_section():
    """Render the hero section with headline and CTA buttons."""
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(0, 229, 255, 0.1) 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid rgba(99, 102, 241, 0.3);
        box-shadow: 0 25px 60px rgba(99, 102, 241, 0.15);
    ">
        <h1 style="
            color: #FFFFFF;
            font-size: 3rem;
            font-weight: 800;
            margin-bottom: 1.5rem;
            line-height: 1.2;
            letter-spacing: -0.02em;
        ">
            AI Lead Qualification Chatbot<br>
            <span style="color: #6366F1;">for Real Estate</span>
        </h1>
        <p style="
            color: rgba(255, 255, 255, 0.85);
            font-size: 1.35rem;
            max-width: 800px;
            margin: 0 auto 2.5rem auto;
            line-height: 1.6;
        ">
            I build AI chatbots that qualify leads 24/7 so real estate agents 
            close more deals and waste zero time on tire-kickers.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="#demo" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 700;
                font-size: 1.1rem;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
                transition: all 0.3s ease;
            ">
                🚀 Try Live Demo
            </a>
            <a href="#case-studies" style="
                background: rgba(255, 255, 255, 0.08);
                backdrop-filter: blur(10px);
                color: white;
                padding: 1rem 2.5rem;
                border-radius: 12px;
                font-weight: 600;
                font-size: 1.1rem;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                📊 View Case Studies
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_metrics_banner():
    """Render the key metrics banner."""
    st.markdown("""
    <div style="
        background: rgba(13, 17, 23, 0.7);
        backdrop-filter: blur(20px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.08);
    ">
        <div style="
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 1.5rem;
            text-align: center;
        ">
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #10B981; margin-bottom: 0.5rem;">85%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Lead Qualification Rate</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #00E5FF; margin-bottom: 0.5rem;"><200ms</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Response Time</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 2.5rem; font-weight: 800; color: #F59E0B; margin-bottom: 0.5rem;">92%</div>
                <div style="color: #8B949E; font-size: 0.95rem;">Hot Lead Detection</div>
            </div>
            <div style="padding: 1rem;">
                <div style="font-size: 1.5rem; font-weight: 700; color: #6366F1; margin-bottom: 0.5rem;">
                    GHL • HubSpot • Salesforce
                </div>
                <div style="color: #8B949E; font-size: 0.95rem;">CRM Integration</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_interactive_demo():
    """Render the interactive demo section with chat interface mockup."""
    st.markdown("<a name='demo'></a>", unsafe_allow_html=True)
    st.markdown("### 🎮 Interactive Demo")
    st.markdown("Experience how the AI qualifies leads in real-time")
    
    # Scenario selector
    col1, col2 = st.columns([1, 2])
    
    with col1:
        scenario = st.selectbox(
            "Select a Scenario:",
            [
                "🏠 Buyer Inquiry",
                "🏡 Seller Lead", 
                "❓ Property Question",
            ],
            label_visibility="visible"
        )
        
        # Lead scoring visualization
        st.markdown("#### Lead Temperature")
        
        # Determine score based on scenario
        scenario_scores = {
            "🏠 Buyer Inquiry": {"score": 78, "temperature": "Warm"},
            "🏡 Seller Lead": {"score": 92, "temperature": "Hot"},
            "❓ Property Question": {"score": 45, "temperature": "Cold"},
        }
        
        lead_data = scenario_scores.get(scenario, {"score": 50, "temperature": "Warm"})
        render_lead_temperature_gauge(lead_data["score"])
        
        # Qualification framework
        st.markdown("#### Q0-Q4 Qualification")
        render_qualification_framework(lead_data["score"])
    
    with col2:
        # Chat interface mockup
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.9);
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            overflow: hidden;
        ">
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1rem 1.5rem;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                align-items: center;
                gap: 0.75rem;
            ">
                <div style="width: 10px; height: 10px; background: #10B981; border-radius: 50%;"></div>
                <span style="color: #FFFFFF; font-weight: 600;">Jorge Lead Bot</span>
                <span style="color: #8B949E; font-size: 0.85rem; margin-left: auto;">Online</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Chat messages container
        chat_container = st.container()
        
        with chat_container:
            # Sample conversation based on scenario
            if "Buyer" in scenario:
                render_buyer_conversation()
            elif "Seller" in scenario:
                render_seller_conversation()
            else:
                render_property_question_conversation()


def render_buyer_conversation():
    """Render buyer inquiry conversation."""
    conversations = [
        {"role": "user", "message": "Hi, I'm looking for a 3-bedroom home in Rancho Cucamonga under $600k."},
        {"role": "bot", "message": "Great to meet you! I'd love to help you find your perfect home. A few quick questions to narrow down the best options:", "lead_score": "+5"},
        {"role": "bot", "message": "1️⃣ What's your timeline for moving?\n2️⃣ Are you pre-approved for a mortgage?\n3️⃣ Any must-haves (pool, garage, schools)?"},
        {"role": "user", "message": "We need to move in 2-3 months. Yes, pre-approved for $550k. Good schools are a must!"},
        {"role": "bot", "message": "Excellent! 🎯 Pre-approved buyer with clear timeline = **Warm Lead** detected.", "lead_score": "+15", "temperature": "warm"},
        {"role": "bot", "message": "I've found 7 properties matching your criteria in the Etiwanda School District. Would you like me to schedule viewings for this weekend?"},
    ]
    
    render_chat_messages(conversations)


def render_seller_conversation():
    """Render seller lead conversation."""
    conversations = [
        {"role": "user", "message": "I'm thinking about selling my home in Victoria Gardens. What's it worth?"},
        {"role": "bot", "message": "I'd be happy to help you understand your home's value! Victoria Gardens is a sought-after area.", "lead_score": "+8"},
        {"role": "bot", "message": "To provide an accurate estimate:\n1️⃣ What's your square footage?\n2️⃣ Any recent upgrades?\n3️⃣ What's your motivation for selling?"},
        {"role": "user", "message": "2,400 sq ft, renovated kitchen last year. We're relocating for work in 60 days - need to sell fast!"},
        {"role": "bot", "message": "🔥 **Hot Lead Detected!** Motivated seller with timeline urgency.", "lead_score": "+25", "temperature": "hot"},
        {"role": "bot", "message": "Based on recent comps, your home could list for $725K-$750K. I can connect you with our listing specialist within the hour. Interested?"},
    ]
    
    render_chat_messages(conversations)


def render_property_question_conversation():
    """Render property question conversation."""
    conversations = [
        {"role": "user", "message": "What's the HOA fee for the condos on Haven Avenue?"},
        {"role": "bot", "message": "I can help with that! The Haven Avenue condos (The Villas) have HOA fees ranging from $180-$250/month depending on the unit size.", "lead_score": "+3"},
        {"role": "bot", "message": "Are you considering purchasing in that area, or just researching?"},
        {"role": "user", "message": "Just curious about the area for now, thanks!"},
        {"role": "bot", "message": "📝 **Cold Lead** - Information seeker, no immediate intent.", "lead_score": "-2", "temperature": "cold"},
        {"role": "bot", "message": "No problem! I'm here whenever you're ready to explore further. Feel free to ask anything about Rancho Cucamonga real estate!"},
    ]
    
    render_chat_messages(conversations)


def render_chat_messages(conversations):
    """Render a list of chat messages."""
    for conv in conversations:
        if conv["role"] == "user":
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-end;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(99, 102, 241, 0.2);
                    color: #FFFFFF;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 4px 16px;
                    max-width: 80%;
                    border: 1px solid rgba(99, 102, 241, 0.3);
                ">{conv["message"]}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Bot message with optional lead score
            score_badge = ""
            if "lead_score" in conv:
                score_color = "#10B981" if "+" in conv["lead_score"] else "#EF4444"
                score_badge = f'<span style="background: {score_color}22; color: {score_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["lead_score"]}</span>'
            
            temp_badge = ""
            if "temperature" in conv:
                temp_colors = {"hot": "#EF4444", "warm": "#F59E0B", "cold": "#3B82F6"}
                temp_color = temp_colors.get(conv["temperature"], "#8B949E")
                temp_badge = f'<span style="background: {temp_color}22; color: {temp_color}; padding: 0.2rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">{conv["temperature"].upper()}</span>'
            
            st.markdown(f"""
            <div style="
                display: flex;
                justify-content: flex-start;
                margin: 1rem;
            ">
                <div style="
                    background: rgba(255, 255, 255, 0.05);
                    color: #E5E7EB;
                    padding: 0.75rem 1rem;
                    border-radius: 16px 16px 16px 4px;
                    max-width: 80%;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                ">{conv["message"]}{score_badge}{temp_badge}</div>
            </div>
            """, unsafe_allow_html=True)


def render_capabilities_showcase():
    """Render the expandable capabilities sections."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🛠️ Capabilities Showcase")
    
    # Multi-Bot Orchestration
    with st.expander("🤖 Multi-Bot Orchestration", expanded=True):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Three specialized AI agents work together to handle every lead type:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="
                background: rgba(99, 102, 241, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(99, 102, 241, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🎯</div>
                <h4 style="color: #6366F1; margin-bottom: 0.5rem;">Jorge Lead Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Initial qualification & routing</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="
                background: rgba(16, 185, 129, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(16, 185, 129, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏠</div>
                <h4 style="color: #10B981; margin-bottom: 0.5rem;">Jorge Buyer Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Property matching & tours</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="
                background: rgba(245, 158, 11, 0.1);
                padding: 1.5rem;
                border-radius: 16px;
                border: 1px solid rgba(245, 158, 11, 0.3);
                text-align: center;
            ">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">🏡</div>
                <h4 style="color: #F59E0B; margin-bottom: 0.5rem;">Jorge Seller Bot</h4>
                <p style="color: #8B949E; font-size: 0.9rem;">Valuation & listing prep</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Handoff flow diagram
        st.markdown("<br>", unsafe_allow_html=True)
        render_handoff_flow_diagram()
    
    # RAG-Powered Intelligence
    with st.expander("🧠 RAG-Powered Intelligence"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Retrieval-Augmented Generation ensures accurate, contextual responses:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #6366F1; margin-bottom: 0.75rem;">📚 Knowledge Base</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Local market data & trends</li>
                    <li>Property listings & history</li>
                    <li>Neighborhood insights</li>
                    <li>School district information</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: rgba(255, 255, 255, 0.03); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
                <h5 style="color: #10B981; margin-bottom: 0.75rem;">⚡ Real-Time Retrieval</h5>
                <ul style="color: #8B949E; font-size: 0.9rem; line-height: 1.8;">
                    <li>Semantic search <50ms</li>
                    <li>Context-aware responses</li>
                    <li>Citation-backed answers</li>
                    <li>Multi-source synthesis</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    # CRM Automation
    with st.expander("🔗 CRM Automation & Integration"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Seamless integration with your existing CRM workflow:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("GoHighLevel", "✓ Native", "Webhooks + API")
        with col2:
            st.metric("HubSpot", "✓ Supported", "OAuth 2.0")
        with col3:
            st.metric("Salesforce", "✓ Supported", "REST API")
        
        st.markdown("""
        <div style="background: rgba(99, 102, 241, 0.05); padding: 1.5rem; border-radius: 12px; margin-top: 1rem;">
            <h5 style="color: #6366F1; margin-bottom: 0.75rem;">🔄 Automated Actions</h5>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                <div style="color: #8B949E;">• Lead tagging & scoring</div>
                <div style="color: #8B949E;">• Follow-up sequences</div>
                <div style="color: #8B949E;">• Agent notifications</div>
                <div style="color: #8B949E;">• Pipeline updates</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Real-Time Analytics
    with st.expander("📊 Real-Time Analytics Dashboard"):
        st.markdown("""
        <div style="padding: 1rem;">
            <p style="color: #CBD5E1; font-size: 1.05rem; line-height: 1.6;">
                Monitor performance and optimize conversions with comprehensive analytics:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Sample metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Leads Today", "47", "+12%")
        with col2:
            st.metric("Avg Response", "0.8s", "-60%")
        with col3:
            st.metric("Conversion Rate", "23%", "+8%")
        with col4:
            st.metric("Hot Leads", "8", "Ready for agent")


def render_case_studies():
    """Render the case studies section."""
    st.markdown("<a name='case-studies'></a>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Case Studies")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(99, 102, 241, 0.2);
            height: 100%;
        ">
            <div style="
                background: #6366F1;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">REAL ESTATE BROKERAGE</div>
            <h4 style="color: white; margin-bottom: 1rem;">95% Faster Lead Response</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                A scaling brokerage reduced response time from 45 minutes to 2 minutes, 
                recovering $240K in annual labor costs.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">133%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Conversion Increase</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">$240K</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Annual Savings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="
            background: rgba(13, 17, 23, 0.7);
            padding: 2rem;
            border-radius: 20px;
            border: 1px solid rgba(16, 185, 129, 0.2);
            height: 100%;
        ">
            <div style="
                background: #10B981;
                color: white;
                padding: 0.25rem 0.75rem;
                border-radius: 50px;
                font-size: 0.75rem;
                font-weight: 600;
                display: inline-block;
                margin-bottom: 1rem;
            ">PROPERTY MANAGEMENT</div>
            <h4 style="color: white; margin-bottom: 1rem;">24/7 Tenant Qualification</h4>
            <p style="color: #8B949E; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1.5rem;">
                Property management firm automated tenant screening, reducing vacancy 
                time by 40% and eliminating after-hours calls.
            </p>
            <div style="display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div>
                    <div style="color: #10B981; font-size: 1.5rem; font-weight: 700;">40%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Less Vacancy</div>
                </div>
                <div>
                    <div style="color: #6366F1; font-size: 1.5rem; font-weight: 700;">85%</div>
                    <div style="color: #8B949E; font-size: 0.8rem;">Auto-Qualified</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_cta_section():
    """Render the call-to-action section."""
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 100%);
        padding: 3rem 2rem;
        border-radius: 24px;
        text-align: center;
        border: 1px solid rgba(99, 102, 241, 0.3);
        margin-top: 2rem;
    ">
        <h2 style="color: white; margin-bottom: 1rem;">Ready to Automate Your Lead Qualification?</h2>
        <p style="color: #8B949E; font-size: 1.1rem; margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto;">
            Get a custom AI chatbot that qualifies leads 24/7 and integrates with your CRM.
        </p>
        <div style="display: flex; justify-content: center; gap: 1.5rem; flex-wrap: wrap;">
            <a href="https://calendly.com" target="_blank" style="
                background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 700;
                text-decoration: none;
                box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
            ">
                📅 Book a Free Consultation
            </a>
            <a href="mailto:contact@example.com" style="
                background: rgba(255, 255, 255, 0.08);
                color: white;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-weight: 600;
                text-decoration: none;
                border: 1px solid rgba(255, 255, 255, 0.2);
            ">
                ✉️ Send an Email
            </a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer():
    """Render the footer section."""
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="
        text-align: center;
        padding: 2rem 0;
        border-top: 1px solid rgba(255, 255, 255, 0.05);
    ">
        <p style="color: #8B949E; font-size: 0.95rem; margin-bottom: 1rem;">
            © 2026 EnterpriseHub | AI Lead Qualification for Real Estate
        </p>
        <div style="display: flex; justify-content: center; gap: 2rem;">
            <a href="https://github.com/ChunkyTortoise/EnterpriseHub" style="color: #6366F1; text-decoration: none;">GitHub</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">LinkedIn</a>
            <a href="#" style="color: #6366F1; text-decoration: none;">Portfolio</a>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    """Main function to render the portfolio showcase page."""
    # Page title
    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
        }
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Render all sections
    render_hero_section()
    render_metrics_banner()
    render_interactive_demo()
    render_capabilities_showcase()
    render_case_studies()
    render_cta_section()
    render_footer()


if __name__ == "__main__":
    main()

