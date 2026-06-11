# GHL Real Estate AI - Streamlit Demo

Interactive demo showcasing AI-powered lead qualification for real estate.

## Features

- 💬 **Chat Interface**: SMS-style conversation with AI agent
- 📊 **Lead Scoring**: Real-time lead qualification (0-100 score)
- 🏷️ **Auto-Tagging**: Automatic tag application based on conversation
- 🏠 **Property Matching**: RAG-powered property recommendations
- 📈 **Visual Dashboard**: Interactive gauges and charts

## Quick Start

### Local Development

```bash
# 1. Navigate to project root
cd /Users/cave/enterprisehub/ghl-real-estate-ai

# 2. Activate virtual environment
source venv/bin/activate

# 3. Run the app
streamlit run streamlit_demo/app.py
```

The app will open at `http://localhost:8501`

Alternative launch from this directory:

```bash
cd ghl_real_estate_ai/streamlit_demo
streamlit run app.py --server.port 8501
```

### Portfolio Showcase Pages

The app includes a "Portfolio Showcase" sidebar category with two pages:
- **Services Portfolio** (`services_portfolio.py`): service catalog with category/industry/price/timeline filters, backed by `data/services_data.py`
- **Case Studies** (`case_studies.py`): EnterpriseHub case study with metrics and timeline, backed by `data/case_studies_data.py`

### Try These Examples

**Cold Lead (Score: ~30)**
```
"Looking for a house in Rancho Cucamonga"
```

**Warm Lead (Score: ~50-60)**
```
"I have a budget of $400k and need 3 bedrooms"
```

**Hot Lead (Score: 70+)**
```
"I'm pre-approved for $400k, need to move ASAP, love Alta Loma"
```

**Objection Handling**
```
"Your prices are too high"
```

## Architecture

```
streamlit_demo/
├── app.py                    # Main application
├── components/               # UI components
│   ├── chat_interface.py    # SMS-style chat
│   ├── lead_dashboard.py    # Scoring & tags
│   └── property_cards.py    # Property matching
├── mock_services/           # Backend simulation
│   ├── mock_claude.py       # AI response patterns
│   ├── mock_rag.py          # Property search
│   └── conversation_state.py # State management
└── requirements.txt         # Dependencies
```

## How It Works

1. **User sends message** → Chat interface
2. **MockClaude extracts data** → Budget, location, timeline, etc.
3. **LeadScorer calculates score** → Uses actual production scorer
4. **Tags auto-applied** → Based on score + preferences
5. **MockRAG searches properties** → Matches from knowledge base
6. **Dashboard updates** → Real-time visualization

## Deployment

### Streamlit Cloud

1. Push code to GitHub
2. Go to https://share.streamlit.io
3. Connect repository
4. Select `streamlit_demo/app.py` as main file
5. Deploy!

### Environment Variables

No API keys needed for demo - fully self-contained.

## Production Integration

This demo uses:
- **Real LeadScorer**: Production-grade scoring algorithm
- **Real Property Data**: Actual listings from knowledge base
- **Mock API**: Simulated Claude responses (replace with real API for production)

To convert to production:
1. Replace `MockClaudeService` with real Anthropic API calls
2. Connect to live CRM (GHL API)
3. Deploy backend API
4. Update property data source

## Testing

All components tested and verified:
- ✅ Mock services work correctly
- ✅ Lead scorer integration successful
- ✅ Property matching accurate
- ✅ UI renders properly
- ✅ State management functional

## Support

For questions or issues, contact the development team.

---

**Built with Claude Sonnet 4.5** | **Demo Version 1.0**
