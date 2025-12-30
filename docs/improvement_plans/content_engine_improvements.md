# Content Engine Module - Improvement Plan

**Module**: Content Engine (`modules/content_engine.py`)
**Current Gig Readiness**: 65%
**Target Gig Readiness**: 90%+
**Evaluator**: Module Improvement Evaluator
**Date**: 2025-12-30

---

## Executive Summary

The Content Engine currently provides AI-powered LinkedIn post generation with 6 templates and 5 tone options. While functional, it's limited to LinkedIn only and lacks critical features that social media management clients expect. This plan proposes 5 improvements to unlock $50-100/hr content strategy gigs by showcasing Google Marketing and Meta Social Media Marketing certifications.

**Top 3 Recommended Improvements** (Total Scores):
1. **Multi-Platform Content Adapter** - 37/40 points
2. **Content Performance Analytics Dashboard** - 35/40 points
3. **A/B Content Variant Generator** - 33/40 points

---

## Current State Analysis

**Strengths**:
- Robust Claude AI integration with retry logic and error handling
- Professional template system (6 templates)
- Brand voice profiles for consistency
- Character count validation for LinkedIn
- Clean 4-panel UX (Input → Template → Generate → Export)

**Critical Gaps** (from Portfolio Analysis):
- ❌ LinkedIn only (no Twitter/X, Instagram, blog, email variants)
- ❌ No A/B content variants for testing
- ❌ No content history or versioning
- ❌ No scheduling integration hooks
- ❌ No multi-post campaign planning
- ❌ No performance analytics or metrics

**Competitive Context**: Social media management clients expect multi-platform capabilities, A/B testing, and data-driven insights. Current implementation looks like a demo, not a professional toolkit.

---

## Proposed Improvements

### 1. Multi-Platform Content Adapter ⭐ TOP PICK

**Description**: Transform the LinkedIn-only generator into a multi-platform content engine that adapts posts for Twitter/X (280 chars), Instagram (2,200 chars + caption format), Facebook (63,206 chars), and email newsletters. Add platform-specific formatting rules (hashtag limits, emoji usage, link handling, thread splitting for Twitter).

**Technical Implementation**:
```python
# New constants in content_engine.py
PLATFORM_SPECS = {
    "LinkedIn": {"char_limit": 3000, "hashtags": (3, 5), "emoji_style": "professional"},
    "Twitter/X": {"char_limit": 280, "hashtags": (1, 3), "emoji_style": "casual", "thread_mode": True},
    "Instagram": {"char_limit": 2200, "hashtags": (5, 10), "emoji_style": "expressive"},
    "Facebook": {"char_limit": 63206, "hashtags": (0, 3), "emoji_style": "friendly"},
    "Email": {"char_limit": None, "subject_line": True, "preheader": True}
}

# New function
def _adapt_content_for_platform(base_content: str, source_platform: str, target_platform: str) -> dict:
    """Adapt existing content to different platform specs using Claude AI."""
    # Returns: {"content": "...", "subject": "...", "hashtags": [...], "thread": [...]}
```

**UX Changes**:
- Add platform selector dropdown in Panel 1 (default: LinkedIn)
- Add "Adapt to Other Platforms" button in Panel 4 (after generation)
- Show side-by-side preview of all platform variants
- Export as ZIP with separate files per platform

**Certification Showcase**:
- **Google Digital Marketing**: Multi-channel content strategy
- **Meta Social Media**: Instagram/Facebook best practices
- Demonstrates understanding of platform algorithms and audience behavior

**Scoring**:
- **Revenue Potential**: 10/10 - Multi-platform is ESSENTIAL for social media management gigs ($75-100/hr)
- **Wow Factor**: 9/10 - Side-by-side platform previews with auto-adaptation is impressive
- **Speed**: 8/10 - ~3.5 hours (new constants, adapt function, UI updates, basic tests)
- **Proof of Expertise**: 10/10 - Directly showcases Meta certification and cross-platform strategy

**Total Score**: 37/40

---

### 2. Content Performance Analytics Dashboard ⭐ TOP PICK

**Description**: Add a lightweight analytics panel that tracks content generation history, provides platform-specific performance predictions (engagement score, optimal posting time, audience match), and shows content improvement suggestions. Uses mock data initially but designed for real analytics API integration.

**Technical Implementation**:
```python
# New session state tracking
if "content_history" not in st.session_state:
    st.session_state.content_history = []

# After each generation
st.session_state.content_history.append({
    "timestamp": datetime.now(),
    "platform": selected_platform,
    "template": template,
    "tone": tone,
    "content": generated_post,
    "char_count": len(generated_post),
    "predicted_engagement": _calculate_engagement_score(generated_post, platform),
    "optimal_posting_time": _suggest_posting_time(platform, target_audience)
})

# New analytics panel (Panel 5)
def _render_analytics_dashboard():
    """Show content history, engagement predictions, and improvement tips."""
    st.subheader("📊 Content Performance Insights")

    # Metrics cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Posts Generated", len(st.session_state.content_history))
    with col2:
        avg_engagement = np.mean([h["predicted_engagement"] for h in history])
        st.metric("Avg Predicted Engagement", f"{avg_engagement:.1f}/10")
    with col3:
        top_template = Counter([h["template"] for h in history]).most_common(1)[0][0]
        st.metric("Top Template", top_template)
    with col4:
        top_platform = Counter([h["platform"] for h in history]).most_common(1)[0][0]
        st.metric("Top Platform", top_platform)

    # Content performance chart (engagement over time)
    fig = px.line(history_df, x="timestamp", y="predicted_engagement",
                  color="platform", title="Predicted Engagement Trends")
    st.plotly_chart(fig)

    # AI-powered improvement suggestions
    st.markdown("### 💡 AI-Powered Improvement Suggestions")
    suggestions = _generate_improvement_suggestions(st.session_state.content_history)
    for suggestion in suggestions:
        st.info(suggestion)
```

**Certification Showcase**:
- **Google Analytics**: Understanding engagement metrics and user behavior
- **Google Marketing**: Data-driven content strategy
- Demonstrates analytical thinking and ROI focus

**Scoring**:
- **Revenue Potential**: 9/10 - Clients pay premium for data-driven insights ($80-100/hr)
- **Wow Factor**: 10/10 - Charts, predictions, and AI suggestions = "I need this person"
- **Speed**: 7/10 - ~4 hours (history tracking, analytics functions, dashboard UI, chart integration)
- **Proof of Expertise**: 9/10 - Shows Google Analytics/Marketing certification application

**Total Score**: 35/40

---

### 3. A/B Content Variant Generator ⭐ TOP PICK

**Description**: Generate 3 variations of the same content brief with different hooks, CTAs, and formatting for A/B testing. Show side-by-side comparison with highlighted differences. Export as CSV with variant metadata for testing campaigns.

**Technical Implementation**:
```python
# New generation mode in Panel 3
generation_mode = st.radio("Generation Mode", ["Single Post", "A/B Test (3 Variants)"])

if generation_mode == "A/B Test (3 Variants)":
    # Generate 3 variants with different strategies
    variants = []
    variant_strategies = [
        {"hook": "question", "cta": "comment", "format": "short_paragraphs"},
        {"hook": "statistic", "cta": "share", "format": "bullet_points"},
        {"hook": "story", "cta": "link_click", "format": "narrative"}
    ]

    for i, strategy in enumerate(variant_strategies):
        variant_prompt = _build_ab_test_prompt(topic, template, tone, strategy)
        variant = _call_claude_api(client, variant_prompt)
        variants.append({
            "variant_id": f"Variant {chr(65+i)}",  # A, B, C
            "content": variant,
            "hook_type": strategy["hook"],
            "cta_type": strategy["cta"],
            "format": strategy["format"],
            "predicted_engagement": _calculate_engagement_score(variant, platform)
        })

    # Panel 4: A/B Test Comparison View
    st.subheader("📤 Panel 4: A/B Test Variants")

    # Side-by-side comparison
    cols = st.columns(3)
    for i, variant in enumerate(variants):
        with cols[i]:
            st.markdown(f"### {variant['variant_id']}")
            st.caption(f"Hook: {variant['hook_type']} | CTA: {variant['cta_type']}")
            st.text_area(f"Content {variant['variant_id']}", variant['content'], height=300)
            st.metric("Predicted Engagement", f"{variant['predicted_engagement']:.1f}/10")

    # Export all variants as CSV
    df = pd.DataFrame(variants)
    st.download_button(
        label="📥 Download A/B Test Package (CSV)",
        data=df.to_csv(index=False),
        file_name=f"ab_test_variants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
```

**Certification Showcase**:
- **Google Marketing**: A/B testing methodology and conversion optimization
- **Meta Social Media**: Facebook/Instagram A/B testing best practices
- Demonstrates scientific approach to content optimization

**Scoring**:
- **Revenue Potential**: 9/10 - A/B testing is core to content strategy gigs ($75-100/hr)
- **Wow Factor**: 9/10 - Side-by-side variants with predictions is very professional
- **Speed**: 8/10 - ~3 hours (variant logic, comparison UI, CSV export, basic tests)
- **Proof of Expertise**: 7/10 - Shows testing methodology but less certification-specific

**Total Score**: 33/40

---

### 4. Content Scheduling Integration Hooks

**Description**: Add scheduling metadata to generated posts (optimal posting time, timezone, frequency recommendations) and export in formats compatible with Buffer, Hootsuite, Later (CSV imports). Include UTM parameter generator for link tracking.

**Technical Implementation**:
```python
# Scheduling metadata
def _suggest_posting_schedule(platform: str, target_audience: str, num_posts: int = 7) -> list:
    """Suggest optimal posting times for a week based on platform and audience."""
    # Uses industry best practices:
    # LinkedIn: Tue-Thu 9am-12pm
    # Twitter: Daily 12pm-3pm
    # Instagram: Mon/Wed/Fri 11am-2pm

    schedule = []
    for day in range(num_posts):
        schedule.append({
            "date": (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d"),
            "time": _get_optimal_time(platform, target_audience),
            "timezone": "America/New_York",  # Configurable
            "platform": platform
        })
    return schedule

# UTM parameter generator
def _generate_utm_params(campaign_name: str, source: str, medium: str) -> str:
    """Generate UTM tracking parameters for links."""
    return f"?utm_source={source}&utm_medium={medium}&utm_campaign={campaign_name}"

# Export with scheduling metadata
export_data = {
    "content": generated_post,
    "platform": platform,
    "scheduled_time": schedule[0]["date"] + " " + schedule[0]["time"],
    "timezone": schedule[0]["timezone"],
    "utm_params": _generate_utm_params(campaign_name, platform, "social")
}

# Export as Buffer/Hootsuite compatible CSV
st.download_button(
    label="📥 Download for Buffer/Hootsuite",
    data=_export_for_scheduler(export_data),
    file_name="content_schedule.csv"
)
```

**Certification Showcase**:
- **Google Marketing**: Campaign tracking and UTM parameters
- **Meta Social Media**: Optimal posting times and audience engagement patterns

**Scoring**:
- **Revenue Potential**: 8/10 - Scheduling is important but not a core differentiator
- **Wow Factor**: 7/10 - Useful but not visually impressive
- **Speed**: 9/10 - ~2.5 hours (scheduling logic, export formats, UTM generator)
- **Proof of Expertise**: 8/10 - Shows practical campaign management knowledge

**Total Score**: 32/40

---

### 5. Multi-Post Campaign Planner

**Description**: Plan a 7-day (or custom) content campaign with thematic consistency. Generate a series of related posts that build on each other (e.g., Monday: introduce topic, Wednesday: deep dive, Friday: case study). Export as campaign calendar with preview grid.

**Technical Implementation**:
```python
# Campaign planner UI
st.subheader("📅 Multi-Post Campaign Planner")

campaign_theme = st.text_input("Campaign Theme", placeholder="Q1 Product Launch")
campaign_duration = st.slider("Campaign Duration (days)", 3, 14, 7)
posts_per_week = st.slider("Posts per Week", 1, 7, 3)

if st.button("🚀 Generate Campaign"):
    # Generate campaign arc
    campaign_arc = [
        {"day": 1, "angle": "introduction", "template": "Professional Insight"},
        {"day": 3, "angle": "deep_dive", "template": "Thought Leadership"},
        {"day": 5, "angle": "case_study", "template": "Case Study"},
        {"day": 7, "angle": "call_to_action", "template": "Personal Story"}
    ]

    campaign_posts = []
    for post_plan in campaign_arc:
        prompt = _build_campaign_post_prompt(
            theme=campaign_theme,
            angle=post_plan["angle"],
            template=post_plan["template"],
            previous_posts=campaign_posts  # Maintain consistency
        )
        post = _call_claude_api(client, prompt)
        campaign_posts.append({
            "day": post_plan["day"],
            "angle": post_plan["angle"],
            "template": post_plan["template"],
            "content": post
        })

    # Show campaign calendar grid
    st.markdown("### 📅 Campaign Calendar Preview")
    for post in campaign_posts:
        with st.expander(f"Day {post['day']}: {post['angle'].replace('_', ' ').title()}"):
            st.caption(f"Template: {post['template']}")
            st.text_area("Content", post['content'], height=200, key=f"campaign_day_{post['day']}")

    # Export as campaign package
    campaign_df = pd.DataFrame(campaign_posts)
    st.download_button(
        label="📥 Download Campaign Package",
        data=campaign_df.to_csv(index=False),
        file_name=f"campaign_{campaign_theme.lower().replace(' ', '_')}.csv"
    )
```

**Certification Showcase**:
- **Google Marketing**: Campaign planning and content sequencing
- **Meta Social Media**: Multi-post storytelling and engagement strategies

**Scoring**:
- **Revenue Potential**: 8/10 - Campaign planning is valuable but niche
- **Wow Factor**: 8/10 - Calendar grid and thematic consistency is impressive
- **Speed**: 6/10 - ~4.5 hours (campaign logic, arc planning, calendar UI, export)
- **Proof of Expertise**: 8/10 - Shows strategic content planning capabilities

**Total Score**: 30/40

---

## Scoring Summary

| Improvement | Revenue | Wow | Speed | Expertise | Total |
|-------------|---------|-----|-------|-----------|-------|
| 1. Multi-Platform Content Adapter ⭐ | 10 | 9 | 8 | 10 | **37** |
| 2. Content Performance Analytics Dashboard ⭐ | 9 | 10 | 7 | 9 | **35** |
| 3. A/B Content Variant Generator ⭐ | 9 | 9 | 8 | 7 | **33** |
| 4. Content Scheduling Integration Hooks | 8 | 7 | 9 | 8 | 32 |
| 5. Multi-Post Campaign Planner | 8 | 8 | 6 | 8 | 30 |

---

## Top 3 Implementation Specs

### IMPLEMENTATION SPEC #1: Multi-Platform Content Adapter

**File**: `modules/content_engine.py`

**Changes Required**:

1. **Add platform constants** (after line 45):
```python
# Platform-specific specifications
PLATFORM_SPECS = {
    "LinkedIn": {
        "char_limit": 3000,
        "optimal_length": (150, 250),  # words
        "hashtag_range": (3, 5),
        "emoji_style": "professional",
        "formatting": "paragraphs_with_breaks",
        "link_style": "inline"
    },
    "Twitter/X": {
        "char_limit": 280,
        "optimal_length": (30, 50),  # words
        "hashtag_range": (1, 3),
        "emoji_style": "casual",
        "formatting": "single_paragraph",
        "link_style": "shortened",
        "thread_mode": True,
        "thread_tweet_limit": 280
    },
    "Instagram": {
        "char_limit": 2200,
        "optimal_length": (100, 150),  # words
        "hashtag_range": (5, 10),
        "emoji_style": "expressive",
        "formatting": "caption_with_breaks",
        "link_style": "bio_link"
    },
    "Facebook": {
        "char_limit": 63206,
        "optimal_length": (100, 200),  # words
        "hashtag_range": (0, 3),
        "emoji_style": "friendly",
        "formatting": "paragraphs",
        "link_style": "inline"
    },
    "Email Newsletter": {
        "char_limit": None,
        "optimal_length": (300, 500),  # words
        "subject_line_limit": 60,
        "preheader_limit": 100,
        "formatting": "html_email",
        "link_style": "call_to_action_buttons"
    }
}
```

2. **Add platform selector** in Panel 1 (after line 318):
```python
# Platform Selection
platform = st.selectbox(
    "Target Platform",
    options=list(PLATFORM_SPECS.keys()),
    index=0,  # Default to LinkedIn
    help="Select the social media platform for optimized formatting"
)

# Show platform specs
specs = PLATFORM_SPECS[platform]
st.caption(
    f"📱 {platform} specs: {specs['char_limit']} char limit | "
    f"{specs['hashtag_range'][0]}-{specs['hashtag_range'][1]} hashtags | "
    f"{specs['emoji_style']} emoji style"
)
```

3. **Update prompt builder** to include platform specs (modify `_build_prompt` function):
```python
def _build_prompt(
    topic: str,
    template: str,
    tone: str,
    platform: str = "LinkedIn",
    keywords: str = "",
    target_audience: str = ""
) -> str:
    """Build platform-optimized prompt."""
    template_info = TEMPLATES[template]
    tone_instruction = TONES[tone]
    platform_specs = PLATFORM_SPECS[platform]

    prompt = f"""{template_info['prompt_prefix']} {topic}.

Platform: {platform}
Style: {template_info['style']}
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
- Character limit: {char_limit if char_limit else 'No limit'}
- Hashtags: {hashtag_range[0]}-{hashtag_range[1]} relevant hashtags
- Emoji style: {platform_specs['emoji_style']}
- Formatting: {platform_specs['formatting']}
"""

    # Special handling for Twitter threads
    if platform == "Twitter/X" and platform_specs.get("thread_mode"):
        prompt += f"""
- If content exceeds {platform_specs['thread_tweet_limit']} chars, split into thread (2-5 tweets)
- Each tweet must be standalone but build on previous
- Number tweets (1/n, 2/n, etc.)
"""

    # Special handling for email
    if platform == "Email Newsletter":
        prompt += f"""
- Include subject line (max {platform_specs['subject_line_limit']} chars)
- Include preheader (max {platform_specs['preheader_limit']} chars)
- Structure: subject line, preheader, then main content
"""

    prompt += """
- Start with a hook to grab attention
- End with a call-to-action appropriate for the platform
- Be authentic and engaging"""

    logger.debug(f"Built platform-optimized prompt for {platform}: {len(prompt)} characters")
    return prompt
```

4. **Add platform adaptation function** (new function after `_build_prompt`):
```python
def _adapt_content_for_platform(
    base_content: str,
    original_platform: str,
    target_platform: str,
    topic: str,
    api_key: str
) -> dict:
    """
    Adapt existing content from one platform to another.

    Args:
        base_content: The original generated content
        original_platform: Source platform name
        target_platform: Target platform name
        topic: Original topic for context
        api_key: Anthropic API key

    Returns:
        dict with adapted content and metadata
    """
    target_specs = PLATFORM_SPECS[target_platform]

    adaptation_prompt = f"""Adapt the following {original_platform} post for {target_platform}.

ORIGINAL POST ({original_platform}):
{base_content}

TARGET PLATFORM: {target_platform}
Requirements:
- Character limit: {target_specs['char_limit'] if target_specs['char_limit'] else 'No limit'}
- Optimal length: {target_specs['optimal_length'][0]}-{target_specs['optimal_length'][1]} words
- Hashtags: {target_specs['hashtag_range'][0]}-{target_specs['hashtag_range'][1]}
- Emoji style: {target_specs['emoji_style']}
- Formatting: {target_specs['formatting']}

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
            "specs": target_specs
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
            result["thread"] = tweets

        logger.info(f"Successfully adapted content from {original_platform} to {target_platform}")
        return result

    except Exception as e:
        logger.error(f"Error adapting content: {str(e)}")
        return {
            "platform": target_platform,
            "content": base_content,  # Fallback to original
            "error": str(e)
        }
```

5. **Add multi-platform export** in Panel 4 (after line 468):
```python
# Multi-platform adaptation
st.markdown("---")
st.markdown("#### 🌐 Adapt to Other Platforms")

col_adapt1, col_adapt2 = st.columns([3, 1])

with col_adapt1:
    target_platforms = st.multiselect(
        "Select platforms to adapt content for:",
        options=[p for p in PLATFORM_SPECS.keys() if p != platform],
        default=["Twitter/X", "Instagram"] if platform == "LinkedIn" else ["LinkedIn"]
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
                        api_key=api_key
                    )
                    adapted_variants[target] = adapted

                st.session_state.adapted_variants = adapted_variants
                st.success(f"✅ Adapted to {len(target_platforms)} platforms!")

# Show adapted variants
if "adapted_variants" in st.session_state and st.session_state.adapted_variants:
    st.markdown("#### 📱 Platform Adaptations")

    # Create tabs for each platform
    platform_tabs = st.tabs([platform] + list(st.session_state.adapted_variants.keys()))

    # Original platform
    with platform_tabs[0]:
        st.caption(f"Original ({platform})")
        st.text_area(
            f"{platform} Content",
            value=st.session_state.generated_post,
            height=250,
            key=f"preview_{platform}"
        )
        st.caption(f"📊 {len(st.session_state.generated_post)} characters")

    # Adapted platforms
    for i, (adapt_platform, adapt_data) in enumerate(st.session_state.adapted_variants.items(), 1):
        with platform_tabs[i]:
            st.caption(f"Adapted for {adapt_platform}")

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
                for idx, tweet in enumerate(adapt_data['thread'], 1):
                    st.text_area(
                        f"Tweet {idx}/{len(adapt_data['thread'])}",
                        value=tweet,
                        height=100,
                        key=f"tweet_{idx}"
                    )
            else:
                st.text_area(
                    f"{adapt_platform} Content",
                    value=adapt_data["content"],
                    height=250,
                    key=f"preview_{adapt_platform}"
                )

            st.caption(f"📊 {adapt_data['char_count']} characters")

    # Export all platforms as ZIP
    st.markdown("---")
    if st.button("📦 Download Multi-Platform Package (ZIP)", use_container_width=True):
        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            # Add original
            zip_file.writestr(f"{platform.lower().replace('/', '_')}_post.txt",
                            st.session_state.generated_post)

            # Add adaptations
            for adapt_platform, adapt_data in st.session_state.adapted_variants.items():
                filename = f"{adapt_platform.lower().replace('/', '_')}_post.txt"

                if adapt_platform == "Email Newsletter" and "subject" in adapt_data:
                    content = f"Subject: {adapt_data['subject']}\n"
                    content += f"Preheader: {adapt_data['preheader']}\n\n"
                    content += adapt_data['content']
                    zip_file.writestr(filename, content)
                elif adapt_platform == "Twitter/X" and "thread" in adapt_data:
                    thread_content = "\n\n---\n\n".join(
                        [f"Tweet {i+1}/{len(adapt_data['thread'])}:\n{tweet}"
                         for i, tweet in enumerate(adapt_data['thread'])]
                    )
                    zip_file.writestr(filename, thread_content)
                else:
                    zip_file.writestr(filename, adapt_data['content'])

        st.download_button(
            label="📦 Download ZIP",
            data=zip_buffer.getvalue(),
            file_name=f"multi_platform_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            use_container_width=True
        )
```

6. **Update `_generate_post` function call** to include platform parameter (line 393):
```python
generated_post = _generate_post(
    api_key=api_key,
    topic=topic.strip(),
    template=st.session_state.selected_template,
    tone=tone,
    platform=platform,  # ADD THIS
    keywords=keywords.strip() if keywords else "",
    target_audience=target_audience.strip() if target_audience else "",
)
```

7. **Update `_generate_post` signature** (line 585):
```python
def _generate_post(
    api_key: str,
    topic: str,
    template: str,
    tone: str,
    platform: str = "LinkedIn",  # ADD THIS
    keywords: str = "",
    target_audience: str = "",
) -> Optional[str]:
```

8. **Add import for datetime and zipfile** (after line 11):
```python
from datetime import datetime
```

**Testing Checklist**:
- [ ] Platform selector displays all 5 platforms
- [ ] Each platform generates content within character limits
- [ ] Twitter thread mode works (splits long content into tweets)
- [ ] Email format includes subject, preheader, body
- [ ] Hashtag counts match platform specs
- [ ] Multi-platform adaptation generates different versions
- [ ] ZIP export includes all platform files
- [ ] Character counts update dynamically

**Estimated Implementation Time**: 3.5 hours

---

### IMPLEMENTATION SPEC #2: Content Performance Analytics Dashboard

**File**: `modules/content_engine.py`

**Changes Required**:

1. **Add imports** (after line 11):
```python
from datetime import datetime, timedelta
from collections import Counter
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
```

2. **Initialize content history** in session state (after line 291):
```python
# Initialize session state for generated content
if "generated_post" not in st.session_state:
    st.session_state.generated_post = None

if "content_history" not in st.session_state:
    st.session_state.content_history = []

if "analytics_enabled" not in st.session_state:
    st.session_state.analytics_enabled = True
```

3. **Add engagement score calculator** (new function after `_validate_template_and_tone`):
```python
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
    cta_keywords = ["comment", "share", "thoughts", "agree", "think", "experience", "click", "learn more"]
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
    hook_indicators = ["did you know", "imagine", "what if", "here's", "stop", "don't", "ever wonder"]
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
            "reasoning": "B2B professionals check LinkedIn during work hours, mid-week has highest engagement"
        },
        "Twitter/X": {
            "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
            "time_range": "12:00 PM - 3:00 PM",
            "peak_time": "1:00 PM",
            "timezone": "EST",
            "reasoning": "Lunch hour browsing, consistent weekday engagement"
        },
        "Instagram": {
            "days": ["Monday", "Wednesday", "Friday"],
            "time_range": "11:00 AM - 2:00 PM",
            "peak_time": "12:00 PM",
            "timezone": "EST",
            "reasoning": "Visual content performs best during midday breaks"
        },
        "Facebook": {
            "days": ["Wednesday", "Thursday", "Friday"],
            "time_range": "1:00 PM - 4:00 PM",
            "peak_time": "2:00 PM",
            "timezone": "EST",
            "reasoning": "Afternoon browsing peaks mid-to-late week"
        },
        "Email Newsletter": {
            "days": ["Tuesday", "Thursday"],
            "time_range": "10:00 AM - 11:00 AM",
            "peak_time": "10:00 AM",
            "timezone": "EST",
            "reasoning": "Morning inbox clearing, avoiding Monday overwhelm and Friday checkout"
        }
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
```

4. **Track content history after generation** (modify Panel 3, after line 404):
```python
if generated_post:
    st.session_state.generated_post = generated_post

    # Track in content history
    if st.session_state.analytics_enabled:
        engagement_score = _calculate_engagement_score(
            content=generated_post,
            platform=platform,
            template=st.session_state.selected_template,
            tone=tone
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
            "optimal_posting_day": posting_time["days"][0]
        }

        st.session_state.content_history.append(history_entry)
        logger.info(f"Tracked content in history: {len(st.session_state.content_history)} total posts")

    logger.info(f"Post generated successfully: {len(generated_post)} chars")
    st.success("✅ Post generated successfully!")
```

5. **Add analytics dashboard** (new Panel 5, after Panel 4 export section around line 468):
```python
# Panel 5: Analytics Dashboard
if st.session_state.content_history:
    st.markdown("---")
    st.subheader("📊 Panel 5: Content Performance Analytics")

    # Toggle analytics
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
        hover_data=["template", "tone"]
    )
    fig_engagement.update_layout(height=400)
    st.plotly_chart(fig_engagement, use_container_width=True)

    # Chart 2: Template & Platform Performance
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### Template Performance")
        template_avg = df_history.groupby("template")["predicted_engagement"].mean().reset_index()
        template_avg = template_avg.sort_values("predicted_engagement", ascending=False)

        fig_template = px.bar(
            template_avg,
            x="predicted_engagement",
            y="template",
            orientation="h",
            title="Avg Engagement by Template",
            labels={"predicted_engagement": "Avg Score", "template": ""}
        )
        fig_template.update_layout(height=300)
        st.plotly_chart(fig_template, use_container_width=True)

    with col_chart2:
        st.markdown("##### Platform Performance")
        platform_avg = df_history.groupby("platform")["predicted_engagement"].mean().reset_index()
        platform_avg = platform_avg.sort_values("predicted_engagement", ascending=False)

        fig_platform = px.bar(
            platform_avg,
            x="predicted_engagement",
            y="platform",
            orientation="h",
            title="Avg Engagement by Platform",
            labels={"predicted_engagement": "Avg Score", "platform": ""}
        )
        fig_platform.update_layout(height=300)
        st.plotly_chart(fig_platform, use_container_width=True)

    # Chart 3: Posting Time Recommendations Heatmap
    st.markdown("#### 🕐 Optimal Posting Times (All Posts)")
    posting_times = df_history.groupby(["optimal_posting_day", "platform"]).size().reset_index(name="count")

    if not posting_times.empty:
        # Create heatmap-style visualization
        fig_heatmap = px.bar(
            posting_times,
            x="optimal_posting_day",
            y="count",
            color="platform",
            title="Recommended Posting Days by Platform",
            labels={"count": "Number of Posts", "optimal_posting_day": "Day of Week"}
        )
        fig_heatmap.update_layout(height=350)
        st.plotly_chart(fig_heatmap, use_container_width=True)

    # AI-Powered Improvement Suggestions
    st.markdown("#### 💡 AI-Powered Improvement Suggestions")

    suggestions = _generate_improvement_suggestions(history)

    for i, suggestion in enumerate(suggestions, 1):
        suggestion_type = suggestion["type"]
        icon = {"success": "✅", "warning": "⚠️", "info": "💡", "tip": "🎯"}[suggestion_type]

        if suggestion_type == "success":
            st.success(f"{icon} {suggestion['message']}")
        elif suggestion_type == "warning":
            st.warning(f"{icon} {suggestion['message']}")
        else:
            st.info(f"{icon} {suggestion['message']}")

    # Content History Table (expandable)
    with st.expander("📋 View Full Content History"):
        # Display table with key metrics
        display_df = df_history[[
            "timestamp", "platform", "template", "tone",
            "predicted_engagement", "word_count", "hashtag_count"
        ]].copy()
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
                    "Engagement Score",
                    format="%.1f ⭐"
                ),
                "word_count": "Words",
                "hashtag_count": "Hashtags"
            },
            hide_index=True,
            use_container_width=True
        )

        # Export history as CSV
        csv_data = df_history.to_csv(index=False)
        st.download_button(
            label="📥 Download History (CSV)",
            data=csv_data,
            file_name=f"content_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
```

6. **Add improvement suggestions function** (new function after `_suggest_posting_time`):
```python
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
        return [{"type": "info", "message": "Generate more content to receive personalized suggestions!"}]

    df = pd.DataFrame(history)

    # Suggestion 1: Template optimization
    template_performance = df.groupby("template")["predicted_engagement"].mean()
    best_template = template_performance.idxmax()
    worst_template = template_performance.idxmin()

    if len(template_performance) >= 3 and template_performance[best_template] - template_performance[worst_template] > 1.5:
        suggestions.append({
            "type": "tip",
            "message": f"Your '{best_template}' template performs {template_performance[best_template] - template_performance[worst_template]:.1f} points better than '{worst_template}'. Consider using it more often!"
        })

    # Suggestion 2: Platform optimization
    if len(df["platform"].unique()) > 1:
        platform_performance = df.groupby("platform")["predicted_engagement"].mean()
        best_platform = platform_performance.idxmax()
        suggestions.append({
            "type": "success",
            "message": f"Your content performs best on {best_platform} (avg score: {platform_performance[best_platform]:.1f}). This platform aligns well with your style!"
        })

    # Suggestion 3: Content length optimization
    avg_engagement = df["predicted_engagement"].mean()
    high_performers = df[df["predicted_engagement"] >= avg_engagement + 1.0]

    if not high_performers.empty:
        avg_words_high = high_performers["word_count"].mean()
        avg_words_all = df["word_count"].mean()

        if abs(avg_words_high - avg_words_all) > 30:
            direction = "longer" if avg_words_high > avg_words_all else "shorter"
            suggestions.append({
                "type": "tip",
                "message": f"Your high-engagement posts are {direction} (avg {avg_words_high:.0f} words vs {avg_words_all:.0f}). Try adjusting content length!"
            })

    # Suggestion 4: Hashtag optimization
    avg_hashtags = df["hashtag_count"].mean()
    optimal_hashtags = df.groupby("platform")["hashtag_count"].mean()

    for platform, avg_ht in optimal_hashtags.items():
        platform_spec = PLATFORM_SPECS[platform]
        min_ht, max_ht = platform_spec["hashtag_range"]

        if avg_ht < min_ht:
            suggestions.append({
                "type": "warning",
                "message": f"You're using {avg_ht:.1f} hashtags on {platform} (recommended: {min_ht}-{max_ht}). Add more hashtags for better discoverability!"
            })
        elif avg_ht > max_ht:
            suggestions.append({
                "type": "warning",
                "message": f"You're using {avg_ht:.1f} hashtags on {platform} (recommended: {min_ht}-{max_ht}). Reduce hashtags to avoid looking spammy!"
            })

    # Suggestion 5: Consistency
    if len(history) >= 5:
        recent_5 = df.tail(5)
        engagement_std = recent_5["predicted_engagement"].std()

        if engagement_std < 1.0:
            suggestions.append({
                "type": "success",
                "message": f"Great consistency! Your last 5 posts have similar engagement scores (std dev: {engagement_std:.2f}). You've found your rhythm!"
            })
        elif engagement_std > 2.5:
            suggestions.append({
                "type": "warning",
                "message": f"High variability in recent posts (std dev: {engagement_std:.2f}). Review your top performers to identify winning patterns!"
            })

    # Suggestion 6: Tone optimization
    if len(df["tone"].unique()) >= 3:
        tone_performance = df.groupby("tone")["predicted_engagement"].mean()
        best_tone = tone_performance.idxmax()
        suggestions.append({
            "type": "tip",
            "message": f"'{best_tone}' tone shows strongest engagement (avg: {tone_performance[best_tone]:.1f}). This resonates with your audience!"
        })

    # Suggestion 7: Growth trajectory
    if len(history) >= 10:
        recent_half = df.tail(len(df) // 2)
        earlier_half = df.head(len(df) // 2)

        recent_avg = recent_half["predicted_engagement"].mean()
        earlier_avg = earlier_half["predicted_engagement"].mean()

        if recent_avg > earlier_avg + 0.5:
            suggestions.append({
                "type": "success",
                "message": f"📈 Your content quality is improving! Recent posts score {recent_avg - earlier_avg:.1f} points higher than earlier ones!"
            })
        elif earlier_avg > recent_avg + 0.5:
            suggestions.append({
                "type": "info",
                "message": f"📉 Recent engagement is lower. Review your earlier high performers (avg: {earlier_avg:.1f}) for inspiration!"
            })

    # Default suggestion if none generated
    if not suggestions:
        suggestions.append({
            "type": "info",
            "message": "Keep creating! Generate more content to unlock personalized insights and recommendations."
        })

    return suggestions[:5]  # Limit to top 5 suggestions
```

**Testing Checklist**:
- [ ] Content history tracks all generations
- [ ] Engagement score calculator returns 1-10 range
- [ ] Posting time recommendations match platform best practices
- [ ] Metrics cards display correct aggregations
- [ ] Engagement trend chart renders correctly
- [ ] Template/platform performance bars show accurate averages
- [ ] Improvement suggestions are contextual and actionable
- [ ] CSV export includes all history fields
- [ ] Clear history button resets analytics

**Estimated Implementation Time**: 4 hours

---

### IMPLEMENTATION SPEC #3: A/B Content Variant Generator

**File**: `modules/content_engine.py`

**Changes Required**:

1. **Add variant strategy constants** (after PLATFORM_SPECS around line 100):
```python
# A/B Testing Variant Strategies
AB_TEST_STRATEGIES = {
    "Variant A": {
        "hook_type": "question",
        "hook_examples": ["Have you ever wondered...", "What if...", "Did you know..."],
        "cta_type": "comment",
        "cta_examples": ["Share your thoughts below!", "What's your experience?", "Let me know in the comments!"],
        "format_style": "short_paragraphs",
        "emoji_density": "low"
    },
    "Variant B": {
        "hook_type": "statistic",
        "hook_examples": ["X% of professionals...", "Research shows...", "According to data..."],
        "cta_type": "share",
        "cta_examples": ["Share this with your network!", "Tag someone who needs this!", "Pass this along!"],
        "format_style": "bullet_points",
        "emoji_density": "medium"
    },
    "Variant C": {
        "hook_type": "story",
        "hook_examples": ["Last week, I...", "Here's what happened...", "Let me tell you about..."],
        "cta_type": "link_click",
        "cta_examples": ["Learn more in the link!", "Check out the full story!", "Read the details here!"],
        "format_style": "narrative_flow",
        "emoji_density": "high"
    }
}
```

2. **Add generation mode selector** in Panel 3 (before generate button, around line 376):
```python
# Panel 3: Generate
st.markdown("---")
st.subheader("🤖 Panel 3: Generate Content")

# Generation mode selector
generation_mode = st.radio(
    "Generation Mode",
    options=["Single Post", "A/B Test (3 Variants)"],
    index=0,
    horizontal=True,
    help="Single: Generate one optimized post | A/B Test: Generate 3 variants for testing"
)

if generation_mode == "A/B Test (3 Variants)":
    st.info(
        "💡 **A/B Testing Mode**: Generates 3 content variants with different hooks, CTAs, "
        "and formatting for split testing. Perfect for optimizing engagement!"
    )

col_gen1, col_gen2 = st.columns([3, 1])
```

3. **Update generate button logic** (replace existing button logic around line 379):
```python
with col_gen1:
    button_label = "✨ Generate LinkedIn Post" if generation_mode == "Single Post" else "✨ Generate A/B Test Variants"

    if st.button(button_label, type="primary", use_container_width=True):
        if not topic or not topic.strip():
            logger.warning("User attempted to generate post without topic")
            st.error("❌ Please enter a topic to write about.")
        elif len(topic.strip()) < 10:
            logger.warning(f"User entered very short topic: {len(topic)} chars")
            st.error("❌ Please provide a more detailed topic (at least 10 characters).")
        else:
            if generation_mode == "Single Post":
                # EXISTING SINGLE POST GENERATION (keep existing code)
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

                            # Track in content history (existing analytics code)
                            if st.session_state.analytics_enabled:
                                engagement_score = _calculate_engagement_score(
                                    content=generated_post,
                                    platform=platform,
                                    template=st.session_state.selected_template,
                                    tone=tone
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
                                    "optimal_posting_day": posting_time["days"][0]
                                }

                                st.session_state.content_history.append(history_entry)

                            logger.info(f"Post generated successfully: {len(generated_post)} chars")
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

            else:  # A/B Test Mode - NEW CODE
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
                            logger.info(f"Successfully generated {len(variants)} A/B test variants")
                            st.success(f"✅ Generated {len(variants)} variants for A/B testing!")

                    except Exception as e:
                        logger.error(f"Error generating A/B variants: {str(e)}", exc_info=True)
                        st.error(f"❌ An error occurred: {str(e)}")
```

4. **Add A/B variant generation function** (new function after `_generate_post`):
```python
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
            target_audience=target_audience
        )

        try:
            variant_content = _call_claude_api(client, variant_prompt)

            # Calculate engagement score for this variant
            engagement_score = _calculate_engagement_score(
                content=variant_content,
                platform=platform,
                template=template,
                tone=tone
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
                "strategy_description": f"{strategy['hook_type'].title()} hook + {strategy['cta_type'].title()} CTA"
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
    target_audience: str = ""
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

    prompt = f"""{template_info['prompt_prefix']} {topic}.

Platform: {platform}
Style: {template_info['style']}
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
- Hook Type: {strategy['hook_type'].upper()} - Start with {', or '.join(strategy['hook_examples'][:2])}
- CTA Type: {strategy['cta_type'].upper()} - End with {strategy['cta_examples'][0]}
- Format Style: {strategy['format_style']}
- Emoji Density: {strategy['emoji_density']} (low=1-2, medium=3-4, high=5+)

PLATFORM REQUIREMENTS ({platform}):
- Length: {platform_specs['optimal_length'][0]}-{platform_specs['optimal_length'][1]} words
- Character limit: {platform_specs['char_limit'] if platform_specs['char_limit'] else 'No limit'}
- Hashtags: {platform_specs['hashtag_range'][0]}-{platform_specs['hashtag_range'][1]}

CRITICAL: This is variant testing. Make this version DISTINCTLY DIFFERENT from other variants by:
1. Using the specified hook type ({strategy['hook_type']})
2. Structuring with the specified format ({strategy['format_style']})
3. Ending with the specified CTA type ({strategy['cta_type']})
4. Matching the emoji density ({strategy['emoji_density']})"""

    return prompt
```

5. **Add A/B test comparison view** (replace Panel 4 when variants exist, after line 428):
```python
# Panel 4: Export (single post) or A/B Comparison (variants)
if st.session_state.generated_post and "ab_test_variants" not in st.session_state:
    # EXISTING SINGLE POST EXPORT CODE (keep as-is)
    st.markdown("---")
    st.subheader("📤 Panel 4: Preview & Export")

    # ... (keep all existing export code)

elif "ab_test_variants" in st.session_state and st.session_state.ab_test_variants:
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
            st.metric(
                f"{medal} {variant['variant_id']}",
                f"{variant['predicted_engagement']:.1f}/10",
                delta=f"{variant['predicted_engagement'] - variants[-1]['predicted_engagement']:.1f} vs worst" if i < len(variants) - 1 else None
            )
            st.caption(variant['strategy_description'])

    # Side-by-side variant comparison
    st.markdown("#### 📋 Variant Content Comparison")

    variant_tabs = st.tabs([v['variant_id'] for v in variants])

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
                value=variant['content'],
                height=300,
                key=f"variant_{variant['variant_id']}_preview",
                label_visibility="collapsed"
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
                engagement_color = "🟢" if variant['predicted_engagement'] >= 7.5 else "🟡" if variant['predicted_engagement'] >= 5.5 else "🔴"
                st.caption(f"{engagement_color} **{variant['predicted_engagement']:.1f}/10** engagement")

    # Difference Highlighter
    with st.expander("🔍 Key Differences Between Variants"):
        st.markdown("**Opening Hook Comparison:**")
        for variant in variants:
            first_line = variant['content'].split("\n")[0]
            st.markdown(f"- **{variant['variant_id']}** ({variant['hook_type']}): _{first_line}_")

        st.markdown("\n**Closing CTA Comparison:**")
        for variant in variants:
            last_lines = variant['content'].strip().split("\n")[-2:]
            cta = " ".join(last_lines)
            st.markdown(f"- **{variant['variant_id']}** ({variant['cta_type']}): _{cta}_")

    # Recommendation
    best_variant = variants[0]
    st.success(
        f"💡 **Recommendation:** Based on predicted engagement, start with **{best_variant['variant_id']}** "
        f"({best_variant['predicted_engagement']:.1f}/10). Test all 3 variants to find your winning formula!"
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
            use_container_width=True
        )

    with export_cols[1]:
        # Export as TXT files in ZIP
        import io
        import zipfile

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for variant in variants:
                filename = f"{variant['variant_id'].lower().replace(' ', '_')}_post.txt"
                header = f"""A/B TEST {variant['variant_id']}
Hook: {variant['hook_type']}
CTA: {variant['cta_type']}
Format: {variant['format_style']}
Predicted Engagement: {variant['predicted_engagement']}/10
---

{variant['content']}"""
                zip_file.writestr(filename, header)

        st.download_button(
            label="📦 Download as ZIP (TXT files)",
            data=zip_buffer.getvalue(),
            file_name=f"ab_test_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip",
            use_container_width=True
        )

    with export_cols[2]:
        # Copy best variant to clipboard
        if st.button("📋 Copy Best Variant", use_container_width=True):
            st.code(best_variant['content'], language=None)
            st.success(f"✅ {best_variant['variant_id']} displayed above - use browser copy")

    # Testing Guide
    with st.expander("📚 How to Run A/B Tests with These Variants"):
        st.markdown("""
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
        """)
```

6. **Add reset button for variants** (update existing reset button around line 422):
```python
with col_gen2:
    if st.button("🔄 Reset", use_container_width=True):
        st.session_state.generated_post = None
        if "ab_test_variants" in st.session_state:
            del st.session_state.ab_test_variants
        if "adapted_variants" in st.session_state:
            del st.session_state.adapted_variants
        st.rerun()
```

**Testing Checklist**:
- [ ] Generation mode selector toggles between single and A/B test
- [ ] A/B test generates exactly 3 variants
- [ ] Each variant has distinct hook, CTA, and format
- [ ] Variants are ranked by predicted engagement
- [ ] Side-by-side comparison shows all variants
- [ ] Key differences section highlights hooks and CTAs
- [ ] CSV export includes all metadata fields
- [ ] ZIP export contains 3 separate TXT files
- [ ] Testing guide expander displays correctly
- [ ] Reset button clears all variant data

**Estimated Implementation Time**: 3 hours

---

## Implementation Roadmap

**Phase 1: Foundation (Week 1)**
- Day 1-2: Implement Multi-Platform Content Adapter (Spec #1)
  - Add platform constants and selector
  - Update prompt builder for platform optimization
  - Add content adaptation function
  - Build multi-platform export UI

- Day 3-4: Implement Content Performance Analytics Dashboard (Spec #2)
  - Add engagement score calculator
  - Build analytics tracking
  - Create dashboard with charts
  - Add improvement suggestions

**Phase 2: Optimization (Week 2)**
- Day 1-2: Implement A/B Content Variant Generator (Spec #3)
  - Add variant strategies
  - Build A/B generation function
  - Create comparison UI
  - Add testing guide

- Day 3: Integration Testing
  - Test all features together
  - Verify analytics tracks multi-platform and A/B variants
  - Cross-platform adaptation with A/B testing
  - End-to-end user flows

- Day 4: Polish & Documentation
  - Add tooltips and help text
  - Create demo video showcasing features
  - Update README with new capabilities
  - Prepare portfolio presentation talking points

**Phase 3: Portfolio Presentation (Week 3)**
- Create demo script highlighting:
  - Multi-platform expertise (Meta/Google certs)
  - Data-driven approach (Analytics cert)
  - A/B testing methodology (Marketing cert)
  - Professional toolkit ready for client work

**Expected Outcome:**
- Gig Readiness: 65% → 92%
- Demo "Wow" Factor: +300%
- Certification Showcase: All 3 certs demonstrated
- Client Pitch: "Full-stack social media content toolkit with multi-platform generation, performance analytics, and A/B testing"

---

## Success Metrics

**Before Implementation:**
- Platforms: 1 (LinkedIn only)
- Export Formats: 2 (TXT, clipboard)
- Analytics: None
- Testing Capabilities: None
- Gig Readiness: 65%

**After Implementation (Top 3):**
- Platforms: 5 (LinkedIn, Twitter/X, Instagram, Facebook, Email)
- Export Formats: 5 (TXT, ZIP, CSV, platform-specific, multi-platform package)
- Analytics: 8 metrics + 4 charts + AI suggestions
- Testing Capabilities: A/B variants with comparison
- Gig Readiness: 92%

**Portfolio Impact:**
- Can demo multi-platform strategy (Meta cert)
- Can show data-driven insights (Google Analytics cert)
- Can explain A/B testing methodology (Google Marketing cert)
- Ready for $75-100/hr social media management gigs

---

## Appendix: Rejected Improvements Analysis

### Why #4 (Content Scheduling Integration Hooks) Wasn't in Top 3:
- **Lower Wow Factor**: Metadata and CSV exports aren't visually impressive
- **Commoditized Feature**: Most scheduling tools already do this well
- **Indirect Value**: Doesn't directly improve content quality, just workflow
- **Better Alternative**: Focus on content quality (A/B testing) first, then workflow

### Why #5 (Multi-Post Campaign Planner) Wasn't in Top 3:
- **Speed Constraint**: 4.5 hours exceeds ideal <4 hour implementation
- **Narrow Use Case**: Not all clients need 7-day campaigns
- **Complexity Risk**: Campaign arc logic is subjective and hard to validate
- **Better Approach**: Let clients use A/B variants + analytics to build campaigns manually

**Key Insight**: The top 3 improvements focus on **breadth** (multi-platform), **intelligence** (analytics), and **optimization** (A/B testing) - the core pillars of professional social media management. The rejected improvements are nice-to-haves that can be added later if clients specifically request them.

---

**End of Improvement Plan**
