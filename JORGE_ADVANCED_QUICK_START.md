# Jorge's Advanced Features - Quick Start Guide

## 🚀 30-Second Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
export ANTHROPIC_API_KEY="your_claude_api_key"
export GHL_API_KEY="your_ghl_api_key"

# 3. Start services
python app.py &
python -m streamlit run ghl_real_estate_ai/streamlit_demo/app.py

# 4. Test system
curl http://localhost:8000/api/jorge-advanced/health
```

## 📱 Quick Test Examples

### Test Voice AI
```python
from ghl_real_estate_ai.services.voice_ai_handler import get_voice_ai_handler

handler = get_voice_ai_handler()
context = await handler.handle_incoming_call("+19095551234", "Test User")
response = await handler.process_voice_input(
    context.call_id,
    "I work for Amazon and need a home in Rancho Cucamonga",
    0.9
)
print(f"Jorge says: {response.text}")
```

### Test Marketing Automation
```python
from ghl_real_estate_ai.services.automated_marketing_engine import AutomatedMarketingEngine

engine = AutomatedMarketingEngine()
campaign = await engine.create_campaign_from_trigger(
    "high_qualified_call",
    {"employer": "Amazon", "timeline": "30_days"}
)
print(f"Campaign created: {campaign.campaign_id}")
```

### Test Client Retention
```python
from ghl_real_estate_ai.services.client_retention_engine import ClientRetentionEngine

engine = ClientRetentionEngine()
await engine.detect_life_event(
    "client_123",
    "job_change",
    {"new_employer": "Amazon"}
)
print("Life event processed!")
```

### Test Market Predictions
```python
from ghl_real_estate_ai.services.market_prediction_engine import MarketPredictionEngine

engine = MarketPredictionEngine()
prediction = await engine.predict_price_appreciation("Etiwanda", "1_year")
print(f"Price appreciation: {prediction.predicted_appreciation:.2%}")
```

## 🔗 Quick API Calls

```bash
# Voice AI - Start call
curl -X POST http://localhost:8000/api/jorge-advanced/voice/start-call \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+19095551234", "caller_name": "John Doe"}'

# Marketing - Create campaign
curl -X POST http://localhost:8000/api/jorge-advanced/marketing/create-campaign \
  -H "Content-Type: application/json" \
  -d '{"trigger_type": "new_listing", "target_audience": {"location": "Rancho Cucamonga"}}'

# Retention - Track referral
curl -X POST http://localhost:8000/api/jorge-advanced/retention/track-referral \
  -H "Content-Type: application/json" \
  -d '{"referrer_client_id": "client_123", "referred_contact_info": {"name": "Jane", "phone": "+1909555"}}'

# Market - Analyze neighborhood
curl -X POST http://localhost:8000/api/jorge-advanced/market/analyze \
  -H "Content-Type: application/json" \
  -d '{"neighborhood": "Etiwanda", "time_horizon": "1_year"}'

# Dashboard - Get metrics
curl http://localhost:8000/api/jorge-advanced/dashboard/metrics
```

## 📊 Key Endpoints

| Feature | Endpoint | Method |
|---------|----------|--------|
| Voice AI | `/api/jorge-advanced/voice/*` | POST/GET |
| Marketing | `/api/jorge-advanced/marketing/*` | POST/GET |
| Retention | `/api/jorge-advanced/retention/*` | POST/GET |
| Market Analysis | `/api/jorge-advanced/market/*` | POST/GET |
| Dashboard | `/api/jorge-advanced/dashboard/*` | GET |
| Health | `/api/jorge-advanced/health` | GET |

## 🔧 Common Configurations

### Voice AI Settings
```python
# In voice_profile.json
{
  "qualification_threshold": 70,
  "max_call_duration": 1800,
  "transfer_score": 80,
  "jorge_personality": "professional_friendly"
}
```

### Marketing Settings
```python
# Environment variables
MARKETING_DEFAULT_BUDGET=5000
MARKETING_AB_TEST_DURATION=14
MARKETING_BRAND_VOICE=jorge_professional
```

### Retention Settings
```python
# Client lifecycle settings
RETENTION_ENGAGEMENT_THRESHOLD=0.7
REFERRAL_REWARD_ENABLED=true
ANNIVERSARY_TRACKING=true
```

### Market Prediction Settings
```python
# ML model configuration
ML_MODEL_VERSION=v2.1
PREDICTION_CACHE_TTL=3600
MARKET_DATA_SOURCE=mls_api
```

## 🚨 Quick Troubleshooting

### Service Not Starting
```bash
# Check logs
tail -f /var/log/jorge/*.log

# Verify dependencies
python -c "import anthropic, fastapi, streamlit, redis, psycopg2"

# Check ports
netstat -tulpn | grep -E "(8000|8501)"
```

### API Errors
```bash
# Test health endpoint
curl http://localhost:8000/api/jorge-advanced/health

# Check module status
curl http://localhost:8000/api/jorge-advanced/health/modules

# Verify authentication
curl -H "X-Location-ID: your_id" -H "X-API-Key: your_key" \
  http://localhost:8000/api/jorge-advanced/health
```

### Performance Issues
```python
# Check cache status
import redis
r = redis.Redis()
print(r.info('memory'))

# Monitor database
SELECT * FROM pg_stat_activity WHERE application_name = 'jorge_advanced';

# Check ML model loading
from ghl_real_estate_ai.services.market_prediction_engine import MarketPredictionEngine
engine = MarketPredictionEngine()
print(engine.model_status)
```

## 📈 Monitoring Dashboard

Access the Streamlit dashboard at: http://localhost:8501

**Key Metrics to Watch:**
- Voice AI: Active calls, qualification scores
- Marketing: Campaign ROI, lead generation
- Retention: Client engagement, referral rates
- Market: Prediction accuracy, opportunity count

## 🎯 Production Checklist

- [ ] Environment variables set
- [ ] Database migrations applied
- [ ] Redis cache running
- [ ] API keys configured
- [ ] Health checks passing
- [ ] Monitoring setup
- [ ] Backup procedures in place
- [ ] Performance benchmarks met

## 📚 File Locations

```
Key Files:
├── ghl_real_estate_ai/services/
│   ├── voice_ai_handler.py           # Voice AI system
│   ├── automated_marketing_engine.py # Marketing automation
│   ├── client_retention_engine.py    # Client retention
│   ├── market_prediction_engine.py   # Market predictions
│   └── jorge_advanced_integration.py # Integration hub
├── ghl_real_estate_ai/api/routes/
│   └── jorge_advanced.py             # API endpoints
├── tests/
│   ├── services/test_*_handler.py    # Service tests
│   └── api/test_jorge_advanced_routes.py # API tests
└── JORGE_ADVANCED_FEATURES_INTEGRATION_GUIDE.md # Full docs
```

---

**Need Help?** Check the full integration guide or review the test files for detailed examples.

*Quick Start Version 1.0 | Last Updated: January 18, 2026*