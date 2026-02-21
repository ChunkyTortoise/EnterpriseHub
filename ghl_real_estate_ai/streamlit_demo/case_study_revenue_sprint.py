"""
Revenue-Sprint Case Study Page
Case study for the Revenue-Sprint project - Marketing Attribution & Revenue Optimization
"""

import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_revenue_sprint_case_study():
    """Render the Revenue-Sprint case study page."""
    st.set_page_config(page_title="Revenue-Sprint Case Study", page_icon="📈", layout="wide")

    # Header
    st.markdown("# 📈 Revenue-Sprint Case Study")
    st.markdown("### Marketing Attribution & Revenue Optimization Platform")
    st.markdown("---")

    # Two-column layout
    col1, col2 = st.columns([2, 1])

    with col1:
        render_main_content()

    with col2:
        render_metrics_sidebar()

    # Full-width sections
    st.markdown("---")
    render_technical_stack()

    st.markdown("---")
    render_architecture()

    st.markdown("---")
    render_testimonials()

    st.markdown("---")
    render_cta()


def render_main_content():
    """Render the main case study content."""
    st.markdown("## Challenge")
    st.markdown("""
    A marketing agency and SaaS company were struggling with fundamental revenue operations problems:
    
    - **Manual Reporting Burden:** 20+ hours per week spent on manual data collection and report generation
    - **Poor Lead Quality:** Inability to effectively qualify and prioritize outbound leads
    - **Slow Proposal Creation:** 45+ minutes to generate customized proposals for each prospect
    - **Inconsistent Follow-up:** No systematic approach to nurturing leads over time
    - **Limited ROI Visibility:** No clear attribution between marketing spend and revenue outcomes
    """)

    st.markdown("## Solution")
    st.markdown("""
    Built a comprehensive revenue optimization platform in 7 days with 212 automated tests:
    
    ### 4-Agent Proposal Pipeline
    - **Scanner Agent:** Monitors Upwork RSS feeds for relevant job postings
    - **Analyst Agent:** Evaluates job fit and extracts requirements
    - **Writer Agent:** Generates customized proposals using prompt templates
    - **Reviewer Agent:** Quality checks proposals before submission
    
    ### LinkedIn Outreach Engine
    - Automated connection requests with personalized messaging
    - Multi-step nurture sequences based on engagement signals
    - A/B testing for subject lines and message templates
    - Response rate tracking and optimization
    
    ### Marketing Attribution Dashboard
    - Real-time ROI visibility across all channels
    - Cohort analysis and conversion tracking
    - Automated weekly reporting (replaced 20 hours of manual work)
    - Campaign optimization recommendations
    """)

    st.markdown("## Implementation Timeline")

    timeline_data = {
        "Day 1-2": "Architecture & Infrastructure",
        "Day 3-4": "Agent Pipeline Development",
        "Day 5-6": "LinkedIn Integration & Testing",
        "Day 7": "Dashboard & Deployment",
    }

    for day, task in timeline_data.items():
        st.markdown(f"**{day}:** {task}")


def render_metrics_sidebar():
    """Render metrics sidebar with key outcomes."""
    st.markdown("### 📊 Key Metrics")
    st.markdown("---")

    metrics = [
        ("3x", "Increase in Qualified Outbound Leads"),
        ("45%", "Improvement in Reply Rates"),
        ("99%", "Faster Proposal Generation (45min → 3-7sec)"),
        ("100%", "Follow-up Consistency"),
        ("20 hrs", "Weekly Time Recovery"),
        ("212", "Automated Tests"),
    ]

    for value, label in metrics:
        st.markdown(
            f"""
        <div style='background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(99, 102, 241, 0.1) 100%); 
                    padding: 1rem; border-radius: 12px; margin-bottom: 0.75rem; border: 1px solid rgba(16, 185, 129, 0.2);'>
            <div style='font-size: 2rem; font-weight: 800; color: #10B981;'>{value}</div>
            <div style='font-size: 0.85rem; color: #64748B; font-weight: 500;'>{label}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown("### 💰 Financial Impact")
    st.markdown("""
    **Annual Savings:** $36,000+  
    **Cost per Qualified Lead:** -60%  
    **Proposal Win Rate:** +25%
    """)

    st.markdown("---")
    st.markdown("### 🔗 Links")
    st.markdown("""
    - [GitHub Repository](https://github.com/ChunkyTortoise/Revenue-Sprint)
    - [CLI Demo](https://github.com/ChunkyTortoise/Revenue-Sprint/blob/main/assets/cli-demo.gif)
    - [Architecture Diagram](https://github.com/ChunkyTortoise/Revenue-Sprint/blob/main/assets/hero-banner.svg)
    """)


def render_technical_stack():
    """Render technical stack section."""
    st.markdown("## Technical Stack")

    tech_stack = {
        "Core": ["Python 3.11", "FastAPI", "AsyncIO", "Pydantic"],
        "AI/ML": ["Claude API", "Prompt Engineering", "A/B Testing"],
        "Integrations": ["Upwork API", "LinkedIn API", "Gumroad API", "SendGrid"],
        "Testing": ["pytest", "212 tests", "CI/CD"],
        "Infrastructure": ["Docker", "GitHub Actions", "RSS Feeds"],
    }

    cols = st.columns(len(tech_stack))

    for col, (category, technologies) in zip(cols, tech_stack.items()):
        with col:
            st.markdown(f"**{category}**")
            for tech in technologies:
                st.markdown(f"- {tech}")


def render_architecture():
    """Render architecture diagram."""
    st.markdown("## Architecture")

    st.markdown("""
    ```
    ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
    │   Upwork RSS    │    │   4-Agent        │    │   LinkedIn      │
    │   Feed Monitor  │───▶│   Proposal       │◄───│   Outreach      │
    │                 │    │   Pipeline       │    │   Engine        │
    └─────────────────┘    └────────┬─────────┘    └─────────────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
            ┌───────────┐   ┌───────────┐   ┌───────────┐
            │  Scanner  │   │  Analyst  │   │  Writer   │
            │   Agent   │   │   Agent   │   │   Agent   │
            └───────────┘   └───────────┘   └───────────┘
                    │             │             │
                    └─────────────┼─────────────┘
                                  ▼
                          ┌───────────┐
                          │  Reviewer │
                          │   Agent   │
                          └─────┬─────┘
                                │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
           ┌────────────────┐       ┌──────────────────┐
           │   Marketing    │       │   Attribution    │
           │   Dashboard    │       │   Analytics      │
           └────────────────┘       └──────────────────┘
    ```
    """)

    st.markdown("""
    **Key Architectural Decisions:**
    
    1. **Agent Pattern:** Each agent has a single responsibility with defined inputs/outputs
    2. **Async Processing:** All I/O operations (API calls, RSS fetching) are non-blocking
    3. **Stateless Design:** Agents don't maintain state between runs - enables horizontal scaling
    4. **Prompt Versioning:** All prompts tracked in Git with A/B test capabilities
    5. **Circuit Breakers:** External API failures don't cascade to other components
    """)


def render_testimonials():
    """Render client testimonials section."""
    st.markdown("## Client Impact")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        > "The proposal generation alone saved us 15 hours per week. 
        > Quality actually improved because the AI maintains consistency 
        > we couldn't achieve manually."
        > 
        > **— Marketing Agency Director**
        """)

    with col2:
        st.markdown("""
        > "We went from sporadic LinkedIn outreach to a systematic 
        > process. Reply rates doubled in the first month."
        > 
        > **— SaaS Founder**
        """)


def render_cta():
    """Render call-to-action section."""
    st.markdown("## Ready to Optimize Your Revenue Operations?")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>📊 View Demo</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>See the CLI in action</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("[CLI Demo GIF](https://github.com/ChunkyTortoise/Revenue-Sprint/blob/main/assets/cli-demo.gif)")

    with col2:
        st.markdown(
            """
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #10B981 0%, #059669 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>💻 Source Code</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>212 tests, full documentation</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("[GitHub Repository](https://github.com/ChunkyTortoise/Revenue-Sprint)")

    with col3:
        st.markdown(
            """
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%); border-radius: 16px; color: white;'>
            <div style='font-size: 1.5rem; font-weight: 700; margin-bottom: 0.5rem;'>📧 Get in Touch</div>
            <div style='font-size: 0.9rem; opacity: 0.9;'>Discuss your project</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        st.markdown("realtorjorgesalas@gmail.com")


if __name__ == "__main__":
    render_revenue_sprint_case_study()
