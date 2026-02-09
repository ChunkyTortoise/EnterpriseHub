"""Page configuration - must be imported and called before any other Streamlit commands."""

import os
import warnings

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

DEMO_MODE = os.getenv("DEMO_MODE", "").lower() in ("true", "1")

# Import async utilities for safe event loop handling
try:
    from ghl_real_estate_ai.streamlit_demo.async_utils import run_async

    ASYNC_UTILS_AVAILABLE = True
except ImportError:
    ASYNC_UTILS_AVAILABLE = False
    run_async = None


def configure_page():
    """Set Streamlit page config. MUST be the first Streamlit call in the app."""
    st.set_page_config(
        page_title="Lyrio Union[AI, Obsidian] Command",
        page_icon="https://raw.githubusercontent.com/ChunkyTortoise/EnterpriseHub/main/assets/favicon.png",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={"About": "Lyrio AI - Obsidian Union[Edition, Premium] Real Estate Intelligence"},
    )
    # Suppress all warnings for professional demo presentation
    warnings.filterwarnings("ignore")
