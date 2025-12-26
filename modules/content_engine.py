"""
Content Engine - AI-Powered LinkedIn Post Generator.

Generates professional LinkedIn content using Claude AI with customizable
templates, tones, and target audiences.
"""

import os
import time
from functools import wraps
from typing import Any, Callable, Optional

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

    # Panel 1.5: Brand Voice
    with st.expander("🎭 Brand Voice Profiles (Optional)", expanded=False):
        st.markdown("Define a consistent voice for your brand to ensure all posts sound the same.")
        brand_name = st.text_input("Brand/User Name", placeholder="e.g., Acme Corp / Jane Doe")
        brand_mission = st.text_area(
            "Brand Mission/Value Prop", placeholder="We help SMEs automate their accounting..."
        )
        voice_traits = st.multiselect(
            "Voice Traits", ["Witty", "Direct", "Academic", "Visionary", "Pragmatic", "Edgy"]
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

    col_gen1, col_gen2 = st.columns([3, 1])

    with col_gen1:
        if st.button("✨ Generate LinkedIn Post", type="primary", use_container_width=True):
            if not topic or not topic.strip():
                logger.warning("User attempted to generate post without topic")
                st.error("❌ Please enter a topic to write about.")
            elif len(topic.strip()) < 10:
                logger.warning(f"User entered very short topic: {len(topic)} chars")
                st.error("❌ Please provide a more detailed topic (at least 10 characters).")
            else:
                logger.info(
                    f"Generating post for topic: {topic[:50]}... with template: {st.session_state.selected_template}"
                )
                with st.spinner("🤖 Claude is writing your post..."):
                    try:
                        generated_post = _generate_post(
                            api_key=api_key,
                            topic=topic.strip(),
                            template=st.session_state.selected_template,
                            tone=tone,
                            keywords=keywords.strip() if keywords else "",
                            target_audience=target_audience.strip() if target_audience else "",
                        )

                        if generated_post:
                            st.session_state.generated_post = generated_post
                            logger.info(f"Post generated successfully: {len(generated_post)} chars")
                            st.success("✅ Post generated successfully!")
                    except RateLimitError as e:
                        logger.error(f"Rate limit exceeded: {str(e)}")
                        st.error("❌ Rate limit exceeded. Please wait a moment and try again.")
                    except (APIConnectionError, APITimeoutError) as e:
                        logger.error(f"Connection error: {str(e)}")
                        st.error(
                            "❌ Connection error. Please check your internet connection and try again."
                        )
                    except Exception as e:
                        logger.error(
                            f"Unexpected error during generation: {str(e)}",
                            exc_info=True,
                        )
                        st.error(f"❌ An error occurred: {str(e)}")

    with col_gen2:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.generated_post = None
            st.rerun()

    # Panel 4: Export
    if st.session_state.generated_post:
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

        # Character count with validation
        char_count = len(st.session_state.generated_post)
        if char_count > LINKEDIN_CHAR_LIMIT:
            st.warning(
                f"⚠️ Character count: {char_count:,} exceeds LinkedIn limit: {LINKEDIN_CHAR_LIMIT:,}"
            )
        else:
            st.caption(
                f"📊 Character count: {char_count:,} (LinkedIn limit: {LINKEDIN_CHAR_LIMIT:,})"
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


def _build_prompt(
    topic: str, template: str, tone: str, keywords: str = "", target_audience: str = ""
) -> str:
    """
    Build the prompt for Claude API based on user inputs.

    Args:
        topic: Main topic/subject of the post
        template: Selected template name
        tone: Desired tone
        keywords: Optional comma-separated keywords
        target_audience: Optional target audience description

    Returns:
        Formatted prompt string for Claude API
    """
    template_info = TEMPLATES[template]
    tone_instruction = TONES[tone]

    prompt = f"""{template_info['prompt_prefix']} {topic}.

Style: {template_info['style']}
Tone: {tone_instruction}"""

    if target_audience:
        prompt += f"\nTarget Audience: {target_audience}"

    if "brand_voice" in st.session_state and st.session_state.brand_voice:
        bv = st.session_state.brand_voice
        prompt += f"\n\nBRAND VOICE CONTEXT:\nBrand: {bv['name']}\nMission: {bv['mission']}\nTraits: {', '.join(bv['traits'])}"

    if keywords:
        prompt += f"\nInclude these keywords naturally: {keywords}"

    prompt += f"""

Requirements:
- Length: {OPTIMAL_POST_MIN_WORDS}-{OPTIMAL_POST_MAX_WORDS} words (LinkedIn optimal)
- Use line breaks for readability
- Include {MIN_HASHTAGS}-{MAX_HASHTAGS} relevant hashtags at the end
- Start with a hook to grab attention
- End with a call-to-action or question
- Be authentic and engaging
- Stay within {LINKEDIN_CHAR_LIMIT} characters total"""

    logger.debug(f"Built prompt with {len(prompt)} characters")
    return prompt


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
    keywords: str = "",
    target_audience: str = "",
) -> Optional[str]:
    """
    Generate LinkedIn post using Claude API with retry logic and error handling.

    This function orchestrates the entire post generation process:
    1. Validates inputs
    2. Builds the prompt
    3. Calls Claude API (with automatic retries for transient failures)
    4. Validates and returns the response

    Args:
        api_key: Anthropic API key (must start with 'sk-ant-')
        topic: Main topic/subject of the post (min 10 characters)
        template: Selected template name (must be in TEMPLATES)
        tone: Desired tone (must be in TONES)
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
        ...     keywords="AI, automation",
        ...     target_audience="CTOs"
        ... )
    """
    logger.info(
        f"Starting post generation - Topic: {topic[:50]}..., Template: {template}, Tone: {tone}"
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

        # Build prompt
        prompt = _build_prompt(topic, template, tone, keywords, target_audience)

        # Call API with retry logic
        generated_text = _call_claude_api(client, prompt)

        # Final validation
        if not generated_text or not generated_text.strip():
            logger.error("Generated text is empty")
            return None

        logger.info(
            f"Successfully generated post: {len(generated_text)} chars, {len(generated_text.split())} words"
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
                "❌ Quota Error: Your API quota has been exceeded. Please check your Anthropic account."
            )
        else:
            st.error(f"❌ API Error: {error_msg}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error generating post: {str(e)}", exc_info=True)
        st.error(f"❌ Unexpected Error: {str(e)}")
        return None
