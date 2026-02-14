"""
EnterpriseHub Professional Showcase Landing Page
Professional certifications and services portfolio for client acquisition.
"""

from typing import Dict, List
import streamlit as st
from pathlib import Path
import sys

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.append(str(project_root))

from streamlit_demo.components.primitives.metric import render_obsidian_metric, MetricConfig
from streamlit_demo.components.primitives.card import render_obsidian_card, CardConfig

# Page configuration
st.set_page_config(
    page_title="EnterpriseHub - AI Systems & Data Infrastructure",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Production-grade AI systems and data infrastructure services | 19 Certifications | 31 Services",
        "Get Help": "https://github.com/yourusername/EnterpriseHub",
    },
)


# Custom CSS for professional styling
def load_custom_css() -> None:
    """Load custom CSS for professional presentation."""
    st.markdown(
        """
        <style>
        /* Professional color palette */
        :root {
            --primary-blue: #1B4F72;
            --accent-blue: #3498DB;
            --success-green: #10B981;
            --warning-amber: #F59E0B;
            --text-primary: #2C3E50;
            --text-secondary: #7F8C8D;
            --bg-light: #F8F9FA;
            --bg-card: #FFFFFF;
        }
        
        /* Hero section styling */
        .hero-section {
            background: linear-gradient(135deg, #1B4F72 0%, #2874A6 50%, #3498DB 100%);
            padding: 3rem 2rem;
            border-radius: 16px;
            margin-bottom: 2rem;
            color: white;
            box-shadow: 0 10px 40px rgba(27, 79, 114, 0.3);
        }
        
        .hero-title {
            font-size: 2.8rem;
            font-weight: 800;
            margin: 0 0 1rem 0;
            line-height: 1.2;
            color: white;
        }
        
        .hero-subtitle {
            font-size: 1.3rem;
            font-weight: 400;
            margin: 0 0 2rem 0;
            opacity: 0.95;
            color: white;
        }
        
        .hero-metrics {
            display: flex;
            gap: 2rem;
            flex-wrap: wrap;
            margin-bottom: 2rem;
        }
        
        .hero-metric-badge {
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(10px);
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-weight: 600;
            font-size: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        /* CTA button styling */
        .cta-button {
            background: white;
            color: #1B4F72;
            padding: 0.875rem 2rem;
            border-radius: 8px;
            font-weight: 700;
            font-size: 1rem;
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
            margin-right: 1rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        
        .cta-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }
        
        .cta-button-secondary {
            background: transparent;
            color: white;
            border: 2px solid white;
        }
        
        /* Section styling */
        .section-header {
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 2rem 0 1rem 0;
            border-bottom: 3px solid var(--primary-blue);
            padding-bottom: 0.5rem;
        }
        
        /* Stat card styling */
        .stat-card {
            background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
            padding: 2rem;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
            transition: all 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
        }
        
        .stat-value {
            font-size: 3rem;
            font-weight: 800;
            color: var(--primary-blue);
            margin: 0;
            line-height: 1;
        }
        
        .stat-label {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-top: 0.5rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Service category card */
        .service-category {
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid var(--accent-blue);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
            margin-bottom: 1rem;
        }
        
        .service-category h4 {
            color: var(--primary-blue);
            margin: 0 0 0.5rem 0;
            font-size: 1.2rem;
        }
        
        .service-category p {
            color: var(--text-secondary);
            margin: 0;
            font-size: 0.95rem;
        }
        
        /* Responsive adjustments */
        @media (max-width: 768px) {
            .hero-title {
                font-size: 2rem;
            }
            .hero-subtitle {
                font-size: 1.1rem;
            }
            .stat-value {
                font-size: 2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero_section() -> None:
    """Render the hero section with headline, metrics, and CTAs."""
    st.markdown(
        """
        <div class="hero-section">
            <h1 class="hero-title">Production-Grade AI Systems & Data Infrastructure</h1>
            <p class="hero-subtitle">
                19 Certifications | 1,768 Training Hours | 31 Services | Proven ROI
            </p>
            
            <div class="hero-metrics">
                <div class="hero-metric-badge">✅ 4,500+ Automated Tests</div>
                <div class="hero-metric-badge">⚡ 87% Efficiency Gains</div>
                <div class="hero-metric-badge">💰 $240K Annual Savings</div>
                <div class="hero-metric-badge">🏆 Production-Ready</div>
            </div>
            
            <div style="margin-top: 2rem;">
                <a href="#services" class="cta-button">View Services</a>
                <a href="#demo" class="cta-button cta-button-secondary">Request Demo</a>
                <a href="#case-studies" class="cta-button cta-button-secondary">See Case Studies</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_key_metrics() -> None:
    """Render key metrics in a professional grid layout."""
    st.markdown('<h2 class="section-header">Key Metrics</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-value">19</div>
                <div class="stat-label">Professional Certifications</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-value">1,768</div>
                <div class="stat-label">Hours Training</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col3:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-value">31</div>
                <div class="stat-label">Service Offerings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col4:
        st.markdown(
            """
            <div class="stat-card">
                <div class="stat-value">87%</div>
                <div class="stat-label">Efficiency Gains</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_case_study_highlights() -> None:
    """Render EnterpriseHub case study highlights."""
    st.markdown('<h2 class="section-header">Proven Results: EnterpriseHub Case Study</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="service-category">
                <h4>🎯 Performance Optimization</h4>
                <ul style="color: #7F8C8D; margin: 0.5rem 0;">
                    <li>89% token cost reduction through intelligent caching</li>
                    <li>87% cache hit rate (L1/L2/L3 architecture)</li>
                    <li>P95 latency < 2 seconds</li>
                    <li>99.9% uptime SLA achievement</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown(
            """
            <div class="service-category">
                <h4>💰 Cost Savings</h4>
                <ul style="color: #7F8C8D; margin: 0.5rem 0;">
                    <li>$240K annual AI infrastructure savings</li>
                    <li>3,200+ hours of manual work automated</li>
                    <li>$156K/year operational efficiency gains</li>
                    <li>ROI achieved in 4.2 months</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    with col2:
        st.markdown(
            """
            <div class="service-category">
                <h4>🤖 AI Orchestration</h4>
                <ul style="color: #7F8C8D; margin: 0.5rem 0;">
                    <li>Multi-LLM coordination (Claude, Gemini, Perplexity)</li>
                    <li>Autonomous agent mesh with self-healing</li>
                    <li>Real-time lead qualification (3 specialized bots)</li>
                    <li>Context-aware conversation intelligence</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.markdown(
            """
            <div class="service-category">
                <h4>📊 Business Intelligence</h4>
                <ul style="color: #7F8C8D; margin: 0.5rem 0;">
                    <li>80+ interactive Streamlit dashboard components</li>
                    <li>Real-time performance monitoring</li>
                    <li>Predictive analytics & churn detection</li>
                    <li>Executive briefing automation</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_service_categories() -> None:
    """Render service category overview."""
    st.markdown('<h2 class="section-header" id="services">Service Categories</h2>', unsafe_allow_html=True)
    
    services: List[Dict[str, str]] = [
        {
            "title": "🧠 AI & Machine Learning",
            "description": "Custom LLM integrations, RAG systems, conversational AI, agent orchestration, ML pipelines",
            "count": "8 services",
        },
        {
            "title": "📊 Data Infrastructure",
            "description": "Database design, ETL pipelines, caching strategies, real-time analytics, data governance",
            "count": "6 services",
        },
        {
            "title": "🎨 Dashboard & BI",
            "description": "Streamlit dashboards, executive reporting, KPI tracking, visualization design, user analytics",
            "count": "5 services",
        },
        {
            "title": "🔗 API & Integration",
            "description": "RESTful APIs, webhook handlers, CRM integrations, third-party connectors, microservices",
            "count": "4 services",
        },
        {
            "title": "🔒 Security & Compliance",
            "description": "Authentication systems, data encryption, regulatory compliance (GDPR, CCPA), audit trails",
            "count": "3 services",
        },
        {
            "title": "⚡ Performance Engineering",
            "description": "Load testing, caching optimization, database tuning, cost reduction, scalability planning",
            "count": "5 services",
        },
    ]
    
    col1, col2 = st.columns(2)
    
    for idx, service in enumerate(services):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            st.markdown(
                f"""
                <div class="service-category">
                    <h4>{service['title']}</h4>
                    <p>{service['description']}</p>
                    <p style="margin-top: 0.5rem; color: var(--primary-blue); font-weight: 600;">
                        {service['count']}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_navigation_tabs() -> None:
    """Render navigation tabs to other showcase sections."""
    st.markdown('<h2 class="section-header">Explore the Platform</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📜 Certifications",
            "🛠️ Services Portfolio",
            "📊 Case Studies",
            "📸 Screenshot Gallery",
            "📞 Contact & Demo",
        ]
    )
    
    with tab1:
        st.markdown("### Professional Certifications Showcase")
        st.info("📜 View the complete certifications showcase page for detailed credential verification.")
        
        cert_highlights: List[str] = [
            "**Google Cloud Professional** - Cloud Architect & Data Engineer",
            "**AWS Certified** - Solutions Architect & Developer",
            "**Microsoft Azure** - AI Engineer & Data Scientist",
            "**Machine Learning** - DeepLearning.AI Specializations",
            "**Data Engineering** - Apache Spark, Kafka, Airflow",
        ]
        
        for cert in cert_highlights:
            st.markdown(f"- {cert}")
        
        if st.button("🎓 View Full Certifications Page", key="cert_btn"):
            st.info("Navigate to: `/showcase_certifications` (to be implemented)")
    
    with tab2:
        st.markdown("### Service Portfolio Details")
        st.info("🛠️ Explore 31 specialized services across 6 categories with pricing and deliverables.")
        
        st.markdown("""
        **Service Tiers:**
        - **Starter** - $2,500-$5,000 (1-2 week delivery)
        - **Professional** - $5,000-$15,000 (2-4 week delivery)
        - **Enterprise** - $15,000-$50,000 (1-3 month delivery)
        - **Custom** - Quote-based (timeline varies)
        """)
        
        if st.button("📋 View Services Portfolio", key="services_btn"):
            st.info("Navigate to: `/showcase_services` (to be implemented)")
    
    with tab3:
        st.markdown("### Case Studies & Results")
        st.info("📊 Deep-dive case studies with technical implementation details and quantified outcomes.")
        
        case_studies: List[Dict[str, str]] = [
            {
                "title": "EnterpriseHub Real Estate AI",
                "result": "$240K annual savings, 87% efficiency gains",
                "tech": "FastAPI, Streamlit, PostgreSQL, Claude AI",
            },
            {
                "title": "Multi-Agent Orchestration System",
                "result": "89% token cost reduction, 3,200+ hours automated",
                "tech": "Agent mesh, RAG pipeline, Redis caching",
            },
        ]
        
        for cs in case_studies:
            st.markdown(f"**{cs['title']}**")
            st.markdown(f"- Result: {cs['result']}")
            st.markdown(f"- Tech Stack: {cs['tech']}")
            st.markdown("---")
        
        if st.button("📈 View Case Studies", key="case_btn"):
            st.info("Navigate to: `/showcase_case_studies` (to be implemented)")
    
    with tab4:
        st.markdown("### Screenshot Gallery")
        st.info("📸 Browse 80+ production screenshots showcasing dashboard UIs, analytics, and workflows.")
        
        st.markdown("""
        **Gallery Categories:**
        - Executive Dashboards
        - Real-Time Analytics
        - Conversation Intelligence
        - Performance Monitoring
        - API Integrations
        - Mobile Responsive Views
        """)
        
        if st.button("🖼️ View Screenshot Gallery", key="gallery_btn"):
            st.info("Navigate to: `/showcase_gallery` (to be implemented)")
    
    with tab5:
        st.markdown("### Request Demo or Consultation")
        
        with st.form("demo_request_form"):
            st.markdown("#### Contact Information")
            
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name *", placeholder="John Doe")
                email = st.text_input("Email Address *", placeholder="john@company.com")
            
            with col2:
                company = st.text_input("Company", placeholder="Acme Corp")
                role = st.selectbox(
                    "Role",
                    [
                        "Select...",
                        "CTO / VP Engineering",
                        "Product Manager",
                        "Engineering Manager",
                        "Data Scientist",
                        "Business Owner",
                        "Other",
                    ],
                )
            
            st.markdown("#### Project Details")
            
            service_interest = st.multiselect(
                "Services of Interest",
                [
                    "AI & Machine Learning",
                    "Data Infrastructure",
                    "Dashboard & BI",
                    "API & Integration",
                    "Security & Compliance",
                    "Performance Engineering",
                ],
            )
            
            project_timeline = st.selectbox(
                "Project Timeline",
                [
                    "Select...",
                    "Immediate (< 2 weeks)",
                    "Near-term (2-4 weeks)",
                    "Medium-term (1-3 months)",
                    "Long-term (3+ months)",
                    "Just exploring",
                ],
            )
            
            budget_range = st.selectbox(
                "Budget Range",
                [
                    "Select...",
                    "< $5,000",
                    "$5,000 - $15,000",
                    "$15,000 - $50,000",
                    "$50,000 - $100,000",
                    "$100,000+",
                    "Not sure yet",
                ],
            )
            
            message = st.text_area(
                "Project Description",
                placeholder="Tell us about your project, challenges, and goals...",
                height=150,
            )
            
            submit = st.form_submit_button("📨 Submit Demo Request", use_container_width=True)
            
            if submit:
                if not name or not email:
                    st.error("Please fill in required fields (Name and Email)")
                else:
                    st.success(
                        f"Thank you, {name}! Your demo request has been received. We'll contact you at {email} within 24 hours."
                    )
                    st.balloons()


def render_technical_highlights() -> None:
    """Render technical stack and achievements."""
    st.markdown('<h2 class="section-header">Technical Highlights</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        render_obsidian_metric(
            value="4,500+",
            label="Automated Tests",
            config=MetricConfig(variant="success", size="medium"),
            metric_icon="check-circle",
        )
        
        render_obsidian_metric(
            value="<2s",
            label="P95 Latency",
            config=MetricConfig(variant="premium", size="medium"),
            metric_icon="gauge-high",
        )
    
    with col2:
        render_obsidian_metric(
            value="99.9%",
            label="Uptime SLA",
            config=MetricConfig(variant="success", size="medium"),
            metric_icon="server",
        )
        
        render_obsidian_metric(
            value="140+",
            label="Microservices",
            config=MetricConfig(variant="default", size="medium"),
            metric_icon="network-wired",
        )
    
    with col3:
        render_obsidian_metric(
            value="89%",
            label="Cost Reduction",
            config=MetricConfig(variant="success", size="medium", trend="up"),
            metric_icon="dollar-sign",
        )
        
        render_obsidian_metric(
            value="80+",
            label="Dashboard Components",
            config=MetricConfig(variant="premium", size="medium"),
            metric_icon="chart-line",
        )


def render_footer() -> None:
    """Render professional footer with links."""
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; padding: 2rem; color: #7F8C8D;">
            <p style="margin-bottom: 1rem;">
                <strong>EnterpriseHub</strong> - Production-Grade AI Systems & Data Infrastructure
            </p>
            <p style="font-size: 0.9rem;">
                Built with FastAPI, Streamlit, PostgreSQL, Redis, Claude AI | 
                Open Source on GitHub | 
                Available for Consulting & Enterprise Licensing
            </p>
            <p style="font-size: 0.85rem; margin-top: 1rem;">
                © 2026 EnterpriseHub. All rights reserved.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_analytics() -> None:
    """Load Google Analytics tracking code (production placeholder)."""
    # ROADMAP-069: Replace with actual Google Analytics ID in production
    # Example: UA-XXXXXXXXX-X or G-XXXXXXXXXX
    ga_id = st.secrets.get("GOOGLE_ANALYTICS_ID", None) if hasattr(st, "secrets") else None

    if ga_id:
        st.markdown(
            f"""
            <!-- Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
            <script>
              window.dataLayer = window.dataLayer || [];
              function gtag(){{dataLayer.push(arguments);}}
              gtag('js', new Date());
              gtag('config', '{ga_id}');
            </script>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    """Main application entry point."""
    # Load analytics (if configured)
    load_analytics()

    # Load custom CSS
    load_custom_css()
    
    # Render hero section
    render_hero_section()
    
    # Key metrics grid
    render_key_metrics()
    
    # Case study highlights
    render_case_study_highlights()
    
    # Service categories
    render_service_categories()
    
    # Technical highlights
    render_technical_highlights()
    
    # Navigation tabs
    render_navigation_tabs()
    
    # Footer
    render_footer()


if __name__ == "__main__":
    main()
