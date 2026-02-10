"""
Case Studies - Detailed implementation showcases
EnterpriseHub and AgentForge success stories
"""

import streamlit as st
import plotly.graph_objects as go
from ghl_real_estate_ai.streamlit_demo.data.case_studies_data import CASE_STUDIES


def render_case_studies():
    """Render the case studies page."""
    st.set_page_config(page_title="Case Studies", page_icon="📊", layout="wide")
    
    # Header
    st.markdown("# 📊 Case Studies")
    st.markdown("### Proven Results from Production AI Implementations")
    st.markdown("---")
    
    # Case study selector
    case_study_names = {
        "enterprisehub": "EnterpriseHub: Real Estate AI Transformation",
        "agentforge": "AgentForge: AI-Powered Lead Qualification",
    }
    
    selected = st.selectbox(
        "Select Case Study",
        list(case_study_names.keys()),
        format_func=lambda x: case_study_names[x]
    )
    
    st.markdown("---")
    
    # Render selected case study
    case_study = CASE_STUDIES[selected]
    render_case_study_detail(case_study)


def render_case_study_detail(case_study: dict):
    """Render detailed case study."""
    # Hero section
    st.markdown(f"# {case_study['title']}")
    st.markdown(f"## {case_study['subtitle']}")
    
    # Metadata badges
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            f"""
            <div style='display: flex; gap: 1rem; margin: 1rem 0;'>
                <span style='background: #6366F1; color: white; padding: 0.5rem 1rem; 
                             border-radius: 6px; font-size: 0.85rem; font-weight: 600;'>
                    🏢 {case_study["client_industry"]}
                </span>
                <span style='background: #10B981; color: white; padding: 0.5rem 1rem; 
                             border-radius: 6px; font-size: 0.85rem; font-weight: 600;'>
                    📈 {case_study["client_size"]}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("---")
    
    # Two-column layout: Main content + Metrics sidebar
    col_main, col_metrics = st.columns([2, 1])
    
    with col_main:
        # Challenge section
        st.markdown(f"### 🎯 {case_study['challenge']['title']}")
        st.markdown(case_study['challenge']['description'])
        
        st.markdown("**Key Pain Points:**")
        for pain_point in case_study['challenge']['pain_points']:
            st.markdown(f"- {pain_point}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Solution section
        st.markdown(f"### 💡 {case_study['solution']['title']}")
        st.markdown(case_study['solution']['description'])
        
        st.markdown("**Solution Components:**")
        for component in case_study['solution']['components']:
            st.markdown(f"- {component}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Technical Stack section
        st.markdown("### 🛠️ Technical Stack")
        render_technical_stack(case_study['technical_stack'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Architecture section
        st.markdown(f"### 🏗️ Architecture: {case_study['architecture']['description']}")
        for feature in case_study['architecture']['key_features']:
            st.markdown(f"- {feature}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Implementation timeline
        st.markdown(f"### ⏱️ Implementation Timeline: {case_study['implementation']['timeline']}")
        render_implementation_timeline(case_study['implementation']['phases'])
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Testimonial
        st.markdown("### 💬 Client Testimonial")
        st.markdown(
            f"""
            <div style='background: #F8FAFC; padding: 2rem; border-left: 4px solid #6366F1; 
                        border-radius: 8px; margin: 1rem 0;'>
                <p style='font-size: 1.1rem; font-style: italic; color: #475569; line-height: 1.7; margin: 0;'>
                    "{case_study['testimonial']['quote']}"
                </p>
                <p style='margin-top: 1rem; color: #64748B; font-weight: 600;'>
                    — {case_study['testimonial']['author']}, {case_study['testimonial']['company']}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    with col_metrics:
        # Outcomes metrics sidebar
        st.markdown("### 📈 Primary Outcomes")
        
        for metric in case_study['outcomes']['primary_metrics']:
            st.markdown(
                f"""
                <div style='background: white; padding: 1rem; border-radius: 8px; 
                            border: 1px solid #E2E8F0; margin-bottom: 1rem;
                            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);'>
                    <div style='font-size: 2rem; font-weight: 800; color: #6366F1; margin-bottom: 0.25rem;'>
                        {metric["value"]}
                    </div>
                    <div style='font-size: 0.9rem; font-weight: 600; color: #1E293B; margin-bottom: 0.25rem;'>
                        {metric["metric"]}
                    </div>
                    <div style='font-size: 0.8rem; color: #64748B;'>
                        {metric["detail"]}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("### 📋 Additional Achievements")
        for achievement in case_study['outcomes']['secondary_metrics']:
            st.markdown(f"- {achievement}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Technologies used
        st.markdown("### 🔧 Technologies Used")
        render_tech_badges(case_study['technologies_used'])
        
        # Download PDF button
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("📥 Download PDF Case Study", use_container_width=True)
    
    # Metrics visualization
    st.markdown("---")
    st.markdown("### 📊 Performance Metrics Visualization")
    render_metrics_charts(case_study['outcomes']['primary_metrics'])


def render_technical_stack(tech_stack: dict):
    """Render technical stack in organized sections."""
    # Create expandable sections for each stack category
    for category, technologies in tech_stack.items():
        with st.expander(f"**{category.replace('_', ' ').title()}**"):
            st.markdown(", ".join(technologies))


def render_implementation_timeline(phases: list):
    """Render implementation timeline as interactive Gantt-style chart."""
    # Create Gantt-style visualization
    fig = go.Figure()
    
    y_labels = []
    for i, phase in enumerate(phases):
        y_labels.append(phase['phase'])
        
        # Add bar for phase duration
        fig.add_trace(go.Bar(
            y=[phase['phase']],
            x=[int(phase['duration'].split()[0])],  # Extract number of days
            orientation='h',
            name=phase['phase'],
            text=phase['duration'],
            textposition='inside',
            marker=dict(
                color=['#6366F1', '#10B981', '#F59E0B', '#8B5CF6'][i % 4],
            ),
            hovertemplate=f"<b>{phase['phase']}</b><br>Duration: {phase['duration']}<extra></extra>",
        ))
    
    fig.update_layout(
        title="Implementation Phases",
        xaxis_title="Duration (Days)",
        yaxis_title="",
        height=300,
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show phase details
    for phase in phases:
        with st.expander(f"{phase['phase']} ({phase['duration']})"):
            st.markdown("**Deliverables:**")
            for deliverable in phase['deliverables']:
                st.markdown(f"- {deliverable}")


def render_tech_badges(technologies: list):
    """Render technology badges."""
    badge_html = ""
    for tech in technologies:
        badge_html += f"""
        <span style='display: inline-block; background: #F1F5F9; color: #475569; 
                     padding: 0.4rem 0.8rem; border-radius: 6px; 
                     font-size: 0.8rem; font-weight: 600; margin: 0.25rem;
                     border: 1px solid #E2E8F0;'>
            {tech}
        </span>
        """
    
    st.markdown(
        f"<div style='line-height: 2.5;'>{badge_html}</div>",
        unsafe_allow_html=True
    )


def render_metrics_charts(metrics: list):
    """Render metrics as bar charts."""
    col1, col2 = st.columns(2)
    
    # Create two charts from metrics
    metrics_subset_1 = metrics[:3]
    metrics_subset_2 = metrics[3:6]
    
    with col1:
        fig1 = create_metric_chart(metrics_subset_1, "Key Performance Indicators")
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        fig2 = create_metric_chart(metrics_subset_2, "Operational Improvements")
        st.plotly_chart(fig2, use_container_width=True)


def create_metric_chart(metrics: list, title: str):
    """Create a bar chart for metrics."""
    metric_names = [m['metric'] for m in metrics]
    
    # Extract numeric values (handle percentages, currency, multipliers)
    metric_values = []
    for m in metrics:
        value_str = m['value']
        # Extract number from string
        import re
        numbers = re.findall(r'[\d.]+', value_str.replace(',', ''))
        if numbers:
            metric_values.append(float(numbers[0]))
        else:
            metric_values.append(0)
    
    fig = go.Figure(data=[
        go.Bar(
            x=metric_names,
            y=metric_values,
            text=[m['value'] for m in metrics],
            textposition='outside',
            marker=dict(
                color=['#6366F1', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#3B82F6'][:len(metrics)],
            ),
            hovertemplate='<b>%{x}</b><br>%{text}<br>%{customdata}<extra></extra>',
            customdata=[m['detail'] for m in metrics],
        )
    ])
    
    fig.update_layout(
        title=title,
        xaxis_title="",
        yaxis_title="",
        height=400,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif"),
        showlegend=False,
    )
    
    return fig


if __name__ == "__main__":
    render_case_studies()
