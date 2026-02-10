"""
Case Studies Data
EnterpriseHub and AgentForge implementations
"""

CASE_STUDIES = {
    "enterprisehub": {
        "title": "EnterpriseHub: Real Estate AI Transformation",
        "subtitle": "87% reduction in manual review time, $240,000 annual savings",
        "client_industry": "Real Estate",
        "client_size": "Mid-market",
        "challenge": {
            "title": "Manual Lead Qualification Bottleneck",
            "description": "Manual lead qualification consuming 20+ hours/week with inconsistent quality. No predictive analytics for conversion probability. Limited visibility into bot performance and conversation quality. Token costs spiraling without optimization.",
            "pain_points": [
                "20+ hours/week spent on manual lead review",
                "Inconsistent lead qualification quality",
                "No conversion probability insights",
                "High token costs without optimization",
                "Limited bot performance visibility",
                "Slow response times to hot leads",
            ],
        },
        "solution": {
            "title": "Multi-Agent AI System with RAG and Predictive Analytics",
            "description": "Production-grade multi-agent AI system orchestrating lead qualification, buyer/seller bots, and intelligent handoff workflows with full observability.",
            "components": [
                "Custom RAG system with vector database (Chroma)",
                "Multi-agent orchestration (Lead/Buyer/Seller bots)",
                "Predictive analytics and lead scoring ML models",
                "Three-tier caching system (L1/L2/L3)",
                "Real-time BI dashboards (Streamlit)",
                "Automated workflow engine with GHL integration",
                "Performance monitoring and alerting system",
            ],
        },
        "technical_stack": {
            "backend": ["FastAPI (async)", "Python 3.11", "PostgreSQL", "Redis", "Alembic migrations"],
            "ai_ml": ["Claude API", "Gemini API", "Perplexity API", "LangChain", "Scikit-Learn", "XGBoost"],
            "infrastructure": ["Docker Compose", "Vector database (Chroma)", "Three-tier cache (L1/L2/L3)"],
            "integrations": ["GoHighLevel CRM", "Stripe", "Webhook system", "REST APIs"],
            "bi_dashboards": ["Streamlit", "Plotly", "80+ dashboard components"],
            "testing": ["Pytest", "4,500+ automated tests", "95%+ code coverage"],
        },
        "architecture": {
            "description": "Microservices-based architecture with async processing and intelligent caching",
            "key_features": [
                "140+ services with single responsibility design",
                "Async/await for I/O operations",
                "Three-tier caching (L1 memory, L2 Redis, L3 fallback)",
                "Agent mesh coordinator for governance and routing",
                "Multi-strategy parsing with fallback chains",
                "Real-time webhook processing",
                "Automated testing and CI/CD integration",
            ],
        },
        "outcomes": {
            "primary_metrics": [
                {"metric": "Manual Review Time Reduction", "value": "87%", "detail": "From 20+ hrs/week to <3 hrs/week"},
                {"metric": "Annual Cost Savings", "value": "$240,000", "detail": "Labor + token cost optimization"},
                {"metric": "Token Cost Reduction", "value": "89%", "detail": "Through intelligent caching"},
                {"metric": "Cache Hit Rate", "value": "87%", "detail": "L1/L2/L3 combined performance"},
                {"metric": "P95 Latency", "value": "<2 seconds", "detail": "AI response time"},
                {"metric": "Qualified Lead Increase", "value": "3x", "detail": "From predictive scoring"},
            ],
            "secondary_metrics": [
                "95%+ code coverage with 4,500+ automated tests",
                "140+ services orchestrated via agent mesh",
                "80+ BI dashboard components for real-time insights",
                "Zero-downtime deployments with Docker Compose",
                "Automated lead temperature tagging (Hot/Warm/Cold)",
                "Cross-bot handoff with circular prevention",
            ],
        },
        "implementation": {
            "timeline": "10-14 business days",
            "phases": [
                {
                    "phase": "Phase 1: Discovery and Architecture",
                    "duration": "2 days",
                    "deliverables": [
                        "Technical architecture design",
                        "Database schema and models",
                        "API endpoint specification",
                        "Caching strategy definition",
                    ],
                },
                {
                    "phase": "Phase 2: Core RAG System",
                    "duration": "3 days",
                    "deliverables": [
                        "Vector database setup (Chroma)",
                        "Document ingestion pipeline",
                        "Semantic search optimization",
                        "Claude orchestration service",
                    ],
                },
                {
                    "phase": "Phase 3: Multi-Agent Workflows",
                    "duration": "3 days",
                    "deliverables": [
                        "Lead/Buyer/Seller bot implementations",
                        "Intent decoder with GHL enhancement",
                        "Handoff service with safeguards",
                        "Agent mesh coordinator",
                    ],
                },
                {
                    "phase": "Phase 4: BI Dashboards and Optimization",
                    "duration": "2-3 days",
                    "deliverables": [
                        "80+ Streamlit dashboard components",
                        "Performance monitoring system",
                        "Alerting and analytics",
                        "Testing suite (4,500+ tests)",
                    ],
                },
            ],
        },
        "testimonial": {
            "quote": "The multi-agent system transformed our lead qualification process. We went from 20+ hours of manual work per week to under 3 hours, while actually improving lead quality. The predictive analytics gave us insights we never had before.",
            "author": "Operations Manager",
            "company": "EnterpriseHub",
        },
        "technologies_used": [
            "FastAPI",
            "PostgreSQL",
            "Redis",
            "Claude API",
            "Gemini API",
            "Perplexity API",
            "LangChain",
            "Chroma",
            "Streamlit",
            "Docker",
            "Pytest",
        ],
    },
    "agentforge": {
        "title": "AgentForge: AI-Powered Lead Qualification",
        "subtitle": "3x increase in qualified leads, 45% improvement in response rates",
        "client_industry": "B2B SaaS",
        "client_size": "Growth-stage startup",
        "challenge": {
            "title": "Low Conversion from Cold Outreach",
            "description": "High volume of inbound leads with low conversion rates. Manual response process causing delays and inconsistent follow-up. No intelligent lead prioritization.",
            "pain_points": [
                "Low conversion rates from cold outreach",
                "Delayed response times to inbound leads",
                "Inconsistent follow-up workflows",
                "No lead prioritization system",
                "Manual qualification consuming sales time",
                "Limited visibility into lead quality",
            ],
        },
        "solution": {
            "title": "AI-Powered Lead Qualification and Response Automation",
            "description": "Intelligent multi-agent system handling lead qualification, automated responses, and intelligent follow-up workflows.",
            "components": [
                "Multi-agent workflow system (CrewAI)",
                "Lead enrichment and research agents",
                "Automated response generation",
                "Follow-up workflow orchestration",
                "Lead scoring ML model",
                "CRM integration (HubSpot)",
            ],
        },
        "technical_stack": {
            "backend": ["Python 3.11", "FastAPI", "PostgreSQL"],
            "ai_ml": ["CrewAI", "Claude API", "LangChain", "Scikit-Learn"],
            "integrations": ["HubSpot CRM", "Zapier", "Slack"],
            "testing": ["Pytest", "300+ automated tests"],
        },
        "architecture": {
            "description": "Multi-agent workflow orchestrating lead research, qualification, and outreach",
            "key_features": [
                "Agent 1: Lead scraping and enrichment",
                "Agent 2: Company research and analysis",
                "Agent 3: Personalized outreach generation",
                "Agent 4: Follow-up scheduling and tracking",
                "Human-in-the-loop checkpoints for high-value leads",
                "Full audit trail of agent decisions",
            ],
        },
        "outcomes": {
            "primary_metrics": [
                {"metric": "Qualified Lead Increase", "value": "3x", "detail": "From 100 to 300 leads/month"},
                {"metric": "Response Rate Improvement", "value": "45%", "detail": "Through personalization"},
                {"metric": "Time Saved", "value": "85%", "detail": "On lead qualification"},
                {"metric": "Follow-up Consistency", "value": "100%", "detail": "Automated workflows"},
            ],
            "secondary_metrics": [
                "200 leads/day processing capacity",
                "340 hours/week saved on manual qualification",
                "Real-time lead quality scoring",
                "Automated CRM field updates",
                "Slack notifications for hot leads",
            ],
        },
        "implementation": {
            "timeline": "5-7 business days",
            "phases": [
                {
                    "phase": "Phase 1: Multi-Agent Setup",
                    "duration": "2 days",
                    "deliverables": [
                        "CrewAI orchestration framework",
                        "Agent definitions and coordination",
                        "Error handling and retry logic",
                    ],
                },
                {
                    "phase": "Phase 2: Lead Scoring Model",
                    "duration": "2 days",
                    "deliverables": [
                        "Historical data analysis",
                        "ML model training (XGBoost)",
                        "Prediction API deployment",
                    ],
                },
                {
                    "phase": "Phase 3: Integration and Testing",
                    "duration": "1-3 days",
                    "deliverables": [
                        "HubSpot CRM integration",
                        "Slack notification system",
                        "Automated test suite (300+ tests)",
                    ],
                },
            ],
        },
        "testimonial": {
            "quote": "The multi-agent system completely transformed our outbound process. We're now processing 3x more leads with the same team size, and our response rates have never been better. The ROI was immediate.",
            "author": "Head of Sales",
            "company": "AgentForge",
        },
        "technologies_used": [
            "Python",
            "FastAPI",
            "CrewAI",
            "Claude API",
            "PostgreSQL",
            "HubSpot",
            "Zapier",
            "Scikit-Learn",
        ],
    },
}
