#!/usr/bin/env python3
"""
🎓 Professional Certifications Showcase
========================================

Interactive showcase of 19 professional certifications across AI/ML, Data Analytics,
Business Intelligence, and Digital Marketing ontario_millss.

Dashboard Features:
- Visual certification cards with provider branding
- Progress tracking for in-progress certifications
- Filterable by provider and topic area
- Total training hours: 1,768 hours
- 10 completed programs, 9 in progress

Providers:
- Google (Cloud, Analytics, Marketing, BI)
- Microsoft (AI, ML, Data Visualization)
- IBM (BI, GenAI Engineering, RAG/Agentic AI)
- Vanderbilt University (GenAI Strategy, Automation)
- DeepLearning.AI (Deep Learning, AI Fundamentals)
- Meta (Social Media Marketing)
- Duke University (LLMOps)
- University of Michigan (Python)

Author: Cave Howell - Professional Portfolio
Date: 2026-02-10
Version: 1.0.0
"""

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Professional Certifications | Cave Howell",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for certification cards
st.markdown(
    """
<style>
    .cert-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .cert-card-completed {
        background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
    }
    .cert-card-inprogress {
        background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
    }
    .provider-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.2);
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
        margin-right: 0.5rem;
    }
    .hours-badge {
        display: inline-block;
        background-color: rgba(255, 255, 255, 0.3);
        padding: 0.3rem 0.8rem;
        border-radius: 15px;
        font-size: 0.9rem;
        font-weight: bold;
    }
    .progress-bar {
        background-color: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        height: 20px;
        margin-top: 0.5rem;
    }
    .progress-fill {
        background-color: rgba(255, 255, 255, 0.8);
        border-radius: 10px;
        height: 100%;
        transition: width 0.3s ease;
    }
    .stats-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .topic-tag {
        display: inline-block;
        background-color: #e3f2fd;
        color: #1976d2;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.75rem;
        margin: 0.2rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Certification data structure
COMPLETED_CERTIFICATIONS: List[Dict[str, Any]] = [
    {
        "name": "Google Data Analytics Certificate",
        "provider": "Google",
        "hours": 181,
        "courses": 9,
        "topics": ["Data Analysis", "R Programming", "SQL", "Visualization"],
        "description": "Comprehensive data analytics training covering data cleaning, analysis, visualization, and R programming.",
        "completion_date": "2025-12",
    },
    {
        "name": "Vanderbilt Generative AI Strategic Leader Specialization",
        "provider": "Vanderbilt University",
        "hours": 40,
        "courses": 4,
        "topics": ["Prompt Engineering", "AI Strategy", "Agentic AI"],
        "description": "Strategic AI leadership training covering prompt engineering, AI strategy, and agentic systems.",
        "completion_date": "2025-11",
    },
    {
        "name": "Microsoft Generative AI for Data Analysis Professional Certificate",
        "provider": "Microsoft",
        "hours": 108,
        "courses": 6,
        "topics": ["GenAI", "Data Cleaning", "Visualization", "Code Generation"],
        "description": "Generative AI applications for data analysis, cleaning, visualization, and automated code generation.",
        "completion_date": "2025-10",
    },
    {
        "name": "Google Cloud Generative AI Leader Certificate",
        "provider": "Google Cloud",
        "hours": 25,
        "courses": 5,
        "topics": ["GenAI Foundations", "AI Applications", "AI Agents"],
        "description": "Google Cloud GenAI fundamentals, application development, and agent-based systems.",
        "completion_date": "2025-09",
    },
    {
        "name": "DeepLearning.AI - AI For Everyone",
        "provider": "DeepLearning.AI",
        "hours": 12,
        "courses": 4,
        "topics": ["AI Fundamentals", "AI Projects", "Business Strategy"],
        "description": "Foundational AI concepts for non-technical leaders and business strategists.",
        "completion_date": "2025-08",
    },
    {
        "name": "Google Digital Marketing & E-commerce Certificate",
        "provider": "Google",
        "hours": 190,
        "courses": 8,
        "topics": ["Digital Marketing", "Email Marketing", "E-commerce", "Analytics"],
        "description": "End-to-end digital marketing and e-commerce training including analytics and optimization.",
        "completion_date": "2025-07",
    },
    {
        "name": "IBM Business Intelligence Analyst Professional Certificate",
        "provider": "IBM",
        "hours": 141,
        "courses": 11,
        "topics": ["Excel", "SQL", "Cognos", "Tableau", "Data Warehousing"],
        "description": "Comprehensive BI analyst training covering Excel, SQL, Cognos, Tableau, and data warehousing.",
        "completion_date": "2025-06",
    },
    {
        "name": "Meta Social Media Marketing Professional Certificate",
        "provider": "Meta",
        "hours": 83,
        "courses": 6,
        "topics": ["Social Media Strategy", "Advertising", "Campaign Optimization"],
        "description": "Meta's official social media marketing training covering strategy, advertising, and analytics.",
        "completion_date": "2025-05",
    },
    {
        "name": "DeepLearning.AI Deep Learning Specialization",
        "provider": "DeepLearning.AI",
        "hours": 120,
        "courses": 5,
        "topics": ["Neural Networks", "CNNs", "RNNs", "Hyperparameter Tuning"],
        "description": "Advanced deep learning specialization covering neural networks, CNNs, RNNs, and optimization.",
        "completion_date": "2025-04",
    },
    {
        "name": "ChatGPT: Excel at Personal Automation with GPTs, AI & Zapier",
        "provider": "Vanderbilt University",
        "hours": 30,
        "courses": 3,
        "topics": ["Prompt Engineering", "Custom GPTs", "Automation", "Zapier"],
        "description": "Practical automation training using ChatGPT, custom GPTs, and Zapier integrations.",
        "completion_date": "2025-03",
    },
]

IN_PROGRESS_CERTIFICATIONS: List[Dict[str, Any]] = [
    {
        "name": "IBM Generative AI Engineering with PyTorch, LangChain & Hugging Face",
        "provider": "IBM",
        "hours": 144,
        "courses": 16,
        "progress": 40,
        "topics": ["Transformers", "RAG", "LangChain", "Fine-tuning", "Deployment"],
        "description": "Advanced GenAI engineering covering transformers, RAG, LangChain, and production deployment.",
        "expected_completion": "Q2 2026",
    },
    {
        "name": "Python for Everybody",
        "provider": "University of Michigan",
        "hours": 60,
        "courses": 5,
        "progress": 50,
        "topics": ["Python Fundamentals", "Data Structures", "Web Scraping", "Databases"],
        "description": "Comprehensive Python programming specialization covering fundamentals through data visualization.",
        "expected_completion": "Q2 2026",
    },
    {
        "name": "Microsoft AI-Enhanced Data Analysis: From Raw Data to Deep Insights",
        "provider": "Microsoft",
        "hours": 120,
        "courses": 5,
        "progress": 80,
        "topics": ["Excel Copilot", "Python", "Power BI", "Integrated Workflows"],
        "description": "AI-enhanced data analysis using Excel Copilot, Python, and Power BI for integrated insights.",
        "expected_completion": "Q1 2026",
    },
    {
        "name": "Microsoft Data Visualization Professional Certificate",
        "provider": "Microsoft",
        "hours": 87,
        "courses": 5,
        "progress": 80,
        "topics": ["Visualization", "Data Modeling", "Analytics", "AI Storytelling"],
        "description": "Advanced data visualization, modeling, and AI-powered storytelling with Microsoft tools.",
        "expected_completion": "Q1 2026",
    },
    {
        "name": "Google Business Intelligence Professional Certificate",
        "provider": "Google",
        "hours": 80,
        "courses": 4,
        "progress": 85,
        "topics": ["BI Foundations", "Data Pipelines", "Dashboards", "Reporting"],
        "description": "Professional BI training covering foundations, pipelines, dashboards, and reporting.",
        "expected_completion": "Q1 2026",
    },
    {
        "name": "Duke University Large Language Model Operations (LLMOps) Specialization",
        "provider": "Duke University",
        "hours": 48,
        "courses": 6,
        "progress": 85,
        "topics": ["LLM Deployment", "Local Models", "Plugins", "Production Ops"],
        "description": "LLMOps specialization covering deployment, local models, plugins, and production operations.",
        "expected_completion": "Q1 2026",
    },
    {
        "name": "IBM RAG and Agentic AI: Build Next-Gen AI Systems Professional Certificate",
        "provider": "IBM",
        "hours": 24,
        "courses": 8,
        "progress": 40,
        "topics": ["RAG", "LangChain", "Vector Databases", "Multi-Agent Systems", "AG2"],
        "description": "Next-generation AI systems using RAG, vector databases, and multi-agent architectures.",
        "expected_completion": "Q2 2026",
    },
    {
        "name": "Google Advanced Data Analytics Certificate",
        "provider": "Google",
        "hours": 200,
        "courses": 8,
        "progress": 30,
        "topics": ["Python", "Statistics", "Regression", "Machine Learning"],
        "description": "Advanced data analytics specialization covering Python, statistics, and machine learning.",
        "expected_completion": "Q3 2026",
    },
    {
        "name": "Microsoft AI & ML Engineering Professional Certificate",
        "provider": "Microsoft",
        "hours": 75,
        "courses": 5,
        "progress": 40,
        "topics": ["ML Algorithms", "Azure Workflows", "Intelligent Agents"],
        "description": "AI and ML engineering with Azure, covering algorithms, workflows, and intelligent agents.",
        "expected_completion": "Q2 2026",
    },
]


def render_certification_card(cert: Dict[str, Any], status: str = "completed") -> None:
    """Render a certification card with provider branding and details."""
    card_class = "cert-card-completed" if status == "completed" else "cert-card-inprogress"
    status_emoji = "✅" if status == "completed" else "🔄"

    # Build topics HTML
    topics_html = "".join([f'<span class="topic-tag">{topic}</span>' for topic in cert["topics"]])

    # Progress bar for in-progress certs
    progress_html = ""
    if status == "in_progress":
        progress = cert.get("progress", 0)
        progress_html = f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <p style="margin-top: 0.3rem; font-size: 0.9rem; opacity: 0.9;">{progress}% Complete • Expected: {cert["expected_completion"]}</p>
        """

    completion_info = (
        f"Completed: {cert['completion_date']}" if status == "completed" else f"Expected: {cert['expected_completion']}"
    )

    card_html = f"""
    <div class="cert-card {card_class}">
        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
            <h3 style="margin: 0; color: white; flex: 1;">{status_emoji} {cert["name"]}</h3>
            <span class="hours-badge">{cert["hours"]} hours</span>
        </div>
        <div style="margin: 0.8rem 0;">
            <span class="provider-badge">{cert["provider"]}</span>
            <span class="provider-badge">{cert["courses"]} courses</span>
        </div>
        <p style="margin: 0.8rem 0; opacity: 0.95;">{cert["description"]}</p>
        <div style="margin-top: 0.8rem;">
            {topics_html}
        </div>
        {progress_html}
        <p style="margin-top: 0.8rem; font-size: 0.85rem; opacity: 0.8;">{completion_info}</p>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def main():
    """Main dashboard application."""

    # Header
    st.title("🎓 Professional Certifications Portfolio")
    st.markdown(
        """
    **Cave Howell** | AI/ML Engineer | Data Analytics & Business Intelligence Specialist

    Comprehensive professional development across AI/ML, Data Analytics, Business Intelligence,
    and Digital Marketing ontario_millss from leading institutions and technology companies.
    """
    )

    # Overall statistics
    total_hours = 1768
    completed_hours = 930
    in_progress_hours = 838
    completed_count = 10
    in_progress_count = 9

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Training Hours", f"{total_hours:,}", help="Cumulative learning hours across all programs")
    with col2:
        st.metric(
            "Completed Programs",
            completed_count,
            delta=f"{completed_hours} hours",
            help="Fully completed certification programs",
        )
    with col3:
        st.metric(
            "In Progress",
            in_progress_count,
            delta=f"{in_progress_hours} hours",
            help="Currently active certification programs",
        )
    with col4:
        completion_rate = int((completed_count / (completed_count + in_progress_count)) * 100)
        st.metric("Completion Rate", f"{completion_rate}%", help="Percentage of programs completed")

    st.divider()

    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Provider filter
    all_providers = sorted(set([cert["provider"] for cert in COMPLETED_CERTIFICATIONS + IN_PROGRESS_CERTIFICATIONS]))
    selected_providers = st.sidebar.multiselect("Filter by Provider", all_providers, default=all_providers)

    # Topic filter
    all_topics = sorted(
        set([topic for cert in COMPLETED_CERTIFICATIONS + IN_PROGRESS_CERTIFICATIONS for topic in cert["topics"]])
    )
    selected_topics = st.sidebar.multiselect("Filter by Topic", all_topics)

    # Status filter
    show_completed = st.sidebar.checkbox("Show Completed", value=True)
    show_in_progress = st.sidebar.checkbox("Show In Progress", value=True)

    st.sidebar.divider()

    # Quick stats in sidebar
    st.sidebar.header("📊 Quick Stats")
    st.sidebar.markdown(
        f"""
    **Total Programs**: {completed_count + in_progress_count}
    **Total Courses**: 119
    **Completed**: {completed_count} programs
    **In Progress**: {in_progress_count} programs
    **Q1 2026 Target**: 4 completions
    """
    )

    st.sidebar.divider()

    # Verification links
    st.sidebar.header("🔗 Verification")
    st.sidebar.markdown(
        """
    - [Coursera Profile](https://www.coursera.org)
    - [LinkedIn Certifications](https://www.linkedin.com)
    - [GitHub Portfolio](https://github.com)
    """
    )

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📚 All Certifications", "📈 Analytics", "🎯 Skills Matrix", "📅 Timeline"])

    with tab1:
        # Filter certifications
        def filter_cert(cert):
            provider_match = cert["provider"] in selected_providers
            topic_match = not selected_topics or any(topic in cert["topics"] for topic in selected_topics)
            return provider_match and topic_match

        # Completed certifications
        if show_completed:
            st.header("✅ Completed Certifications (10 Programs)")
            filtered_completed = [cert for cert in COMPLETED_CERTIFICATIONS if filter_cert(cert)]

            if filtered_completed:
                for cert in filtered_completed:
                    render_certification_card(cert, status="completed")
            else:
                st.info("No completed certifications match the selected filters.")

        st.divider()

        # In-progress certifications
        if show_in_progress:
            st.header("🔄 In Progress (9 Programs)")
            filtered_in_progress = [cert for cert in IN_PROGRESS_CERTIFICATIONS if filter_cert(cert)]

            if filtered_in_progress:
                # Sort by progress descending
                filtered_in_progress.sort(key=lambda x: x["progress"], reverse=True)
                for cert in filtered_in_progress:
                    render_certification_card(cert, status="in_progress")
            else:
                st.info("No in-progress certifications match the selected filters.")

    with tab2:
        st.header("📈 Training Analytics")

        # Provider breakdown chart
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Training Hours by Provider")
            provider_data = {}
            for cert in COMPLETED_CERTIFICATIONS + IN_PROGRESS_CERTIFICATIONS:
                provider = cert["provider"]
                provider_data[provider] = provider_data.get(provider, 0) + cert["hours"]

            fig = px.pie(
                values=list(provider_data.values()),
                names=list(provider_data.keys()),
                title="Distribution of Training Hours",
                hole=0.4,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Programs by Status")
            status_data = {"Completed": completed_count, "In Progress": in_progress_count}
            fig = px.bar(
                x=list(status_data.keys()),
                y=list(status_data.values()),
                title="Certification Status",
                labels={"x": "Status", "y": "Number of Programs"},
                color=list(status_data.keys()),
                color_discrete_map={"Completed": "#4CAF50", "In Progress": "#2196F3"},
            )
            st.plotly_chart(fig, use_container_width=True)

        # Progress tracking for in-progress certs
        st.subheader("In-Progress Certifications Timeline")
        progress_df = pd.DataFrame(
            [
                {
                    "Certification": cert["name"][:40] + "..." if len(cert["name"]) > 40 else cert["name"],
                    "Progress": cert["progress"],
                    "Hours": cert["hours"],
                    "Expected": cert["expected_completion"],
                }
                for cert in IN_PROGRESS_CERTIFICATIONS
            ]
        )
        progress_df = progress_df.sort_values("Progress", ascending=True)

        fig = px.bar(
            progress_df,
            x="Progress",
            y="Certification",
            orientation="h",
            title="Completion Progress",
            labels={"Progress": "Completion %", "Certification": ""},
            color="Progress",
            color_continuous_scale="Blues",
            hover_data=["Hours", "Expected"],
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

        # Provider table
        st.subheader("Provider Breakdown")
        provider_stats = []
        for provider in all_providers:
            completed = len([c for c in COMPLETED_CERTIFICATIONS if c["provider"] == provider])
            in_prog = len([c for c in IN_PROGRESS_CERTIFICATIONS if c["provider"] == provider])
            total_hours = sum(
                [c["hours"] for c in COMPLETED_CERTIFICATIONS + IN_PROGRESS_CERTIFICATIONS if c["provider"] == provider]
            )
            provider_stats.append(
                {
                    "Provider": provider,
                    "Completed": completed,
                    "In Progress": in_prog,
                    "Total Programs": completed + in_prog,
                    "Total Hours": total_hours,
                }
            )

        provider_df = pd.DataFrame(provider_stats)
        provider_df = provider_df.sort_values("Total Hours", ascending=False)
        st.dataframe(provider_df, use_container_width=True, hide_index=True)

    with tab3:
        st.header("🎯 Skills & Competencies Matrix")

        # Topic frequency analysis
        topic_counts = {}
        for cert in COMPLETED_CERTIFICATIONS + IN_PROGRESS_CERTIFICATIONS:
            for topic in cert["topics"]:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("Topic Coverage")
            topic_df = pd.DataFrame([{"Topic": topic, "Programs": count} for topic, count in topic_counts.items()])
            topic_df = topic_df.sort_values("Programs", ascending=False)

            fig = px.bar(
                topic_df,
                x="Programs",
                y="Topic",
                orientation="h",
                title="Skills Across Programs",
                labels={"Programs": "Number of Programs", "Topic": ""},
                color="Programs",
                color_continuous_scale="Viridis",
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Skill Categories")
            skill_categories = {
                "AI & Machine Learning": [
                    "Generative AI",
                    "Deep Learning",
                    "Neural Networks",
                    "Transformers",
                    "RAG",
                    "Agentic AI",
                ],
                "Data Analytics": ["Data Analysis", "Python", "R Programming", "SQL", "Statistics"],
                "Business Intelligence": ["BI Foundations", "Dashboards", "Visualization", "Reporting"],
                "Marketing": ["Digital Marketing", "Social Media Strategy", "Email Marketing"],
            }

            for category, skills in skill_categories.items():
                matching_skills = [s for s in skills if any(s.lower() in t.lower() for t in all_topics)]
                if matching_skills:
                    with st.expander(f"**{category}**", expanded=True):
                        for skill in matching_skills:
                            st.markdown(f"- {skill}")

    with tab4:
        st.header("📅 Learning Timeline & Roadmap")

        # 2026 completion roadmap
        st.subheader("2026 Completion Roadmap")

        quarters = {
            "Q1 2026": [
                "Microsoft AI-Enhanced Data Analysis",
                "Microsoft Data Visualization",
                "Google Business Intelligence",
                "Duke University LLMOps",
            ],
            "Q2 2026": [
                "IBM Generative AI Engineering",
                "Python for Everybody",
                "Microsoft AI & ML Engineering",
                "IBM RAG and Agentic AI",
            ],
            "Q3 2026": ["Google Advanced Data Analytics"],
        }

        for quarter, certs in quarters.items():
            with st.expander(f"**{quarter}** ({len(certs)} programs)", expanded=True):
                for cert_name in certs:
                    # Find the cert to get progress
                    cert = next((c for c in IN_PROGRESS_CERTIFICATIONS if c["name"] == cert_name), None)
                    if cert:
                        progress = cert["progress"]
                        hours = cert["hours"]
                        st.progress(progress / 100)
                        st.markdown(f"**{cert_name}**  \n{progress}% complete • {hours} hours • {cert['provider']}")

        st.divider()

        # Historical timeline
        st.subheader("Completion History (2025)")

        # Create timeline visualization
        timeline_data = []
        for cert in COMPLETED_CERTIFICATIONS:
            timeline_data.append(
                {
                    "Date": cert["completion_date"],
                    "Certification": cert["name"][:50] + "..." if len(cert["name"]) > 50 else cert["name"],
                    "Hours": cert["hours"],
                    "Provider": cert["provider"],
                }
            )

        timeline_df = pd.DataFrame(timeline_data)
        timeline_df = timeline_df.sort_values("Date")

        fig = px.scatter(
            timeline_df,
            x="Date",
            y="Certification",
            size="Hours",
            color="Provider",
            title="2025 Certification Completions",
            labels={"Date": "Completion Date", "Certification": ""},
            hover_data=["Hours"],
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    # Footer
    st.divider()
    st.markdown(
        """
    <div style="text-align: center; color: #666; padding: 2rem 0;">
        <p><strong>Professional Certifications Portfolio</strong> • Last Updated: February 10, 2026</p>
        <p>Total Investment: 1,768 Training Hours • 19 Programs • 8 Leading Institutions</p>
        <p>🔗 <a href="https://www.coursera.org">Coursera Profile</a> •
           <a href="https://www.linkedin.com">LinkedIn</a> •
           <a href="https://github.com">GitHub Portfolio</a></p>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
