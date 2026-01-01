"""
Content Engine - AI-Powered LinkedIn Post Generator.

Generates professional LinkedIn content using Claude AI with customizable
templates, tones, and target audiences.
"""

import io
import os
import time
import zipfile
from collections import Counter
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import utils.ui as ui
from utils.logger import get_logger

# Conditional import for Claude API
try:
    from anthropic import (
        Anthropic,
        APIConnectionError,
        APIError,
        APITimeoutError,
        RateLimitError,
    )

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)


def _display_demo_posts() -> None:
    """Display demo generated posts from pre-loaded JSON file."""
    import json
    
    # Load demo data
    demo_file = "data/demo_content_posts.json"
    try:
        with open(demo_file, 'r') as f:
            demo_data = json.load(f)
    except FileNotFoundError:
        st.error(f"Demo data file not found: {demo_file}")
        return
    
    posts = demo_data.get("generated_posts", [])
    analytics = demo_data.get("analytics_summary", {})
    
    # Display analytics summary
    st.markdown("---")
    st.subheader("📊 Content Performance Analytics")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Posts", analytics.get("total_posts", 0))
    with col2:
        st.metric("Avg Engagement", f"{analytics.get('average_engagement_score', 0):.1f}/10")
    with col3:
        st.metric("Total Reach", f"{analytics.get('total_estimated_reach', 0):,}")
    with col4:
        st.metric("Total Impressions", f"{analytics.get('total_estimated_impressions', 0):,}")
    
    st.caption(f"🕐 Optimal Posting Schedule: {analytics.get('optimal_posting_schedule', 'N/A')}")
    
    # Display each post
    st.markdown("---")
    st.subheader("📝 Generated LinkedIn Posts")
    
    for post in posts:
        with st.expander(f"📄 {post['title']}", expanded=(post['id'] == 1)):
            # Post content
            st.markdown("#### Content:")
            st.markdown(post['content'])
            
            st.markdown("---")
            
            # Metrics
            st.markdown("#### Performance Metrics:")
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            
            with metric_col1:
                st.metric("Engagement Score", f"{post['engagement_score']}/10")
                st.metric("Estimated Reach", f"{post['estimated_reach']:,}")
            
            with metric_col2:
                st.metric("Estimated Impressions", f"{post['estimated_impressions']:,}")
                st.metric("Likes", post['likes'])
            
            with metric_col3:
                st.metric("Comments", post['comments'])
                st.metric("Shares", post['shares'])
            
            st.markdown("---")
            
            # Post details
            st.markdown("#### Post Details:")
            st.markdown(f"**Target Audience:** {post['target_audience']}")
            st.markdown(f"**Best Time to Post:** {post['best_time_to_post']}")
            st.markdown(f"**Hashtags:** {', '.join(post['hashtags'])}")
            
            if post.get('call_to_action'):
                st.info(f"💬 **Call to Action:** {post['call_to_action']}")
            
            # Copy button
            st.markdown("---")
            if st.button(f"📋 Copy Post {post['id']} to Clipboard", key=f"copy_{post['id']}"):
                st.code(post['content'], language=None)
                st.success("✅ Content displayed above - copy manually")
    
    # Insights
    st.markdown("---")
    st.subheader("💡 Content Strategy Insights")
    
    st.markdown(f"""
    **Key Findings:**
    - Best performing post: Post #{analytics.get('best_performing_post_id', 1)} with {posts[0]['engagement_score']}/10 engagement
    - Average engagement across all posts: {analytics.get('average_engagement_score', 0):.1f}/10
    - Total potential reach: {analytics.get('total_estimated_reach', 0):,} professionals
    
    **Recommendations:**
    - Post during: {analytics.get('optimal_posting_schedule', 'Peak hours')}
    - Focus on: ROI metrics, technical deep dives, and thought leadership
    - Include: Quantifiable results, before/after comparisons, and clear CTAs
    """)


# Constants
DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
DEFAULT_MAX_TOKENS = 1024
MAX_RETRY_ATTEMPTS = 3
INITIAL_RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF_FACTOR = 2.0
API_TIMEOUT = 30.0  # seconds
LINKEDIN_CHAR_LIMIT = 3000
OPTIMAL_POST_MIN_WORDS = 150
OPTIMAL_POST_MAX_WORDS = 250
MIN_HASHTAGS = 3
MAX_HASHTAGS = 5

# Platform-specific specifications
PLATFORM_SPECS = {
    "LinkedIn": {
        "char_limit": 3000,
        "optimal_length": (150, 250),  # words
        "hashtag_range": (3, 5),
        "emoji_style": "professional",
        "formatting": "paragraphs_with_breaks",
        "link_style": "inline",
    },
    "Twitter/X": {
        "char_limit": 280,
        "optimal_length": (30, 50),  # words
        "hashtag_range": (1, 3),
        "emoji_style": "casual",
        "formatting": "single_paragraph",
        "link_style": "shortened",
        "thread_mode": True,
        "thread_tweet_limit": 280,
    },
    "Instagram": {
        "char_limit": 2200,
        "optimal_length": (100, 150),  # words
        "hashtag_range": (5, 10),
        "emoji_style": "expressive",
        "formatting": "caption_with_breaks",
        "link_style": "bio_link",
    },
    "Facebook": {
        "char_limit": 63206,
        "optimal_length": (100, 200),  # words
        "hashtag_range": (0, 3),
        "emoji_style": "friendly",
        "formatting": "paragraphs",
        "link_style": "inline",
    },
    "Email Newsletter": {
        "char_limit": None,
        "optimal_length": (300, 500),  # words
        "subject_line_limit": 60,
        "preheader_limit": 100,
        "formatting": "html_email",
        "link_style": "call_to_action_buttons",
    },
}

# A/B Testing Variant Strategies
AB_TEST_STRATEGIES = {
    "Variant A": {
        "hook_type": "question",
        "hook_examples": ["Have you ever wondered...", "What if...", "Did you know..."],
        "cta_type": "comment",
        "cta_examples": [
            "Share your thoughts below!",
            "What's your experience?",
            "Let me know in the comments!",
        ],
        "format_style": "short_paragraphs",
        "emoji_density": "low",
    },
    "Variant B": {
        "hook_type": "statistic",
        "hook_examples": ["X% of professionals...", "Research shows...", "According to data..."],
        "cta_type": "share",
        "cta_examples": [
            "Share this with your network!",
            "Tag someone who needs this!",
            "Pass this along!",
        ],
        "format_style": "bullet_points",
        "emoji_density": "medium",
    },
    "Variant C": {
        "hook_type": "story",
        "hook_examples": ["Last week, I...", "Here's what happened...", "Let me tell you about..."],
        "cta_type": "link_click",
        "cta_examples": [
            "Learn more in the link!",
            "Check out the full story!",
            "Read the details here!",
        ],
        "format_style": "narrative_flow",
        "emoji_density": "high",
    },
}

# LinkedIn Post Templates
TEMPLATES = {
    "Professional Insight": {
        "description": "Share industry insights with professional tone",
        "prompt_prefix": "Write a professional LinkedIn post sharing an industry insight about",
        "style": "Professional, informative, authoritative",
    },
    "Thought Leadership": {
        "description": "Position yourself as a thought leader",
        "prompt_prefix": "Write a thought-leadership LinkedIn post discussing",
        "style": "Visionary, forward-thinking, inspiring",
    },
    "Case Study": {
        "description": "Share a success story or case study",
        "prompt_prefix": "Write a LinkedIn post presenting a case study about",
        "style": "Story-driven, results-focused, credible",
    },
    "How-To Guide": {
        "description": "Educational content with actionable tips",
        "prompt_prefix": "Write a how-to LinkedIn post teaching professionals about",
        "style": "Educational, practical, step-by-step",
    },
    "Industry Trend": {
        "description": "Analyze current trends and predictions",
        "prompt_prefix": "Write a LinkedIn post analyzing current trends in",
        "style": "Analytical, data-informed, forward-looking",
    },
    "Personal Story": {
        "description": "Share personal experience and lessons learned",
        "prompt_prefix": "Write a personal LinkedIn post sharing a story about",
        "style": "Authentic, relatable, reflective",
    },
}

TONES = {
    "Professional": "Maintain a formal, business-appropriate tone",
    "Casual": "Use a conversational, friendly tone",
    "Inspirational": "Be motivating and uplifting",
    "Analytical": "Be data-driven and logical",
    "Storytelling": "Use narrative structure and emotional connection",
}


def retry_with_exponential_backoff(
    max_attempts: int = MAX_RETRY_ATTEMPTS,
    initial_delay: float = INITIAL_RETRY_DELAY,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
) -> Callable:
    """
    Decorator to retry a function with exponential backoff on failure.

    This decorator will retry API calls that fail due to rate limiting,
    connection errors, or temporary failures. It uses exponential backoff
    to progressively increase the delay between retry attempts.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        backoff_factor: Multiplier for delay after each retry (default: 2.0)

    Returns:
        Decorated function with retry logic

    Example:
        @retry_with_exponential_backoff(max_attempts=3, initial_delay=1.0)
        def make_api_call():
            # API call logic
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    last_exception = e
                    logger.warning(
                        f"Rate limit hit on attempt {attempt}/{max_attempts}. "
                        f"Retrying in {delay:.1f}s... Error: {str(e)}"
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"Rate limit exceeded after {max_attempts} attempts")
                        raise
                except (APIConnectionError, APITimeoutError) as e:
                    last_exception = e
                    logger.warning(
                        f"Connection/timeout error on attempt {attempt}/{max_attempts}. "
                        f"Retrying in {delay:.1f}s... Error: {str(e)}"
                    )
                    if attempt < max_attempts:
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(f"Connection failed after {max_attempts} attempts")
                        raise
                except APIError as e:
                    # Don't retry on other API errors (e.g., invalid API key, bad request)
                    logger.error(f"Non-retryable API error: {str(e)}")
                    raise
                except Exception as e:
                    # Unexpected errors should not be retried
                    logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
                    raise

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def render() -> None:
    """Render the Content Engine module."""
    ui.section_header("Content Engine", "AI-Powered LinkedIn Post Generator")

    # Demo Mode Toggle
    demo_mode = st.checkbox(
        "🎯 Demo Mode (View Sample Posts)",
        value=True,
        help="Toggle to view pre-generated sample LinkedIn posts without API calls"
    )
    
    if demo_mode:
        _display_demo_posts()
        return

    if not ANTHROPIC_AVAILABLE:
        st.error("⚠️ Anthropic package not installed. Run: `pip install anthropic`")
        return

    try:
        # Check for API key
        api_key = _get_api_key()

        if not api_key:
            _render_api_key_setup()
            return

        # Main 4-Panel Layout
        _render_four_panel_interface(api_key)

    except Exception as e:
        logger.error(f"An unexpected error occurred in Content Engine: {e}", exc_info=True)
        st.error("An unexpected error occurred.")
        if st.checkbox("Show error details", key="ce_error_details"):
            st.exception(e)


def _get_api_key() -> Optional[str]:
    """
    Get Anthropic API key from environment or session state.

    Retrieves the API key with the following priority:
    1. ANTHROPIC_API_KEY environment variable
    2. Session state (anthropic_api_key)

    Returns:
        API key string if found, None otherwise

    Note:
        The API key is validated for basic format (starts with 'sk-ant-')
        but not for actual validity with the API.
    """
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if api_key:
        logger.debug("API key found in environment variable")
        if not api_key.startswith("sk-ant-"):
            logger.warning("API key format appears invalid (should start with 'sk-ant-')")
        return api_key

    # Check session state
    if "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key
        if api_key:
            logger.debug("API key found in session state")
            if not api_key.startswith("sk-ant-"):
                logger.warning("API key format appears invalid (should start with 'sk-ant-')")
            return api_key

    logger.warning("No API key found in environment or session state")
    return None


def _render_api_key_setup() -> None:
    """
    Render API key setup interface.

    Displays a form for users to enter their Anthropic API key.
    The key is stored in session state only and not persisted to disk.

    Side effects:
        - Updates st.session_state.anthropic_api_key on form submission
        - Triggers page rerun after successful key submission
    """
    logger.info("Rendering API key setup interface")
    st.warning("🔑 **API Key Required**")
    st.markdown(
        """
    To use the Content Engine, you need an Anthropic API key:

    1. Get your free API key at [console.anthropic.com](https://console.anthropic.com/)
    2. Free tier includes $5 credit (≈ 1,000 LinkedIn posts)
    3. Enter your API key below (stored in session only, not saved)
    """
    )

    with st.form("api_key_form"):
        api_key_input = st.text_input(
            "Anthropic API Key", type="password", placeholder="sk-ant-..."
        )
        submitted = st.form_submit_button("Save API Key")

        if submitted and api_key_input:
            if not api_key_input.startswith("sk-ant-"):
                logger.warning("User entered API key with unexpected format")
                st.error("⚠️ Warning: API key should start with 'sk-ant-'. Please verify your key.")
            else:
                logger.info("Valid API key format submitted")
            st.session_state.anthropic_api_key = api_key_input
            st.success("✅ API key saved! Reload the page.")
            st.rerun()


def _render_four_panel_interface(api_key: str) -> None:
    """
    Render the main 4-panel interface: Input → Template → Generate → Export.

    Creates an interactive UI with four sequential panels:
    1. Input panel: Topic, tone, audience, and keywords
    2. Template panel: Selection of LinkedIn post templates
    3. Generate panel: Trigger content generation
    4. Export panel: Preview and download generated content

    Args:
        api_key: Valid Anthropic API key for content generation

    Side effects:
        - Updates st.session_state.generated_post with generated content
        - Updates st.session_state.selected_template with template choice
        - Displays Streamlit UI components
    """
    logger.debug("Rendering four-panel interface")

    # Initialize session state for generated content
    if "generated_post" not in st.session_state:
        st.session_state.generated_post = None
    if "adapted_variants" not in st.session_state:
        st.session_state.adapted_variants = None
    if "content_history" not in st.session_state:
        st.session_state.content_history = []
    if "analytics_enabled" not in st.session_state:
        st.session_state.analytics_enabled = True
    if "ab_test_variants" not in st.session_state:
        st.session_state.ab_test_variants = None

    # Panel 1: Input
    st.markdown("---")
    st.subheader("📝 Panel 1: Input Your Content Brief")

    col1, col2 = st.columns([2, 1])

    with col1:
        topic = st.text_area(
            "What do you want to write about?",
            placeholder="Example: The impact of AI on software development workflows",
            height=100,
            key="topic_input",
        )

    with col2:
        tone = st.selectbox(
            "Tone",
            options=list(TONES.keys()),
            help="Select the overall tone for your post",
        )

        target_audience = st.text_input(
            "Target Audience (optional)", placeholder="e.g., Software engineers, CTOs"
        )

    # Platform Selection
    platform = st.selectbox(
        "Target Platform",
        options=list(PLATFORM_SPECS.keys()),
        index=0,  # Default to LinkedIn
        help="Select the social media platform for optimized formatting",
    )

    # Show platform specs
    specs = PLATFORM_SPECS[platform]
    char_limit_text = f"{specs['char_limit']:,}" if specs["char_limit"] else "No limit"
    st.caption(
        f"📱 {platform} specs: {char_limit_text} char limit | "
        f"{specs['hashtag_range'][0]}-{specs['hashtag_range'][1]} hashtags | "
        f"{specs['emoji_style']} emoji style"
    )

    # Panel 1.5: Brand Voice
    with st.expander("🎭 Brand Voice Profiles (Optional)", expanded=False):
        st.markdown("Define a consistent voice for your brand to ensure all posts sound the same.")
        brand_name = st.text_input("Brand/User Name", placeholder="e.g., Acme Corp / Jane Doe")
        brand_mission = st.text_area(
            "Brand Mission/Value Prop",
            placeholder="We help SMEs automate their accounting...",
        )
        voice_traits = st.multiselect(
            "Voice Traits",
            ["Witty", "Direct", "Academic", "Visionary", "Pragmatic", "Edgy"],
        )

        if brand_name and brand_mission:
            st.session_state.brand_voice = {
                "name": brand_name,
                "mission": brand_mission,
                "traits": voice_traits,
            }
            st.success(f"Applying '{brand_name}' Brand Voice to generations.")

    keywords = st.text_input(
        "Keywords to include (comma-separated, optional)",
        placeholder="AI, automation, productivity",
    )

    # Panel 2: Template Selection
    st.markdown("---")
    st.subheader("🎨 Panel 2: Select Template")

    template_cols = st.columns(3)
    selected_template = None

    for idx, (template_name, template_info) in enumerate(TEMPLATES.items()):
        col_idx = idx % 3
        with template_cols[col_idx]:
            if st.button(
                f"**{template_name}**\n\n{template_info['description']}",
                key=f"template_{idx}",
                use_container_width=True,
            ):
                selected_template = template_name

    # Show selected template
    if "selected_template" not in st.session_state:
        st.session_state.selected_template = "Professional Insight"

    if selected_template:
        st.session_state.selected_template = selected_template

    st.info(f"**Selected Template:** {st.session_state.selected_template}")
    st.caption(f"Style: {TEMPLATES[st.session_state.selected_template]['style']}")

    # Panel 3: Generate
    st.markdown("---")
    st.subheader("🤖 Panel 3: Generate Content")

    # Generation mode selector
    generation_mode = st.radio(
        "Generation Mode",
        options=["Single Post", "A/B Test (3 Variants)"],
        index=0,
        horizontal=True,
        help="Single: Generate one optimized post | A/B Test: Generate 3 variants for testing",
    )

    if generation_mode == "A/B Test (3 Variants)":
        st.info(
            "💡 **A/B Testing Mode**: Generates 3 content variants with different hooks, CTAs, "
            "and formatting for split testing. Perfect for optimizing engagement!"
        )

    col_gen1, col_gen2 = st.columns([3, 1])

    with col_gen1:
        button_label = (
            "✨ Generate LinkedIn Post"
            if generation_mode == "Single Post"
            else "✨ Generate A/B Test Variants"
        )

        if st.button(button_label, type="primary", use_container_width=True):
            if not topic or not topic.strip():
                logger.warning("User attempted to generate post without topic")
                st.error("❌ Please enter a topic to write about.")
            elif len(topic.strip()) < 10:
                logger.warning(f"User entered very short topic: {len(topic)} chars")
                st.error("❌ Please provide a more detailed topic (at least 10 characters).")
            else:
                if generation_mode == "Single Post":
                    # EXISTING SINGLE POST GENERATION
                    logger.info(
                        f"Generating post for topic: {topic[:50]}... "
                        f"with template: {st.session_state.selected_template}"
                    )
                    with st.spinner("🤖 Claude is writing your post..."):
                        try:
                            generated_post = _generate_post(
                                api_key=api_key,
                                topic=topic.strip(),
                                template=st.session_state.selected_template,
                                tone=tone,
                                platform=platform,
                                keywords=keywords.strip() if keywords else "",
                                target_audience=target_audience.strip() if target_audience else "",
                            )

                            if generated_post:
                                st.session_state.generated_post = generated_post

                                # Track in content history
                                if st.session_state.analytics_enabled:
                                    engagement_score = _calculate_engagement_score(
                                        content=generated_post,
                                        platform=platform,
                                        template=st.session_state.selected_template,
                                        tone=tone,
                                    )

                                    posting_time = _suggest_posting_time(platform, target_audience)

                                    history_entry = {
                                        "timestamp": datetime.now(),
                                        "platform": platform,
                                        "template": st.session_state.selected_template,
                                        "tone": tone,
                                        "target_audience": target_audience,
                                        "content": generated_post,
                                        "char_count": len(generated_post),
                                        "word_count": len(generated_post.split()),
                                        "hashtag_count": generated_post.count("#"),
                                        "predicted_engagement": engagement_score,
                                        "optimal_posting_time": posting_time["peak_time"],
                                        "optimal_posting_day": posting_time["days"][0],
                                    }

                                    st.session_state.content_history.append(history_entry)
                                    logger.info(
                                        f"Tracked content in history: "
                        f"{len(st.session_state.content_history)} total posts"
                                    )

                                logger.info(
                                    f"Post generated successfully: {len(generated_post)} chars"
                                )
                                st.success("✅ Post generated successfully!")
                        except RateLimitError as e:
                            logger.error(f"Rate limit exceeded: {str(e)}")
                            st.error("❌ Rate limit exceeded. Please wait a moment and try again.")
                        except (APIConnectionError, APITimeoutError) as e:
                            logger.error(f"Connection error: {str(e)}")
                            st.error(
                                "❌ Connection error. Please check your internet "
                                "connection and try again."
                            )
                        except Exception as e:
                            logger.error(
                                f"Unexpected error during generation: {str(e)}",
                                exc_info=True,
                            )
                            st.error(f"❌ An error occurred: {str(e)}")

                else:  # A/B Test Mode
                    logger.info(f"Generating A/B test variants for topic: {topic[:50]}...")
                    with st.spinner("🤖 Claude is generating 3 A/B test variants..."):
                        try:
                            variants = _generate_ab_test_variants(
                                api_key=api_key,
                                topic=topic.strip(),
                                template=st.session_state.selected_template,
                                tone=tone,
                                platform=platform,
                                keywords=keywords.strip() if keywords else "",
                                target_audience=target_audience.strip() if target_audience else "",
                            )

                            if variants:
                                st.session_state.ab_test_variants = variants
                                logger.info(
                                    f"Successfully generated {len(variants)} A/B test variants"
                                )
                                st.success(
                                    f"✅ Generated {len(variants)} variants for A/B testing!"
                                )

                        except Exception as e:
                            logger.error(f"Error generating A/B variants: {str(e)}", exc_info=True)
                            st.error(f"❌ An error occurred: {str(e)}")

    with col_gen2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.generated_post = None
            st.session_state.adapted_variants = None
            if "ab_test_variants" in st.session_state:
                st.session_state.ab_test_variants = None
            st.rerun()

    # Panel 4: Export (single post) or A/B Comparison (variants)
    if st.session_state.generated_post and not st.session_state.ab_test_variants:
        st.markdown("---")
        st.subheader("📤 Panel 4: Preview & Export")

        # Preview
        st.markdown("#### Preview")
        st.text_area(
            "Generated Post",
            value=st.session_state.generated_post,
            height=300,
            key="preview_area",
        )

        # Character count and engagement score
        char_count = len(st.session_state.generated_post)

        # Display engagement score if available
        engagement_score = None
        if st.session_state.content_history:
            latest_entry = st.session_state.content_history[-1]
            if latest_entry.get("content") == st.session_state.generated_post:
                engagement_score = latest_entry.get("predicted_engagement")

        # If not in history, calculate it now
        if engagement_score is None:
            engagement_score = _calculate_engagement_score(
                content=st.session_state.generated_post,
                platform=platform,
                template=st.session_state.get("selected_template", "Professional Insight"),
                tone=tone,
            )

        # Display metrics in columns
        metric_col1, metric_col2, metric_col3 = st.columns(3)

        with metric_col1:
            if char_count > LINKEDIN_CHAR_LIMIT:
                st.metric(
                    "Character Count",
                    f"{char_count:,}",
                    delta=f"+{char_count - LINKEDIN_CHAR_LIMIT:,} over limit",
                    delta_color="inverse",
                )
            else:
                st.metric(
                    "Character Count",
                    f"{char_count:,}",
                    delta=f"{LINKEDIN_CHAR_LIMIT - char_count:,} remaining",
                )

        with metric_col2:
            word_count = len(st.session_state.generated_post.split())
            st.metric("Word Count", word_count)

        with metric_col3:
            # Engagement score with color coding
            engagement_color = (
                "🟢" if engagement_score >= 7.5 else "🟡" if engagement_score >= 5.5 else "🔴"
            )
            engagement_label = (
                "Excellent"
                if engagement_score >= 7.5
                else "Good"
                if engagement_score >= 5.5
                else "Needs Work"
            )
            st.metric(
                f"{engagement_color} Predicted Engagement",
                f"{engagement_score:.1f}/10",
                delta=engagement_label,
            )

        # Export options
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            st.download_button(
                label="📥 Download as TXT",
                data=st.session_state.generated_post,
                file_name="linkedin_post.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_exp2:
            # Copy to clipboard using JavaScript (via markdown)
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.generated_post, language=None)
                st.success("✅ Content displayed above - use your browser's copy function")

        # Multi-platform adaptation
        st.markdown("---")
        st.markdown("#### 🌐 Adapt to Other Platforms")

        col_adapt1, col_adapt2 = st.columns([3, 1])

        with col_adapt1:
            target_platforms = st.multiselect(
                "Select platforms to adapt content for:",
                options=[p for p in PLATFORM_SPECS.keys() if p != platform],
                default=(["Twitter/X", "Instagram"] if platform == "LinkedIn" else ["LinkedIn"]),
            )

        with col_adapt2:
            if st.button("🔄 Generate Adaptations", use_container_width=True):
                if target_platforms:
                    with st.spinner("Adapting content for selected platforms..."):
                        adapted_variants = {}

                        for target in target_platforms:
                            adapted = _adapt_content_for_platform(
                                base_content=st.session_state.generated_post,
                                original_platform=platform,
                                target_platform=target,
                                topic=topic,
                                api_key=api_key,
                            )
                            adapted_variants[target] = adapted

                        st.session_state.adapted_variants = adapted_variants
                        st.success(f"✅ Adapted to {len(target_platforms)} platforms!")
                else:
                    st.warning("Please select at least one platform to adapt to.")

        # Show adapted variants
        if st.session_state.adapted_variants:
            st.markdown("#### 📱 Platform Adaptations")

            # Create tabs for each platform
            all_platforms = [platform] + list(st.session_state.adapted_variants.keys())
            platform_tabs = st.tabs(all_platforms)

            # Original platform
            with platform_tabs[0]:
                st.caption(f"Original ({platform})")
                st.text_area(
                    f"{platform} Content",
                    value=st.session_state.generated_post,
                    height=250,
                    key=f"preview_{platform}",
                )
                st.caption(f"📊 {len(st.session_state.generated_post)} characters")

            # Adapted platforms
            for i, (adapt_platform, adapt_data) in enumerate(
                st.session_state.adapted_variants.items(), 1
            ):
                with platform_tabs[i]:
                    st.caption(f"Adapted for {adapt_platform}")

                    # Check for errors
                    if "error" in adapt_data:
                        st.error(f"Error adapting content: {adapt_data['error']}")
                        st.text_area(
                            f"{adapt_platform} Content (Original)",
                            value=adapt_data["content"],
                            height=250,
                            key=f"preview_{adapt_platform}",
                        )
                        continue

                    # Special display for email
                    if adapt_platform == "Email Newsletter" and "subject" in adapt_data:
                        st.markdown("**Subject Line:**")
                        st.code(adapt_data["subject"])
                        st.markdown("**Preheader:**")
                        st.code(adapt_data["preheader"])
                        st.markdown("**Email Body:**")

                    # Special display for Twitter threads
                    if adapt_platform == "Twitter/X" and "thread" in adapt_data:
                        st.markdown(f"**Thread ({len(adapt_data['thread'])} tweets):**")
                        for idx, tweet in enumerate(adapt_data["thread"], 1):
                            st.text_area(
                                f"Tweet {idx}/{len(adapt_data['thread'])}",
                                value=tweet,
                                height=100,
                                key=f"tweet_{idx}",
                            )
                    else:
                        st.text_area(
                            f"{adapt_platform} Content",
                            value=adapt_data["content"],
                            height=250,
                            key=f"preview_{adapt_platform}",
                        )

                    st.caption(f"📊 {adapt_data['char_count']} characters")

            # Export all platforms as ZIP
            st.markdown("---")
            st.markdown("#### 📦 Download Multi-Platform Package")

            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                # Add original
                zip_file.writestr(
                    f"{platform.lower().replace('/', '_')}_post.txt",
                    st.session_state.generated_post,
                )

                # Add adaptations
                for adapt_platform, adapt_data in st.session_state.adapted_variants.items():
                    if "error" in adapt_data:
                        continue

                    filename = f"{adapt_platform.lower().replace('/', '_')}_post.txt"

                    if adapt_platform == "Email Newsletter" and "subject" in adapt_data:
                        content = f"Subject: {adapt_data['subject']}\n"
                        content += f"Preheader: {adapt_data['preheader']}\n\n"
                        content += adapt_data["content"]
                        zip_file.writestr(filename, content)
                    elif adapt_platform == "Twitter/X" and "thread" in adapt_data:
                        thread_content = "\n\n---\n\n".join(
                            [
                                f"Tweet {i + 1}/{len(adapt_data['thread'])}:\n{tweet}"
                                for i, tweet in enumerate(adapt_data["thread"])
                            ]
                        )
                        zip_file.writestr(filename, thread_content)
                    else:
                        zip_file.writestr(filename, adapt_data["content"])

            st.download_button(
                label="📦 Download Multi-Platform ZIP",
                data=zip_buffer.getvalue(),
                file_name=f"multi_platform_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True,
            )

    elif st.session_state.ab_test_variants:
        # NEW A/B TEST COMPARISON VIEW
        st.markdown("---")
        st.subheader("📤 Panel 4: A/B Test Variant Comparison")

        variants = st.session_state.ab_test_variants

        # Performance Summary
        st.markdown("#### 🏆 Predicted Performance Ranking")
        rank_cols = st.columns(len(variants))

        for i, variant in enumerate(variants):
            with rank_cols[i]:
                medal = ["🥇", "🥈", "🥉"][i] if i < 3 else ""
                # Calculate engagement delta vs worst variant
                eng_diff = (
                    variant["predicted_engagement"] - variants[-1]["predicted_engagement"]
                )
                st.metric(
                    label=f"{medal} Variant {i + 1}",
                    value=f"{variant['predicted_engagement']:.1f}/10",
                    delta=f"{eng_diff:.1f} vs worst" if i < len(variants) - 1 else None,
                )
                st.caption(variant["strategy_description"])

        # Side-by-side variant comparison
        st.markdown("#### 📋 Variant Content Comparison")

        variant_tabs = st.tabs([v["variant_id"] for v in variants])

        for i, variant in enumerate(variants):
            with variant_tabs[i]:
                # Metadata row
                meta_cols = st.columns(4)
                with meta_cols[0]:
                    st.caption(f"**Hook:** {variant['hook_type'].title()}")
                with meta_cols[1]:
                    st.caption(f"**CTA:** {variant['cta_type'].title()}")
                with meta_cols[2]:
                    st.caption(f"**Format:** {variant['format_style'].replace('_', ' ').title()}")
                with meta_cols[3]:
                    st.caption(f"**Emoji:** {variant['emoji_density'].title()}")

                # Content preview
                st.text_area(
                    f"{variant['variant_id']} Content",
                    value=variant["content"],
                    height=300,
                    key=f"variant_{variant['variant_id']}_preview",
                    label_visibility="collapsed",
                )

                # Stats row
                stat_cols = st.columns(4)
                with stat_cols[0]:
                    st.caption(f"📊 **{variant['char_count']}** chars")
                with stat_cols[1]:
                    st.caption(f"📝 **{variant['word_count']}** words")
                with stat_cols[2]:
                    st.caption(f"#️⃣ **{variant['hashtag_count']}** hashtags")
                with stat_cols[3]:
                    engagement_color = (
                        "🟢"
                        if variant["predicted_engagement"] >= 7.5
                        else "🟡"
                        if variant["predicted_engagement"] >= 5.5
                        else "🔴"
                    )
                    st.caption(
                        f"{engagement_color} "
                        f"**{variant['predicted_engagement']:.1f}/10** engagement"
                    )

        # Difference Highlighter
        with st.expander("🔍 Key Differences Between Variants"):
            st.markdown("**Opening Hook Comparison:**")
            for variant in variants:
                first_line = variant["content"].split("\n")[0]
                st.markdown(
                    f"- **{variant['variant_id']}** ({variant['hook_type']}): _{first_line}_"
                )

            st.markdown("\n**Closing CTA Comparison:**")
            for variant in variants:
                last_lines = variant["content"].strip().split("\n")[-2:]
                cta = " ".join(last_lines)
                st.markdown(f"- **{variant['variant_id']}** ({variant['cta_type']}): _{cta}_")

        # Recommendation
        best_variant = variants[0]
        st.success(
            f"💡 **Recommendation:** Based on predicted engagement, start with "
            f"**{best_variant['variant_id']}** "
            f"({best_variant['predicted_engagement']:.1f}/10). "
            f"Test all 3 variants to find your winning formula!"
        )

        # Export Options
        st.markdown("---")
        st.markdown("#### 📥 Export A/B Test Package")

        export_cols = st.columns(3)

        with export_cols[0]:
            # Export as CSV with metadata
            df_variants = pd.DataFrame(variants)
            csv_data = df_variants.to_csv(index=False)

            st.download_button(
                label="📊 Download as CSV (with metadata)",
                data=csv_data,
                file_name=f"ab_test_variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        with export_cols[1]:
            # Export as TXT files in ZIP
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for variant in variants:
                    filename = f"{variant['variant_id'].lower().replace(' ', '_')}_post.txt"
                    header = f"""A/B TEST {variant["variant_id"]}
Hook: {variant["hook_type"]}
CTA: {variant["cta_type"]}
Format: {variant["format_style"]}
Predicted Engagement: {variant["predicted_engagement"]}/10
---

{variant["content"]}"""
                    zip_file.writestr(filename, header)

            st.download_button(
                label="📦 Download as ZIP (TXT files)",
                data=zip_buffer.getvalue(),
                file_name=f"ab_test_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True,
            )

        with export_cols[2]:
            # Copy best variant to clipboard
            if st.button("📋 Copy Best Variant", use_container_width=True):
                st.code(best_variant["content"], language=None)
                st.success(f"✅ {best_variant['variant_id']} displayed above - use browser copy")

        # Testing Guide
        with st.expander("📚 How to Run A/B Tests with These Variants"):
            st.markdown(
                """
**A/B Testing Best Practices:**

1. **Platform Selection:**
   - LinkedIn: Use LinkedIn's native A/B testing or post at same time on different days
   - Facebook/Instagram: Use Meta's A/B testing tools
   - Twitter: Post variants at same time of day across 3 days

2. **Testing Timeline:**
   - Minimum: 3-7 days per variant
   - Post at optimal times (see Analytics panel)
   - Ensure similar audience exposure

3. **Success Metrics:**
   - **Engagement Rate**: (Likes + Comments + Shares) / Impressions
   - **Click-Through Rate**: Clicks / Impressions (if link included)
   - **Comment Quality**: Depth of conversation started

4. **Sample Size:**
   - Minimum 1,000 impressions per variant
   - 100+ engagements for statistical significance

5. **Declare Winner:**
   - Variant with highest engagement rate wins
   - Use winner's strategy (hook/CTA/format) for future posts
   - Re-test periodically (audience preferences change)

6. **Tracking:**
   - Use UTM parameters for link tracking
   - Tag posts in your social media scheduler
   - Record results in Analytics panel
        """
            )

    # Panel 5: Analytics Dashboard
    if st.session_state.content_history:
        st.markdown("---")
        st.subheader("📊 Panel 5: Content Performance Analytics")

        # Toggle analytics and clear history
        col_toggle1, col_toggle2 = st.columns([3, 1])
        with col_toggle2:
            if st.button("🔄 Clear History", use_container_width=True):
                st.session_state.content_history = []
                st.rerun()

        history = st.session_state.content_history

        # Metrics Row 1: Overall Stats
        st.markdown("#### 📈 Overall Performance Metrics")
        metric_cols = st.columns(4)

        with metric_cols[0]:
            st.metric("Total Posts Generated", len(history))

        with metric_cols[1]:
            avg_engagement = np.mean([h["predicted_engagement"] for h in history])
            st.metric("Avg Predicted Engagement", f"{avg_engagement:.1f}/10")

        with metric_cols[2]:
            top_template = Counter([h["template"] for h in history]).most_common(1)[0]
            st.metric("Top Template", top_template[0])
            st.caption(f"Used {top_template[1]} times")

        with metric_cols[3]:
            top_platform = Counter([h["platform"] for h in history]).most_common(1)[0]
            st.metric("Top Platform", top_platform[0])
            st.caption(f"Used {top_platform[1]} times")

        # Metrics Row 2: Content Quality
        st.markdown("#### 📝 Content Quality Metrics")
        quality_cols = st.columns(4)

        with quality_cols[0]:
            avg_word_count = np.mean([h["word_count"] for h in history])
            st.metric("Avg Word Count", f"{avg_word_count:.0f}")

        with quality_cols[1]:
            avg_char_count = np.mean([h["char_count"] for h in history])
            st.metric("Avg Character Count", f"{avg_char_count:.0f}")

        with quality_cols[2]:
            avg_hashtags = np.mean([h["hashtag_count"] for h in history])
            st.metric("Avg Hashtags", f"{avg_hashtags:.1f}")

        with quality_cols[3]:
            high_engagement_count = sum(1 for h in history if h["predicted_engagement"] >= 7.5)
            st.metric("High Engagement Posts", f"{high_engagement_count}")
            st.caption("(Score ≥ 7.5)")

        # Chart 1: Engagement Trend Over Time
        st.markdown("#### 📉 Engagement Trends")

        df_history = pd.DataFrame(history)
        df_history["timestamp_formatted"] = df_history["timestamp"].dt.strftime("%m/%d %H:%M")

        fig_engagement = px.line(
            df_history,
            x="timestamp",
            y="predicted_engagement",
            color="platform",
            markers=True,
            title="Predicted Engagement Score Over Time",
            labels={"predicted_engagement": "Engagement Score", "timestamp": "Date/Time"},
            hover_data=["template", "tone"],
        )
        fig_engagement.update_layout(height=400)
        st.plotly_chart(fig_engagement, use_container_width=True)

        # Chart 2: Template & Platform Performance
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("##### Template Performance")
            template_avg = (
                df_history.groupby("template")["predicted_engagement"].mean().reset_index()
            )
            template_avg = template_avg.sort_values("predicted_engagement", ascending=False)

            fig_template = px.bar(
                template_avg,
                x="predicted_engagement",
                y="template",
                orientation="h",
                title="Avg Engagement by Template",
                labels={"predicted_engagement": "Avg Score", "template": ""},
            )
            fig_template.update_layout(height=300)
            st.plotly_chart(fig_template, use_container_width=True)

        with col_chart2:
            st.markdown("##### Platform Performance")
            platform_avg = (
                df_history.groupby("platform")["predicted_engagement"].mean().reset_index()
            )
            platform_avg = platform_avg.sort_values("predicted_engagement", ascending=False)

            fig_platform = px.bar(
                platform_avg,
                x="predicted_engagement",
                y="platform",
                orientation="h",
                title="Avg Engagement by Platform",
                labels={"predicted_engagement": "Avg Score", "platform": ""},
            )
            fig_platform.update_layout(height=300)
            st.plotly_chart(fig_platform, use_container_width=True)

        # Chart 3: Posting Time Recommendations
        st.markdown("#### 🕐 Optimal Posting Times (All Posts)")
        posting_times = (
            df_history.groupby(["optimal_posting_day", "platform"]).size().reset_index(name="count")
        )

        if not posting_times.empty:
            fig_heatmap = px.bar(
                posting_times,
                x="optimal_posting_day",
                y="count",
                color="platform",
                title="Recommended Posting Days by Platform",
                labels={"count": "Number of Posts", "optimal_posting_day": "Day of Week"},
            )
            fig_heatmap.update_layout(height=350)
            st.plotly_chart(fig_heatmap, use_container_width=True)

        # AI-Powered Improvement Suggestions
        st.markdown("#### 💡 AI-Powered Improvement Suggestions")

        suggestions = _generate_improvement_suggestions(history)

        for i, suggestion in enumerate(suggestions, 1):
            suggestion_type = suggestion["type"]
            icon = {
                "success": "✅",
                "warning": "⚠️",
                "info": "💡",
                "tip": "🎯",
            }[suggestion_type]

            if suggestion_type == "success":
                st.success(f"{icon} {suggestion['message']}")
            elif suggestion_type == "warning":
                st.warning(f"{icon} {suggestion['message']}")
            else:
                st.info(f"{icon} {suggestion['message']}")

        # Content History Table (expandable)
        with st.expander("📋 View Full Content History"):
            # Display table with key metrics
            display_df = df_history[
                [
                    "timestamp",
                    "platform",
                    "template",
                    "tone",
                    "predicted_engagement",
                    "word_count",
                    "hashtag_count",
                ]
            ].copy()
            display_df["timestamp"] = display_df["timestamp"].dt.strftime("%Y-%m-%d %H:%M")
            display_df = display_df.sort_values("timestamp", ascending=False)

            st.dataframe(
                display_df,
                column_config={
                    "timestamp": "Date/Time",
                    "platform": "Platform",
                    "template": "Template",
                    "tone": "Tone",
                    "predicted_engagement": st.column_config.NumberColumn(
                        "Engagement Score", format="%.1f ⭐"
                    ),
                    "word_count": "Words",
                    "hashtag_count": "Hashtags",
                },
                hide_index=True,
                use_container_width=True,
            )

            # Export history as CSV
            csv_data = df_history.to_csv(index=False)
            st.download_button(
                label="📥 Download History (CSV)",
                data=csv_data,
                file_name=f"content_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )


def _validate_template_and_tone(template: str, tone: str) -> None:
    """
    Validate that template and tone are valid choices.

    Args:
        template: Template name to validate
        tone: Tone name to validate

    Raises:
        ValueError: If template or tone is not in valid options
    """
    if template not in TEMPLATES:
        raise ValueError(f"Invalid template: {template}. Valid options: {list(TEMPLATES.keys())}")
    if tone not in TONES:
        raise ValueError(f"Invalid tone: {tone}. Valid options: {list(TONES.keys())}")


def _calculate_engagement_score(content: str, platform: str, template: str, tone: str) -> float:
    """
    Predict engagement score (1-10) based on content characteristics.

    Uses heuristics based on social media best practices:
    - Content length optimal for platform
    - Presence of question/CTA
    - Emoji usage appropriate for platform
    - Hashtag optimization
    - Hook strength (first 50 chars)

    Args:
        content: Generated post content
        platform: Target platform name
        template: Template used
        tone: Tone used

    Returns:
        Engagement score from 1.0 to 10.0
    """
    score = 5.0  # Base score
    platform_specs = PLATFORM_SPECS.get(platform, PLATFORM_SPECS["LinkedIn"])

    # Factor 1: Length optimization (±1.5 points)
    word_count = len(content.split())
    optimal_min, optimal_max = platform_specs["optimal_length"]
    if optimal_min <= word_count <= optimal_max:
        score += 1.5
    elif word_count < optimal_min * 0.7 or word_count > optimal_max * 1.3:
        score -= 1.5

    # Factor 2: Question/CTA presence (±1.0 points)
    if "?" in content:
        score += 0.7
    cta_keywords = [
        "comment",
        "share",
        "thoughts",
        "agree",
        "think",
        "experience",
        "click",
        "learn more",
    ]
    if any(keyword in content.lower() for keyword in cta_keywords):
        score += 0.5

    # Factor 3: Emoji usage (±1.0 points)
    emoji_count = sum(1 for char in content if ord(char) > 127462)  # Unicode emoji range
    if platform_specs["emoji_style"] == "expressive" and emoji_count >= 3:
        score += 1.0
    elif platform_specs["emoji_style"] == "professional" and 1 <= emoji_count <= 3:
        score += 0.8
    elif platform_specs["emoji_style"] == "casual" and emoji_count >= 2:
        score += 0.9
    elif emoji_count == 0 and platform_specs["emoji_style"] != "professional":
        score -= 0.5

    # Factor 4: Hashtag optimization (±0.8 points)
    hashtag_count = content.count("#")
    min_hashtags, max_hashtags = platform_specs["hashtag_range"]
    if min_hashtags <= hashtag_count <= max_hashtags:
        score += 0.8
    elif hashtag_count < min_hashtags or hashtag_count > max_hashtags:
        score -= 0.5

    # Factor 5: Hook strength - first 50 characters (±1.0 points)
    first_line = content.split("\n")[0][:50]
    hook_indicators = [
        "did you know",
        "imagine",
        "what if",
        "here's",
        "stop",
        "don't",
        "ever wonder",
    ]
    if any(indicator in first_line.lower() for indicator in hook_indicators):
        score += 1.0
    elif first_line.isupper():  # All caps hook
        score += 0.7

    # Factor 6: Template bonus (±0.7 points)
    high_engagement_templates = ["Personal Story", "Thought Leadership", "How-To Guide"]
    if template in high_engagement_templates:
        score += 0.7

    # Factor 7: Tone bonus (±0.5 points)
    high_engagement_tones = ["Storytelling", "Inspirational"]
    if tone in high_engagement_tones:
        score += 0.5

    # Factor 8: Line breaks for readability (±0.5 points)
    line_count = content.count("\n\n")
    if 2 <= line_count <= 5:
        score += 0.5

    # Clamp score between 1 and 10
    score = max(1.0, min(10.0, score))

    logger.debug(f"Calculated engagement score: {score:.1f}/10 for {platform}")
    return round(score, 1)


def _suggest_posting_time(platform: str, target_audience: str = "") -> dict:
    """
    Suggest optimal posting time based on platform and audience.

    Based on industry research and platform algorithms:
    - LinkedIn: Tue-Thu 9am-12pm (B2B audience active)
    - Twitter/X: Daily 12pm-3pm (lunch hour engagement)
    - Instagram: Mon/Wed/Fri 11am-2pm (visual content peak)
    - Facebook: Wed-Fri 1pm-4pm (afternoon browsing)
    - Email: Tue/Thu 10am (morning inbox clearing)

    Args:
        platform: Target platform name
        target_audience: Optional audience description

    Returns:
        dict with recommended day, time, timezone, and reasoning
    """
    posting_times = {
        "LinkedIn": {
            "days": ["Tuesday", "Wednesday", "Thursday"],
            "time_range": "9:00 AM - 12:00 PM",
            "peak_time": "10:00 AM",
            "timezone": "EST",
            "reasoning": (
                "B2B professionals check LinkedIn during work hours, "
                "mid-week has highest engagement"
            ),
        },
        "Twitter/X": {
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time_range": "12:00 PM - 3:00 PM",
            "peak_time": "1:00 PM",
            "timezone": "EST",
            "reasoning": "Lunch hour browsing, consistent weekday engagement",
        },
        "Instagram": {
            "days": ["Monday", "Wednesday", "Friday"],
            "time_range": "11:00 AM - 2:00 PM",
            "peak_time": "12:00 PM",
            "timezone": "EST",
            "reasoning": "Visual content performs best during midday breaks",
        },
        "Facebook": {
            "days": ["Wednesday", "Thursday", "Friday"],
            "time_range": "1:00 PM - 4:00 PM",
            "peak_time": "2:00 PM",
            "timezone": "EST",
            "reasoning": "Afternoon browsing peaks mid-to-late week",
        },
        "Email Newsletter": {
            "days": ["Tuesday", "Thursday"],
            "time_range": "10:00 AM - 11:00 AM",
            "peak_time": "10:00 AM",
            "timezone": "EST",
            "reasoning": "Morning inbox clearing, avoiding Monday overwhelm and Friday checkout",
        },
    }

    recommendation = posting_times.get(platform, posting_times["LinkedIn"])

    # Adjust for specific audiences
    if target_audience:
        audience_lower = target_audience.lower()
        if "europe" in audience_lower or "uk" in audience_lower:
            recommendation["timezone"] = "GMT"
            recommendation["reasoning"] += " (adjusted for European audience)"
        elif "asia" in audience_lower or "australia" in audience_lower:
            recommendation["timezone"] = "AEST"
            recommendation["reasoning"] += " (adjusted for Asia-Pacific audience)"

    logger.debug(f"Suggested posting time for {platform}: {recommendation['peak_time']}")
    return recommendation


def _generate_improvement_suggestions(history: list) -> list:
    """
    Generate AI-powered content improvement suggestions based on history.

    Analyzes patterns in content history to provide actionable recommendations
    for improving engagement.

    Args:
        history: List of content history entries

    Returns:
        List of suggestion dicts with type and message
    """
    suggestions = []

    if not history:
        return [
            {
                "type": "info",
                "message": "Generate more content to receive personalized suggestions!",
            }
        ]

    df = pd.DataFrame(history)

    # Suggestion 1: Template optimization
    if len(df["template"].unique()) >= 2:
        template_performance = df.groupby("template")["predicted_engagement"].mean()
        best_template = template_performance.idxmax()
        worst_template = template_performance.idxmin()

        if (
            len(template_performance) >= 3
            and template_performance[best_template] - template_performance[worst_template] > 1.5
        ):
            # Calculate performance difference
            p_best = template_performance[best_template]
            p_worst = template_performance[worst_template]
            perf_diff = p_best - p_worst
            suggestions.append(
                {
                    "type": "tip",
                    "message": (
                        f"Your '{best_template}' template performs "
                        f"{perf_diff:.1f} points better than "
                        f"'{worst_template}'. Consider using it more often!"
                    ),
                }
            )

                # Suggestion 2: Platform optimization
    if len(df["platform"].unique()) > 1:
        platform_performance = df.groupby("platform")["predicted_engagement"].mean()
        best_platform = platform_performance.idxmax()
        suggestions.append(
            {
                "type": "success",
                "message": f"Your content performs best on {best_platform} "
                f"(avg score: {platform_performance[best_platform]:.1f}). "
                "This platform aligns well with your style!",
            }
        )

    # Suggestion 3: Content length optimization
    avg_engagement = df["predicted_engagement"].mean()
    high_performers = df[df["predicted_engagement"] >= avg_engagement + 1.0]

    if not high_performers.empty:
        avg_words_high = high_performers["word_count"].mean()
        avg_words_all = df["word_count"].mean()

        if abs(avg_words_high - avg_words_all) > 30:
            direction = "longer" if avg_words_high > avg_words_all else "shorter"
            suggestions.append(
                {
                    "type": "tip",
                    "message": f"Your high-engagement posts are {direction} "
                    f"(avg {avg_words_high:.0f} words vs {avg_words_all:.0f}). "
                    "Try adjusting content length!",
                }
            )

    # Suggestion 4: Hashtag optimization
    if len(df) >= 3:
        platform_groups = df.groupby("platform")

        for platform, group_df in platform_groups:
            if len(group_df) < 2:
                continue

            avg_ht = group_df["hashtag_count"].mean()
            platform_spec = PLATFORM_SPECS[platform]
            min_ht, max_ht = platform_spec["hashtag_range"]

            if avg_ht < min_ht:
                suggestions.append(
                    {
                        "type": "warning",
                        "message": f"You're using {avg_ht:.1f} hashtags on {platform} "
                        f"(recommended: {min_ht}-{max_ht}). "
                        "Add more hashtags for better discoverability!",
                    }
                )
                break  # Only show one hashtag warning
            elif avg_ht > max_ht:
                suggestions.append(
                    {
                        "type": "warning",
                        "message": f"You're using {avg_ht:.1f} hashtags on {platform} "
                        f"(recommended: {min_ht}-{max_ht}). "
                        "Reduce hashtags to avoid looking spammy!",
                    }
                )
                break  # Only show one hashtag warning

    # Suggestion 5: Consistency
    if len(history) >= 5:
        recent_5 = df.tail(5)
        engagement_std = recent_5["predicted_engagement"].std()

        if engagement_std < 1.0:
            suggestions.append(
                {
                    "type": "success",
                    "message": (
                        f"Great consistency! Your last 5 posts have similar engagement scores "
                        f"(std dev: {engagement_std:.2f}). You've found your rhythm!"
                    ),
                }
            )
        elif engagement_std > 2.5:
            suggestions.append(
                {
                    "type": "warning",
                    "message": f"High variability in recent posts (std dev: {engagement_std:.2f}). "
                    "Review your top performers to identify winning patterns!",
                }
            )

    # Suggestion 6: Tone optimization
    if len(df["tone"].unique()) >= 3:
        tone_performance = df.groupby("tone")["predicted_engagement"].mean()
        best_tone = tone_performance.idxmax()
        suggestions.append(
            {
                "type": "tip",
                "message": f"'{best_tone}' tone shows strongest engagement "
                f"(avg: {tone_performance[best_tone]:.1f}). This resonates with your audience!",
            }
        )

    # Suggestion 7: Growth trajectory
    if len(history) >= 10:
        recent_half = df.tail(len(df) // 2)
        earlier_half = df.head(len(df) // 2)

        recent_avg = recent_half["predicted_engagement"].mean()
        earlier_avg = earlier_half["predicted_engagement"].mean()

        if recent_avg > earlier_avg + 0.5:
            suggestions.append(
                {
                    "type": "success",
                    "message": f"📈 Your content quality is improving! Recent posts score "
                    f"{recent_avg - earlier_avg:.1f} points higher than earlier ones!",
                }
            )
        elif earlier_avg > recent_avg + 0.5:
            suggestions.append(
                {
                    "type": "info",
                    "message": (
                        f"📉 Recent engagement is lower. Review your earlier high performers "
                        f"(avg: {earlier_avg:.1f}) for inspiration!"
                    ),
                }
            )

    # Default suggestion if none generated
    if not suggestions:
        suggestions.append(
            {
                "type": "info",
                "message": (
                    "Keep creating! Generate more content to unlock personalized "
                    "insights and recommendations."
                ),
            }
        )

    return suggestions[:5]  # Limit to top 5 suggestions


def _build_prompt(
    topic: str,
    template: str,
    tone: str,
    platform: str = "LinkedIn",
    keywords: str = "",
    target_audience: str = "",
) -> str:
    """
    Build platform-optimized prompt for Claude API based on user inputs.

    Args:
        topic: Main topic/subject of the post
        template: Selected template name
        tone: Desired tone
        platform: Target platform name (default: LinkedIn)
        keywords: Optional comma-separated keywords
        target_audience: Optional target audience description

    Returns:
        Formatted prompt string for Claude API
    """
    template_info = TEMPLATES[template]
    tone_instruction = TONES[tone]
    platform_specs = PLATFORM_SPECS[platform]

    prompt = f"""{template_info["prompt_prefix"]} {topic}.

Platform: {platform}
Style: {template_info["style"]}
Tone: {tone_instruction}"""

    if target_audience:
        prompt += f"\nTarget Audience: {target_audience}"

    if "brand_voice" in st.session_state and st.session_state.brand_voice:
        bv = st.session_state.brand_voice
        prompt += (
            f"\n\nBRAND VOICE CONTEXT:\nBrand: {bv['name']}\n"
            f"Mission: {bv['mission']}\nTraits: {', '.join(bv['traits'])}"
        )

    if keywords:
        prompt += f"\nInclude these keywords naturally: {keywords}"

    # Platform-specific requirements
    char_limit = platform_specs["char_limit"]
    word_range = platform_specs["optimal_length"]
    hashtag_range = platform_specs["hashtag_range"]

    prompt += f"""

PLATFORM-SPECIFIC REQUIREMENTS ({platform}):
- Length: {word_range[0]}-{word_range[1]} words (optimal for {platform})
- Character limit: {char_limit if char_limit else "No limit"}
- Hashtags: {hashtag_range[0]}-{hashtag_range[1]} relevant hashtags
- Emoji style: {platform_specs["emoji_style"]}
- Formatting: {platform_specs["formatting"]}
"""

    # Special handling for Twitter threads
    if platform == "Twitter/X" and platform_specs.get("thread_mode"):
        prompt += f"""
- If content exceeds {platform_specs["thread_tweet_limit"]} chars, split into thread (2-5 tweets)
- Each tweet must be standalone but build on previous
- Number tweets (1/n, 2/n, etc.)
"""

    # Special handling for email
    if platform == "Email Newsletter":
        prompt += f"""
- Include subject line (max {platform_specs["subject_line_limit"]} chars)
- Include preheader (max {platform_specs["preheader_limit"]} chars)
- Structure: subject line, preheader, then main content
"""

    prompt += """
- Start with a hook to grab attention
- End with a call-to-action appropriate for the platform
- Be authentic and engaging"""

    logger.debug(f"Built platform-optimized prompt for {platform}: {len(prompt)} characters")
    return prompt


def _adapt_content_for_platform(
    base_content: str,
    original_platform: str,
    target_platform: str,
    topic: str,
    api_key: str,
) -> dict:
    """
    Adapt existing content from one platform to another.

    Uses Claude AI to intelligently adapt content while preserving core message
    and adjusting format, length, and style for the target platform.

    Args:
        base_content: The original generated content
        original_platform: Source platform name
        target_platform: Target platform name
        topic: Original topic for context
        api_key: Anthropic API key

    Returns:
        dict with adapted content and metadata:
        - platform: target platform name
        - content: adapted content text
        - char_count: character count
        - specs: platform specifications
        - subject: (email only) subject line
        - preheader: (email only) preheader text
        - thread: (Twitter only) list of tweets
        - error: (on error) error message
    """
    target_specs = PLATFORM_SPECS[target_platform]

    adaptation_prompt = f"""Adapt the following {original_platform} post for {target_platform}.

ORIGINAL POST ({original_platform}):
{base_content}

TARGET PLATFORM: {target_platform}
Requirements:
- Character limit: {target_specs["char_limit"] if target_specs["char_limit"] else "No limit"}
- Optimal length: {target_specs["optimal_length"][0]}-{target_specs["optimal_length"][1]} words
- Hashtags: {target_specs["hashtag_range"][0]}-{target_specs["hashtag_range"][1]}
- Emoji style: {target_specs["emoji_style"]}
- Formatting: {target_specs["formatting"]}

ADAPTATION GUIDELINES:
- Preserve the core message and key points
- Adjust length to fit platform constraints
- Modify tone/style for platform audience
- Reformat for platform best practices
- Keep hashtags and CTAs platform-appropriate

Return ONLY the adapted content, no explanations."""

    if target_platform == "Email Newsletter":
        adaptation_prompt += """
Format as:
SUBJECT: [subject line]
PREHEADER: [preheader text]
CONTENT: [email body]
"""

    if target_platform == "Twitter/X" and target_specs.get("thread_mode"):
        adaptation_prompt += """
If content requires multiple tweets, format as:
TWEET 1/n: [first tweet]
TWEET 2/n: [second tweet]
...
"""

    try:
        client = Anthropic(api_key=api_key)
        adapted_text = _call_claude_api(client, adaptation_prompt)

        # Parse response based on platform
        result = {
            "platform": target_platform,
            "content": adapted_text,
            "char_count": len(adapted_text),
            "specs": target_specs,
        }

        # Special parsing for email
        if target_platform == "Email Newsletter" and "SUBJECT:" in adapted_text:
            lines = adapted_text.split("\n")
            for line in lines:
                if line.startswith("SUBJECT:"):
                    result["subject"] = line.replace("SUBJECT:", "").strip()
                elif line.startswith("PREHEADER:"):
                    result["preheader"] = line.replace("PREHEADER:", "").strip()
                elif line.startswith("CONTENT:"):
                    result["content"] = adapted_text.split("CONTENT:")[1].strip()

        # Special parsing for Twitter threads
        if target_platform == "Twitter/X" and "TWEET" in adapted_text:
            tweets = []
            for line in adapted_text.split("\n"):
                if line.startswith("TWEET"):
                    tweet_content = line.split(":", 1)[1].strip() if ":" in line else line
                    tweets.append(tweet_content)
            if tweets:
                result["thread"] = tweets

        logger.info(f"Successfully adapted content from {original_platform} to {target_platform}")
        return result

    except Exception as e:
        logger.error(f"Error adapting content: {str(e)}")
        return {
            "platform": target_platform,
            "content": base_content,  # Fallback to original
            "error": str(e),
        }


@retry_with_exponential_backoff(max_attempts=MAX_RETRY_ATTEMPTS)
def _call_claude_api(client: Anthropic, prompt: str) -> str:
    """
    Make the actual API call to Claude with retry logic.

    This function is decorated with retry logic for handling rate limits
    and temporary failures.

    Args:
        client: Initialized Anthropic client
        prompt: The prompt to send to Claude

    Returns:
        Generated text from Claude

    Raises:
        APIError: For API-related errors
        RateLimitError: When rate limits are exceeded (after retries)
        APIConnectionError: For connection issues (after retries)
        APITimeoutError: For timeout issues (after retries)
    """
    logger.debug(f"Calling Claude API with model: {DEFAULT_MODEL}")

    message = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=DEFAULT_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
        timeout=API_TIMEOUT,
    )

    # Validate response structure
    if not message.content or len(message.content) == 0:
        logger.error("API returned empty content")
        raise ValueError("API returned empty response")

    if not hasattr(message.content[0], "text"):
        logger.error(f"API returned unexpected content type: {type(message.content[0])}")
        raise ValueError("API returned malformed response")

    generated_text = message.content[0].text
    logger.debug(f"API call successful, received {len(generated_text)} characters")

    return generated_text


def _generate_post(
    api_key: str,
    topic: str,
    template: str,
    tone: str,
    platform: str = "LinkedIn",
    keywords: str = "",
    target_audience: str = "",
) -> Optional[str]:
    """
    Generate platform-optimized post using Claude API with retry logic and error handling.

    This function orchestrates the entire post generation process:
    1. Validates inputs
    2. Builds the platform-optimized prompt
    3. Calls Claude API (with automatic retries for transient failures)
    4. Validates and returns the response

    Args:
        api_key: Anthropic API key (must start with 'sk-ant-')
        topic: Main topic/subject of the post (min 10 characters)
        template: Selected template name (must be in TEMPLATES)
        tone: Desired tone (must be in TONES)
        platform: Target platform (default: LinkedIn)
        keywords: Optional comma-separated keywords to include naturally
        target_audience: Optional target audience description

    Returns:
        Generated post text, or None if generation fails

    Raises:
        ValueError: If template or tone is invalid
        APIError: For non-retryable API errors (e.g., invalid API key)
        RateLimitError: If rate limit exceeded after all retries
        APIConnectionError: If connection failed after all retries
        APITimeoutError: If request timed out after all retries

    Example:
        >>> post = _generate_post(
        ...     api_key="sk-ant-xxx",
        ...     topic="AI trends in 2025",
        ...     template="Professional Insight",
        ...     tone="Professional",
        ...     platform="LinkedIn",
        ...     keywords="AI, automation",
        ...     target_audience="CTOs"
        ... )
    """
    logger.info(
        f"Starting post generation - Topic: {topic[:50]}..., Template: {template}, "
        f"Tone: {tone}, Platform: {platform}"
    )

    try:
        # Validate inputs
        _validate_template_and_tone(template, tone)

        if not api_key or not api_key.strip():
            logger.error("Empty API key provided")
            raise ValueError("API key cannot be empty")

        if not topic or not topic.strip():
            logger.error("Empty topic provided")
            raise ValueError("Topic cannot be empty")

        # Initialize client
        client = Anthropic(api_key=api_key)
        logger.debug("Anthropic client initialized")

        # Build platform-optimized prompt
        prompt = _build_prompt(topic, template, tone, platform, keywords, target_audience)

        # Call API with retry logic
        generated_text = _call_claude_api(client, prompt)

        # Final validation
        if not generated_text or not generated_text.strip():
            logger.error("Generated text is empty")
            return None

        logger.info(
            f"Successfully generated post: {len(generated_text)} chars, "
            f"{len(generated_text.split())} words"
        )
        return generated_text

    except (RateLimitError, APIConnectionError, APITimeoutError):
        # These are already handled by the retry decorator and logged
        # Just re-raise to be caught by the caller
        raise
    except APIError as e:
        error_msg = str(e)
        logger.error(f"Anthropic API error: {error_msg}", exc_info=True)

        # Provide user-friendly error messages
        if "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            st.error("❌ Authentication Error: Invalid API key. Please check your API key.")
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            st.error(
                "❌ Quota Error: Your API quota has been exceeded. "
                "Please check your Anthropic account."
            )
        else:
            st.error(f"❌ API Error: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating post: {str(e)}", exc_info=True)
        st.error(f"❌ Unexpected Error: {str(e)}")
        return None


def _generate_ab_test_variants(
    api_key: str,
    topic: str,
    template: str,
    tone: str,
    platform: str = "LinkedIn",
    keywords: str = "",
    target_audience: str = "",
) -> list:
    """
    Generate 3 A/B test variants with different hooks, CTAs, and formatting.

    Each variant uses a different strategy to test what resonates best
    with the audience.

    Args:
        api_key: Anthropic API key
        topic: Main topic/subject
        template: Selected template name
        tone: Desired tone
        platform: Target platform
        keywords: Optional keywords
        target_audience: Optional target audience

    Returns:
        List of variant dicts with content and metadata
    """
    client = Anthropic(api_key=api_key)
    variants = []

    for variant_name, strategy in AB_TEST_STRATEGIES.items():
        logger.info(f"Generating {variant_name} with {strategy['hook_type']} hook...")

        # Build variant-specific prompt
        variant_prompt = _build_ab_test_prompt(
            topic=topic,
            template=template,
            tone=tone,
            platform=platform,
            strategy=strategy,
            keywords=keywords,
            target_audience=target_audience,
        )

        try:
            variant_content = _call_claude_api(client, variant_prompt)

            # Calculate engagement score for this variant
            engagement_score = _calculate_engagement_score(
                content=variant_content, platform=platform, template=template, tone=tone
            )

            variant_data = {
                "variant_id": variant_name,
                "content": variant_content,
                "hook_type": strategy["hook_type"],
                "cta_type": strategy["cta_type"],
                "format_style": strategy["format_style"],
                "emoji_density": strategy["emoji_density"],
                "char_count": len(variant_content),
                "word_count": len(variant_content.split()),
                "hashtag_count": variant_content.count("#"),
                "predicted_engagement": engagement_score,
                "strategy_description": (
                    f"{strategy['hook_type'].title()} hook + {strategy['cta_type'].title()} CTA"
                ),
            }

            variants.append(variant_data)
            logger.info(f"{variant_name} generated: {engagement_score:.1f}/10 predicted engagement")

        except Exception as e:
            logger.error(f"Error generating {variant_name}: {str(e)}")
            # Continue generating other variants even if one fails
            continue

    # Sort variants by predicted engagement (best first)
    variants.sort(key=lambda x: x["predicted_engagement"], reverse=True)

    return variants


def _build_ab_test_prompt(
    topic: str,
    template: str,
    tone: str,
    platform: str,
    strategy: dict,
    keywords: str = "",
    target_audience: str = "",
) -> str:
    """
    Build a prompt for A/B test variant with specific strategy.

    Args:
        topic: Main topic
        template: Template name
        tone: Tone name
        platform: Platform name
        strategy: Strategy dict from AB_TEST_STRATEGIES
        keywords: Optional keywords
        target_audience: Optional target audience

    Returns:
        Formatted prompt string
    """
    template_info = TEMPLATES[template]
    tone_instruction = TONES[tone]
    platform_specs = PLATFORM_SPECS[platform]

    prompt = f"""{template_info["prompt_prefix"]} {topic}.

Platform: {platform}
Style: {template_info["style"]}
Tone: {tone_instruction}"""

    if target_audience:
        prompt += f"\nTarget Audience: {target_audience}"

    if "brand_voice" in st.session_state and st.session_state.brand_voice:
        bv = st.session_state.brand_voice
        prompt += (
            f"\n\nBRAND VOICE CONTEXT:\nBrand: {bv['name']}\n"
            f"Mission: {bv['mission']}\nTraits: {', '.join(bv['traits'])}"
        )

    if keywords:
        prompt += f"\nInclude these keywords naturally: {keywords}"

    # Add A/B test strategy requirements
    prompt += f"""

A/B TEST VARIANT STRATEGY:
- Hook Type: {strategy["hook_type"].upper()} - Start with
  {", or ".join(strategy["hook_examples"][:2])}
- CTA Type: {strategy["cta_type"].upper()} - End with
  {strategy["cta_examples"][0]}
- Format Style: {strategy["format_style"]}
- Emoji Density: {strategy["emoji_density"]} (low=1-2, medium=3-4, high=5+)

PLATFORM REQUIREMENTS ({platform}):
- Length: {platform_specs["optimal_length"][0]}-{platform_specs["optimal_length"][1]} words
- Character limit: {platform_specs["char_limit"] if platform_specs["char_limit"] else "No limit"}
- Hashtags: {platform_specs["hashtag_range"][0]}-{platform_specs["hashtag_range"][1]}

CRITICAL: This is variant testing. Make this version DISTINCTLY DIFFERENT from other variants by:
1. Using the specified hook type ({strategy["hook_type"]})
2. Structuring with the specified format ({strategy["format_style"]})
3. Ending with the specified CTA type ({strategy["cta_type"]})
4. Matching the emoji density ({strategy["emoji_density"]})"""

    return prompt
