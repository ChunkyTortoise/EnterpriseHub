"""Interactive chatbot demo widget for Streamlit BI dashboard.

Provides a conversational UI with canned demo responses and optional
live-mode integration with the real Jorge bot backends.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Streamlit is optional at import time so the module can be tested
# without a running Streamlit server.
try:
    import streamlit as st
except ModuleNotFoundError:  # pragma: no cover
    st = None  # type: ignore[assignment]


# ------------------------------------------------------------------
# Bot type definitions
# ------------------------------------------------------------------

BOT_TYPES: list[str] = ["Lead Bot", "Buyer Bot", "Seller Bot"]

# ------------------------------------------------------------------
# Canned responses keyed by (bot_type, trigger_substring)
# ------------------------------------------------------------------

CANNED_RESPONSES: dict[str, dict[str, str]] = {
    "Lead Bot": {
        "looking to buy": (
            "That's great to hear! I'd love to help you find your dream home "
            "in Rancho Cucamonga. Could you tell me a bit about your budget "
            "and what you're looking for in a property?"
        ),
        "sell my house": (
            "I can definitely help with that! Let me connect you with our "
            "seller specialist who can provide a Comparative Market Analysis "
            "for your property."
        ),
        "hello": (
            "Welcome! I'm Jorge, your real estate AI assistant. Are you "
            "interested in buying, selling, or just exploring the Rancho "
            "Cucamonga market?"
        ),
        "price": (
            "Home prices in Rancho Cucamonga vary by neighborhood. The "
            "median price is around $650K. Would you like me to look up "
            "specific areas?"
        ),
    },
    "Buyer Bot": {
        "pre-approved": (
            "Having a pre-approval is a huge advantage in today's market! "
            "What's your approved amount? That'll help me find properties "
            "in the right range."
        ),
        "budget": (
            "Understanding your budget is the first step. Would you like me "
            "to run an affordability analysis based on your income and "
            "down payment?"
        ),
        "schools": (
            "Great question! Rancho Cucamonga has several highly-rated "
            "school districts. The Etiwanda and Alta Loma areas are "
            "especially popular with families."
        ),
        "looking to buy": (
            "Welcome! I specialize in helping buyers navigate the Rancho "
            "Cucamonga market. Do you have a pre-approval yet, or would "
            "you like to start with affordability?"
        ),
    },
    "Seller Bot": {
        "home worth": (
            "I can help with that! To give you an accurate estimate, I'll "
            "need your property address. I'll run a CMA (Comparative Market "
            "Analysis) using recent sales in your area."
        ),
        "cma": (
            "A CMA compares your home to similar recently-sold properties. "
            "It's the most accurate way to determine listing price. Shall "
            "I prepare one for you?"
        ),
        "listing": (
            "When it comes to listing, timing and pricing strategy are key. "
            "The current market in Rancho Cucamonga favors sellers in most "
            "neighborhoods. Would you like a detailed market report?"
        ),
        "sell my house": (
            "I'd be happy to help you sell! Let's start by understanding "
            "your property and your timeline. When are you hoping to have "
            "the sale completed?"
        ),
    },
}

DEFAULT_RESPONSE = (
    "Thanks for your message! Could you tell me more about what "
    "you're looking for? I can help with buying, selling, or general "
    "real estate questions in the Rancho Cucamonga area."
)

# ------------------------------------------------------------------
# Preset demo questions
# ------------------------------------------------------------------

DEMO_QUESTIONS: dict[str, list[str]] = {
    "Lead Bot": [
        "I'm looking to buy a home",
        "I want to sell my house",
        "What are home prices like?",
        "Hello!",
    ],
    "Buyer Bot": [
        "I'm looking to buy a home",
        "I'm pre-approved for $500K",
        "What's my budget look like?",
        "How are the schools?",
    ],
    "Seller Bot": [
        "What's my home worth?",
        "Can you run a CMA?",
        "I want to sell my house",
        "How do I list my property?",
    ],
}


# ------------------------------------------------------------------
# Helper functions (testable without Streamlit)
# ------------------------------------------------------------------


def get_canned_response(bot_type: str, user_message: str) -> str:
    """Return a canned response matching the first trigger found.

    Args:
        bot_type: One of BOT_TYPES.
        user_message: The user's input text.

    Returns:
        Matching canned response or DEFAULT_RESPONSE.
    """
    triggers = CANNED_RESPONSES.get(bot_type, {})
    lower_msg = user_message.lower()
    for trigger, response in triggers.items():
        if trigger in lower_msg:
            return response
    return DEFAULT_RESPONSE


def get_demo_questions(bot_type: str) -> list[str]:
    """Return preset demo questions for the given bot type."""
    return DEMO_QUESTIONS.get(bot_type, DEMO_QUESTIONS["Lead Bot"])


def init_session_state(session: dict[str, Any]) -> dict[str, Any]:
    """Initialise session-state keys if missing.

    Works with a plain dict (for testing) or st.session_state.

    Returns the session dict for convenience.
    """
    if "chatbot_messages" not in session:
        session["chatbot_messages"] = []
    if "chatbot_bot_type" not in session:
        session["chatbot_bot_type"] = BOT_TYPES[0]
    if "chatbot_live_mode" not in session:
        session["chatbot_live_mode"] = False
    return session


def add_message(
    session: dict[str, Any],
    role: str,
    content: str,
) -> None:
    """Append a message to the session history."""
    init_session_state(session)
    session["chatbot_messages"].append({"role": role, "content": content})


def clear_messages(session: dict[str, Any]) -> None:
    """Clear the message history."""
    session["chatbot_messages"] = []


# ------------------------------------------------------------------
# Streamlit widget
# ------------------------------------------------------------------


@dataclass
class InteractiveChatbotDemo:
    """Interactive chatbot demo component for Streamlit dashboards.

    Attributes:
        live_mode: When True, would route to the real bot backend
                   (not implemented in demo).
    """

    live_mode: bool = False
    _session: dict[str, Any] = field(default_factory=dict)

    def render(self) -> None:  # pragma: no cover — requires Streamlit runtime
        """Render the chatbot widget inside a Streamlit app."""
        if st is None:
            raise RuntimeError("Streamlit is not installed")

        # Use Streamlit's session_state as our backing store
        self._session = st.session_state  # type: ignore[assignment]
        init_session_state(self._session)

        # ---- Sidebar controls ----
        with st.sidebar:
            st.subheader("Chatbot Settings")
            bot_type = st.selectbox(
                "Select Bot",
                BOT_TYPES,
                index=BOT_TYPES.index(
                    self._session.get("chatbot_bot_type", BOT_TYPES[0])
                ),
                key="chatbot_bot_selector",
            )
            if bot_type != self._session["chatbot_bot_type"]:
                self._session["chatbot_bot_type"] = bot_type
                clear_messages(self._session)

            st.markdown("**Quick questions:**")
            for q in get_demo_questions(bot_type):
                if st.button(q, key=f"demo_q_{q}"):
                    self._handle_user_input(q)
                    st.rerun()

            if st.button("Clear conversation"):
                clear_messages(self._session)
                st.rerun()

        # ---- Main chat area ----
        st.subheader(f"Chat with {self._session['chatbot_bot_type']}")

        for msg in self._session["chatbot_messages"]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Type your message...")
        if user_input:
            self._handle_user_input(user_input)
            st.rerun()

    def _handle_user_input(self, text: str) -> None:
        """Process user input: add to history and generate response."""
        add_message(self._session, "user", text)
        bot_type = self._session.get("chatbot_bot_type", BOT_TYPES[0])

        if self.live_mode:
            # In live mode we would call the real bot backend here.
            # For now, fall back to canned responses.
            response = get_canned_response(bot_type, text)
        else:
            response = get_canned_response(bot_type, text)

        add_message(self._session, "assistant", response)
