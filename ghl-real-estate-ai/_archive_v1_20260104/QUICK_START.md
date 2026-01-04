# 🚀 Quick Start Guide

**Project:** GHL Real Estate AI
**Status:** ✅ Ready for Testing
**Location:** `/Users/cave/enterprisehub/ghl-real-estate-ai/`

---

## ⚡ 5-Minute Quick Start

### Step 1: Setup Environment (2 min)
```bash
cd /Users/cave/enterprisehub/ghl-real-estate-ai
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Configure API Keys (2 min)
```bash
cp .env.example .env
# Edit .env and add:
# - ANTHROPIC_API_KEY=sk-ant-xxxxx
# - GHL_API_KEY=your_key
# - GHL_LOCATION_ID=your_id
```

### Step 3: Load Data & Test (1 min)
```bash
python scripts/load_knowledge_base.py
pytest tests/ -v
uvicorn api.main:app --reload
```

### Step 4: Test Webhook
Open new terminal:
```bash
curl -X POST http://localhost:8000/api/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{"type":"InboundMessage","contactId":"test_123","locationId":"test","message":{"type":"SMS","body":"Looking for a house in Austin","direction":"inbound"},"contact":{"firstName":"Jane"}}'
```

---

## 📚 Full Documentation

- **SESSION_HANDOFF.md** - Complete handoff for next session
- **IMPLEMENTATION_SUMMARY.md** - Feature overview
- **README.md** - Full setup guide
- **RAILWAY_DEPLOYMENT_GUIDE.md** - Deployment steps

---

## 🆘 Troubleshooting

**Server won't start?**
```bash
# Check Python version (need 3.11+)
python --version

# Verify .env exists
cat .env
```

**Tests failing?**
```bash
# Ensure dependencies installed
pip list | grep -E "(fastapi|anthropic|chromadb)"
```

**Need API keys?**
- Anthropic: https://console.anthropic.com
- GHL: Your GHL account → Settings → API

---

**Ready to deploy?** See `RAILWAY_DEPLOYMENT_GUIDE.md`
