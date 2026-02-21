"""
Portfolio Landing Page - Signature Offer for Potential Clients

A streamlined, client-focused entry point that bypasses technical jargon
to demonstrate immediate value. Includes ROI calculator and live bot demo.

Target Audience: Non-technical stakeholders (potential clients seeking
AI lead qualification services for their real estate business).

Author: EnterpriseHub
Last Updated: 2026-02-13
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# Streamlit is optional at import time
try:
    import streamlit as st
except ModuleNotFoundError:
    st = None


# =============================================================================
# ROI Calculator Data & Logic
# =============================================================================


@dataclass
class PricingTier:
    """Service pricing tier definition"""

    name: str
    price: int
    description: str
    features: List[str]
    popular: bool = False


PRICING_TIERS = [
    PricingTier(
        name="Lead Audit",
        price=1500,
        description="Perfect for understanding your automation potential",
        features=[
            "GHL Setup Review & Optimization",
            "Lead Flow Analysis",
            "ROI Projection Report",
            "30-Minute Strategy Call",
        ],
    ),
    PricingTier(
        name="Jorge Bot Lite",
        price=5000,
        description="Most popular - Get started with AI qualification",
        features=[
            "Custom Lead Qual Bot",
            "GoHighLevel Integration",
            "30 Days Monitoring",
            "Setup & Training Included",
            "Email Support",
        ],
        popular=True,
    ),
    PricingTier(
        name="Jorge Bot Pro",
        price=10000,
        description="Full-featured for scaling teams",
        features=[
            "Lead + Buyer + Seller Bots",
            "Advanced CRM Integration",
            "Custom Prompt Engineering",
            "90 Days Monitoring",
            "Priority Support",
            "BI Dashboard Access",
        ],
    ),
    PricingTier(
        name="Revenue Engine",
        price=15000,
        description="Enterprise-grade AI automation",
        features=[
            "Multi-Agent Swarm",
            "Full BI Dashboard Suite",
            "Dedicated Account Manager",
            "24/7 SLA Support",
            "Custom Integrations",
            "Quarterly Strategy Reviews",
        ],
    ),
]


def calculate_roi(
    monthly_leads: int,
    avg_deal_value: int,
    current_response_time: int,
    conversion_rate: float,
) -> Dict[str, Any]:
    """
    Calculate ROI metrics for implementing Jorge Bot.

    Args:
        monthly_leads: Number of leads per month
        avg_deal_value: Average value of a closed deal
        current_response_time: Current average response time in minutes
        conversion_rate: Current lead-to-deal conversion rate

    Returns:
        Dictionary with calculated ROI metrics
    """
    # Industry benchmarks
    BOT_RESPONSE_TIME = 2  # minutes
    BOT_CONVERSION_LIFT = 0.20  # 20% improvement
    IMPLEMENTATION_COST = 5000  # Lite tier

    # Current metrics
    leads_responded_current = monthly_leads * (1 - (current_response_time / 60))
    current_deals = leads_responded_current * conversion_rate
    current_revenue = current_deals * avg_deal_value

    # With Jorge Bot
    leads_responded_bot = monthly_leads * (1 - (BOT_RESPONSE_TIME / 60))
    new_conversion_rate = conversion_rate * (1 + BOT_CONVERSION_LIFT)
    bot_deals = leads_responded_bot * new_conversion_rate
    bot_revenue = bot_deals * avg_deal_value

    # ROI calculations
    additional_revenue = bot_revenue - current_revenue
    annual_additional_revenue = additional_revenue * 12
    roi_percentage = ((annual_additional_revenue - IMPLEMENTATION_COST) / IMPLEMENTATION_COST) * 100
    payback_months = IMPLEMENTATION_COST / additional_revenue if additional_revenue > 0 else 0

    return {
        "current_revenue": current_revenue,
        "projected_revenue": bot_revenue,
        "additional_revenue": additional_revenue,
        "annual_revenue": annual_additional_revenue,
        "roi_percentage": roi_percentage,
        "payback_months": payback_months,
        "leads_saved": monthly_leads - leads_responded_current,
    }


def render_roi_calculator() -> None:
    """Render the simplified ROI calculator for clients."""
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #1e293b 0%, #334155 100%); 
                padding: 2rem; border-radius: 16px; margin: 2rem 0;">
        <h2 style="color: white; margin-bottom: 1.5rem; text-align: center;">
            💰 Calculate Your ROI
        </h2>
        <p style="color: rgba(255,255,255,0.8); text-align: center; margin-bottom: 2rem;">
            See how much revenue you're leaving on the table with slow response times
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Input columns
    col1, col2, col3 = st.columns(3)

    with col1:
        monthly_leads = st.number_input(
            "Monthly Leads",
            min_value=50,
            max_value=5000,
            value=500,
            step=50,
            help="How many leads do you get per month?",
        )

    with col2:
        avg_deal_value = st.number_input(
            "Avg Deal Value ($)",
            min_value=10000,
            max_value=2000000,
            value=450000,
            step=10000,
            help="Average commission per closed deal",
        )

    with col3:
        current_response_time = st.number_input(
            "Current Response Time (min)",
            min_value=1,
            max_value=240,
            value=45,
            step=5,
            help="How long does it typically take to respond?",
        )

    conversion_rate = st.slider(
        "Current Conversion Rate",
        min_value=0.01,
        max_value=0.50,
        value=0.12,
        step=0.01,
        format="%.0f%%",
        help="What percentage of leads become clients?",
    )

    # Calculate ROI
    metrics = calculate_roi(
        monthly_leads=monthly_leads,
        avg_deal_value=avg_deal_value,
        current_response_time=current_response_time,
        conversion_rate=conversion_rate,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # Display results
    result_col1, result_col2, result_col3, result_col4 = st.columns(4)

    with result_col1:
        st.metric(
            label="Annual Revenue Increase",
            value=f"${metrics['annual_revenue']:,.0f}",
            delta="Projected",
        )

    with result_col2:
        st.metric(
            label="Monthly Revenue Lift",
            value=f"${metrics['additional_revenue']:,.0f}",
        )

    with result_col3:
        st.metric(
            label="ROI",
            value=f"{metrics['roi_percentage']:,.0f}%",
            delta="First year",
        )

    with result_col4:
        st.metric(
            label="Payback Period",
            value=f"{metrics['payback_months']:.1f} months",
            delta="Jorge Bot Lite" if metrics["payback_months"] <= 3 else None,
        )

    # Context note
    st.info(
        f"📊 Based on industry data: Jorge Bot typically improves conversion by 20% and response time from {current_response_time} min to 2 min."
    )


# =============================================================================
# Bot Demo Component
# =============================================================================

# Canned responses for demo (simplified version)
DEMO_RESPONSES = {
    "Lead Bot": {
        "buy": "That's exciting! Let me connect you with our buyer specialist. What's your budget range?",
        "sell": "I'd love to help you sell! Can you tell me about your property and timeline?",
        "hello": "Hi! Welcome to [Your Company]. Are you looking to buy or sell?",
        "default": "Thanks for reaching out! Tell me more about what you're looking for.",
    },
    "Buyer Bot": {
        "pre-approval": "Having pre-approval is great! What amount are you approved for?",
        "budget": "Let's talk budget. What range are you comfortable with?",
        "default": "I can help you find the perfect home. What's most important to you - location, price, or size?",
    },
    "Seller Bot": {
        "worth": "I'll run a CMA for you. What's your property address?",
        "default": "Let's get your home sold! What's the best number to reach you?",
    },
}


def render_bot_demo() -> None:
    """Render an interactive bot demo section."""
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); 
                padding: 2rem; border-radius: 16px; margin: 2rem 0;">
        <h2 style="color: white; margin-bottom: 1rem; text-align: center;">
            🤖 Try the Bot Demo
        </h2>
        <p style="color: rgba(255,255,255,0.7); text-align: center;">
            Select a bot type and send a message to see how it qualifies leads
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # Bot selection
    bot_options = ["Lead Bot", "Buyer Bot", "Seller Bot"]
    selected_bot = st.radio(
        "Select Bot Type:",
        bot_options,
        horizontal=True,
        help="Each bot specializes in different lead types",
    )

    # Demo questions based on bot type
    demo_questions = {
        "Lead Bot": ["I'm looking to buy a home", "I want to sell my house", "Hello!"],
        "Buyer Bot": ["I'm pre-approved for $500K", "What's my budget?", "I need a 3BR"],
        "Seller Bot": ["What's my home worth?", "How do I list?", "When to sell?"],
    }

    # Chat container
    chat_container = st.container()

    with chat_container:
        # Display demo messages
        st.markdown("#### 💬 Sample Conversation")

        # Sample conversation based on bot
        sample_conv = [
            ("visitor", "Hi, I'm interested in buying a home"),
            (selected_bot, "That's great! What's your budget range?"),
            ("visitor", "Around $500K"),
            (selected_bot, "Perfect. Are you pre-approved yet, or would you like help with that?"),
        ]

        for role, message in sample_conv:
            if role == selected_bot:
                st.markdown(
                    f"""
                <div style="background: rgba(99, 102, 241, 0.2); 
                            padding: 1rem; border-radius: 12px; 
                            margin: 0.5rem 0; border-left: 4px solid #6366F1;">
                    <strong style="color: #6366F1;">🤖 {selected_bot}:</strong><br>
                    <span style="color: #e2e8f0;">{message}</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"""
                <div style="background: rgba(255, 255, 255, 0.05); 
                            padding: 1rem; border-radius: 12px; 
                            margin: 0.5rem 0; border-left: 4px solid #10B981;">
                    <strong style="color: #10B981;">👤 You:</strong><br>
                    <span style="color: #e2e8f0;">{message}</span>
                </div>
                """,
                    unsafe_allow_html=True,
                )

        # Quick try buttons
        st.markdown("##### Quick Demo Questions:")
        cols = st.columns(3)
        for i, question in enumerate(demo_questions[selected_bot]):
            with cols[i]:
                st.button(question, key=f"demo_{selected_bot}_{i}", disabled=True)

        st.caption("🔒 Demo mode - Try these phrases to see bot responses")


# =============================================================================
# Main Portfolio Landing Page
# =============================================================================


def render_portfolio_landing() -> None:
    """
    Main entry point for the portfolio landing page.

    This is designed for non-technical clients who want to see:
    1. Business impact (ROI)
    2. Live bot demo
    3. Pricing tiers
    4. Call to action
    """

    # Page config
    if st:
        st.set_page_config(
            page_title="Jorge Bot - AI Lead Qualification",
            page_icon="🏠",
            layout="wide",
        )

    # Custom CSS
    st.markdown(
        """
    <style>
    .main-header {
        background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
        padding: 4rem 2rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 3rem;
    }
    .main-header h1 {
        color: white;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 1rem;
    }
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.4rem;
        max-width: 800px;
        margin: 0 auto;
    }
    .pricing-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        height: 100%;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .pricing-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.15);
    }
    .pricing-card.popular {
        border: 3px solid #6366F1;
        position: relative;
    }
    .pricing-card.popular::before {
        content: 'Most Popular';
        position: absolute;
        top: -12px;
        left: 50%;
        transform: translateX(-50%);
        background: #6366F1;
        color: white;
        padding: 4px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
    }
    .price-tag {
        font-size: 2.5rem;
        font-weight: 800;
        color: #1e293b;
        margin: 1rem 0;
    }
    .price-label {
        color: #64748b;
        font-size: 1rem;
    }
    .feature-list {
        text-align: left;
        margin: 1.5rem 0;
    }
    .feature-list li {
        color: #475569;
        margin: 0.5rem 0;
    }
    .cta-button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 12px;
        font-weight: 700;
        text-decoration: none;
        display: inline-block;
        width: 100%;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # =====================================================================
    # Hero Section
    # =====================================================================
    st.markdown(
        """
    <div class="main-header">
        <h1>🤖 Jorge Bot</h1>
        <h2 style="color: #6366F1; font-size: 2rem; margin-bottom: 1rem;">
            AI-Powered Lead Qualification for Real Estate
        </h2>
        <p>
            Convert more leads while you sleep. Jorge Bot qualifies prospects 24/7,
            integrates with your CRM, and delivers ready-to-close clients to your team.
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # =====================================================================
    # Key Benefits (Business Impact First)
    # =====================================================================
    st.markdown("## 📈 Business Impact")

    benefit_col1, benefit_col2, benefit_col3, benefit_col4 = st.columns(4)

    with benefit_col1:
        st.markdown(
            """
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">⚡</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10B981;">95%</div>
            <div style="color: #64748b;">Faster Response</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with benefit_col2:
        st.markdown(
            """
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">💰</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10B981;">89%</div>
            <div style="color: #64748b;">Cost Reduction</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with benefit_col3:
        st.markdown(
            """
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📈</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10B981;">133%</div>
            <div style="color: #64748b;">Conversion Increase</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with benefit_col4:
        st.markdown(
            """
        <div style="text-align: center; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08);">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🎯</div>
            <div style="font-size: 2rem; font-weight: 800; color: #10B981;">92%</div>
            <div style="color: #64748b;">Lead Score Accuracy</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # =====================================================================
    # ROI Calculator
    # =====================================================================
    render_roi_calculator()

    st.markdown("---")

    # =====================================================================
    # Bot Demo
    # =====================================================================
    render_bot_demo()

    st.markdown("---")

    # =====================================================================
    # Pricing Section
    # =====================================================================
    st.markdown("## 💼 Investment Options")

    pricing_cols = st.columns(4)

    for i, tier in enumerate(PRICING_TIERS):
        with pricing_cols[i]:
            popular_class = "popular" if tier.popular else ""
            st.markdown(
                f"""
            <div class="pricing-card {popular_class}">
                <div class="price-label">{tier.name}</div>
                <div class="price-tag">${tier.price:,}</div>
                <div style="color: #64748b; margin-bottom: 1rem;">{tier.description}</div>
                <ul class="feature-list">
            """,
                unsafe_allow_html=True,
            )

            for feature in tier.features:
                st.markdown(f"<li>✅ {feature}</li>", unsafe_allow_html=True)

            st.markdown(
                """
                </ul>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # =====================================================================
    # Call to Action
    # =====================================================================
    st.markdown(
        """
    <div style="background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); 
                padding: 3rem; border-radius: 20px; text-align: center; margin: 2rem 0;">
        <h2 style="color: white; margin-bottom: 1rem;">Ready to Stop Losing Leads?</h2>
        <p style="color: rgba(255,255,255,0.9); font-size: 1.2rem; margin-bottom: 2rem;">
            Book a free 30-minute strategy call to see how Jorge Bot can transform your business.
        </p>
        <a href="https://calendly.com/caymanroden/discovery-call" 
           class="cta-button" 
           target="_blank">
            📅 Book Your Free Strategy Call
        </a>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # =====================================================================
    # Footer
    # =====================================================================
    st.markdown("---")
    st.markdown(
        """
    <div style="text-align: center; padding: 2rem; color: #64748b;">
        <p>🏠 Jorge Bot by EnterpriseHub | Real Estate AI Solutions</p>
        <p style="font-size: 0.9rem;">
            Serving Rancho Cucamonga & Southern California
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Standalone Entry Point
# =============================================================================

if __name__ == "__main__":
    if st:
        render_portfolio_landing()
    else:
        print("Streamlit not available. Run with: streamlit run portfolio_landing.py")
