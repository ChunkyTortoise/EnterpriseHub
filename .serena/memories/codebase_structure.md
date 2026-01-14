# Codebase Structure Overview

## Root Directory
```
EnterpriseHub/
├── app.py                          # Main entry point (redirects to Elite v4.0)
├── requirements.txt                # Production dependencies
├── Makefile                        # Development commands
├── pyproject.toml                  # Project configuration
├── docker-compose.yml              # Container orchestration
├── .env.example                    # Environment template
└── README.md                       # Project documentation
```

## Core Application (Elite v4.0)
```
ghl_real_estate_ai/
├── streamlit_demo/
│   ├── app.py                      # Main Streamlit application (3K+ lines)
│   ├── components/                 # 26+ UI components
│   │   ├── lead_intelligence_hub.py    # Main lead analysis interface
│   │   ├── property_matcher_ai.py      # AI-powered property matching
│   │   ├── interactive_lead_map.py     # Geographic lead visualization
│   │   ├── conversation_simulator.py   # AI chat simulation
│   │   ├── executive_dashboard.py      # Executive metrics
│   │   └── ui_elements.py              # Reusable UI components
│   ├── services/                   # Business logic layer
│   │   ├── claude_assistant.py         # Claude AI integration
│   │   ├── lead_scorer.py              # Lead scoring algorithms
│   │   └── ai_predictive_lead_scoring.py
│   └── pages/                      # Additional page modules
├── services/                       # Core backend services
├── agent_system/                   # Agent orchestration
└── api/                           # FastAPI backend
```

## Data & Configuration
```
data/
├── marketplace/                    # GHL marketplace integrations
├── memory/                         # Agent memory storage (deleted in git)
├── workflows/                      # Automation workflows
├── dashboard_state/                # UI state persistence
├── telemetry/                      # Analytics data
└── tenants/                        # Multi-tenant configurations
```

## Testing Infrastructure
```
tests/
├── test_lead_scorer.py
├── test_property_matcher.py
├── test_claude_integration.py
└── ...                            # 517+ automated tests
```

## Documentation & Deployment
```
docs/                              # Technical documentation
.github/workflows/                 # CI/CD pipelines
.devcontainer/                     # Development environment
scripts/                           # Utility scripts
```

## Key Components by Function

### Lead Intelligence (Core Value)
- `lead_intelligence_hub.py`: Main command center with 8 tabs
- `interactive_lead_map.py`: Geographic visualization with CRM sync
- `segmentation_pulse.py`: Smart lead segmentation with AI insights
- `conversion_predictor.py`: ML-powered conversion forecasting

### Property Matching (AI Engine)
- `property_matcher_ai.py`: Claude-powered matching with 15 factors
- `property_cards.py`: Visual property presentation
- `neighborhood_intelligence.py`: Market context analysis

### Executive & Analytics
- `executive_dashboard.py`: C-suite metrics and KPIs
- `performance_dashboard.py`: Operational analytics
- `churn_early_warning_dashboard.py`: Predictive customer retention

### AI & Automation
- `claude_assistant.py`: Persistent AI reasoning
- `automation_studio.py`: Workflow design interface
- `ai_behavioral_tuning.py`: AI personality configuration

### Integration & Communication
- `ghl_status_panel.py`: GHL webhook monitoring
- `conversation_simulator.py`: AI chat testing
- `voice_intelligence.py`: Call analysis and insights