"""
Content Engine - AI-Powered LinkedIn Post Generator.

Generates professional LinkedIn content using Claude AI with customizable
templates, tones, and target audiences.
"""
import streamlit as st
import os
from typing import Optional
from utils.logger import get_logger

# Conditional import for Claude API
try:
    from anthropic import Anthropic, APIError
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = get_logger(__name__)

# LinkedIn Post Templates
TEMPLATES = {
    "Professional Insight": {
        "description": "Share industry insights with professional tone",
        "prompt_prefix": "Write a professional LinkedIn post sharing an industry insight about",
        "style": "Professional, informative, authoritative"
    },
    "Thought Leadership": {
        "description": "Position yourself as a thought leader",
        "prompt_prefix": "Write a thought-leadership LinkedIn post discussing",
        "style": "Visionary, forward-thinking, inspiring"
    },
    "Case Study": {
        "description": "Share a success story or case study",
        "prompt_prefix": "Write a LinkedIn post presenting a case study about",
        "style": "Story-driven, results-focused, credible"
    },
    "How-To Guide": {
        "description": "Educational content with actionable tips",
        "prompt_prefix": "Write a how-to LinkedIn post teaching professionals about",
        "style": "Educational, practical, step-by-step"
    },
    "Industry Trend": {
        "description": "Analyze current trends and predictions",
        "prompt_prefix": "Write a LinkedIn post analyzing current trends in",
        "style": "Analytical, data-informed, forward-looking"
    },
    "Personal Story": {
        "description": "Share personal experience and lessons learned",
        "prompt_prefix": "Write a personal LinkedIn post sharing a story about",
        "style": "Authentic, relatable, reflective"
    }
}

TONES = {
    "Professional": "Maintain a formal, business-appropriate tone",
    "Casual": "Use a conversational, friendly tone",
    "Inspirational": "Be motivating and uplifting",
    "Analytical": "Be data-driven and logical",
    "Storytelling": "Use narrative structure and emotional connection"
}


def render() -> None:
    """Render the Content Engine module."""
    st.title("✍️ Content Engine")
    st.markdown("### AI-Powered LinkedIn Post Generator")

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
    """Get Anthropic API key from environment or session state."""
    # Try environment variable first
    api_key = os.getenv("ANTHROPIC_API_KEY")

    # Check session state
    if not api_key and "anthropic_api_key" in st.session_state:
        api_key = st.session_state.anthropic_api_key

    return api_key


def _render_api_key_setup() -> None:
    """Render API key setup interface."""
    st.warning("🔑 **API Key Required**")
    st.markdown("""
    To use the Content Engine, you need an Anthropic API key:

    1. Get your free API key at [console.anthropic.com](https://console.anthropic.com/)
    2. Free tier includes $5 credit (≈ 1,000 LinkedIn posts)
    3. Enter your API key below (stored in session only, not saved)
    """)

    with st.form("api_key_form"):
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            placeholder="sk-ant-..."
        )
        submitted = st.form_submit_button("Save API Key")

        if submitted and api_key_input:
            st.session_state.anthropic_api_key = api_key_input
            st.success("✅ API key saved! Reload the page.")
            st.rerun()


def _render_four_panel_interface(api_key: str) -> None:
    """Render the main 4-panel interface: Input → Template → Generate → Export."""

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
            key="topic_input"
        )

    with col2:
        tone = st.selectbox(
            "Tone",
            options=list(TONES.keys()),
            help="Select the overall tone for your post"
        )

        target_audience = st.text_input(
            "Target Audience (optional)",
            placeholder="e.g., Software engineers, CTOs"
        )

    keywords = st.text_input(
        "Keywords to include (comma-separated, optional)",
        placeholder="AI, automation, productivity"
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
                use_container_width=True
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
            if not topic:
                st.error("Please enter a topic to write about.")
            else:
                with st.spinner("🤖 Claude is writing your post..."):
                    generated_post = _generate_post(
                        api_key=api_key,
                        topic=topic,
                        template=st.session_state.selected_template,
                        tone=tone,
                        keywords=keywords,
                        target_audience=target_audience
                    )

                    if generated_post:
                        st.session_state.generated_post = generated_post
                        st.success("✅ Post generated successfully!")

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
            key="preview_area"
        )

        # Character count
        char_count = len(st.session_state.generated_post)
        st.caption(f"📊 Character count: {char_count:,} (LinkedIn limit: 3,000)")

        # Export options
        col_exp1, col_exp2 = st.columns(2)

        with col_exp1:
            st.download_button(
                label="📥 Download as TXT",
                data=st.session_state.generated_post,
                file_name="linkedin_post.txt",
                mime="text/plain",
                use_container_width=True
            )

        with col_exp2:
            # Copy to clipboard using JavaScript (via markdown)
            if st.button("📋 Copy to Clipboard", use_container_width=True):
                st.code(st.session_state.generated_post, language=None)
                st.success("✅ Content displayed above - use your browser's copy function")


def _generate_post(
    api_key: str,
    topic: str,
    template: str,
    tone: str,
    keywords: str = "",
    target_audience: str = ""
) -> Optional[str]:
    """
    Generate LinkedIn post using Claude API.

    Args:
        api_key: Anthropic API key
        topic: Main topic/subject of the post
        template: Selected template name
        tone: Desired tone
        keywords: Optional comma-separated keywords
        target_audience: Optional target audience description

    Returns:
        Generated post text, or None if generation fails
    """
    try:
        client = Anthropic(api_key=api_key)

        # Build prompt
        template_info = TEMPLATES[template]
        tone_instruction = TONES[tone]

        prompt = f"""{template_info['prompt_prefix']} {topic}.

Style: {template_info['style']}
Tone: {tone_instruction}"""

        if target_audience:
            prompt += f"\nTarget Audience: {target_audience}"

        if keywords:
            prompt += f"\nInclude these keywords naturally: {keywords}"

        prompt += """

Requirements:
- Length: 150-250 words (LinkedIn optimal)
- Use line breaks for readability
- Include 3-5 relevant hashtags at the end
- Start with a hook to grab attention
- End with a call-to-action or question
- Be authentic and engaging"""

        # Call Claude API
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract generated text
        generated_text = message.content[0].text

        logger.info(f"Successfully generated post for topic: {topic[:50]}...")
        return generated_text

    except APIError as e:
        logger.error(f"Anthropic API error: {e}", exc_info=True)
        st.error(f"❌ API Error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error generating post: {e}", exc_info=True)
        st.error(f"❌ Generation failed: {str(e)}")
        return None
