"""
Case Studies Data
EnterpriseHub implementation
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
                {
                    "metric": "Manual Review Time Reduction",
                    "value": "87%",
                    "detail": "From 20+ hrs/week to <3 hrs/week",
                },
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
}
