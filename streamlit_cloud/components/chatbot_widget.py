"""Interactive chatbot widget for Streamlit Cloud demo.

Provides a reusable chat interface with live lead qualification scoring.
Works without any external dependencies (no DB, Redis, or API keys) --
all responses are mock data, and scoring is keyword-driven.

Author: Claude Code Assistant
Created: 2026-02-08
"""

from __future__ import annotations

from dataclasses import dataclass

import streamlit as st


@dataclass
class QualificationScores:
    """Live qualification scores displayed in sidebar."""

    temperature: str = "Cold"
    lead_score: int = 0
    urgency: float = 0.0
    motivation: float = 0.0
    financial_readiness: float = 0.0
    engagement_level: float = 0.0

    @property
    def temperature_color(self) -> str:
        colors = {"Hot": "#FF4B4B", "Warm": "#FFA500", "Cold": "#4B9CD3"}
        return colors.get(self.temperature, "#4B9CD3")

    @property
    def temperature_emoji(self) -> str:
        emojis = {"Hot": "\U0001f525", "Warm": "\U0001f321\ufe0f", "Cold": "\u2744\ufe0f"}
        return emojis.get(self.temperature, "\u2744\ufe0f")


# Mock response templates by bot type and industry
MOCK_RESPONSES: dict[str, dict[str, list[str]]] = {
    "real_estate": {
        "lead": [
            "Welcome! I'm Jorge, your real estate assistant for Rancho Cucamonga. What brings you to our market today?",
            "Great question! The Rancho Cucamonga market is showing strong activity. The median home price is around $650K. Are you looking to buy or sell?",
            "I'd love to help you explore options. Do you have a specific budget range in mind?",
            "That's a solid budget for this market. I can help you find properties that match. Would you like to schedule a showing?",
        ],
        "buyer": [
            "I see you're interested in buying! Let me help narrow down your search. What's your pre-approval amount?",
            "Excellent! With that budget, you have great options in the Victoria Gardens and Terra Vista areas. What size home are you looking for?",
            "Perfect. I'll compile a curated list of properties matching your criteria. Want me to set up alerts for new listings?",
        ],
        "seller": [
            "Thinking about selling? Great timing! The Rancho Cucamonga market favors sellers right now. When are you looking to list?",
            "I can prepare a Comparative Market Analysis (CMA) for your property. What's your property address?",
            "Based on recent comparable sales, properties in your area are selling within 15-30 days. Would you like a detailed pricing strategy?",
        ],
    },
    "dental": {
        "lead": [
            "Welcome to Bright Smile Dental! I'm here to help you with your dental care needs. What service are you interested in?",
            "We offer comprehensive dental services including cleanings, whitening, and cosmetic procedures. Do you have dental insurance?",
            "I can help you schedule a consultation. What days and times work best for you?",
        ],
        "buyer": [],
        "seller": [],
    },
    "hvac": {
        "lead": [
            "Welcome to ComfortAir HVAC! How can I help you today? Are you looking for installation, repair, or maintenance?",
            "I understand. We offer 24/7 emergency service and free estimates on new installations. What type of system do you currently have?",
            "Great, I can get a technician scheduled for you. What's a convenient time for a home visit?",
        ],
        "buyer": [],
        "seller": [],
    },
}

# Keywords that trigger qualification score changes
SCORE_TRIGGERS: dict[str, list[str]] = {
    "hot_keywords": [
        "pre-approved",
        "ready to buy",
        "this week",
        "cash buyer",
        "schedule",
        "showing",
        "urgent",
        "immediately",
        "offer",
    ],
    "warm_keywords": [
        "budget",
        "looking",
        "interested",
        "timeline",
        "months",
        "planning",
        "considering",
        "comparing",
    ],
    "financial_keywords": [
        "pre-approval",
        "mortgage",
        "budget",
        "down payment",
        "financing",
        "loan",
        "afford",
        "credit",
    ],
    "urgency_keywords": [
        "asap",
        "urgent",
        "this week",
        "today",
        "immediately",
        "relocating",
        "deadline",
    ],
    "motivation_keywords": [
        "growing family",
        "downsizing",
        "relocating",
        "investment",
        "dream home",
        "first home",
    ],
}


class ChatbotWidget:
    """Interactive chatbot demo with live qualification scoring.

    Usage::

        widget = ChatbotWidget(industry="real_estate")
        widget.render()  # renders chat + sidebar scores
    """

    def __init__(self, industry: str = "real_estate") -> None:
        self.industry = industry
        self._init_session_state()

    def _init_session_state(self) -> None:
        """Initialize Streamlit session state with defaults."""
        if "messages" not in st.session_state:
            st.session_state["messages"] = []
        if "bot_type" not in st.session_state:
            st.session_state["bot_type"] = "lead"
        if "scores" not in st.session_state:
            st.session_state["scores"] = QualificationScores()
        if "message_count" not in st.session_state:
            st.session_state["message_count"] = 0
        if "industry" not in st.session_state:
            st.session_state["industry"] = self.industry

    def _update_scores(self, user_message: str) -> None:
        """Update qualification scores based on user message keywords."""
        msg_lower = user_message.lower()
        scores: QualificationScores = st.session_state["scores"]

        # Count keyword matches per category
        hot_matches = sum(
            1 for kw in SCORE_TRIGGERS["hot_keywords"] if kw in msg_lower
        )
        warm_matches = sum(
            1 for kw in SCORE_TRIGGERS["warm_keywords"] if kw in msg_lower
        )
        financial_matches = sum(
            1 for kw in SCORE_TRIGGERS["financial_keywords"] if kw in msg_lower
        )
        urgency_matches = sum(
            1 for kw in SCORE_TRIGGERS["urgency_keywords"] if kw in msg_lower
        )
        motivation_matches = sum(
            1 for kw in SCORE_TRIGGERS["motivation_keywords"] if kw in msg_lower
        )

        # Update scores (capped at 100 for lead_score, 1.0 for floats)
        if hot_matches:
            scores.lead_score = min(100, scores.lead_score + hot_matches * 15)
        if warm_matches:
            scores.lead_score = min(100, scores.lead_score + warm_matches * 8)

        scores.financial_readiness = min(
            1.0, scores.financial_readiness + financial_matches * 0.25
        )
        scores.urgency = min(1.0, scores.urgency + urgency_matches * 0.3)
        scores.motivation = min(1.0, scores.motivation + motivation_matches * 0.25)
        scores.engagement_level = min(
            1.0, 0.1 * st.session_state["message_count"]
        )

        # Update temperature based on lead score
        if scores.lead_score >= 80:
            scores.temperature = "Hot"
        elif scores.lead_score >= 40:
            scores.temperature = "Warm"
        else:
            scores.temperature = "Cold"

        # Detect bot type handoff signals
        buyer_signals = ["buy", "purchase", "pre-approval", "mortgage", "budget"]
        seller_signals = ["sell", "list", "cma", "home worth", "market value"]
        if any(s in msg_lower for s in buyer_signals):
            st.session_state["bot_type"] = "buyer"
        elif any(s in msg_lower for s in seller_signals):
            st.session_state["bot_type"] = "seller"

    def _get_mock_response(self) -> str:
        """Get a mock bot response based on industry and bot type."""
        industry = st.session_state.get("industry", self.industry)
        bot_type: str = st.session_state["bot_type"]
        responses = MOCK_RESPONSES.get(industry, MOCK_RESPONSES["real_estate"])
        bot_responses = responses.get(bot_type, responses["lead"])
        if not bot_responses:
            bot_responses = responses["lead"]
        idx = min(st.session_state["message_count"], len(bot_responses) - 1)
        return bot_responses[idx]

    def render_sidebar(self) -> None:
        """Render qualification scores in sidebar."""
        scores: QualificationScores = st.session_state["scores"]
        st.sidebar.markdown("---")
        st.sidebar.markdown("### \U0001f4ca Live Qualification Scores")

        # Temperature badge
        st.sidebar.markdown(
            f"**Temperature:** <span style='color:{scores.temperature_color};"
            f"font-size:1.3em'>{scores.temperature_emoji} "
            f"{scores.temperature}</span>",
            unsafe_allow_html=True,
        )

        # Lead score with progress bar
        st.sidebar.metric("Lead Score", f"{scores.lead_score}/100")
        st.sidebar.progress(scores.lead_score / 100)

        # Individual metrics in two-column layout
        col1, col2 = st.sidebar.columns(2)
        col1.metric("Urgency", f"{scores.urgency:.0%}")
        col2.metric("Motivation", f"{scores.motivation:.0%}")

        col3, col4 = st.sidebar.columns(2)
        col3.metric("Financial", f"{scores.financial_readiness:.0%}")
        col4.metric("Engagement", f"{scores.engagement_level:.0%}")

        # Active bot indicator
        bot_labels = {
            "lead": "\U0001f3af Lead Bot",
            "buyer": "\U0001f3e0 Buyer Bot",
            "seller": "\U0001f4b0 Seller Bot",
        }
        st.sidebar.markdown(
            f"**Active Bot:** "
            f"{bot_labels.get(st.session_state['bot_type'], '\U0001f3af Lead Bot')}"
        )

    def render_chat(self) -> None:
        """Render the chat interface."""
        # Display message history
        for msg in st.session_state["messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Chat input
        if prompt := st.chat_input("Type your message..."):
            # Add user message
            st.session_state["messages"].append(
                {"role": "user", "content": prompt}
            )
            st.session_state["message_count"] += 1

            # Update qualification scores
            self._update_scores(prompt)

            # Display user message
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get and display bot response
            response = self._get_mock_response()
            st.session_state["messages"].append(
                {"role": "assistant", "content": response}
            )
            with st.chat_message("assistant"):
                st.markdown(response)

    def render(self) -> None:
        """Render the complete widget (chat + sidebar scores)."""
        self.render_sidebar()
        self.render_chat()

    def reset(self) -> None:
        """Reset chat state to defaults."""
        st.session_state["messages"] = []
        st.session_state["bot_type"] = "lead"
        st.session_state["scores"] = QualificationScores()
        st.session_state["message_count"] = 0
